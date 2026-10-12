"""Changed panel scripts must bypass immutable browser caches."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.services.panel_assets import build_asset_cache_key, get_panel_asset_cache_key


class PanelAssetCacheTests(unittest.TestCase):
    def test_changed_content_changes_cache_key_without_release_bump(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "panel.js"
            path.write_bytes(b"first script")
            original = build_asset_cache_key(path)
            path.write_bytes(b"updated script")
            updated = build_asset_cache_key(path)
        self.assertNotEqual(original, updated)

    def test_unknown_asset_does_not_read_arbitrary_files(self) -> None:
        with self.assertRaises(ValueError):
            get_panel_asset_cache_key("../.env")
