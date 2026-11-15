"""Score saved predictions only; no inference imports or model calls."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument('predictions', type=Path, nargs='+')
    p.add_argument('--output', type=Path, default=ROOT / 'results/evaluation.json')
    a = p.parse_args()
    questions = ROOT.parent / 'datasets/junction-dataset/questions.jsonl'
    summary = json.loads((ROOT / 'manifests/dataset-summary.json').read_text())
    if hashlib.sha256(questions.read_bytes()).hexdigest() != summary['questions_sha256']:
        raise ValueError('Question file changed since sample selection')
    rows = [json.loads(line) for line in questions.open()]
    scores, seen = [], set()
    for path in a.predictions:
        pred = json.loads(path.read_text())
        if pred['status'] != 'success':
            raise ValueError(f'Cannot score failed inference: {path}')
        s = pred['sample']
        if s['id'] in seen:
            raise ValueError('Duplicate sample would bias accuracy')
        seen.add(s['id'])
        q = rows[s['question_line'] - 1]
        if s['question'] != q['question'] or not s['image'].endswith('/' + q['path']):
            raise ValueError('Question alignment mismatch')
        expected, predicted = q['answer'], pred['predicted_count']
        scores.append(dict(id=s['id'], expected=expected, predicted=predicted,
                           exact_match=predicted == expected, absolute_error=abs(predicted - expected)))
    report = dict(n=len(scores), exact_match_accuracy=sum(s['exact_match'] for s in scores)/len(scores),
                  mean_absolute_error=sum(s['absolute_error'] for s in scores)/len(scores), samples=scores,
                  scope='Development smoke sample; not held-out accuracy. No box-level annotations evaluated.')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
