"""Miniapp: welcome inline only — not ReplyKeyboard / menu DnD."""

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

    def test_btn_miniapp_still_editable_in_main_labels(self):
        from app.services.settings_button_labels import BTN_MAIN_MENU

        keys = {f[0] for f in BTN_MAIN_MENU}
        self.assertIn("btn_miniapp", keys)


class MiniappInlineKeyboardTests(unittest.TestCase):
    def test_inline_uses_label_and_style_without_menu_order(self):
        from app.bot.keyboards import miniapp_inline_keyboard

        ui = {
            "btn_miniapp": "🚀 اپ من",
            "btn_style_miniapp": "success",
            "menu_order": "shop,wallet",  # no miniapp
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


class MiniappReplyKeyboardTests(unittest.TestCase):
    def test_reply_entries_never_include_miniapp(self):
        from app.bot.reply_keyboards import _reply_user_entries

        entries = _reply_user_entries(
            "user",
            has_services=True,
            ui={"menu_order": "shop,miniapp,wallet", "btn_shop": "خرید", "btn_wallet": "کیف"},
        )
        self.assertNotIn("miniapp", {a for a, _ in entries})

    def test_pack_reply_button_rejects_miniapp(self):
        from app.bot.keyboards import REPLY_ACTION_MINIAPP
        from app.bot.reply_keyboards import _pack_reply_button

        self.assertIsNone(_pack_reply_button(REPLY_ACTION_MINIAPP, "مینی‌اپ", {}))


class RenderHomeMiniappTests(unittest.IsolatedAsyncioTestCase):
    async def test_welcome_attaches_inline_and_seeds_reply_kb(self):
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

        ui = {
            "welcome_text": "سلام",
            "shop_title": "فروشگاه",
            "menu_order": "shop,wallet",
            "btn_miniapp": "📱 مینی‌اپ",
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
                "app.bot.menu_nav.build_main_reply_keyboard",
                new=AsyncMock(return_value=(main_kb, ui, "user")),
            ),
            patch(
                "app.bot.keyboards.miniapp_inline_keyboard",
                return_value=mini_kb,
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
        self.assertIs(call.kwargs.get("reply_markup"), mini_kb)
        seed.assert_awaited_once()

    async def test_welcome_no_inline_when_disabled(self):
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

        ui = {
            "welcome_text": "سلام",
            "shop_title": "فروشگاه",
            "menu_order": "shop",
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

        call = message.answer.await_args
        self.assertIs(call.kwargs.get("reply_markup"), main_kb)
        seed.assert_not_awaited()

    async def test_shop_bot_skips_miniapp(self):
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
        ui = {"welcome_text": "سلام", "shop_title": "فروشگاه", "menu_order": "shop"}
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
                "app.bot.menu_nav.build_main_reply_keyboard",
                new=AsyncMock(return_value=(main_kb, ui, "user")),
            ),
            patch(
                "app.bot.keyboards.miniapp_inline_keyboard",
            ) as mini,
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
                is_reseller_bot=True,
                reseller_owner_id=9,
            )

        mini.assert_not_called()
        self.assertIs(message.answer.await_args.kwargs.get("reply_markup"), main_kb)


if __name__ == "__main__":
    unittest.main()
