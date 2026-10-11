"""Miniapp: welcome ahead-inline + reply KB last — all platform roles."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import MessageEntity

from app.bot.keyboards import DEFAULT_MENU_ORDER, REMOVED_MENU_KEYS, _menu_order
from app.services.rich_text import pack_rich_text
from app.services.users import DEFAULT_SETTINGS


class MiniappMenuCatalogTests(unittest.TestCase):
    def test_miniapp_not_in_default_menu_order(self):
        self.assertNotIn("miniapp", DEFAULT_MENU_ORDER)
        self.assertIn("miniapp", REMOVED_MENU_KEYS)
        active = [
            p.strip()
            for p in str(DEFAULT_SETTINGS.get("menu_order") or "").split(",")
            if p.strip()
        ]
        self.assertNotIn("miniapp", active)

    def test_menu_order_strips_legacy_miniapp(self):
        ordered = _menu_order({"menu_order": "shop,miniapp,wallet"})
        self.assertEqual(ordered, ["shop", "wallet"])


class MiniappInlineKeyboardTests(unittest.TestCase):
    def test_inline_uses_label_and_style_without_menu_order(self):
        from app.bot.keyboards import miniapp_inline_keyboard

        ui = {
            "btn_miniapp": "🚀 اپ من",
            "btn_style_miniapp": "success",
            "menu_order": "shop,wallet",
        }
        with (
            patch(
                "app.services.users.current_shop_reseller_id",
                return_value=None,
            ),
            patch(
                "app.bot.keyboards.get_settings",
                return_value=MagicMock(
                    miniapp_enabled=True,
                    miniapp_url="https://example.com/miniapp/",
                    miniapp_deep_url=lambda view="": "https://example.com/miniapp/",
                ),
            ),
        ):
            markup = miniapp_inline_keyboard(ui)
        self.assertIsNotNone(markup)
        btn = markup.inline_keyboard[0][0]
        self.assertEqual(btn.text, "🚀 اپ من")
        self.assertEqual(getattr(btn, "style", None), "success")
        self.assertIsNotNone(btn.web_app)
        self.assertIsNone(getattr(btn, "icon_custom_emoji_id", None))

    def test_inline_none_when_disabled(self):
        from app.bot.keyboards import miniapp_inline_keyboard

        with (
            patch(
                "app.services.users.current_shop_reseller_id",
                return_value=None,
            ),
            patch(
                "app.bot.keyboards.get_settings",
                return_value=MagicMock(
                    miniapp_enabled=False,
                    miniapp_url="",
                    miniapp_deep_url=lambda view="": "",
                ),
            ),
        ):
            self.assertIsNone(miniapp_inline_keyboard({}))

    def test_inline_none_on_shop_bot(self):
        from app.bot.keyboards import miniapp_inline_keyboard

        with (
            patch(
                "app.services.users.current_shop_reseller_id",
                return_value=42,
            ),
            patch(
                "app.bot.keyboards.get_settings",
                return_value=MagicMock(
                    miniapp_enabled=True,
                    miniapp_url="https://example.com/miniapp/",
                    miniapp_deep_url=lambda view="": "https://example.com/miniapp/",
                ),
            ),
        ):
            self.assertIsNone(miniapp_inline_keyboard({}))

    def test_inline_omits_premium_icon_field(self):
        from app.bot.keyboards import miniapp_inline_keyboard

        body = "📱 مینی‌اپ"
        packed = pack_rich_text(
            body,
            [
                MessageEntity(
                    type="custom_emoji",
                    offset=0,
                    length=2,
                    custom_emoji_id="42",
                )
            ],
        )
        ui = {"btn_miniapp": packed}
        with (
            patch(
                "app.services.users.current_shop_reseller_id",
                return_value=None,
            ),
            patch(
                "app.bot.keyboards.get_settings",
                return_value=MagicMock(
                    miniapp_enabled=True,
                    miniapp_url="https://example.com/app",
                    miniapp_deep_url=lambda view="": "https://example.com/app",
                ),
            ),
        ):
            markup = miniapp_inline_keyboard(ui)
        btn = markup.inline_keyboard[0][0]
        self.assertIsNone(getattr(btn, "icon_custom_emoji_id", None))


class RenderHomeMiniappTests(unittest.IsolatedAsyncioTestCase):
    async def _run_home(self, *, role: str, is_reseller_bot: bool, mini_kb, main_kb, ui):
        from app.bot.handlers.start import render_home

        message = AsyncMock()
        message.answer = AsyncMock(return_value=MagicMock())
        session = AsyncMock()
        db_user = MagicMock()
        db_user.id = 1
        db_user.role = role
        db_user.full_name = "Test"
        db_user.telegram_id = 123
        db_user.username = "t"

        with (
            patch(
                "app.bot.handlers.start.get_all_settings",
                new=AsyncMock(return_value=ui),
            ),
            patch(
                "app.services.reseller_access.effective_menu_role",
                new=AsyncMock(return_value=role),
            ),
            patch(
                "app.bot.menu_nav.build_main_reply_keyboard",
                new=AsyncMock(return_value=(main_kb, ui, role)),
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
                "app.services.rich_text.outbound_setting_text",
                return_value=("HOME_TEXT", {}),
            ),
            patch(
                "app.bot.handlers.start.seed_main_reply_kb",
                new=AsyncMock(),
            ) as seed,
        ):
            await render_home(
                message,
                session,
                db_user,
                ui=ui,
                effective_role=role,
                is_reseller_bot=is_reseller_bot,
                reseller_owner_id=9 if is_reseller_bot else None,
            )
        return message, send_last, seed

    async def test_user_welcome_uses_send_last_no_keyboard_emoji_seed(self):
        ui = {"welcome_text": "سلام", "shop_title": "فروشگاه", "btn_miniapp": "مینی اپ"}
        main_kb = MagicMock(name="MAIN_REPLY")
        mini_kb = MagicMock(name="MINI_INLINE")
        message, send_last, seed = await self._run_home(
            role="user",
            is_reseller_bot=False,
            mini_kb=mini_kb,
            main_kb=main_kb,
            ui=ui,
        )
        send_last.assert_awaited_once()
        ahead_list = send_last.await_args.kwargs.get("ahead")
        self.assertIsNotNone(ahead_list)
        self.assertEqual(ahead_list[0][1], mini_kb)
        self.assertEqual(ahead_list[0][0], "\u3164")
        self.assertNotIn("⌨️", ahead_list[0][0])
        self.assertIs(send_last.await_args.args[2], main_kb)
        seed.assert_not_awaited()
        message.answer.assert_not_awaited()

    async def test_admin_also_gets_miniapp_ahead(self):
        ui = {"shop_title": "فروشگاه", "btn_miniapp": "مینی اپ"}
        main_kb = MagicMock(name="MAIN_REPLY")
        mini_kb = MagicMock(name="MINI_INLINE")
        _message, send_last, seed = await self._run_home(
            role="admin",
            is_reseller_bot=False,
            mini_kb=mini_kb,
            main_kb=main_kb,
            ui=ui,
        )
        send_last.assert_awaited_once()
        ahead_list = send_last.await_args.kwargs.get("ahead")
        self.assertEqual(ahead_list[0][1], mini_kb)
        seed.assert_not_awaited()

    async def test_reseller_on_platform_bot_gets_miniapp(self):
        ui = {"shop_title": "فروشگاه", "btn_miniapp": "مینی اپ"}
        main_kb = MagicMock(name="MAIN_REPLY")
        mini_kb = MagicMock(name="MINI_INLINE")
        # On platform bot, reseller role still sees customer welcome path when
        # effective_role is user-like; when effective_role is reseller on main
        # bot they still get mini (not a shop bot).
        _message, send_last, seed = await self._run_home(
            role="reseller",
            is_reseller_bot=False,
            mini_kb=mini_kb,
            main_kb=main_kb,
            ui=ui,
        )
        send_last.assert_awaited_once()
        self.assertEqual(send_last.await_args.kwargs["ahead"][0][1], mini_kb)
        seed.assert_not_awaited()

    async def test_shop_bot_skips_miniapp(self):
        ui = {"welcome_text": "سلام", "shop_title": "فروشگاه", "menu_order": "shop"}
        main_kb = MagicMock(name="MAIN_REPLY")
        message, send_last, seed = await self._run_home(
            role="user",
            is_reseller_bot=True,
            mini_kb=MagicMock(name="SHOULD_NOT"),
            main_kb=main_kb,
            ui=ui,
        )
        send_last.assert_not_awaited()
        seed.assert_not_awaited()
        message.answer.assert_awaited_once()
        self.assertIs(message.answer.await_args.kwargs.get("reply_markup"), main_kb)

    async def test_no_mini_when_disabled_single_welcome(self):
        ui = {"welcome_text": "سلام", "shop_title": "فروشگاه"}
        main_kb = MagicMock(name="MAIN_REPLY")
        message, send_last, seed = await self._run_home(
            role="user",
            is_reseller_bot=False,
            mini_kb=None,
            main_kb=main_kb,
            ui=ui,
        )
        send_last.assert_not_awaited()
        seed.assert_not_awaited()
        self.assertIs(message.answer.await_args.kwargs.get("reply_markup"), main_kb)


class SeedMainReplyNoKeyboardEmojiTests(unittest.IsolatedAsyncioTestCase):
    async def test_seed_main_reply_kb_rejects_keyboard_emoji_tip(self):
        from app.bot.handlers.start import seed_main_reply_kb

        message = AsyncMock()
        reply_kb = MagicMock()
        with patch(
            "app.bot.tg_utils.attach_reply_keyboard",
            new=AsyncMock(),
        ) as attach:
            await seed_main_reply_kb(message, reply_kb, tip="⌨️")
            attach.assert_awaited_once()
            self.assertNotIn("⌨️", attach.await_args.kwargs.get("text", ""))
            self.assertEqual(attach.await_args.kwargs.get("text"), "منوی اصلی")


if __name__ == "__main__":
    unittest.main()
