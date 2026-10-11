"""Optional main-menu «guides» item — in catalog/pool, off by default."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.bot.keyboards import (
    DEFAULT_ACTIVE_MENU_ORDER,
    DEFAULT_MENU_ORDER,
    REPLY_ACTION_GUIDES,
    _menu_order,
    main_menu,
    main_reply_keyboard,
    reply_action_map,
    sync_show_flags_for_order,
)
from app.services.settings_button_labels import BTN_MAIN_MENU
from app.services.users import DEFAULT_SETTINGS


class MenuGuidesOptionalTests(unittest.TestCase):
    def test_guides_in_catalog_not_in_default_active(self):
        self.assertIn("guides", DEFAULT_MENU_ORDER)
        self.assertNotIn("guides", DEFAULT_ACTIVE_MENU_ORDER)
        active = [
            p.strip()
            for p in str(DEFAULT_SETTINGS.get("menu_order") or "").split(",")
            if p.strip()
        ]
        self.assertNotIn("guides", active)
        self.assertEqual(active, list(DEFAULT_ACTIVE_MENU_ORDER))

    def test_default_menu_order_excludes_guides(self):
        ui = {"menu_order": DEFAULT_SETTINGS["menu_order"]}
        self.assertNotIn("guides", _menu_order(ui))

    def test_guides_appears_when_enabled(self):
        ui = {
            "menu_order": "shop,guides,wallet",
            "btn_shop": "خرید",
            "btn_guides": "📘 آموزش‌ها",
            "btn_wallet": "کیف",
            "menu_layout": "classic",
            "support_contacts": "[]",
        }
        self.assertEqual(_menu_order(ui), ["shop", "guides", "wallet"])
        with patch("app.bot.keyboards.get_settings") as gs:
            gs.return_value.miniapp_enabled = False
            gs.return_value.miniapp_url = ""
            markup = main_menu("user", has_services=False, ui=ui)
        labels = [btn.text for row in markup.inline_keyboard for btn in row]
        self.assertIn("📘 آموزش‌ها", labels)
        guide_btn = next(
            b
            for row in markup.inline_keyboard
            for b in row
            if b.text == "📘 آموزش‌ها"
        )
        self.assertEqual(guide_btn.callback_data, "guide:list:0")

    def test_reply_keyboard_and_action_map(self):
        ui = {
            "menu_order": "shop,guides",
            "btn_shop": "خرید",
            "btn_guides": "آموزش‌ها",
            "btn_menu_home": "🏠 منوی اصلی",
            "btn_back": "⬅️ بازگشت",
            "loyalty_enabled": "0",
            "menu_layout": "classic",
        }
        with patch("app.bot.keyboards.get_settings") as gs:
            gs.return_value.miniapp_enabled = False
            gs.return_value.miniapp_url = ""
            kb = main_reply_keyboard("user", has_services=False, ui=ui)
        texts = [b.text for row in kb.keyboard for b in row]
        self.assertIn("آموزش‌ها", texts)
        mapping = reply_action_map(
            "user", ui=ui, include_submenus=True, is_reseller_bot=False
        )
        self.assertEqual(mapping.get("آموزش‌ها"), REPLY_ACTION_GUIDES)
        # Service-card alias still available via setdefault when not on main
        ui_off = {
            **ui,
            "menu_order": "shop",
        }
        mapping_off = reply_action_map(
            "user", ui=ui_off, include_submenus=True, is_reseller_bot=False
        )
        self.assertEqual(mapping_off.get("آموزش‌ها"), "svc_guide")

    def test_show_guides_flag(self):
        flags = sync_show_flags_for_order(["shop", "guides"])
        self.assertEqual(flags["show_guides"], "1")
        flags_off = sync_show_flags_for_order(["shop", "wallet"])
        self.assertEqual(flags_off["show_guides"], "0")

    def test_btn_guides_in_main_menu_label_group(self):
        keys = {f[0] for f in BTN_MAIN_MENU}
        self.assertIn("btn_guides", keys)

    def test_menu_tab_pool_lists_guides(self):
        values = {"menu_order": ",".join(DEFAULT_ACTIVE_MENU_ORDER)}
        order = [
            k
            for k in (values.get("menu_order") or "").split(",")
            if k.strip() and k.strip() in DEFAULT_MENU_ORDER
        ]
        self.assertNotIn("guides", order)
        self.assertIn("guides", DEFAULT_MENU_ORDER)
        pool = [k for k in DEFAULT_MENU_ORDER if k not in order and k != "shop"]
        self.assertIn("guides", pool)


if __name__ == "__main__":
    unittest.main()
