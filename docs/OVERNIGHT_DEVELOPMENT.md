# Overnight development comparison

Generated 2026-11-15T04:51:56.408960+02:00. All 9,544 quick questions are DEVELOPMENT, across448 drawing/project groups. Fixed valid references9,471; narrative/ungraded73. Failures, abstentions and unsupported responses stay in the primary denominator. The primary target85% has not been reached.

|Candidate|Correct / valid references|Correct / all questions|Answer coverage|
|---|---:|---:|---:|
|baseline|6641/9471 (70.12%)|6641/9544 (69.58%)|See frozen baseline rows|
|local_specialists|7205/9471 (76.07%)|7205/9544 (75.49%)|94.42%|
|best_offline|7925/9471 (83.68%)|7925/9544 (83.04%)|96.18%|
|production_policy_estimate|7923/9471 (83.66%)|7923/9544 (83.02%)|96.18%|

The production-oriented policy keeps fast structural specialist routes rather than invoking review for the extra two correct opening questions. This is not a claim that a fresh live run reproduces every cached batched review: live single-question context can differ.

## Matched outcomes

|Comparison|Rescues|Regressions|Unchanged correct|Unresolved|
|---|---:|---:|---:|---:|
|baseline_to_production_policy|1428|146|6495|1402|
|local_specialists_to_production_policy|764|46|7159|1502|

Count errors on 8276 valid answered count predictions: MAE 0.484050; signed bias -0.250121; undercounts 641, overcounts 545. This error denominator excludes unanswered counts; primary correctness does not. Text:73 ungraded,0 graded; no invented semantic credit.

## Selected policy groups

|Group|Correct / valid references|Answered / total|
|---|---:|---:|
|format:.png|5496/6404|6404/6404|
|type:count|7090/8423|8276/8423|
|target:door|394/715|705/720|
|target:window|537/901|892/907|
|target:toilet_fixture|822/884|868/885|
|target:sink|752/868|860/868|
|target:shower_bath|528/672|672/672|
|target:storey|702/722|722/722|
|target:bedroom|362/426|426/426|
|target:kitchen|458/476|476/476|
|target:bathroom|328/356|356/356|
|target:wc_room|326/350|350/350|
|target:sauna|476/492|492/492|
|target:balcony|202/218|218/218|
|format:.ifc|3/4|23/74|
|type:text|0/0|20/73|
|target:software_schema|0/0|2/2|
|target:building|0/1|2/19|
|target:unknown|0/23|0/38|
|target:wall|1/37|5/46|
|target:material|0/0|4/6|
|target:room|1497/1690|1564/1694|
|target:sanitary|0/2|0/3|
|target:stair|0/4|0/5|
|target:slab|0/5|1/7|
|target:beam|1/4|1/6|
|target:column|1/7|1/8|
|format:.pdf|2424/3063|2752/3066|
|type:area|833/1026|883/1026|
|type:length|0/8|0/8|
|type:volume|0/14|0/14|
|target:apartment|422/448|442/448|
|target:shower|38/49|40/49|
|target:bathtub|76/121|80/121|

## Evidence and limits

Original v3 predictions and all alternative experiment outputs are preserved. Reusable custom detector observations:361sources,360success/1size-boundunsupported. Grounded Flash review:358successful scene observations/361attempted sources; final failed sources retain Local. These scene calls are not one fresh call per translated question. No localization precision/recall is claimed without compatible spatial ground truth.

Known high-volume residuals include windows, doors, shower/bath fixtures and native-PDF room scope/areas. An absent class is not established as the sole cause. Model-proposed review regions are not verified object annotations.

Timing in this comparison is cached; fresh browser/server timings are recorded separately in external deployment verification. Original evaluation manifest and graders remain unchanged.

Reproduce: `.venv/bin/python -m campaign.report_development`. Machine summary: `results/overnight-20261115/development-report/summary.json`; question rows remain in the hashed run directories.


## Positive versus zero count references

These are evaluator-only DEVELOPMENT strata. No reference sign is an inference feature. Repeated translations can overweight drawings, so drawing counts are included.

|Target|Reference|Correct / questions|Unique drawing groups|
|---|---|---:|---:|
|apartment|positive|162/162 (100.0%)|81|
|balcony|positive|112/118 (94.9%)|59|
|balcony|zero|90/100 (90.0%)|50|
|bathroom|positive|308/332 (92.8%)|166|
|bathroom|zero|20/24 (83.3%)|12|
|bathtub|positive|76/121 (62.8%)|64|
|bedroom|positive|328/364 (90.1%)|182|
|bedroom|zero|34/62 (54.8%)|31|
|door|positive|394/713 (55.3%)|351|
|kitchen|positive|456/474 (96.2%)|237|
|room|positive|924/960 (96.2%)|83|
|sauna|positive|274/282 (97.2%)|141|
|sauna|zero|202/210 (96.2%)|105|
|shower|positive|38/49 (77.6%)|26|
|shower_bath|positive|498/638 (78.1%)|319|
|shower_bath|zero|30/34 (88.2%)|17|
|sink|positive|728/841 (86.6%)|424|
|sink|zero|24/27 (88.9%)|14|
|storey|positive|702/722 (97.2%)|361|
|toilet_fixture|positive|792/852 (93.0%)|426|
|toilet_fixture|zero|30/32 (93.8%)|16|
|wc_room|positive|138/146 (94.5%)|73|
|wc_room|zero|188/204 (92.2%)|102|
|window|positive|535/899 (59.5%)|445|

## Visual audit of correct count-head cases

Four selected numerically correct DEVELOPMENT predictions were rendered from their saved source regions; no new inference or reference geometry was created. Original source attribution remains on the external overlays. This small audit is not localization accuracy.

|Question ID|Target / answer|Observed source evidence|Interpretation|
|---|---|---|---|
|q-000040|Storeys2|Two actual plan regions labelled1.krs and2.krs|Supports two depicted storeys; no inference about hidden building levels|
|q-000072|Kitchen1|One boxed KK kitchenette with cooking fixtures|Visually consistent with the room role; source containment inspected|
|q-000074|Bathroom1|One boxed KH room with sanitary/shower fixtures|Visually consistent with a bathroom, rather than a separate WC room|
|q-000184|Sauna1|S label/bench is present, but the coarse box extends into garage context|Count agrees; boundary localization is imprecise. Agreement is not spatial correctness|

Overlays and original saved records: `results/overnight-20261115/count-evidence-audit/{storey,kitchen,bathroom,sauna}.{png,json}`. No images or bulk predictions are committed. A zero answer with no evidence is never evidence of verified absence.
