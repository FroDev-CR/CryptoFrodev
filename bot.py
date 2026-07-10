"""
Bot de trading BTC/USDT — modo paper (simulado) y live (dinero real).

Uso:
    python bot.py            -> corre en loop según config.json
    python bot.py --once     -> un solo ciclo (para probar)

Estrategia: cruce de medias SMA sobre velas horarias.
El estado se guarda en state.json (sobrevive reinicios).

MODO LIVE: requiere `pip install ccxt`, API keys de Binance SIN permiso
de retiros, y entender que puedes perder el dinero. Los límites
max_usd_por_trade y stop_si_equity_baja_de_usd son obligatorios.
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(HERE, "config.json")))
STATE_FILE = os.path.join(HERE, "state.json")
LOG_FILE = os.path.join(HERE, "results", "trades_log.csv")


# ---------- Datos ----------

def get_klines(symbol: str, interval: str, limit: int = 100) -> list[float]:
    """Cierres de las últimas `limit` velas desde la API pública de Binance."""
    url = (f"https://data-api.binance.vision/api/v3/klines"
           f"?symbol={symbol}&interval={interval}&limit={limit}")
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.load(r)
    return [float(k[4]) for k in data]  # índice 4 = precio de cierre


# ---------- Estrategia ----------

def señal_sma(closes: list[float], fast: int, slow: int) -> int:
    """1 = estar comprado, 0 = estar fuera. Usa solo velas cerradas."""
    cerradas = closes[:-1]  # la última vela aún no cierra: no usarla
    sma_fast = sum(cerradas[-fast:]) / fast
    sma_slow = sum(cerradas[-slow:]) / slow
    return 1 if sma_fast > sma_slow else 0


# ---------- Estado ----------

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))
    return {"usd": CONFIG["paper"]["capital_inicial_usd"], "btc": 0.0,
            "posicion": 0, "trades": 0, "creado": str(datetime.now(timezone.utc))}


def save_state(state: dict):
    json.dump(state, open(STATE_FILE, "w"), indent=2)


def log_trade(accion: str, precio: float, equity: float, modo: str):
    nuevo = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a") as f:
        if nuevo:
            f.write("fecha_utc,modo,accion,precio,equity\n")
        f.write(f"{datetime.now(timezone.utc).isoformat()},{modo},{accion},{precio:.2f},{equity:.2f}\n")


# ---------- Ejecución de órdenes ----------

def comprar_paper(state, precio):
    fee = CONFIG["fee_por_lado"]
    state["btc"] = (state["usd"] * (1 - fee)) / precio
    state["usd"] = 0.0


def vender_paper(state, precio):
    fee = CONFIG["fee_por_lado"]
    state["usd"] = state["btc"] * precio * (1 - fee)
    state["btc"] = 0.0


def get_exchange():
    import ccxt  # pip install ccxt
    live = CONFIG["live"]
    if "AQUI" in live["api_key"]:
        sys.exit("ERROR: pon tus API keys reales en config.json (sección live).")
    return ccxt.binance({"apiKey": live["api_key"], "secret": live["api_secret"]})


def comprar_live(state, precio):
    ex = get_exchange()
    usd = min(CONFIG["live"]["max_usd_por_trade"],
              ex.fetch_balance()["USDT"]["free"])
    if usd < 5:
        print("  [live] Saldo USDT insuficiente para el mínimo de orden (~$5).")
        return
    orden = ex.create_market_buy_order("BTC/USDT", usd / precio)
    state["btc"] = float(orden["filled"])
    state["usd"] = 0.0
    print(f"  [live] COMPRA ejecutada: {orden['filled']} BTC")


def vender_live(state, precio):
    ex = get_exchange()
    btc = ex.fetch_balance()["BTC"]["free"]
    if btc * precio < 5:
        print("  [live] Posición BTC demasiado pequeña para vender.")
        return
    orden = ex.create_market_sell_order("BTC/USDT", btc)
    state["usd"] = float(orden["cost"])
    state["btc"] = 0.0
    print(f"  [live] VENTA ejecutada: {btc} BTC")


# ---------- Ciclo principal ----------

def ciclo():
    modo = CONFIG["mode"]
    s = CONFIG["strategy"]
    state = load_state()

    closes = get_klines(CONFIG["symbol"], CONFIG["interval"], s["sma_slow"] + 2)
    precio = closes[-1]
    señal = señal_sma(closes, s["sma_fast"], s["sma_slow"])
    equity = state["usd"] + state["btc"] * precio

    # Kill-switch en modo live
    if modo == "live" and equity < CONFIG["live"]["stop_si_equity_baja_de_usd"]:
        print(f"KILL-SWITCH: equity ${equity:.2f} bajo el límite. Bot detenido.")
        sys.exit(1)

    accion = "esperar"
    if señal == 1 and state["posicion"] == 0:
        (comprar_live if modo == "live" else comprar_paper)(state, precio)
        state["posicion"], accion = 1, "COMPRA"
        state["trades"] += 1
    elif señal == 0 and state["posicion"] == 1:
        (vender_live if modo == "live" else vender_paper)(state, precio)
        state["posicion"], accion = 0, "VENTA"
        state["trades"] += 1

    equity = state["usd"] + state["btc"] * precio
    if accion != "esperar":
        log_trade(accion, precio, equity, modo)
    save_state(state)

    # Snapshot para el dashboard
    eq_log = os.path.join(HERE, "results", "equity_log.csv")
    nuevo = not os.path.exists(eq_log)
    with open(eq_log, "a") as f:
        if nuevo:
            f.write("fecha_utc,precio,equity,posicion,senal\n")
        f.write(f"{datetime.now(timezone.utc).isoformat()},{precio:.2f},{equity:.4f},{state['posicion']},{señal}\n")

    inicial = CONFIG["paper"]["capital_inicial_usd"]
    pnl = (equity / inicial - 1) * 100
    hora = datetime.now(timezone.utc).strftime("%H:%M UTC")
    pos = "COMPRADO" if state["posicion"] else "FUERA"
    print(f"[{hora}] [{modo}] BTC ${precio:,.0f} | señal={'alcista' if señal else 'bajista'} "
          f"| {pos} | acción: {accion} | equity ${equity:.2f} ({pnl:+.2f}%) | trades: {state['trades']}")


if __name__ == "__main__":
    if CONFIG["mode"] == "live":
        print("*** MODO LIVE: dinero real. Ctrl+C para detener. ***")
    if "--once" in sys.argv:
        ciclo()
    else:
        print(f"Bot corriendo. Revisa cada {CONFIG['check_every_seconds']}s. Ctrl+C para salir.")
        while True:
            try:
                ciclo()
            except Exception as e:
                print(f"Error (reintento en 60s): {e}")
                time.sleep(60)
                continue
            time.sleep(CONFIG["check_every_seconds"])
