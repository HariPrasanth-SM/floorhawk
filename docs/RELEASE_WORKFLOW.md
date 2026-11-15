# Current event deployment and release workflow

Current source d1ae1e2, immutable operational snapshot `floorhawk-modal/releases/event-capacity-path`. Models/routing/frontend remain frozen. Presenter1/1T4;judges2/5;public2/5. Application cumulative dollar/query/permit gates are retired, history retained.

[Actual parallel verification](EVENT_CAPACITY.md) · [Status, warming, shutdown, deployment and rollback](EVENT_OPERATIONS.md). Previous records are preserved under reports/history.

Export an explicit committed source snapshot with `deploy/modal/export_release.py --commit COMMIT --output NEW --mode backend --frontend PREVIOUS --extra-assets results/overnight-20261115/extra-assets.json`; restore external manifests/assets first. Backend-only export preserves the selected frontend and APIcontract. Never export a moving working tree. Select each role explicitly via campaign.operator before deploying.
