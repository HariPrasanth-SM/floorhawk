"""Freeze32 group-aware DEVELOPMENT questions; inference receives no reference data.

Only metadata from the existing quick development references is used for strata.
Answer fields are discarded immediately; no scores/predictions guide selection.
"""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT, sha, write_json
from runtime_paths import DATASET_ROOT, RESULTS_ROOT

SEED = 'agile-hour1-v1'
COUNT_CATEGORIES = ['count_doors', 'count_windows', 'count_toilet_fixtures',
                    'count_sinks', 'count_showers_and_baths']
META_FIELDS = ['sample_id', 'path', 'question', 'source', 'group_id', 'language', 'type', 'category', 'unit']


def order(value):
    return hashlib.sha256((SEED + ':' + value).encode()).hexdigest()


def metadata():
    source = ROOT / 'benchmarks/qa-v3/quick.answers.jsonl'
    rows = []
    with source.open() as stream:
        for line in stream:
            row = json.loads(line)
            rows.append({k: row.get(k) for k in META_FIELDS})
    return rows, source


def select(rows, inventory):
    rows = [r for r in rows if r.get('language') == 'en']
    group = lambda r: inventory.get(r['path'], {}).get('group') or r.get('group_id') or r['path']
    selected = []
    source_counts = collections.Counter()

    def drawing_sets(source, suffix, categories, number):
        paths = collections.defaultdict(lambda: collections.defaultdict(list))
        for row in rows:
            if row.get('source') == source and Path(row['path']).suffix.lower() == suffix and row.get('category') in categories:
                paths[row['path']][row['category']].append(row)
        complete = [path for path, cats in paths.items() if all(cat in cats for cat in categories)]
        by_group = collections.defaultdict(list)
        for path in complete:
            by_group[group(next(iter(paths[path].values()))[0])].append(path)
        groups = sorted(by_group, key=order)[:number]
        if len(groups) != number:
            raise ValueError('Not enough complete distinct development drawings for ' + source)
        result = []
        for drawing in groups:
            path = min(by_group[drawing], key=order)
            for category in categories:
                candidates = paths[path][category]
                chosen = min(candidates, key=lambda r: order(r['sample_id'] + ':' + r['question']))
                result.append((chosen, drawing))
        return result

    for row, drawing in drawing_sets('cubicasa5k', '.png', COUNT_CATEGORIES, 4):
        selected.append((row, drawing, 'CubiCasa five native fixture/opening queries'))
    for row, drawing in drawing_sets('swiss_dwellings', '.pdf', ['count_doors', 'area_room'], 4):
        selected.append((row, drawing, 'Swiss PDF doors plus explicit room area'))

    ifc = [r for r in rows if Path(r['path']).suffix.lower() == '.ifc' and r.get('type') == 'text']
    by_group = collections.defaultdict(list)
    for row in ifc:
        by_group[group(row)].append(row)
    if not by_group:
        raise ValueError('No English IFC text questions in the development manifest')
    chosen_ifc = []
    used_ids = set()
    for drawing in sorted(by_group, key=order):
        row = min(by_group[drawing], key=lambda r: order(r['sample_id'] + ':' + r['question']))
        chosen_ifc.append((row, drawing, 'IFC explicit metadata/properties text'))
        used_ids.add(row['sample_id'])
        if len(chosen_ifc) == 4:
            break
    for row in sorted(ifc, key=lambda r: order(r['sample_id'] + ':' + r['question'])):
        if len(chosen_ifc) >= 4:
            break
        if row['sample_id'] not in used_ids:
            chosen_ifc.append((row, group(row), 'IFC extra distinct semantic query on an available source group'))
            used_ids.add(row['sample_id'])
    if len(chosen_ifc) != 4:
        raise ValueError('Not enough distinct IFC development questions')
    selected.extend(chosen_ifc)
    if len(selected) != 32 or len({r['sample_id'] for r, _, _ in selected}) != 32:
        raise ValueError('Selection failed exact32 unique-ID contract')
    if len({(r['path'], r['question']) for r, _, _ in selected}) != 32:
        raise ValueError('Duplicate question/source semantics in selection')
    return selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=RESULTS_ROOT / 'agile1/experiment')
    args = parser.parse_args()
    out = args.output
    if (out / 'questions.jsonl').exists() or (out / 'selection.json').exists():
        raise SystemExit('Existing frozen agile selection preserved; do not overwrite')
    rows, metadata_source = metadata()
    inventory_source = ROOT / 'benchmarks/qa-v3/file-inventory.json'
    inventory = json.loads(inventory_source.read_text())
    chosen = select(rows, inventory)
    source_files = []
    for path in sorted({r['path'] for r, _, _ in chosen}):
        actual = (DATASET_ROOT / path).resolve()
        if not actual.is_relative_to(DATASET_ROOT.resolve()) or not actual.is_file():
            raise ValueError('Missing/unsafe original development input: ' + path)
        actual_sha = sha(actual)
        if inventory.get(path, {}).get('sha256') not in (None, actual_sha):
            raise ValueError('Original development file hash no longer matches frozen inventory')
        source_files.append({'path': path, 'sha256': actual_sha, 'bytes': actual.stat().st_size,
                             'group': inventory.get(path, {}).get('group'),
                             'pixel_sha256': inventory.get(path, {}).get('pixel_sha256')})
    questions = [{k: r[k] for k in ['sample_id', 'path', 'question']} for r, _, _ in chosen]
    out.mkdir(parents=True, exist_ok=True)
    (out / 'questions.jsonl').write_text(''.join(json.dumps(q, ensure_ascii=False) + '\n' for q in questions))
    cases = [{**{k: r[k] for k in ['sample_id', 'path', 'source', 'language', 'type', 'category']},
              'group': group, 'stratum': stratum} for r, group, stratum in chosen]
    manifest = {
        'version': SEED, 'seed': SEED, 'role': 'diagnostic DEVELOPMENT only, not representative final accuracy',
        'n': len(cases), 'numeric_n': sum(c['type'] in ['count', 'area', 'length', 'volume'] for c in cases),
        'text_n': sum(c['type'] == 'text' for c in cases),
        'drawing_groups': len({group for _, group, _ in chosen}),
        'physical_source_files': len(source_files), 'questions_sha256': sha(out / 'questions.jsonl'),
        'metadata_source': 'benchmarks/qa-v3/quick.answers.jsonl (metadata fields only; answers discarded)',
        'metadata_source_sha256': sha(metadata_source), 'inventory_sha256': sha(inventory_source),
        'source_counts': dict(collections.Counter(r['source'] for r, _, _ in chosen)),
        'format_counts': dict(collections.Counter(Path(r['path']).suffix.lower() for r, _, _ in chosen)),
        'cases': cases, 'source_files': source_files,
        'sampling': 'Four distinct CubiCasa source groups with5 English queries each, four distinct Swiss PDF groups with doors+one room-area query, four distinct IFC questions spread over available source groups before repeating any group. Seeded SHA order; no prediction/answer-based selection. Exact byte/pixel/group aliases retained in provenance.',
        'limits': ['Custom YOLO4200 CubiCasa training memberships unavailable; overlap assumed possible.',
                   'No held-out/reserved/final questions or answers inspected.',
                   'IFC has fewer than4 available drawing groups; a fourth different semantic question may repeat a group.',
                   'Count/questions overweight drawings deliberately for shared-extraction diagnostics; report drawing counts separately.'],
    }
    write_json(out / 'selection.json', manifest)
    print(json.dumps({k: manifest[k] for k in ['n', 'numeric_n', 'text_n', 'drawing_groups', 'physical_source_files', 'source_counts', 'questions_sha256']}))


if __name__ == '__main__':
    main()
