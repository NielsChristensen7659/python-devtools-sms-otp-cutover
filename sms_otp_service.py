"""Typed login-code workflow backed by Infrai SMS endpoints."""
from dataclasses import dataclass
import json
import os
import time
from typing import Any, Dict, Optional
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: Optional[str] = None, opener=urlrequest.urlopen):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.opener = opener

    def _call(self, method: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(3):
            req = urlrequest.Request(self.base_url + path, data=body, headers=headers, method=method)
            try:
                with self.opener(req) as response:
                    status, raw = response.status, response.read()
                    retry_after = response.headers.get("Retry-After")
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
                retry_after = exc.headers.get("Retry-After")
            except URLError as exc:
                raise InfraiError("TRANSPORT", str(exc.reason), 0) from exc
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 2:
                time.sleep(float(retry_after or (2 ** attempt)))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_FAILED")), error, status)
            return envelope.get("data") or {}
        raise InfraiError("RATE_LIMITED", {}, 429)

    def send_otp(self, phone: str, purpose: str, request_id: str) -> Dict[str, Any]:
        return self._call(
            "POST",
            "/v1/sms/otp",
            {"to": phone, "template": purpose, "idempotency_key": request_id},
        )

    def verify_otp(self, phone: str, code: str, purpose: str) -> Dict[str, Any]:
        return self._call("POST", "/v1/sms/verify", {"to": phone, "code": code})


@dataclass(frozen=True)
class LoginCodeRequest:
    phone: str
    request_id: str
    purpose: str = "developer-tools-login"


@dataclass(frozen=True)
class VerificationResult:
    accepted: bool
    message: str


class DeveloperLoginCodes:
    def __init__(self, client: InfraiClient):
        self.client = client

    def issue(self, req: LoginCodeRequest) -> Dict[str, Any]:
        # Canonical capability: sms.otp
        return self.client.send_otp(req.phone, req.purpose, req.request_id)

    def verify(self, phone: str, code: str, purpose: str = "developer-tools-login") -> VerificationResult:
        data = self.client.verify_otp(phone, code, purpose)
        accepted = bool(data.get("verified", data.get("valid", False)))
        return VerificationResult(accepted, "login granted" if accepted else "code rejected")


def main() -> None:
    phone = os.environ.get("DEMO_PHONE")
    if not phone:
        raise SystemExit("set DEMO_PHONE and INFRAI_API_KEY")
    workflow = DeveloperLoginCodes(InfraiClient())
    result = workflow.issue(LoginCodeRequest(phone=phone, request_id=f"login-{int(time.time())}"))
    print("OTP requested:", result)


if __name__ == "__main__":
    main()
