from satcfdi_bridge.registry import capabilities
from satcfdi_bridge import operations  # noqa: F401


def test_expected_operations_registered():
    ops = capabilities()
    assert "csf.download" in ops
    assert "compliance.download" in ops
    assert "mass.cfdi.status" in ops
    assert "portal.rfc_valid" in ops
