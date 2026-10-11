"""Home/back: one welcome + lasting main ReplyKeyboard (Option B)."""

from __future__ import annotations

import inspect
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]


class RenderHomeReplyLastTests(unittest.IsolatedAsyncioTestCase):
    async def test_render_home_without_miniapp_single_message_reply_kb(self):
        """When Mini App HTTPS is off, welcome is one message with ReplyKeyboard."""
        from app.bot.handlers.start import render_home
        from app.db.models import Role

        message = AsyncMock()
        message.answer = AsyncMock(return_value=MagicMock())
        session = AsyncMock()
        db_user = MagicMock()
        db_user.id = 1
        db_user.role = Role.USER.value
        db_user.full_name = "Test"
        db_user.telegram_id = 123
        db_user.username = "t"
        db_user.referred_by_id = None

        ui = {
            "nav_mode": "inline",
            "welcome_text": "سلام",
            "shop_title": "فروشگاه",
            "menu_order": "shop,wallet",
            "btn_menu_home": "🏠 منوی اصلی",
        }
        main_kb = MagicMock(name="MAIN_REPLY")

        with (
            patch(
                "app.bot.handlers.start.get_all_settings",
                new=AsyncMock(return_value=ui),
            ),
            patch(
                "app.services.reseller_access.effective_menu_role",
                new=AsyncMock(return_value="user"),
            ),
            patch(
                "app.services.reseller_access.is_shop_owner_on_main_bot",
                return_value=False,
            ),
            patch(
                "app.bot.handlers.start._has_services",
                new=AsyncMock(return_value=False),
            ),
            patch(
                "app.bot.menu_nav.build_main_reply_keyboard",
                new=AsyncMock(return_value=(main_kb, ui, "user")),
            ),
            patch(
                "app.bot.keyboards.miniapp_inline_keyboard",
                return_value=None,
            ),
            patch(
                "app.bot.handlers.start.seed_main_reply_kb",
                new=AsyncMock(),
            ) as seed,
            patch(
                "app.services.rich_text.outbound_setting_text",
                return_value=("HOME_TEXT", {}),
            ),
        ):
            await render_home(
                message,
                session,
                db_user,
                ui=ui,
                effective_role="user",
                is_reseller_bot=False,
            )

        self.assertEqual(message.answer.await_count, 1)
        call = message.answer.await_args
        self.assertEqual(call.args[0], "HOME_TEXT")
        self.assertIs(call.kwargs.get("reply_markup"), main_kb)
        seed.assert_not_awaited()

    async def test_render_home_with_miniapp_uses_send_reply_keyboard_last(self):
        """Mini ahead + welcome with ReplyKeyboard last — no ⌨️ filler seed."""
        from app.bot.handlers.start import render_home
        from app.db.models import Role

        message = AsyncMock()
        message.answer = AsyncMock(return_value=MagicMock())
        session = AsyncMock()
        db_user = MagicMock()
        db_user.id = 1
        db_user.role = Role.USER.value
        db_user.full_name = "Test"
        db_user.telegram_id = 123
        db_user.username = "t"
        db_user.referred_by_id = None

        ui = {
            "nav_mode": "inline",
            "welcome_text": "سلام",
            "shop_title": "فروشگاه",
            "menu_order": "shop,wallet",
            "btn_menu_home": "🏠 منوی اصلی",
            "btn_miniapp": "مینی اپ",
        }
        main_kb = MagicMock(name="MAIN_REPLY")
        mini_kb = MagicMock(name="MINI_INLINE")

        with (
            patch(
                "app.bot.handlers.start.get_all_settings",
                new=AsyncMock(return_value=ui),
            ),
            patch(
                "app.services.reseller_access.effective_menu_role",
                new=AsyncMock(return_value="user"),
            ),
            patch(
                "app.services.reseller_access.is_shop_owner_on_main_bot",
                return_value=False,
            ),
            patch(
                "app.bot.handlers.start._has_services",
                new=AsyncMock(return_value=False),
            ),
            patch(
                "app.bot.menu_nav.build_main_reply_keyboard",
                new=AsyncMock(return_value=(main_kb, ui, "user")),
            ),
            patch(
                "app.bot.keyboards.miniapp_inline_keyboard",
                return_value=mini_kb,
            ),
            patch(
                "app.bot.tg_utils.send_reply_keyboard_last",
                new=AsyncMock(),
            ) as send_last,
            patch(
                "app.bot.handlers.start.seed_main_reply_kb",
                new=AsyncMock(),
            ) as seed,
            patch(
                "app.services.rich_text.outbound_setting_text",
                return_value=("HOME_TEXT", {}),
            ),
        ):
            await render_home(
                message,
                session,
                db_user,
                ui=ui,
                effective_role="user",
                is_reseller_bot=False,
            )

        message.answer.assert_not_awaited()
        send_last.assert_awaited_once()
        self.assertEqual(send_last.await_args.args[1], "HOME_TEXT")
        self.assertIs(send_last.await_args.args[2], main_kb)
        ahead = send_last.await_args.kwargs["ahead"]
        self.assertEqual(ahead[0][1], mini_kb)
        self.assertNotIn("⌨️", ahead[0][0])
        seed.assert_not_awaited()

    async def test_render_home_without_mini_still_attaches_reply(self):
        from app.bot.handlers.start import render_home
        from app.db.models import Role

        message = AsyncMock()
        message.answer = AsyncMock(return_value=MagicMock())
        session = AsyncMock()
        db_user = MagicMock()
        db_user.id = 1
        db_user.role = Role.USER.value
        db_user.full_name = "Test"
        db_user.telegram_id = 123
        db_user.username = None

        ui = {"welcome_text": "سلام", "shop_title": "فروشگاه", "menu_order": "shop"}
        main_kb = MagicMock(name="MAIN_REPLY")

        with (
            patch(
                "app.services.reseller_access.effective_menu_role",
                new=AsyncMock(return_value="user"),
            ),
            patch(
                "app.services.reseller_access.is_shop_owner_on_main_bot",
                return_value=False,
            ),
            patch(
                "app.bot.handlers.start._has_services",
                new=AsyncMock(return_value=False),
            ),
            patch(
                "app.bot.menu_nav.build_main_reply_keyboard",
                new=AsyncMock(return_value=(main_kb, ui, "user")),
            ),
            patch(
                "app.bot.keyboards.miniapp_inline_keyboard",
                return_value=None,
            ),
            patch(
                "app.services.rich_text.outbound_setting_text",
                return_value=("HOME_TEXT", {}),
            ),
        ):
            await render_home(
                message,
                session,
                db_user,
                ui=ui,
                effective_role="user",
                is_reseller_bot=False,
            )

        message.answer.assert_awaited_once()
        self.assertIs(message.answer.await_args.kwargs.get("reply_markup"), main_kb)


class HomeReplySourceGuards(unittest.TestCase):
    def test_render_home_welcome_paths_and_seed(self):
        from app.bot.handlers import start

        src = inspect.getsource(start.render_home)
        self.assertIn("send_reply_keyboard_last", src)
        self.assertIn("miniapp_inline_keyboard", src)
        self.assertIn("if not is_reseller_bot:", src)
        self.assertNotIn('effective_role not in {"admin", "reseller"}', src)
        self.assertIn("message.answer(text, reply_markup=reply_kb", src)
        self.assertNotIn('await message.answer("📱"', src)
        self.assertNotIn('tip: str = "⌨️"', inspect.getsource(start.seed_main_reply_kb))
        seed = inspect.getsource(start.seed_main_reply_kb)
        self.assertIn("attach_reply_keyboard", seed)
        self.assertNotIn("ephemeral=True", seed)

    def test_home_and_back_use_render_home(self):
        from app.bot.handlers import reply_nav

        home_src = inspect.getsource(reply_nav.reply_main_nav)
        self.assertIn("REPLY_ACTION_HOME", home_src)
        self.assertIn("render_home", home_src)
        back_src = inspect.getsource(reply_nav.handle_back)
        self.assertIn("render_home", back_src)

    def test_start_no_longer_ephemeral_only_seed(self):
        src = (ROOT / "app/bot/handlers/start.py").read_text(encoding="utf-8")
        # Legacy ephemeral polish removed from home path
        self.assertNotIn("ephemeral=True", src)


if __name__ == "__main__":
    unittest.main()
