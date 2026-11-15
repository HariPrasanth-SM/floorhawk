# Final deployed model handoff

The current release requires30assets:28base assets plus the supplied YOLO checkpoint and proposal selector. [config/deployed-assets.json](config/deployed-assets.json) records every filename, size, SHA256, source/revision, role, license and restoration path. Qwen, FloorCAD and other disabled models are not in this inventory.

An allowlisted, verified OCR-only package is ready outsideGit:
`../floorhawk-modal/handoff/event-readiness/floorhawk-redistributable-ocr.zip`.
It contains3unchanged Apache-2.0 PP-OCR ONNX models, the full inventory, RESTORE.md, license and notices. It is **not** the complete runtime bundle. Restricted or unclear CubiCasa/RT-DETR/custom weights and calibrations are excluded; restore them from their recorded upstream sources or authenticated Modal paths below. Custom detector author attribution remains pending. No datasets, drawings, references, predictions, credentials, caches, venvs or transcripts enter the ZIP.

Reproduce with `.venv/bin/python scripts/package_deployed_assets.py` after restoring exact local assets; the command refuses to overwrite an existing package. It checks free disk, source hashes, archive allowlist, CRC and extracted model hashes. Package metadata/checksum is beside the ZIP in `package-verification.json`. No authorized Google Drive upload tool was available, so no upload/share URL is claimed. Upload this package manually if desired; review included license/notices.

# External artifacts

## Overnight event assets

The existing Modal asset version is `a18a52dae0e7-3ec800c811f2`:28files,288,554,394bytes, verified remotely at resident startup. The supplied YOLO checkpoint is separately versioned as `campaign-assets-v1/floorplan_yolo11m.pt` (40,569,507bytes; SHA256 `95fd78b75b72f50963c03d710dbd38b9c7259e21e141c019f58ab7fbb57e54ea`). Its4200-plan training identities are unavailable; do not claim disjoint CubiCasa evaluation.

The own selector is27,664bytes at `campaign-release-assets/568decc669d2ce00ed71f9f0cd0345dfedda5f2302293acb9d7777e0333c0c69/selector.json`; the directory component is its SHA256. These are external model/calibration assets, never Git blobs. Exact metadata is in `config/artifacts.json` and each external release's `extra-assets.json`.

An authenticated operator can restore the supplied checkpoint without a public sharing URL:

```bash
mkdir -p external/custom-yolo
.venv/bin/modal volume get floorhawk-assets /campaign-assets-v1/floorplan_yolo11m.pt external/custom-yolo/floorplan_yolo11m.pt
```

Restore the exact previously uploaded standard manifest directly from the owning workspace, without rebuilding or uploading weights:

```bash
mkdir -p ../floorhawk-modal
.venv/bin/modal volume get floorhawk-assets /a18a52dae0e7-3ec800c811f2/assets.json ../floorhawk-modal/assets.json
.venv/bin/modal volume get floorhawk-assets /campaign-release-assets/568decc669d2ce00ed71f9f0cd0345dfedda5f2302293acb9d7777e0333c0c69/selector.json external/selector.json
```

Standard manifest SHA256: `46b40fe74c1877a7127a082893038bac78c4f45f1e9af488f5d189f702fe84dc`. The standard manifest contains only the28standard assets; the separately versioned custom checkpoint/selector are additionally required by the frozen event config. The old `assets.py` omitted-assets note concerns its earlier base release, not the current extra-assets registry. Existing active asset bytes must not be overwritten. Gallery restoration requires the owner's protected source/geometry resources and existing access secrets; no source redistribution permission is granted here.

Verify the recorded checksum before loading. The other28assets remain under the recorded version directory. Modal Volume access requires the owning workspace; no credentials are bundled. Six protected gallery drawings and source-matched IFC GLB display assets remain outside Git; redistribution permission is not established. Do not package those into a public code archive. Restore the same monetary authority/history rather than creating an empty ledger on another machine.

No datasets, weights, caches, generated geometry, bulk predictions, SQLite databases, credentials or transcripts are tracked. Existing locations remain in place. Set paths using `.env.example` in the server shell; no asset relocation is necessary.

`config/artifacts.json` records exact filenames, byte sizes, SHA256, source, revision and license restrictions. `MODEL_REGISTRY.json`, `v2/registry.json` and pinned downloaders contain detailed third-party provenance and official URLs. Restore dependencies into `.venv` using requirements*.txt, then third-party assets with the existing reviewed download scripts. Verify SHA256 before loading. Restore CubiCasa's pinned source and compatibility shim with `prepare_cubi_compat.py` after the official source download. Do not assume checkpoint redistribution/commercial rights.

Generate manifest: `.venv/bin/python scripts/artifacts.py`. Optional allowlisted custom-only archive: `.venv/bin/python scripts/artifacts.py --package-custom`. Only the three small custom calibration artifacts are permitted; no construction drawings, company datasets, third-party checkpoints or secrets enter this archive. It remains under external results; nothing uploads. Source models carry their existing restrictions; no blanket project license is assigned. Three.js MIT license is bundled; PyMuPDF/IfcOpenShell and other dependency licenses remain applicable.

Copy custom artifacts to the corresponding paths beneath PROOFPLAN_MODEL_ROOT and verify manifest hashes. Dataset restoration requires the separately authorized original dataset, not Git or this archive. Original saved predictions/replay/indexes stay under PROOFPLAN_RESULTS_ROOT; see docs/demo.md. An external storage URL can be added only after upload authorization and license review; none is fabricated here.

Reproduction environment specification: `bash scripts/restore_environment.sh` (not executed this iteration because the working .venv was preserved). It installs the known CUDA12.4 PyTorch build into .venv only. Third-party restoration commands are `.venv/bin/python assets.py cubi`, `.venv/bin/python prepare_cubi_compat.py` and `.venv/bin/python download_v2_assets.py`; these perform downloads and should be run under an explicitly authorized resource window. Qwen is optional via `.venv/bin/python assets.py qwen`; no Qwen download occurred in this iteration. Do not run cleanup against unknown assets.
