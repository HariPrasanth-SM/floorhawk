# Public access correction

Public https://sm-hariprasanth--web.us-east.modal.run now opens the application directly. A fresh GET/ issues a unique random192-bit visitor identity signed with the existing server-only session key. The cookie is Secure, HttpOnly, SameSiteStrict and valid for8hours. Bootstrap responses are private/no-store and vary byCookie. No shared anonymous account, access code or API key is sent in HTML, JavaScript or URLs. API clients first visit/ to obtain their session cookie.

Only the explicit server deployment role `public` enables this behavior. Judges and presenter retain code authentication. Every job endpoint still checks session ownership; idempotency, one active job/session, short-burst flood protection, validation and bounded queues are unchanged.

## Actual fresh-browser verification

- No saved cookies: public portal opened without a code form.
- Public example: “How many windows are shown on this floor plan?” completed with answer2 and2visible evidence regions in8.71seconds.
- A second fresh context received a distinct signed cookie and404when requesting the first session's job.
- Fresh judges and presenter contexts displayed their code forms and returned401for unauthenticated job access.
- Browser runtime errors:0. Focused access/admission tests:17passed.

Only public was deployed: source3d262e0, immutable snapshot `floorhawk-modal/releases/public-anonymous-fixed`. Judges/presenter remain on d1ae1e2. Model weights, routing, frontendSHAa111edce02bc2803837609cf4b15bfc19d3ee1e9ff2f003826aa2a2c49aafae8, GPUcapacity and Gemini configuration are unchanged. An initial scope-shadowing bug was caught by the browser test, corrected and regression-tested; the failed report remains preserved.

Raw report and job artifacts remain outsideGit under `floorhawk-modal/verification/public-anonymous/`. Previous verified snapshot `releases/event-capacity-path` remains intact for public rollback. Use that snapshot's OWN deployment entrypoint with explicit FLOORHAWK_WORKSPACE/FLOORHAWK_RELEASE/PYTHONPATH as documented in EVENT_OPERATIONS.md; do not combine current helpers with an old image. No judges/presenter redeployment or secret change occurred.
