# Bundled viewer dependencies

Three.js **0.170.0**, MIT licence in `LICENSE.three`.

Downloaded during this iteration from the pinned npm release at:
- https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js
- https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/controls/OrbitControls.js
- https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/loaders/GLTFLoader.js
- https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/utils/BufferGeometryUtils.js
- https://cdn.jsdelivr.net/npm/three@0.170.0/LICENSE

Imports were rewritten to these relative local files. Runtime rendering uses no CDN, credentials, external textures or model inference. `checksums.json` records the shipped bytes including those import edits.
