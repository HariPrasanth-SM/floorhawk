# Evaluation discipline

The9,544-question quick set is DEVELOPMENT. The new deterministic diagnostic has16 questions/15 source groups,13 numeric and3 narrative text. It includes PNG fixtures/windows, Swiss-PDF doors, PDF area abstentions and IFC property questions; do not extrapolate to full-data accuracy. No duplicate translations were selected. Selection was frozen before new inference.

V1 and V2 predictions are immutable external files. V2 changes only schema/proposal handling and reuses EXACT Local results/evidence hashes; it makes fresh Hybrid requests. Both versions are reported separately. Source paths/configuration/manifest/prediction hashes and token/rate/cache telemetry are retained. Later dispatch accounting/rate fixes are smoke-tested infrastructure changes, not rescored model improvements. Default v3 policies remain.

Numeric scorer is a verbatim copy of the supplied evaluator in evaluation/numeric.py; exact counts and existing unit/2% quantity rules remain unchanged. Text rubric config/text-rubric.json was frozen before scoring: Unicode NFKC/whitespace/case normalization, whole-string scalar/controlled aliases, explicit list precision/recall/F1/exact set equality, no substring/exhaustive-guess credit. Extra fields/items are rejected unless explicitly permitted. Actual selected narrative references remain ungraded, with unsupported semantics stated;0 newly graded narrative cases is not an invented combined score.

Final eligibility: external results/iteration60/final-evaluation/questions.jsonl and manifest.json hold6,876 provisional eligible questions/354 grouped drawings. No final reference answer was read and no final inference was run. Exclusions conservatively cover all train-candidate groups, quick/smoke/exposed/reserved/diagnostic groups, saved-run drawings and known spatial-training/quarantine manifests; corrected group and byte/pixel identities keep aliases together. Preview shares original identities. Manual project/near-duplicate provenance review remains required, and unknown pretrained overlap remains. The provisional manifest is not advertised as a certified untouched benchmark.

Offline regeneration:

```bash
.venv/bin/python scripts/account_pair.py
.venv/bin/python scripts/score_paired.py --run paired-v1
.venv/bin/python scripts/score_paired.py --run paired-v2
.venv/bin/python scripts/current_analytics.py
```

`account_pair.py` corrects raw reused-operation counters using the append-only ledger's run row ranges, leaving predictions untouched. New dispatches use unique UUIDs. Report actual HTTP invocation separately from enabled mode; reservations are not settled charges. Full-dev frozen Local and small Hybrid results are never presented as a matched pair. Current summaries/rows are external results/iteration60/current-*; compact current Markdown is in docs/current-analytics.md.
