import unittest
from unittest.mock import Mock, patch

from ev_app import app, cache, fetch_charger_status, parse_charger_status


def payload(hardware_status="available", network_status="available", evse_status="enabled"):
    return {
        "chargePoint": {"id": 4095, "status": "active", "networkStatus": network_status},
        "evses": [{
            "physicalReference": "1389", "status": evse_status,
            "hardwareStatus": hardware_status,
            "connectors": [{"status": "enabled"}],
        }],
    }


class ChargerStatusTests(unittest.TestCase):
    def tearDown(self):
        cache.update(data=None, timestamp=0)

    def test_hardware_status_determines_availability(self):
        for hardware, expected in [
            ("available", "AVAILABLE"), ("charging", "CHARGING"),
            ("occupied", "IN_USE"), ("reserved", "RESERVED"),
            ("suspendedEV", "SUSPENDED_EV"), ("faulted", "FAULTED"),
            (None, "UNKNOWN"), ("new-status", "UNKNOWN"),
        ]:
            with self.subTest(hardware=hardware):
                self.assertEqual(parse_charger_status(payload(hardware), 1389), expected)

    def test_offline_or_disabled_overrides_available_hardware(self):
        self.assertEqual(parse_charger_status(payload(network_status="offline"), 1389), "UNAVAILABLE")
        self.assertEqual(parse_charger_status(payload(evse_status="outOfOrder"), 1389), "UNAVAILABLE")

    def test_selects_physical_reference_instead_of_first_evse(self):
        data = payload()
        data["evses"].insert(0, {"physicalReference": "other", "hardwareStatus": "charging"})
        self.assertEqual(parse_charger_status(data, 1389), "AVAILABLE")
        with self.assertRaises(ValueError):
            parse_charger_status(data, 1391)

    @patch("ev_app.requests.get")
    def test_fetch_uses_new_charge_point_id_and_tenant(self, get):
        get.return_value = Mock(json=Mock(return_value={"data": payload()}))
        self.assertEqual(fetch_charger_status(1389)["status"], "AVAILABLE")
        self.assertEqual(get.call_args.kwargs["params"], {"chargePointId": 4095})
        self.assertEqual(get.call_args.kwargs["headers"]["Tenant"], "ev_ev_passport_operator")
        data = payload()
        data["chargePoint"]["id"] = 4002
        get.return_value.json.return_value = {"data": data}
        with self.assertRaises(ValueError):
            fetch_charger_status(1389)

    @patch("ev_app.fetch_charger_status")
    def test_manual_refresh_bypasses_cache(self, fetch):
        fetch.side_effect = lambda cid: {"id": cid, "status": "AVAILABLE"}
        client = app.test_client()
        client.get("/chargers")
        self.assertEqual(fetch.call_count, 4)
        client.get("/chargers")
        self.assertEqual(fetch.call_count, 4)
        client.get("/chargers?refresh=1")
        self.assertEqual(fetch.call_count, 8)


if __name__ == "__main__":
    unittest.main()
