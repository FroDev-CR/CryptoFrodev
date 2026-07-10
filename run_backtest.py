"""Corre todas las estrategias sobre BTC/USDT diario y compara resultados."""

import os
import pandas as pd
from backtester import run_backtest
from strategies import ESTRATEGIAS

HERE = os.path.dirname(os.path.abspath(__file__))

df = pd.read_csv(os.path.join(HERE, "data", "btc_daily.csv"), parse_dates=["date"])
print(f"Datos: BTC/USDT diario, {df.date.min().date()} -> {df.date.max().date()} ({len(df)} velas)")
print(f"Capital inicial: $10,000 | Comisión 0.1% + slippage 0.05% por lado\n")

resultados = {}
curvas = {}
for nombre, estrategia in ESTRATEGIAS.items():
    señal = estrategia(df)
    metricas, equity = run_backtest(df, señal)
    resultados[nombre] = metricas
    curvas[nombre] = equity

tabla = pd.DataFrame(resultados).T
print(tabla.to_string())

# Guardar curvas de equity para graficar después
pd.DataFrame(curvas).to_csv(os.path.join(HERE, "results", "equity_curves.csv"))
tabla.to_csv(os.path.join(HERE, "results", "metricas.csv"))
print("\nGuardado en results/: equity_curves.csv y metricas.csv")
