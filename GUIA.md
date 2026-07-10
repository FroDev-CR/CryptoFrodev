# Guía: arrancar el bot hoy

## Paso 1 — Modo paper (hoy mismo, 5 minutos)

Necesitas Python 3.10+ instalado. En una terminal, dentro de la carpeta `cryptobot`:

```bash
python bot.py
```

Ya está. Cada 5 minutos verás una línea como:

```
[17:18 UTC] [paper] BTC $63,900 | señal=alcista | COMPRADO | acción: esperar | equity $15.20 (+1.33%) | trades: 2
```

- `señal` — lo que la estrategia opina ahora (SMA 20/60 en velas de 1 hora)
- `COMPRADO / FUERA` — si el bot tiene posición
- `equity` — cuánto valen tus $15 simulados en este momento
- El historial de operaciones queda en `results/trades_log.csv`
- Si cierras la terminal y lo vuelves a abrir, continúa donde iba (`state.json`)

Con velas de 1 hora el bot opera cada varios días. La mayoría de los ciclos
dirán "esperar" — eso es normal y correcto. Un bot que opera a cada rato
solo enriquece al exchange.

## Paso 2 — Modo live (cuando tu cuenta esté lista)

**Antes necesitas:**

1. Cuenta en Binance verificada (KYC) — toma de horas a un día
2. Depositar tus $15 en USDT
3. Crear una API key en Binance: perfil → API Management
   - Habilitar SOLO "Enable Spot Trading"
   - **NUNCA habilitar "Enable Withdrawals"** — así, aunque roben la key, no pueden sacar tu dinero
4. `pip install ccxt`

**Luego en `config.json`:**

```json
"mode": "live",
"live": {
  "api_key": "tu_key",
  "api_secret": "tu_secret",
  "max_usd_por_trade": 15.0,
  "stop_si_equity_baja_de_usd": 10.0
}
```

Y borra `state.json` para empezar de cero. El bot:

- Nunca compra más de `max_usd_por_trade`
- Se apaga solo si tu cuenta cae debajo de `stop_si_equity_baja_de_usd`
  (kill-switch: con $15 y stop en $10, tu pérdida máxima es ~$5)

## Expectativas honestas con $15

- Mínimo por orden en Binance: ~$5. Con $15 juegas con 1 posición.
- Cada operación paga ~0.1% de comisión: 1.5 centavos por trade.
- En un mes bueno quizás ganes o pierdas $1-3. El objetivo NO es la plata,
  es aprender el flujo completo con riesgo acotado.

## Reglas de supervivencia

1. No apagues el bot porque va perdiendo — las rachas malas son parte de toda estrategia.
2. No le subas el capital porque tuvo una semana buena.
3. No toques los parámetros (20/60) cada vez que pierde: eso es sobreajustar.
4. Revisa `trades_log.csv` semanalmente, no cada hora.
5. Guarda las API keys solo en `config.json` local. Jamás las subas a GitHub.

*Nada de esto es asesoría financiera; es un proyecto educativo con riesgo real acotado.*
