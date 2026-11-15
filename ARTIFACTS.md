# External artifacts

## Overnight event assets

The existing Modal asset version is `a18a52dae0e7-3ec800c811f2`:28files,288,554,394bytes, verified remotely at resident startup. The supplied YOLO checkpoint is separately versioned as `campaign-assets-v1/floorplan_yolo11m.pt` (40,569,507bytes; SHA256 `95fd78b75b72f50963c03d710dbd38b9c7259e21e141c019f58ab7fbb57e54ea`). Its4200-plan training identities are unavailable; do not claim disjoint CubiCasa evaluation.

The own selector is27,664bytes at `campaign-release-assets/568decc669d2ce00ed71f9f0cd0345dfedda5f2302293acb9d7777e0333c0c69/selector.json`; the directory component is its SHA256. These are external model/calibration assets, never Git blobs. Exact metadata is in `config/artifacts.json` and each external release's `extra-assets.json`.

An authenticated operator can restore the supplied checkpoint without a public sharing URL:

```bash
mkdir -p external/custom-yolo
.venv/bin/modal volume get floorhawk-assets /campaign-assets-v1/floorplan_yolo11m.pt external/custom-yolo/floorplan_yolo11m.pt
```

Verify the recorded checksum before loading. The other28assets remain under the recorded version directory. Modal Volume access requires the owning workspace; no credentials are bundled. Six protected gallery drawings and source-matched IFC GLB display assets remain outside Git; redistribution permission is not established. Do not package those into a public code archive. Restore the same monetary authority/history rather than creating an empty ledger on another machine.

No datasets, weights, caches, generated geometry, bulk predictions, SQLite databases, credentials or transcripts are tracked. Existing locations remain in place. Set paths using `.env.example` in the server shell; no asset relocation is necessary.

`config/artifacts.json` records exact filenames, byte sizes, SHA256, source, revision and license restrictions. `MODEL_REGISTRY.json`, `v2/registry.json` and pinned downloaders contain detailed third-party provenance and official URLs. Restore dependencies into `.venv` using requirements*.txt, then third-party assets with the existing reviewed download scripts. Verify SHA256 before loading. Restore CubiCasa's pinned source and compatibility shim with `prepare_cubi_compat.py` after the official source download. Do not assume checkpoint redistribution/commercial rights.

Generate manifest: `.venv/bin/python scripts/artifacts.py`. Optional allowlisted custom-only archive: `.venv/bin/python scripts/artifacts.py --package-custom`. Only the three small custom calibration artifacts are permitted; no construction drawings, company datasets, third-party checkpoints or secrets enter this archive. It remains under external results; nothing uploads. Source models carry their existing restrictions; no blanket project license is assigned. Three.js MIT license is bundled; PyMuPDF/IfcOpenShell and other dependency licenses remain applicable.

Copy custom artifacts to the corresponding paths beneath PROOFPLAN_MODEL_ROOT and verify manifest hashes. Dataset restoration requires the separately authorized original dataset, not Git or this archive. Original saved predictions/replay/indexes stay under PROOFPLAN_RESULTS_ROOT; see docs/demo.md. An external storage URL can be added only after upload authorization and license review; none is fabricated here.

Reproduction environment specification: `bash scripts/restore_environment.sh` (not executed this iteration because the working .venv was preserved). It installs the known CUDA12.4 PyTorch build into .venv only. Third-party restoration commands are `.venv/bin/python assets.py cubi`, `.venv/bin/python prepare_cubi_compat.py` and `.venv/bin/python download_v2_assets.py`; these perform downloads and should be run under an explicitly authorized resource window. Qwen is optional via `.venv/bin/python assets.py qwen`; no Qwen download occurred in this iteration. Do not run cleanup against unknown assets.
