import unittest

from gp_gui.client import ConnectionStatus, GlobalProtectError, GlobalProtectClient, parse_status_output


class StubClient(GlobalProtectClient):
    def __init__(self):
        super().__init__(binary="globalprotect")
        self.last_args = None
        self.help_text = ""

    def ensure_available(self) -> None:
        return

    def run(self, args, timeout_seconds=None):
        self.last_args = list(args)

        class Result:
            returncode = 0
            stdout = "Connected\nPortal: vpn.example.com\nGateway: gw.example.com\nUser: alice\nIP: 10.1.2.3"
            stderr = ""

        if args == ["connect", "--help"]:
            r = Result()
            r.stdout = self.help_text
            return r
        return Result()


class TestClient(unittest.TestCase):
    def test_connect_builds_expected_args(self):
        c = StubClient()
        c.help_text = "options: --portal --username"
        c.connect("vpn.example.com", "alice")
        self.assertEqual(c.last_args, ["connect", "--portal", "vpn.example.com", "--username", "alice"])

    def test_connect_supports_short_flags(self):
        c = StubClient()
        c.help_text = "usage: connect -p PORTAL -u USER"
        c.connect("vpn.example.com", "alice")
        self.assertEqual(c.last_args, ["connect", "-p", "vpn.example.com", "-u", "alice"])

    def test_connect_requires_portal(self):
        c = GlobalProtectClient()
        with self.assertRaises(GlobalProtectError):
            c.connect("   ", None)

    def test_parse_status_connected(self):
        out = "Connected\nPortal: vpn.example.com\nGateway: eu-gw\nUser: bob\nIP: 10.0.0.8"
        status = parse_status_output(out)
        self.assertEqual(status.state, "connected")
        self.assertEqual(status.portal, "vpn.example.com")
        self.assertEqual(status.gateway, "eu-gw")
        self.assertEqual(status.user, "bob")
        self.assertEqual(status.ip, "10.0.0.8")

    def test_parse_status_disconnected(self):
        status = parse_status_output("Not Connected")
        self.assertEqual(status.state, "disconnected")

    def test_wait_for_connected_returns_connected(self):
        class WaitClient(StubClient):
            def __init__(self):
                super().__init__()
                self.calls = 0

            def show_status(self):
                self.calls += 1
                class R:
                    returncode = 0
                    stderr = ""
                    stdout = "Connecting" if self.calls == 1 else "Connected\nUser: demo"
                return R()

        c = WaitClient()
        status = c.wait_for_connected(max_wait_seconds=2, poll_seconds=1)
        self.assertIsInstance(status, ConnectionStatus)
        self.assertEqual(status.state, "connected")


if __name__ == "__main__":
    unittest.main()
