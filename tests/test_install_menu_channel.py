"""CLI menu redesign + main/dev install channel (pgclock.sh / get.sh)."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SH = ROOT / "pgclock.sh"
GET = ROOT / "get.sh"


class InstallMenuChannelTests(unittest.TestCase):
    def test_brand_orange_mrclockbot_menu(self):
        src = SH.read_text(encoding="utf-8")
        self.assertIn("MrClockBot", src)
        self.assertIn("38;5;208m", src)  # orange accent
        self.assertIn("print_status_box", src)
        self.assertIn("Not installed", src)
        self.assertIn("Low resources", src)
        self.assertIn("hw_is_minimal", src)
        # Former cyan default removed from accent assignment
        self.assertNotIn("C=$'\\033[0;36m'", src)
        # Menu copy stays English
        self.assertIn("Select channel", src)
        self.assertIn("Development", src)
        self.assertNotIn("نصب نیست", src)

    def test_status_box_and_version_helpers(self):
        src = SH.read_text(encoding="utf-8")
        self.assertIn("panel_is_installed", src)
        self.assertIn("read_app_version", src)
        self.assertIn("read_hw_summary", src)
        box = src.split("print_status_box() {", 1)[1].split("show_menu() {", 1)[0]
        self.assertIn("Install :", box)
        self.assertIn("Version :", box)
        self.assertIn("Channel :", box)
        self.assertIn("Not installed", box)

    def test_install_update_channel_wiring(self):
        src = SH.read_text(encoding="utf-8")
        self.assertIn("prompt_install_channel", src)
        self.assertIn("sync_code_to_channel", src)
        self.assertIn("persist_channel_env", src)
        self.assertIn("UPDATE_CHANNEL", src)
        self.assertIn("DEPLOYED_CHANNEL", src)
        install = src.split("cmd_install() {", 1)[1].split("cmd_update() {", 1)[0]
        self.assertIn("prompt_install_channel", install)
        self.assertIn("sync_code_to_channel", install)
        self.assertIn("persist_channel_env", install)
        update = src.split("cmd_update() {", 1)[1].split("cmd_edit_env() {", 1)[0]
        self.assertIn("prompt_install_channel", update)
        self.assertIn("sync_code_to_channel", update)
        # Must not hard-fallback to main when updating a selected channel
        self.assertNotIn("syncing hard to origin/main", update)

    def test_get_sh_clones_selected_branch(self):
        src = GET.read_text(encoding="utf-8")
        self.assertIn('git clone -b "$REMOTE_BRANCH" --single-branch', src)
        self.assertIn("PGCLOCK_CHANNEL", src)
        self.assertIn('REMOTE_BRANCH="dev"', src)
        self.assertIn("CHANNEL_FROM_ENV", src)


class WriteEnvChannelTests(unittest.TestCase):
    def test_write_env_includes_channel_keys(self):
        src = (ROOT / "scripts" / "write_env.py").read_text(encoding="utf-8")
        self.assertIn('"UPDATE_CHANNEL"', src)
        self.assertIn('"DEPLOYED_CHANNEL"', src)


if __name__ == "__main__":
    unittest.main()
