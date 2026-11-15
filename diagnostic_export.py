"""Bounded, reference-free diagnostic ZIPs. No extraction or inference is run."""
from __future__ import annotations
import hashlib
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

MAX_SOURCE_BYTES = 20 * 1024 * 1024
_DROP = re.compile(r'(secret|credential|password|authorization|api[_-]?key|private[_-]?key|raw[_-]?prompt|system[_-]?prompt|transcript|checkpoint|expected|reference|ground[_-]?truth|grading|gold)', re.I)
_PATH = re.compile(r'(?<!\w)(?:/(?:home|tmp|root|mnt|media|Users|var)/[^\s\"\'<>;,)]*|[A-Za-z]:\\[^\s\"\'<>;,)]*)')

def _hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def sanitize(value):
    """Remove private fields recursively; retain token *usage*, never tokens."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            name = str(key)
            lower = name.lower()
            if _DROP.search(name) or lower in {'prompt', 'prompts', 'headers', 'token', 'access_token', 'refresh_token', 'id_token', 'raw_response', 'provider_response', 'request_payload', 'response_payload', 'gemini_cache', 'cloud_cache', 'transcripts', 'logs'}:
                continue
            if ('token' in lower and not any(part in lower for part in ('usage', 'count', 'tokens', 'limit', 'budget'))):
                continue
            if lower.endswith(('path', 'paths', 'directory', 'directories')):
                continue
            result[name] = sanitize(item)
        return result
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        return _PATH.sub('[private path]', value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)

def build_archive(job, source_path, preview_path, output_dir) -> Path:
    """Export supplied results and a supplied preview; never load an AI model.

    Original source is included only for PNG/JPEG/PDF at <=20 MiB. Evidence
    coordinates are copied unchanged. The annotation uses the same preview and
    box coordinate contract as the application's existing PNG export.
    """
    source, preview, out = Path(source_path), Path(preview_path), Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    source_hash = _hash(source)
    prediction = sanitize(job.get('prediction', {}))
    review = sanitize(job.get('review', {}))
    payload = {
        'schema': 'proofplan.diagnostic.v1',
        'query': sanitize(job.get('question', '')),
        'input': {'sha256': source_hash, 'kind': job.get('input_kind'),
                  'bytes': source.stat().st_size, 'pages': sanitize(job.get('pages', []))},
        'configuration': sanitize(job.get('configuration', job.get('config', {}))),
        'original_prediction': prediction,
        'human_review': review,
        'local_evidence_catalog': sanitize(job.get('evidence_catalog', [])),
        'hybrid_evidence': sanitize(job.get('hybrid_evidence', [])),
        'hybrid_view_boxes': sanitize(job.get('hybrid_view_boxes', [])),
        'credit': sanitize(job.get('credit', 'Attribution not provided')),
        'warnings': ['Original model outcomes and human review are separate. Detector scores are not probabilities.',
                     'Overlay uses the supplied preview coordinate system; source-coordinate evidence remains unchanged in JSON.'],
    }
    key_material = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()
    digest = hashlib.sha256(key_material).hexdigest()
    target = out / ('diagnostic-' + source_hash[:12] + '-' + digest[:20] + '.zip')
    if target.is_file():
        return target
    with tempfile.TemporaryDirectory(prefix='diagnostic-', dir=out) as temp:
        temp = Path(temp)
        members = {}
        extension = source.suffix.lower()
        if extension in {'.png', '.jpg', '.jpeg', '.pdf'} and source.stat().st_size <= MAX_SOURCE_BYTES:
            members['source' + extension] = source
            payload['input']['source_included'] = True
        else:
            payload['input']['source_included'] = False
            payload['warnings'].append('Original source omitted: unsupported archive format or over 20 MiB.')
        if preview.is_file():
            from PIL import Image
            with Image.open(preview) as image:
                width, height = image.size
                if width * height > 20_000_000:
                    raise ValueError('Diagnostic preview exceeds bounded 20 MP rendering budget')
            from detector import render
            boxes = [b for b in review.get('boxes', []) if b.get('page', 1) == 1 and isinstance(b.get('xyxy'), list)]
            overlay = temp / 'local-evidence.png'
            render(preview, boxes, overlay, payload['credit'],
                   'Human-reviewed Local evidence' if review.get('reviewed') else 'Local model/tool evidence')
            members['local-evidence.png'] = overlay
            if job.get('hybrid_view_boxes'):
                hybrid_overlay=temp/'hybrid-evidence.png'
                render(preview,job['hybrid_view_boxes'],hybrid_overlay,payload['credit'],'Hybrid cited source evidence; proposals unverified')
                members['hybrid-evidence.png']=hybrid_overlay
            payload['input']['preview_dimensions'] = [width, height]
        else:
            payload['warnings'].append('No supplied preview available; JSON evidence remains available.')
        metadata = temp / 'diagnostic.json'
        metadata.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
        members['diagnostic.json'] = metadata
        archive = temp / 'archive.zip'
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as handle:
            for name, path in members.items():
                handle.write(path, arcname=name)
        os.replace(archive, target)
    return target
