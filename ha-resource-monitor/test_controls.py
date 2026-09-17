import unittest
from unittest.mock import patch
import server


class ControlsTests(unittest.TestCase):
    def test_protected_and_invalid(self):
        with patch.object(server, "api_get") as api:
            for slug in ("core", "supervisor", "self", "local_ha_resource_monitor", "../core", None):
                with self.subTest(slug=slug), self.assertRaises(ValueError):
                    server.stop_addon(slug)
            api.assert_not_called()

    def test_stopped_or_unknown(self):
        with patch.object(server, "api_get", return_value={"addons": []}) as api:
            with self.assertRaises(ValueError):
                server.stop_addon("core_mosquitto")
            self.assertEqual(api.call_count, 1)

    def test_only_selected_app_is_stopped(self):
        with patch.object(server, "api_get", side_effect=[
            {"addons": [{"slug": "core_mosquitto", "state": "started"}]}, {}
        ]) as api:
            server.stop_addon("core_mosquitto")
            api.assert_called_with("/addons/core_mosquitto/stop", method="POST")
            self.assertIsNone(server.SNAPSHOT)

    def test_cache_reuses_measurement(self):
        server.SNAPSHOT = None
        with patch.object(server, "collect", return_value={"timestamp": 1}) as collect:
            self.assertEqual(server.snapshot(), server.snapshot())
            collect.assert_called_once()
        server.SNAPSHOT = None


if __name__ == "__main__":
    unittest.main()
