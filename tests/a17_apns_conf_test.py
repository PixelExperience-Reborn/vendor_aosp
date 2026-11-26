#!/usr/bin/env python3
"""The world APN list must be a well-formed apns-conf.xml TelephonyProvider loads whole.

TelephonyProvider parses /system/etc/apns-conf.xml with a pull parser and
stops at the first malformed element, so one broken attribute drops every
APN after it. Each entry needs the numeric of the network (mcc + mnc).
"""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

APNS = Path(__file__).resolve().parents[1] / "prebuilt/common/etc/apns-conf.xml"
KNOWN = {"carrier", "mcc", "mnc", "apn", "proxy", "port", "mmsc", "mmsproxy", "mmsport",
         "user", "password", "server", "authtype", "type", "protocol", "roaming_protocol",
         "carrier_enabled", "bearer", "bearer_bitmask", "network_type_bitmask",
         "mvno_type", "mvno_match_data", "profile_id", "modem_cognitive", "max_conns",
         "wait_time", "max_conns_time", "mtu", "mtu_v4", "mtu_v6", "apn_set_id",
         "user_visible", "user_editable", "skip_464xlat", "carrier_id", "lingering_network_type_bitmask",
         "always_on", "infrastructure_bitmask", "esim_bootstrap_provisioning", "edited"}
# Carrier extensions some entries carry; TelephonyProvider ignores them.
IGNORED = {"name", "mmsc2", "mmsprotocol", "inactivetimer"}


class ApnsConfTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.parse(APNS).getroot()

    def test_root(self):
        self.assertEqual(self.root.tag, "apns")
        self.assertGreater(len(self.root.findall("apn")), 3000)

    def test_every_apn_has_a_network(self):
        for apn in self.root.iter("apn"):
            with self.subTest(apn=apn.attrib):
                self.assertRegex(apn.get("mcc", ""), r"^\d{3}$")
                self.assertRegex(apn.get("mnc", ""), r"^\d{2,3}$")
                self.assertIn("apn", apn.attrib)

    def test_attributes_are_known(self):
        unknown = {k for apn in self.root.iter("apn") for k in apn.attrib} - KNOWN - IGNORED
        self.assertFalse(unknown, f"attributes TelephonyProvider does not read: {sorted(unknown)}")


if __name__ == "__main__":
    unittest.main(verbosity=1)
