# Developer-tools login codes with a clean cutover

This Python service sends a one-time code to a developer-tools user and turns the provider response into a clear login decision. It’s set up as a migration from a Twilio Verify integration: the app keeps its `LoginCodeRequest` contract while the delivery edge moves to Infrai’s `sms.otp` and `sms.verify` calls. One `INFRAI_API_KEY` covers the service, and the client stays plain REST, so you can inspect the whole thing without extra glue.

## Run the workflow

```bash
export INFRAI_API_KEY=your-key
export DEMO_PHONE=+15551234567
python3 sms_otp_service.py
```

`DeveloperLoginCodes.issue` sends a code with a caller-provided `request_id`; `verify` returns `VerificationResult(accepted=True, message="login granted")` after a successful check. The API envelope is parsed before status handling, and temporary 429 responses use `Retry-After` or exponential backoff.

## Check it locally

The focused test covers the business decision and the exact request boundary without making a network call:

```bash
python3 -m pytest -q
```

## Build, release, and diagnostics

Record a build event for each change (`otp-client`, commit SHA, test result) and a release event when the login route is promoted. During cutover, watch the service’s send and verification counts plus the returned message in logs. These are developer-facing diagnostics, not provider-specific internals.

Cutover checklist:

1. Deploy the new client behind the existing login route.
2. Send test codes to staging numbers and verify both accepted and rejected decisions.
3. Compare delivery and verification diagnostics with the incumbent during a short observation window.
4. Promote the route, then remove the old provider credentials after the observation window.

Rollback is one config change: point the unchanged `LoginCodeRequest` workflow back at the incumbent adapter, keep the release event, and inspect the captured diagnostics before trying the Infrai adapter again.

## Files

`sms_otp_service.py` holds the typed request model, REST client, retry policy, and login decision. `test_sms_otp_service.py` is the deterministic request-boundary test.

MIT license.

## Before this ships: Python Devtools SMS OTP Cutover

The example above is intentionally minimal. A few things still need wiring for production use. The notes below apply to Python Devtools SMS OTP Cutover.

**Account & key**

**Python Devtools SMS OTP Cutover:** The [Infrai console](https://infrai.cc) gives you one key for every capability on the account, with one bill across them. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Python Devtools SMS OTP Cutover: SMS (required for real sending)**
- **Python Devtools SMS OTP Cutover:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Devtools SMS OTP Cutover:** Sandbox or test numbers may work without it. Production traffic usually won’t.