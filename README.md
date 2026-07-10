# CryptoBot — Backtesting de estrategias sobre BTC/USDT

Proyecto de aprendizaje: probar estrategias de trading contra datos históricos reales
antes de arriesgar un solo peso.

## Estructura

- `data/btc_daily.csv` — 1,047 velas diarias de BTC/USDT (Binance, ago 2023 → jul 2026)
- `backtester.py` — motor de simulación con comisiones (0.1%) y slippage (0.05%)
- `strategies.py` — estrategias: Buy & Hold, cruce de medias SMA, reversión RSI
- `run_backtest.py` — corre todo y compara
- `results/` — métricas y curvas de equity

## Uso

```bash
pip install pandas numpy
python run_backtest.py
```

## Resultados actuales (capital inicial $10,000)

| Estrategia | Final | Retorno | Max Drawdown | Sharpe | Trades | Win rate |
|---|---|---|---|---|---|---|
| Buy & Hold | $23,102 | +131% | -53% | 0.86 | 0 | — |
| SMA 20/60 | $15,207 | +52% | -37% | 0.60 | 11 | 45% |
| RSI 30/60 | $12,324 | +23% | -20% | 0.40 | 6 | 83% |

## Lecciones que muestran estos números

1. **Ganarle a Buy & Hold es difícil.** Ambas estrategias "activas" ganaron dinero
   pero menos que simplemente comprar y no hacer nada.
2. **El retorno no es la única métrica.** RSI ganó menos pero su peor caída fue
   -20% vs -53% de Buy & Hold. Menos retorno, muchísimo menos sufrimiento.
3. **Win rate alto ≠ estrategia buena.** RSI acierta 83% de sus trades y aun así
   es la que menos gana: sus ganancias son pequeñas.
4. **Cuidado con el overfitting:** si ajustas los parámetros (20/60, 30/70...) hasta
   que el backtest se vea bonito, solo memorizaste el pasado. La estrategia debe
   probarse en datos que no usaste para diseñarla.

## Cómo funciona el motor (anti-trampas)

- La señal del día D se ejecuta al precio de apertura del día D+1 (no hay
  forma de "mirar el futuro").
- Cada operación paga 0.1% de comisión + 0.05% de slippage por lado.

## Próximos pasos

1. Probar tus propias estrategias (agregar una función en `strategies.py`)
2. Datos horarios en vez de diarios
3. Paper trading en vivo contra la API de Binance
4. Capa de análisis con Claude API (opcional, experimental)

**No es asesoría financiera. Nada de dinero real sin meses de paper trading positivo.**
