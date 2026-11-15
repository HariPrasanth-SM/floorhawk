"""Offline final-evaluation reporting after the owned inference process stops.

Never imported by inference. Does not alter grading, routes or predictions.
"""
import collections
import hashlib
import json
import statistics
from datetime import datetime
from pathlib import Path

from campaign.clock import atomic, now
from campaign.score import evaluate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/overnight-20261115'


def read_rows(path):
    return [json.loads(line) for line in Path(path).open() if line.strip()]


def main():
    task = json.loads((OUT / 'tasks/final_local_cpu.json').read_text())
    if task['status'] == 'running':
        raise RuntimeError('Final inference is still running; no interim score inspection')
    dest = OUT / 'final-local'
    sources = [json.loads(p.read_text()) for p in sorted((dest / 'sources').glob('*.json'))]
    rows = [r for source in sources for r in source['rows']]
    if len({r['sample_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate checkpoint IDs')
    if any(r['source_commit'] != '5827eab5e423bae3eb7413a2c773183afa2f60f0' for r in rows):
        raise ValueError('Mixed inference versions')
    # A process interrupted between its atomic source checkpoint and aggregate
    # checkpoint must not lose those real results. Preserve the earlier aggregate.
    predictions = dest / 'predictions.from-source-checkpoints.jsonl'
    predictions.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    answers = OUT / 'evaluation-only/final.answers.jsonl'
    manifest = OUT / 'final-eligibility/questions.jsonl'
    qs = read_rows(manifest)
    ids = {r['sample_id'] for r in rows}
    if ids - {q['sample_id'] for q in qs}:
        raise ValueError('Unexpected prediction ID')
    completed = dest / 'recorded.questions.jsonl'
    completed.write_text(''.join(json.dumps(q, ensure_ascii=False) + '\n' for q in qs if q['sample_id'] in ids))
    reports = {}
    for label, path in {
        'all_eligible': manifest,
        'recorded_subset': completed,
        'known_unexposed': OUT / 'final-eligibility/known-unexposed.questions.jsonl',
        'unknown_custom_overlap': OUT / 'final-eligibility/unknown-custom-overlap.questions.jsonl',
    }.items():
        reports[label] = evaluate(predictions, path, answers, dest / 'metrics' / label)
    source_seconds = [call['source_seconds'] for source in sources for call in source['source_calls']]
    query_seconds = [r['evaluation_query_seconds'] for r in rows if isinstance(r.get('evaluation_query_seconds'), (int, float))]
    telemetry = read_rows(OUT / 'final-resources.jsonl')
    resumed = OUT / 'final-resources-resume.jsonl'
    if resumed.exists():
        telemetry += read_rows(resumed)
    telemetry.sort(key=lambda r: r['time'])
    gaps = [{'after_epoch': a['time'], 'before_epoch': b['time'], 'seconds': b['time'] - a['time']}
            for a, b in zip(telemetry, telemetry[1:]) if b['time'] - a['time'] > 5]
    main_summary = reports['all_eligible']['summary']
    detailed = read_rows(dest / 'metrics/all_eligible/rows.jsonl')
    quantities = {}
    for typ in ['count', 'area', 'length', 'volume']:
        values = [r for r in detailed if r['type'] == typ and r['absolute_error'] is not None]
        quantities[typ] = {
            'valid_answer_error_n': len(values),
            'mae': statistics.mean(r['absolute_error'] for r in values) if values else None,
            'signed_bias': statistics.mean(r['signed_error'] for r in values) if values else None,
            'units': dict(collections.Counter(str(r['unit']) for r in values)),
        }
    drawing_rows = collections.defaultdict(list)
    for row in detailed:
        drawing_rows[row['drawing_group']].append(row)
    execution_errors = main_summary['outcomes'].get('Execution error', 0)
    extra = {
        'generated': now(), 'mode': 'Frozen Local CPU only; not a Hybrid serving score',
        'inference_source_commit': '5827eab5e423bae3eb7413a2c773183afa2f60f0',
        'deployment_source_commit': '8fce90834c82935f6180baac8a7071763269b183',
        'provider_attempts': 0,
        'source_checkpoints': len(sources),
        'complete_source_checkpoints': sum(s['complete'] for s in sources),
        'eligible_sources': len({q['path'] for q in qs}),
        'recorded_drawing_groups': sum(any(r['recorded'] for r in rs) for rs in drawing_rows.values()),
        'fully_recorded_drawing_groups': sum(all(r['recorded'] for r in rs) for rs in drawing_rows.values()),
        'summaries': {k: v['summary'] for k, v in reports.items()},
        'quantity_errors': quantities,
        'execution_failure_rate_recorded': execution_errors / len(rows) if rows else None,
        'execution_failure_rate_all_eligible': execution_errors / len(qs) if qs else None,
        'source_processing_seconds': {'n': len(source_seconds), 'sum': sum(source_seconds), 'median': statistics.median(source_seconds) if source_seconds else None, 'min': min(source_seconds) if source_seconds else None, 'max': max(source_seconds) if source_seconds else None},
        'query_elapsed_seconds_including_source_cache_reuse': {'n': len(query_seconds), 'median': statistics.median(query_seconds) if query_seconds else None, 'min': min(query_seconds) if query_seconds else None, 'max': max(query_seconds) if query_seconds else None},
        'resource_samples': {'n': len(telemetry), 'cpu_percent_max_sampled': max((r['cpu_percent'] for r in telemetry), default=None), 'ram_percent_max_sampled': max((r['ram_used_percent'] for r in telemetry), default=None), 'disk_free_bytes_min_sampled': min((r['disk_free_bytes'] for r in telemetry), default=None)},
        'resource_telemetry_gaps_over_5_seconds': gaps,
        'model_loading_seconds': None,
        'limits': [
            'No model/router/prompt/threshold/grade tuning after final evaluation.',
            'Partial deterministic source order is not representative random sampling.',
            'All eligible denominator retains missing predictions as Not recorded.',
            'Recorded-subset accuracy excludes unprocessed questions and must be labelled partial.',
            'Known-unexposed means no known local custom-training/dev overlap, not known absence from external pretrained training.',
            'CubiCasa custom training identities are unavailable; unknown-overlap results are never certified held out.',
            'Query elapsed includes cached source reuse; not cold inference latency.',
            'Raw loading zero is unmeasured, not zero load cost; report N/A.',
            'CPU versus CUDA output differences are possible; this is not deployed Hybrid accuracy.',
            'Telemetry is sampled, not an instantaneous utilization guarantee.',
            'The telemetry-only process stopped and was resumed; gaps are explicit. The separate inference supervisor/admission remained active.',
        ],
        'runner': task,
        'wall_elapsed_seconds': ((datetime.fromisoformat(task['finished']) - datetime.fromisoformat(task['started'])).total_seconds()
                                 if task.get('finished') and task.get('started') else None),
    }
    atomic(dest / 'final-summary.json', extra)
    print(json.dumps(extra, indent=2))


if __name__ == '__main__':
    main()
