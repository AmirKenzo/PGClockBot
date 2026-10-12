"""User keyboard column layout, list caps and admin plan list rows."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.bot.keyboards import (
    LIST_BUTTON_CAP,
    list_overflow_line,
    pay_methods,
    plans_keyboard,
    services_keyboard,
)


def _plan(plan_id: int, name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=plan_id, name=name, price=1, category_id=None, button_style=None, is_trial=False
    )


class UserKeyboardLayoutTests(unittest.TestCase):
    def test_pay_methods_wallet_alone_and_back_cancel_share_row(self) -> None:
        ui = {
            "pay_wallet_enabled": "1",
            "pay_card_enabled": "1",
            "pay_gateway_enabled": "1",
            "pay_psp_enabled": "0",
            "pay_crypto_enabled": "0",
            "pay_stars_enabled": "0",
            "pay_discount_enabled": "0",
        }
        rows = pay_methods(7, ui).inline_keyboard
        self.assertEqual([b.callback_data for b in rows[0]], ["pay:wallet:7"])
        self.assertEqual([b.callback_data for b in rows[1]], ["pay:card:7", "pay:gateway:7"])
        self.assertEqual([b.callback_data for b in rows[-1]], ["pay:back:7", "menu:home"])

    def test_plans_use_two_columns_only_for_short_labels(self) -> None:
        plans = [_plan(1, "a"), _plan(2, "b"), _plan(3, "x" * 40)]
        rows = plans_keyboard(plans, {}, back_callback="shop:list").inline_keyboard
        self.assertEqual([len(r) for r in rows], [2, 1, 1])

    def test_services_are_capped_and_two_columns(self) -> None:
        services = [SimpleNamespace(id=i, pg_username=f"u{i}") for i in range(LIST_BUTTON_CAP + 5)]
        rows = services_keyboard(services, {}).inline_keyboard
        self.assertEqual(sum(len(r) for r in rows), LIST_BUTTON_CAP)
        self.assertTrue(all(len(r) <= 2 for r in rows))
        self.assertIn("5", list_overflow_line(len(services)))
        self.assertEqual(list_overflow_line(3), "")


if __name__ == "__main__":
    unittest.main()
