# Changelog — RF Liquidity Pro

## 2026-08-19

### Architecture
- Reduced `main.py` to startup/orchestration only.
- Added explicit `strategy`, `portfolio`, `execution`, `news`, `config`, and `scanner/deep_scanner` boundaries.
- Preserved the supplied 9,885-line source as `source_original_mBOT_1.py`.
- Kept the existing RF/Institutional core as the compatibility kernel instead of performing a risky all-at-once rewrite.

### Portfolio
- Added per-symbol state isolation around the legacy single-position engine.
- Added configurable `MAX_OPEN_POSITIONS` with default 6.
- Added portfolio ranking and multi-position supervision.
- Dashboard now displays all active positions and available capacity.
- Manual dashboard trades use the same portfolio boundary.

### Deep Scanner
- Added venue-wide crypto discovery.
- Added configurable Gold/Oil/Index/Stock symbols with strict venue validation.
- Added institutional scoring, momentum/flow evidence, narrative evidence, and news risk adjustment.
- Added ranked portfolio candidates.

### News
- Added optional RSS event-risk service.
- News is advisory only; unavailable feeds do not block the strategy.

### Reliability
- Fixed the paper-mode close/finalization ordering bug.
- Added a safe fallback for paper-mode mark price during finalization.
- Fixed runtime orchestration so `keep_alive` and `safe_main_loop` are actually provided by `core.runtime`.
- Expanded compile and structural tests.

### Validation
- Full first-party Python compilation passes.
- Portfolio isolation test passes.
- News scoring test passes.

## Known limitation
Live non-crypto execution requires the connected broker/exchange to expose those instruments. The build deliberately does not fake support for assets that are absent from the venue.

## 2026-08-19 — Windows Test Runner Hotfix
- Fixed `tests/test_news_service.py` leaking a fake `requests` module into `sys.modules`.
- The leak caused the dashboard import test to fail inside CCXT with `cannot import name 'Session' from requests`.
- News tests now patch `requests.get` locally without replacing the real Requests package.

## 2026-08-19 — Modular Portfolio + Deep Radar Hardening

- Fixed dashboard `/` crash caused by an unescaped JavaScript object literal inside a Python f-string.
- Added canonical `core.engine.get_smart_zones()` so strategy/deep paths do not depend on scanner import order.
- Upgraded DeepScanner to staged venue-wide radar -> deep institutional analysis -> news risk -> ranked candidates.
- Added asset-class discovery for crypto, gold, oil, indices and venue-exposed stocks.
- Kept non-supported instruments explicit: unavailable venue instruments are skipped, never fabricated.
- Enabled six-position portfolio capacity with portfolio-safe default sizing: 10% margin per position and 60% aggregate cap.
- Added configurable per-asset-class exposure cap.
- Added Deep Institutional Radar panel to the existing dashboard.
- Added regression tests for the dashboard crash, smart-zone provider and six-position sizing policy.

## 2026-08-20 — Institutional Queue Hardening

- Changed the engine's implicit default to PAPER mode when `PAPER_MODE` is absent; LIVE still requires explicit credentials and `PAPER_MODE=False`.
- Reworked Execution Queue order-block scoring to require a causal displacement leg, volume support, freshness/touch count, and broken-zone detection instead of treating the latest candle wick as an order block.
- Added a hard institutional readiness gate: READY now requires persistent confirmation plus minimum order-block, liquidity, institutional-confidence, and structure scores.
- Added regression coverage for fake-vs-causal order blocks, the institutional READY gate, and safe paper defaults.
- Windows launcher now installs dependencies only when imports are missing, avoiding unnecessary network/package operations on every restart.

## 2026-09-03 — External Intelligence + reliability hardening
- Added alert-only Finviz/OpenInsider/SEC EDGAR intelligence providers.
- Added multi-source evidence fusion with conservative BUY-bias gating.
- Added dashboard publication and Telegram alerting for high-confidence external setups.
- Added bounded HTTP timeout/cache/retry layer for external providers.
- Set CCXT exchange timeout from environment (default 10s).
- Removed packaged `.env` credentials and sanitized `.env.example`.
- Updated stale pipeline test expectation to match the existing ATOM hard-reject invariant for over-mitigated zones.
