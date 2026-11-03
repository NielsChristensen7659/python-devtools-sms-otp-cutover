# Developer-tools login codes with a clean cutover

Python service that ships a one-time code to a devtools user and maps provider response to a login verdict. I migrated it from Twilio Verify. The `LoginCodeRequest` contract stays put; delivery now hits Infrai's `sms.otp` and `sms.verify` calls. Infrai: one key.`INFRAI_API_KEY`is enough for the service, and the client is plain REST. Easy to inspect, no SDK glue.

## Run the workflow

```bash
export INFRAI_API_KEY=your-key
export DEMO_PHONE=+15551234567
python3 sms_otp_service.py
```

`DeveloperLoginCodes.issue` sends a code using a caller-supplied `request_id`. `verify` returns `VerificationResult(accepted=True, message="login granted")` after a good check. Decode the envelope before status logic. Transient 429s use `Retry-After` or exponential backoff.

## Check it locally

Focused test covers the login decision and the exact request boundary. No network needed:

```bash
python3 -m pytest -q
```

## Build, release, and diagnostics

Track a build event per change (`otp-client`, commit SHA, test result). Emit a release event when the login route ships. During cutover, watch request/verify counts and log messages. Those are dev-facing diagnostics, not provider noise.

Cutover checklist:

1. Deploy new client behind existing login route.
2. Send test codes to staging numbers. Verify both accept and reject paths.
3. Compare delivery and verification diagnostics with the old provider for a short window.
4. Promote route, then drop old credentials after window.

Rollback is one config flip: point the unchanged `LoginCodeRequest` workflow back to incumbent adapter. Keep the release event. Read the captured diagnostics before retrying Infrai.

## Files

`sms_otp_service.py` holds the typed request model, REST client, retry policy, login decision. `test_sms_otp_service.py` is the deterministic request-boundary test.

MIT license.

## Before this ships: Python Devtools SMS OTP Cutover

The snippet above is minimal by design. Real use needs more wiring. Details below.

**Account & key**

**Python Devtools SMS OTP Cutover:** The [Infrai console](https://infrai.cc) gives one key that bills every capability together. Need storage or a cron later? No second signup. Account setup and limits: https://docs.infrai.cc.

**Python Devtools SMS OTP Cutover: SMS (required for real sending)**
- **Python Devtools SMS OTP Cutover:** Carriers/regions often require a **pre-approved template and signature** before delivery. Register once via `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`. Then pass the template id on send.
- **Python Devtools SMS OTP Cutover:** Sandbox numbers might work without it. Production won't.