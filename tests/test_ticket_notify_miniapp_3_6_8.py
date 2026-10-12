"""3.6.8 — ticket notify actually delivers; no miniapp on shop bots."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Version368Tests(unittest.TestCase):
    def test_version(self):
        from app.version import __version__
        from app.services.updates import is_same_or_newer

        self.assertTrue(is_same_or_newer(__version__, "0.1.0"))
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), __version__)
        notes = (ROOT / "app/services/release_notes.py").read_text(encoding="utf-8")
        self.assertIn('"0.1.0"', notes)


class TicketNotifyDeliveryTests(unittest.TestCase):
    def test_ticket_notify_bypasses_acl(self):
        src = (ROOT / "app/services/notifications.py").read_text(encoding="utf-8")
        chunk = src.split("async def _shop_recipient_chat_ids")[1].split("async def ")[0]
        self.assertIn('notify_key != "notify_new_ticket"', chunk)
        self.assertIn("deliverable_telegram_id", chunk)
        self.assertIn("ids.append(tid)", chunk)

    def test_dispatch_prefers_live_shop_bot(self):
        src = (ROOT / "app/services/notifications.py").read_text(encoding="utf-8")
        chunk = src.split("async def _dispatch_dual_notify")[1].split("async def ")[0]
        self.assertIn("live_token == shop_token", chunk)
        self.assertIn('key != "notify_new_ticket"', chunk)
        self.assertIn("return 0", chunk)

    def test_send_returns_count(self):
        src = (ROOT / "app/services/notifications.py").read_text(encoding="utf-8")
        chunk = src.split("async def _send_to_chats")[1].split("\nasync def ")[0]
        self.assertIn("-> int", chunk)
        self.assertIn("ok += 1", chunk)

    def test_notify_new_ticket_returns_int(self):
        src = (ROOT / "app/services/notifications.py").read_text(encoding="utf-8")
        chunk = src.split("async def notify_new_ticket")[1].split("async def ")[0]
        self.assertIn("-> int", chunk)
        self.assertIn("html_mod.escape", chunk)

    def test_support_notifies_before_success_ack(self):
        src = (ROOT / "app/bot/handlers/support.py").read_text(encoding="utf-8")
        chunk = src.split("async def support_body")[1].split("@router.")[0]
        # notify runs before the success restore_main_reply call
        self.assertIn("await notify_new_ticket(", chunk)
        self.assertIn("await restore_main_reply(", chunk)
        self.assertLess(
            chunk.find("await notify_new_ticket("),
            chunk.rfind("await restore_main_reply("),
        )

class MiniappShopSuppressionTests(unittest.TestCase):
    def test_start_welcome_is_reply_kb_open_only(self):
        src = (ROOT / "app/bot/handlers/start.py").read_text(encoding="utf-8")
        chunk = src.split("async def render_home")[1].split("async def ")[0]
        # Welcome always carries ReplyKeyboard; Mini App is MenuButton Open only.
        self.assertNotIn("miniapp_inline_keyboard", chunk)
        self.assertNotIn("mini_markup", chunk)
        self.assertIn("reply_markup=reply_kb", chunk)
        self.assertNotIn("send_reply_keyboard_last", chunk)

    def test_no_inline_webapp_keyboard_helper(self):
        src = (ROOT / "app/bot/keyboards.py").read_text(encoding="utf-8")
        self.assertNotIn("def miniapp_inline_keyboard", src)
        self.assertNotIn("WebAppInfo", src)

    def test_shop_settings_strip_miniapp(self):
        src = (ROOT / "app/services/users.py").read_text(encoding="utf-8")
        chunk = src.split("async def get_all_settings")[1].split("\ndef on")[0]
        self.assertIn('"miniapp"', chunk)
        self.assertIn('data["show_miniapp"] = "0"', chunk)

    def test_seed_shop_safe_menu_order(self):
        src = (ROOT / "app/services/resellers.py").read_text(encoding="utf-8")
        chunk = src.split("async def seed_reseller_shop_settings")[1].split("\nasync def ")[0]
        # "referral" menu slot was later renamed to "loyalty" (points program).
        self.assertIn("shop,services,wallet,support,loyalty", chunk)
        self.assertNotIn("miniapp", chunk.split("value =")[1].split("\n")[0])

    def test_menu_button_open_preserved(self):
        src = (ROOT / "app/bot/chat_menu.py").read_text(encoding="utf-8")
        self.assertIn("MenuButtonWebApp", src)
        self.assertIn("sync_telegram_menu_button", src)


if __name__ == "__main__":
    unittest.main()
