"""Mean-reversion BTC bot for make.fun's "Race a BTC trading bot live for 24 hours".

Strategy (long only, one position, full size):
  - Entry: the 21-bar RSI crosses back above 30 after dipping below it — an
    oversold bounce with confirmation, instead of catching a falling knife.
  - Exit: RSI rises above 75 (overbought), or the position gains 2% over its
    cost (take profit), or it loses 2% against its cost (stop loss).
  - No new entries in the last 120 bars of the 1440-bar window: a trade needs
    time to mature, and a position opened at the end is flattened at the last
    close whether the bounce came or not.
  - Every order caps slippage at 200 bps from the close it was decided on.

The bot speaks agent-fun/bars-replay/v1 through the kit's Python shim
(vendor/makefun_bars.py, a byte-identical copy of sdk/makefun_bars.py). It is
fully deterministic: the RSI runs on float64 + - * / alone over the closes it
has seen, it reads no clock, no environment and no randomness, so two runs on
the same bars send the same orders. Standard library only, no network.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars  # noqa: E402

SYMBOL = "CBBTC"
RSI_BARS = 21
RSI_OVERSOLD = 30.0
RSI_OVERBOUGHT = 75.0
STOP_BPS = 200
TAKE_PROFIT_BPS = 200
# No new entries once fewer than this many bars of the window remain.
NO_ENTRY_LAST_BARS = 120
WINDOW_BARS = 1440
MAX_SLIPPAGE_BPS = 200


class Rsi:
    """Wilder's RSI, updated one close at a time.

    Seeded with the plain mean of the first RSI_BARS gains and losses, then
    smoothed as avg = (avg * (n - 1) + new) / n. RSI is None until seeded.
    """

    def __init__(self, n):
        self.n = n
        self.prev_close = None
        self.seed_gains = []
        self.seed_losses = []
        self.avg_gain = None
        self.avg_loss = None
        self.value = None
        self.prev_value = None

    def push(self, close):
        if self.prev_close is not None:
            delta = close - self.prev_close
            gain = float(delta) if delta > 0 else 0.0
            loss = float(-delta) if delta < 0 else 0.0
            if self.avg_gain is None:
                self.seed_gains.append(gain)
                self.seed_losses.append(loss)
                if len(self.seed_gains) == self.n:
                    self.avg_gain = sum(self.seed_gains) / self.n
                    self.avg_loss = sum(self.seed_losses) / self.n
                    self.value = self._rsi()
            else:
                self.avg_gain = (self.avg_gain * (self.n - 1) + gain) / self.n
                self.avg_loss = (self.avg_loss * (self.n - 1) + loss) / self.n
                self.prev_value = self.value
                self.value = self._rsi()
        self.prev_close = close

    def _rsi(self):
        if self.avg_loss == 0:
            return 100.0
        return 100.0 - 100.0 / (1.0 + self.avg_gain / self.avg_loss)


rsi = Rsi(RSI_BARS)


def on_batch(state, batch):
    # Only a fresh bar for our symbol moves the indicators or the orders.
    bar = None
    for b in batch["bars"]:
        if b["symbol"] == SYMBOL:
            bar = b
            break
    if bar is None:
        return []
    rsi.push(int(bar["c"]))
    if state.warming_up:
        return []

    held = state.positions.get(SYMBOL)
    if held is None:
        # Entry: RSI crossed back above oversold on this bar.
        if rsi.prev_value is None or rsi.value is None:
            return []
        if rsi.prev_value >= RSI_OVERSOLD or rsi.value < RSI_OVERSOLD:
            return []
        if state.seq >= state.warmup_bars + WINDOW_BARS - NO_ENTRY_LAST_BARS:
            return []
        cash = state.cash
        min_notional = int(state.hello["fees"]["min_notional_quote_units"])
        if cash < min_notional:
            return []
        return [{
            "side": "buy",
            "symbol": SYMBOL,
            "notional_quote_units": cash,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]

    # Exit: overbought, take profit, or stop loss (all re-checked every bar,
    # so a refused sell is sent again while its reason still holds).
    if rsi.value is not None and rsi.value > RSI_OVERBOUGHT:
        return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    worth = state.value(SYMBOL, held.qty)
    if worth * 10000 > held.cost * (10000 + TAKE_PROFIT_BPS):
        return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    if worth * 10000 < held.cost * (10000 - STOP_BPS):
        return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
