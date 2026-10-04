"""K-line port auto-detection never picks a GPS receiver (ADR-0009)."""
from d2diag import ports


def test_auto_skips_ublox_by_id(monkeypatch):
    links = {
        "/dev/serial/by-id/*": ["/dev/serial/by-id/usb-u-blox_AG_u-blox_GNSS_receiver-if00",
                                "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"],
    }
    monkeypatch.setattr(ports.glob, "glob", lambda pat: links.get(pat, []))
    assert ports.resolve_serial_port("auto").endswith("1a86_USB_Serial-if00-port0")
    assert all("u-blox" not in p for p in ports.list_serial_ports())


def test_explicit_path_is_never_filtered():
    gps = "/dev/serial/by-id/usb-u-blox_AG_u-blox_GNSS_receiver-if00"
    assert ports.resolve_serial_port(gps) == gps
