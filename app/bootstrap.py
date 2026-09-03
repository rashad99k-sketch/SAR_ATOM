"""Application bootstrap boundary.

Keeps process startup separate from the trading kernel, scanner, portfolio,
and dashboard modules.
"""
from __future__ import annotations
import os
import threading
from dotenv import load_dotenv

load_dotenv()

import core.engine as E
import scanner.scanner as S
import core.runtime as R
from dashboard import app as DASHBOARD_APP

# Compatibility wiring: the preserved kernel remains the execution authority.
for name in getattr(S, "SCANNER_EXPORTS", []):
    if hasattr(S, name):
        setattr(E, name, getattr(S, name))
for name in getattr(R, "RUNTIME_EXPORTS", []):
    if hasattr(R, name):
        setattr(E, name, getattr(R, name))
for name in (
    "get_usdt_perp_symbols", "scan_market_rf", "smart_scanner_v2",
    "monitor_watchlist", "rebuild_radar_watchlist", "refresh_radar_watchlist",
    "global_discovery_scan", "promote_to_queue", "process_queue_entry",
    "build_rf_dashboard", "run_scanner_v2", "sniper_engine_v2",
    "update_institutional_flow_scanner", "live_institutional_updater",
    "build_40_symbol_universe", "WatchlistRotation", "SNIPER_MODE",
    "CANDIDATE_SCAN_INTERVAL",
):
    if hasattr(S, name):
        setattr(E, name, getattr(S, name))
for name in getattr(R, "RUNTIME_EXPORTS", []):
    if hasattr(R, name):
        setattr(E, name, getattr(R, name))


def run() -> None:
    print("=" * 72)
    print("RF LIQUIDITY PRO — MULTI-MARKET WINDOWS BUILD")
    print(f"MODE: {'LIVE' if E.MODE_LIVE else 'PAPER'}")
    print(f"MAX OPEN POSITIONS: {R.PORTFOLIO.max_positions}")
    print("MARKETS: CRYPTO | STOCKS | INDICES | GOLD | OIL")
    print("NEWS: ENABLED" if os.getenv("NEWS_ENABLED", "true").lower() in {"1", "true", "yes", "on"} else "NEWS: DISABLED")
    print("=" * 72)

    threading.Thread(target=R.keep_alive, daemon=True, name="keep_alive").start()
    threading.Thread(target=R.safe_main_loop, args=(DASHBOARD_APP,), daemon=True,
                     name="portfolio_supervisor").start()

    port = int(os.environ.get("PORT", "8000"))
    print(f"[START] Dashboard: http://127.0.0.1:{port}")
    DASHBOARD_APP.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
