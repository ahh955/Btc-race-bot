# Btc-race-bot

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/ahh955/Btc-race-bot/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/ahh955/Btc-race-bot/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A mean-reversion bot that trades Coinbase Wrapped BTC (cbBTC) against USDC on 1-minute on-chain bars, with $1,000 of paper money — simulation only, no real money is traded.

Strategy: buy the full cash balance when the 21-bar RSI crosses back above 30 after dipping below it (an oversold bounce with confirmation, not a falling knife). Sell the whole position when RSI rises above 75, when the position gains 2% over its cost, or when it loses 2% against its cost. No new entries in the last 120 bars of the window, so every trade has time to mature before the final flatten. Every order caps slippage at 200 bps from the close it was decided on. Fully deterministic: the RSI runs on the closes seen so far only, with no clock, no network and no randomness, so two runs on the same bars send identical orders.

On the kit's frozen 24-hour dev window the bot made +$23.55 net PnL after all fees (6 trades, max drawdown 1.70%), clearing the dev gate. Past-window profit is no promise about the race window.

## Run it

```sh
python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=xsff4jzh&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>
