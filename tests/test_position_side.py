import os
import re
import unittest
from unittest import mock

os.environ.setdefault("PAPER_MODE", "False")

import core.engine as engine

from core.engine import OrderManager


class _MockExchange:
    """Records create_order params so tests can assert the exact BingX payload."""

    def __init__(self):
        self.created = []
        self.fetch_order = lambda *a, **k: {"status": "closed", "filled": 1.0}
        self.fetch_positions = lambda *a, **k: []
        self.amount_to_precision = lambda sym, qty: qty

    def create_order(self, sym, order_type, side, amount, params=None):
        params = params or {}
        self.created.append(
            {"sym": sym, "type": order_type, "side": side, "amount": amount, "params": params}
        )
        return {"id": "mock-order-id", "status": "closed"}


def _patch_market_registry():
    engine.ex.markets = {
        "BTC/USDT:USDT": {},
        "BTC/USDT": {},
        "BTC:-USDT": {},
    }


class PositionSideOpenOrders(unittest.TestCase):
    BINGX_SAFE_CHARS = re.compile(r"^[A-Za-z0-9_]+$")

    def setUp(self):
        _patch_market_registry()
        self.ex = _MockExchange()
        self.mgr = OrderManager(self.ex)

    def _assert_order_ok(self, sym, side, params):
        self.assertEqual(params.get("positionSide"), "BOTH",
                         "Open order must send positionSide BOTH (one-way mode)")
        cid = params.get("clientOrderId", "")
        self.assertLessEqual(len(cid), 40)
        self.assertRegex(cid, self.BINGX_SAFE_CHARS)

    def test_buy_open_sends_position_side_both(self):
        self.mgr.submit_order("BTC/USDT:USDT", "buy", 0.01, 10)
        self.assertEqual(len(self.ex.created), 1)
        rec = self.ex.created[0]
        self.assertEqual(rec["side"], "buy")
        self.assertEqual(rec["params"]["leverage"], 10)
        self._assert_order_ok(rec["sym"], "buy", rec["params"])

    def test_sell_open_sends_position_side_both(self):
        self.mgr.submit_order("BTC/USDT:USDT", "sell", 0.01, 10)
        self.assertEqual(len(self.ex.created), 1)
        rec = self.ex.created[0]
        self.assertEqual(rec["side"], "sell")
        self._assert_order_ok(rec["sym"], "sell", rec["params"])

    def test_explicit_short_client_order_id_keeps_position_side_both(self):
        self.mgr.submit_order("BTC/USDT:USDT", "buy", 0.01, 10,
                              client_order_id="short_cid")
        rec = self.ex.created[0]
        self.assertEqual(rec["params"]["clientOrderId"], "short_cid")
        self.assertEqual(rec["params"]["positionSide"], "BOTH")


class PositionSideCloseOrders(unittest.TestCase):
    def setUp(self):
        _patch_market_registry()
        engine.PAPER_MODE = False
        engine._closing_in_progress = False
        engine._reconciliation_pending = False
        engine.STATE["open"] = True
        engine.STATE["current_symbol"] = "BTC/USDT:USDT"
        engine.STATE["remaining_qty"] = 0.1
        engine.ex = _MockExchange()

        self.patches = [
            mock.patch.object(engine, "fetch_position",
                              return_value=None),
            mock.patch.object(engine, "verify_order_filled",
                              return_value=(True, 0.05)),
            mock.patch.object(engine, "finalize_trade_with_reality",
                              return_value=None),
            mock.patch.object(engine, "_exchange_sync"),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in self.patches])

    def _captured_create_call(self):
        for rec in engine.ex.created:
            return rec
        return None

    def test_close_partial_buy_side_sends_both(self):
        engine.STATE["side"] = "BUY"
        engine.close_partial(0.5)
        rec = self._captured_create_call()
        self.assertIsNotNone(rec)
        self.assertEqual(rec["side"], "sell")
        self.assertEqual(rec["params"]["reduceOnly"], True)
        self.assertEqual(rec["params"]["positionSide"], "BOTH")

    def test_close_partial_sell_side_sends_both(self):
        engine.STATE["side"] = "SELL"
        engine.close_partial(0.5)
        rec = self._captured_create_call()
        self.assertIsNotNone(rec)
        self.assertEqual(rec["side"], "buy")
        self.assertEqual(rec["params"]["reduceOnly"], True)
        self.assertEqual(rec["params"]["positionSide"], "BOTH")

    def test_close_position_full_buy_sends_both(self):
        engine.STATE["side"] = "BUY"
        engine.close_position_full()
        rec = self._captured_create_call()
        self.assertIsNotNone(rec)
        self.assertEqual(rec["side"], "sell")
        self.assertEqual(rec["params"]["reduceOnly"], True)
        self.assertEqual(rec["params"]["positionSide"], "BOTH")

    def test_close_position_full_sell_sends_both(self):
        engine.STATE["side"] = "SELL"
        engine.close_position_full()
        rec = self._captured_create_call()
        self.assertIsNotNone(rec)
        self.assertEqual(rec["side"], "buy")
        self.assertEqual(rec["params"]["reduceOnly"], True)
        self.assertEqual(rec["params"]["positionSide"], "BOTH")

    def test_close_position_function_sends_both(self):
        engine.STATE["side"] = "BUY"
        engine.PAPER_MODE = False
        engine.close_position(0.1, "BTC/USDT:USDT")
        recs = [r for r in engine.ex.created]
        self.assertTrue(recs, "close_position should place an order")
        for rec in recs:
            self.assertEqual(rec["params"]["reduceOnly"], True)
            self.assertEqual(rec["params"]["positionSide"], "BOTH")


if __name__ == "__main__":
    unittest.main()
