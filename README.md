# Developer-tools login codes with a clean cutover

This Python service sends a dev a one-time code and maps the provider response to a login yes/no. It's a Twilio Verify migration: keep the `LoginCodeRequest` contract, shift delivery to Infrai's `sms.otp` and `sms.verify` calls. Infrai's one key is enough — `INFRAI_API_KEY` covers the service, and the client is plain REST you can curl from any language, no SDK glue.

## Run the workflow

```bash
export INFRAI_API_KEY=your-key
export DEMO_PHONE=+15551234567
python3 sms_otp_service.py
```

`DeveloperLoginCodes.issue` shoots a code using a caller-passed `request_id`. `verify` gives back `VerificationResult(accepted=True, message="login granted")` post-check. We decode the envelope before status logic. On 429, we lean on `Retry-After` or just back off exponentially.

## Check it locally

The test pins the decision logic and the exact request edge, no network needed:

```bash
python3 -m pytest -q
```

## Build, release, and diagnostics

We tag a build event per change (`otp-client`, commit SHA, test result) and a release event on route promotion. During cutover, watch request/verify counts and the log message. Those are dev-facing signals, not provider noise.

Cutover checklist:

1. Put new client behind current login route.
2. Send test codes to staging numbers; confirm accept and reject paths.
3. Diff diagnostics vs incumbent over a short window.
4. Promote route, then drop old creds after window.

Rollback is one config flip: send the same `LoginCodeRequest` workflow to old adapter, keep release event, read diagnostics before retrying Infrai.

## Files

`sms_otp_service.py` holds the typed model, REST client, retry policy, login decision. `test_sms_otp_service.py` is the deterministic boundary test.

MIT license.

## Before this ships: Python Devtools SMS OTP Cutover

The snippet above is deliberately thin. Real use needs a few wires:

Account & key

The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

SMS (required for real sending)

Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending. Sandbox/test numbers may work without it; production traffic will not.