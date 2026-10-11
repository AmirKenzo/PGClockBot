"""Miniapp premium icon + settings Back hub + silent cancel heal."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import MessageEntity

from app.services.rich_text import pack_rich_text


class MiniappPremiumIconTests(unittest.TestCase):
    def test_reply_button_sets_icon_custom_emoji_id(self):
        from app.bot.nav_inline import miniapp_reply_button

        body = "📱 مینی‌اپ"
        packed = pack_rich_text(
            body,
            [
                MessageEntity(
                    type="custom_emoji",
                    offset=0,
                    length=2,
                    custom_emoji_id="999001",
                )
            ],
        )
        ui = {
            "btn_miniapp": packed,
            "menu_order": "shop,wallet,miniapp",
        }
        with (
            patch(
                "app.services.users.current_shop_reseller_id",
                return_value=None,
            ),
            patch(
                "app.config.get_settings",
                return_value=MagicMock(
                    miniapp_enabled=True,
                    miniapp_url="https://example.com/app",
                ),
            ),
        ):
            btn = miniapp_reply_button(ui)
        self.assertIsNotNone(btn)
        self.assertEqual(btn.icon_custom_emoji_id, "999001")
        self.assertEqual(btn.text, "مینی‌اپ")
        self.assertIsNotNone(btn.web_app)

    def test_inline_keyboard_sets_icon_for_default_label(self):
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
        ui = {"btn_miniapp": packed, "menu_order": "miniapp"}
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
        self.assertIsNotNone(markup)
        btn = markup.inline_keyboard[0][0]
        self.assertEqual(btn.icon_custom_emoji_id, "42")


class SettingsHubBackTests(unittest.IsolatedAsyncioTestCase):
    async def test_render_hub_uses_section_keyboard(self):
        from app.bot.handlers.admin_settings import _render_hub

        callback = AsyncMock()
        callback.message = AsyncMock()
        session = AsyncMock()
        ui = {"menu_order": "shop"}

        with (
            patch(
                "app.bot.handlers.admin_settings.get_all_settings",
                AsyncMock(return_value=ui),
            ),
            patch(
                "app.bot.handlers.admin_settings.safe_edit_text",
                new_callable=AsyncMock,
            ) as edit,
            patch(
                "app.bot.nav_inline.admin_settings_hub_keyboard",
                return_value=MagicMock(name="HUB_KB"),
            ) as hub_kb,
        ):
            await _render_hub(callback, session)

        hub_kb.assert_called_once_with(ui)
        edit.assert_awaited()
        kwargs = edit.await_args.kwargs
        self.assertIs(kwargs.get("reply_markup"), hub_kb.return_value)
        self.assertIn("دکمه‌های زیر", edit.await_args.args[1])
        self.assertNotIn("کیبورد پایین", edit.await_args.args[1])


class SilentCancelHealTests(unittest.IsolatedAsyncioTestCase):
    async def test_answer_staff_nav_skips_لغو_شد_heal_when_reopening(self):
        from app.bot.nav_chrome import answer_staff_nav

        message = AsyncMock()
        session = AsyncMock()
        db_user = MagicMock()
        state = AsyncMock()
        reopen = AsyncMock()

        with (
            patch(
                "app.bot.nav_chrome.get_all_settings",
                AsyncMock(return_value={}),
            ),
            patch(
                "app.bot.nav_chrome.heal_main_reply",
                new_callable=AsyncMock,
            ) as heal,
            patch(
                "app.bot.nav_inline.is_bot_panel_message",
                return_value=True,
            ),
        ):
            await answer_staff_nav(
                message,
                session,
                db_user,
                text="لغو شد.",
                classic=None,
                state=state,
                reopen_panel=reopen,
                clear_state=True,
                is_reseller_bot=False,
                reseller_owner_id=None,
            )

        heal.assert_not_awaited()
        reopen.assert_awaited()


if __name__ == "__main__":
    unittest.main()
