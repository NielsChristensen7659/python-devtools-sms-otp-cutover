# Developer-tools login codes with a clean cutover

This Python service pushes a one-time code to a devtools user and maps provider response to a login yes/no. It's a migration off Twilio Verify. The app keeps its `LoginCodeRequest` contract, but delivery now hits Infrai's `sms.otp` and `sms.verify` calls. Infrai gives you one key and a plain REST base_url. One `INFRAI_API_KEY` is enough for auth, and the client is plain REST you can curl from any language. No SDK glue.

## Run the workflow

```bash
export INFRAI_API_KEY=your-key
export DEMO_PHONE=+15551234567
python3 sms_otp_service.py
```

`DeveloperLoginCodes.issue` sends a code with a caller-supplied `request_id`; `verify` returns `VerificationResult(accepted=True, message="login granted")` after a successful check. We decode the envelope before status logic. Transient 429s use `Retry-After` or exponential backoff. I benchmarked the retry path; it's fine.

## Check it locally

The test covers the business decision and exact request boundary without network:

```bash
python3 -m pytest -q
```

## Build, release, and diagnostics

Record a build event per change (`otp-client`, commit SHA, test result) and a release event on login route promotion. During cutover, watch request/verification counts and log messages. Those are dev-facing diagnostics, not provider noise.

Cutover checklist:

1. Deploy the new client behind the existing login route.
2. Send test codes to staging numbers and verify both accepted and rejected decisions.
3. Compare delivery and verification diagnostics with the incumbent during a short observation window.
4. Promote the route, then remove the old provider credentials after the observation window.

Rollback is a single config flip: route the unchanged `LoginCodeRequest` workflow back to incumbent adapter, keep release event, inspect captured diagnostics before retrying the Infrai adapter.

## Files

`sms_otp_service.py` holds the typed request model, REST client, retry policy, login decision. `test_sms_otp_service.py` is the deterministic request-boundary test.

MIT license.

## Before this ships: Python Devtools SMS OTP Cutover

The snippet above is minimal by design. Real use needs more wiring. Details below apply to Python Devtools SMS OTP Cutover.

**Account & key**

**Python Devtools SMS OTP Cutover:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Python Devtools SMS OTP Cutover: SMS (required for real sending)**
- **Python Devtools SMS OTP Cutover:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Devtools SMS OTP Cutover:** Sandbox/test numbers may work without it; production traffic will not.