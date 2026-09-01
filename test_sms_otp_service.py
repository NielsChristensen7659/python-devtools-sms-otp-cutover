import json
from sms_otp_service import DeveloperLoginCodes, InfraiClient


class Reply:
    status = 200
    headers = {}

    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def test_login_code_is_accepted_when_api_verifies_it():
    def opener(req):
        assert req.method == "POST"
        assert req.full_url.endswith("/v1/sms/verify")
        return Reply({"ok": True, "data": {"verified": True}, "error": None, "metadata": {}})

    result = DeveloperLoginCodes(InfraiClient("test-key", opener)).verify("+15551234567", "246810")
    assert result.accepted is True
    assert result.message == "login granted"
