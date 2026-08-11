from satcfdi_bridge.engine import run_request
from satcfdi_bridge.protocol import dump_json


def test_unknown_operation_is_structured():
    payload, code = run_request({"schema_version": "1.0", "operation": "missing", "params": {}})
    assert code == 2
    assert payload["ok"] is False
    assert payload["error"]["code"] == "INVALID_REQUEST"


def test_json_is_compact_by_default():
    assert dump_json({"a": 1}) == '{"a":1}'
