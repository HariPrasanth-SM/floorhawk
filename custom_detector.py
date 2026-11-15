"""Supplied YOLO11m adapter, opt-in only; never reads questions/references.

The supplied weights stay outside source Git. ``infer`` is one model forward;
``parse`` adds a content/configuration/device cache. Callers using the existing
host GPU queue already hold the advisory lock and must pass acquire_lock=False.
"""
import contextlib
import copy
import gc
import hashlib
import importlib.metadata
import json
import math
import os
import threading
import time
from pathlib import Path

from qa.common import ROOT, inference_lock, sha, write_json
from runtime_paths import CACHE_ROOT, MODEL_ROOT

VERSION = 'custom-yolo11m-v1'
WEIGHT_SHA256 = '95fd78b75b72f50963c03d710dbd38b9c7259e21e141c019f58ab7fbb57e54ea'
RAW_CLASSES = ['electrical_appliance', 'door', 'bathtub', 'shower', 'window',
               'sauna_bench', 'stairs', 'toilet', 'sink']
CLASS_ALIASES = {'toilet': 'toilet_fixture', 'stairs': 'stair'}
QUESTION_CLASSES = {
    'door': ['door'], 'window': ['window'], 'toilet_fixture': ['toilet_fixture'],
    'sink': ['sink'], 'shower_bath': ['shower', 'bathtub'],
    'shower': ['shower'], 'bathtub': ['bathtub'], 'stair': ['stair'],
}
SETTINGS = {'imgsz': 1024, 'conf': .4, 'iou': .7, 'max_det': 500,
            'batch': 1, 'preprocess': 'Ultralytics YOLO letterbox; source-pixel result boxes',
            'profile': 'supplied README author defaults, not benchmark tuned'}
LICENSE = 'CubiCasa-derived CC BY-NC-SA4.0/non-commercial per supplied README; Ultralytics AGPL-3.0'
_MODEL = None
_MODEL_KEY = None
_MODEL_LOCK = threading.RLock()


def weights_path():
    configured = os.environ.get('PROOFPLAN_CUSTOM_YOLO_WEIGHTS')
    if configured:
        return Path(configured).expanduser().resolve()
    restored = MODEL_ROOT / 'custom-yolo/floorplan_yolo11m.pt'
    return restored if restored.is_file() else ROOT.parent / 'floorplan_detector/floorplan_yolo11m.pt'


def model_info():
    path = weights_path()
    if not path.is_file():
        raise FileNotFoundError('Custom YOLO weights absent; set PROOFPLAN_CUSTOM_YOLO_WEIGHTS or restore the supplied detector asset')
    digest = sha(path)
    if digest != WEIGHT_SHA256:
        raise ValueError('Custom YOLO checksum differs from the inspected supplied checkpoint')
    return {
        'name': 'Supplied floorplan YOLO11m', 'weight_sha256': digest,
        'weight_bytes': path.stat().st_size, 'source': 'user supplied floorplan_detector',
        'revision': 'supplied checkpoint epoch29 per README; no source Git revision supplied',
        'class_map': dict(enumerate(RAW_CLASSES)), 'license': LICENSE,
        'training_domain': 'CubiCasa5K4200 Finnish real-estate plans per supplied README',
        'training_overlap': 'Exact source memberships unavailable; potential overlap with quick development and pretrained backbones. Not held-out evidence.',
        'source_pixel_coordinates': True,
    }


def _device(device):
    value = str(device)
    if value in ('0', 'cuda', 'cuda:0'):
        if os.environ.get('PROOFPLAN_IN_HOST') != '1':
            raise ValueError('Custom YOLO CUDA execution must use the existing authenticated host worker queue')
        return 'cuda:0'
    if value != 'cpu':
        raise ValueError('Supported devices are cpu or the admitted host cuda:0')
    return value


def _names(names):
    actual = [str(names[i]) for i in range(len(names))] if isinstance(names, dict) else list(names)
    if actual != RAW_CLASSES:
        raise ValueError('Checkpoint class identities do not match the audited supplied YOLO11m class contract')
    return actual


def entities_from_rows(boxes, classes, scores, names, image_size, source_hash):
    """Pure validation/translation; Ultralytics already maps letterbox boxes back."""
    names = _names(names)
    width, height = image_size
    if not (len(boxes) == len(classes) == len(scores)):
        raise ValueError('Mismatched prediction vectors')
    entities = []
    for index, (coords, cls, score) in enumerate(zip(boxes, classes, scores), 1):
        if type(cls) not in (int, float) or not math.isfinite(cls) or int(cls) != cls or not 0 <= int(cls) < len(names):
            raise ValueError('Invalid custom detector class ID')
        if len(coords) != 4 or any(type(v) not in (int, float) or not math.isfinite(v) for v in coords):
            raise ValueError('Invalid custom detector coordinates')
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError('Invalid custom detector score')
        x1, y1, x2, y2 = coords
        # Small FP roundoff may place an edge just outside the source; never pad.
        box = [max(0., min(float(width), x1)), max(0., min(float(height), y1)),
               max(0., min(float(width), x2)), max(0., min(float(height), y2))]
        if not box[0] < box[2] or not box[1] < box[3]:
            raise ValueError('Custom detector returned an empty source region')
        original = names[int(cls)]
        entities.append({
            'id': f'custom-yolo-{index}', 'kind': 'detected_instance',
            'class': CLASS_ALIASES.get(original, original), 'original_class': original,
            'class_id': int(cls), 'bbox': box, 'score': float(score), 'page': 1,
            'coordinate_system': 'original image pixels', 'source_sha256': source_hash,
            'model': 'Supplied floorplan YOLO11m', 'weight_sha256': WEIGHT_SHA256,
            'method': 'custom_yolo11m',
            'provenance': 'Supplied YOLO11m detection; detector score is not a calibrated probability or completeness claim',
        })
    return entities


def counts_for(entities):
    counts = {}
    for entity in entities:
        counts[entity['class']] = counts.get(entity['class'], 0) + 1
    return counts, {target: sum(counts.get(cls, 0) for cls in classes)
                    for target, classes in QUESTION_CLASSES.items()}


def _admission(device):
    from v2.supervisor import Admission, sample, fresh_host
    telemetry = fresh_host() if device.startswith('cuda') else sample(gpu=False)
    decision = Admission().check(telemetry, device.startswith('cuda'))
    if decision != 'admit':
        raise RuntimeError('Custom YOLO resource admission: ' + decision)


def _load(path, device):
    global _MODEL, _MODEL_KEY
    key = (str(path), WEIGHT_SHA256, device)
    if _MODEL is None or _MODEL_KEY != key:
        release()
        from ultralytics import YOLO
        _MODEL = YOLO(str(path))
        _names(_MODEL.names)
        _MODEL_KEY = key
    return _MODEL


def infer(file, device='cpu', acquire_lock=True):
    """Run one admitted uncached forward; no counting/routing policy is installed."""
    source = Path(file)
    selected = _device(device)
    info = model_info()
    from PIL import Image
    with Image.open(source) as image:
        if image.width * image.height > 30_000_000:
            raise ValueError('Use original-resolution bounded tiles for sources over30MP; custom detector does not silently reduce the whole large sheet')
    _admission(selected)
    started = time.perf_counter()
    context = inference_lock() if acquire_lock else contextlib.nullcontext()
    if not acquire_lock and os.environ.get('PROOFPLAN_IN_HOST') != '1':
        raise ValueError('Only the authenticated host path may rely on the caller-owned inference lock')
    with context, _MODEL_LOCK:
        import torch
        torch.set_num_threads(2)
        if selected.startswith('cuda'):
            torch.cuda.reset_peak_memory_stats()
        cold = _MODEL is None or _MODEL_KEY != (str(weights_path()), WEIGHT_SHA256, selected)
        loading_start = time.perf_counter()
        model = _load(weights_path(), selected)
        loading = time.perf_counter() - loading_start
        observed = set()
        def capture(module, args):
            for value in args:
                if isinstance(value, torch.Tensor):
                    observed.add(str(value.device))
        hook = model.model.register_forward_pre_hook(capture)
        infer_start = time.perf_counter()
        try:
            prediction = model.predict(str(source), imgsz=1024, conf=.4, iou=.7,
                                       max_det=500, batch=1, device=selected,
                                       verbose=False, save=False)[0]
            if selected.startswith('cuda'):
                torch.cuda.synchronize()
        finally:
            hook.remove()
        seconds = time.perf_counter() - infer_start
        actual = str(next(model.model.parameters()).device)
        if selected not in observed:
            raise RuntimeError('Requested model input device was not observed in the actual custom YOLO forward')
        source_hash = sha(source)
        image_size = [int(prediction.orig_shape[1]), int(prediction.orig_shape[0])]
        entities = entities_from_rows(prediction.boxes.xyxy.tolist(), prediction.boxes.cls.tolist(),
                                      prediction.boxes.conf.tolist(), model.names, image_size, source_hash)
        counts, question_counts = counts_for(entities)
        execution = {'device': actual, 'observed_tensor_devices': sorted(observed),
                     'executing_pid': os.getpid(), 'model': 'custom_yolo11m', 'cache_hit': False,
                     'peak_gpu_memory_bytes': torch.cuda.max_memory_allocated() if selected.startswith('cuda') else None}
        return {'kind': 'raster', 'version': VERSION, 'source_sha256': source_hash,
                'image_size': image_size, 'entities': entities, 'counts': counts,
                'question_counts': question_counts, 'model': info, 'settings': dict(SETTINGS, device=selected),
                'class_map': dict(enumerate(RAW_CLASSES)), 'execution': execution,
                'device': actual, 'cache_hit': False,
                'timing': {'model_loading_seconds': loading, 'inference_seconds': seconds,
                           'total_seconds': time.perf_counter() - started, 'cold_model': cold},
                'warnings': ['Native sauna_bench detections are not sauna-room counts.',
                             'Source-domain/training overlap is uncertain; detections are unverified evidence, not complete inventory.']}


def parse(file, device='cpu', use_cache=True):
    """Content/config/model/device cache, preserving original execution separately."""
    source = Path(file)
    selected = _device(device)
    info = model_info()
    identity = {'source_sha256': sha(source), 'weight_sha256': info['weight_sha256'],
                'version': VERSION, 'adapter_sha256': sha(__file__), 'settings': SETTINGS,
                'ultralytics_version': importlib.metadata.version('ultralytics'), 'device': selected}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    cache = CACHE_ROOT / 'custom-yolo11m' / (key + '.json')
    started = time.perf_counter()
    if use_cache and cache.is_file():
        result = json.loads(cache.read_text())
        result['cache_hit'] = True
        result['execution'] = dict(result['execution'], cache_hit=True)
        result['retrieval_seconds'] = time.perf_counter() - started
        result['cache_identity'] = identity
        return result
    result = infer(source, selected)
    result['cache_identity'] = identity
    write_json(cache, result)
    return result


def answer(facts, target):
    """Optional count proposal from cached facts; no automatic baseline override."""
    if target not in QUESTION_CLASSES:
        return {'status': 'unsupported', 'answer': None, 'unit': None, 'evidence': [],
                'warnings': ['Requested target is not a direct custom YOLO class/count mapping. Sauna benches do not establish sauna-room counts.']}
    selected = [copy.deepcopy(e) for e in facts['entities'] if e['class'] in QUESTION_CLASSES[target]]
    return {'status': 'success', 'answer': len(selected), 'unit': 'count', 'evidence': selected,
            'route': 'custom.yolo11m.count-proposal', 'model': facts['model'],
            'warnings': list(facts.get('warnings', [])),
            'calculation_trace': [{'operation': 'count_unique_included_entities',
                                   'entity_ids': [e['id'] for e in selected], 'value': len(selected)}]}


def release():
    global _MODEL, _MODEL_KEY
    with _MODEL_LOCK:
        had_cuda = _MODEL_KEY is not None and str(_MODEL_KEY[-1]).startswith('cuda')
        _MODEL = None
        _MODEL_KEY = None
        gc.collect()
        if had_cuda:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
