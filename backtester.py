"""
Motor de backtesting simple (long-only, all-in/all-out).

Reglas del motor — importantes para que el resultado sea realista:
1. La señal se calcula con datos hasta el cierre del día D.
2. La orden se ejecuta al OPEN del día D+1 (no puedes comprar en el pasado).
3. Cada operación paga comisión (fee) y slippage.
"""

import pandas as pd
import numpy as np

FEE = 0.001       # 0.1% por lado (tarifa típica de exchange spot)
SLIPPAGE = 0.0005 # 0.05% de deslizamiento por lado


def run_backtest(df: pd.DataFrame, signal: pd.Series, capital_inicial: float = 10_000):
    """
    df: DataFrame con columnas date, open, high, low, close.
    signal: Serie alineada con df. 1 = quiero estar comprado, 0 = quiero estar fuera.
            Calculada SOLO con información disponible al cierre de cada día.
    Devuelve dict de métricas y la curva de equity.
    """
    # La señal del día D se ejecuta al open del día D+1
    position = signal.shift(1).fillna(0).astype(int)

    cash = capital_inicial
    btc = 0.0
    equity = []
    trades = []          # (precio_entrada, precio_salida)
    entry_price = None

    for i in range(len(df)):
        o, c = df["open"].iloc[i], df["close"].iloc[i]
        pos_hoy = position.iloc[i]
        pos_ayer = position.iloc[i - 1] if i > 0 else 0

        if pos_hoy == 1 and pos_ayer == 0:      # comprar al open
            precio = o * (1 + SLIPPAGE)
            btc = (cash * (1 - FEE)) / precio
            cash = 0.0
            entry_price = precio
        elif pos_hoy == 0 and pos_ayer == 1:    # vender al open
            precio = o * (1 - SLIPPAGE)
            cash = btc * precio * (1 - FEE)
            trades.append((entry_price, precio))
            btc = 0.0
            entry_price = None

        equity.append(cash + btc * c)

    equity = pd.Series(equity, index=df["date"].values, name="equity")

    # ---- Métricas ----
    total_ret = equity.iloc[-1] / capital_inicial - 1
    dias = len(df)
    cagr = (equity.iloc[-1] / capital_inicial) ** (365 / dias) - 1
    rolling_max = equity.cummax()
    max_dd = ((equity - rolling_max) / rolling_max).min()
    daily_ret = equity.pct_change().dropna()
    sharpe = np.sqrt(365) * daily_ret.mean() / daily_ret.std() if daily_ret.std() > 0 else 0.0
    wins = sum(1 for e, s in trades if s > e)
    win_rate = wins / len(trades) if trades else float("nan")

    return {
        "capital_final": round(equity.iloc[-1], 2),
        "retorno_total_%": round(total_ret * 100, 2),
        "CAGR_%": round(cagr * 100, 2),
        "max_drawdown_%": round(max_dd * 100, 2),
        "sharpe": round(sharpe, 2),
        "n_trades": len(trades),
        "win_rate_%": round(win_rate * 100, 1) if trades else None,
    }, equity
