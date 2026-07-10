"""
Bot 24/7 en la nube — corre en GitHub Actions cada 15 minutos.

Paper trading con $15 ficticios, estrategia SMA 20/60 en velas de 1h.
- Datos: API pública de Kraken (accesible desde los servidores de GitHub)
- Estado: un Gist de GitHub (estado.json) que la web lee en vivo

Variables de entorno requeridas (GitHub Secrets):
    GIST_ID     -> el id del gist (lo que va después de tu usuario en la URL)
    GIST_TOKEN  -> token clásico con scope "gist"
"""

import json
import os
import time
import urllib.request
from datetime import datetime, timezone

FEE = 0.001
CAPITAL = 15.0
SMA_FAST, SMA_SLOW = 20, 60

GIST_ID = os.environ["GIST_ID"]
TOKEN = os.environ["GIST_TOKEN"]
API_GIST = f"https://api.github.com/gists/{GIST_ID}"


# ---------- Gist (estado compartido) ----------

def _gh(req: urllib.request.Request):
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "cryptofrodev-bot")
    return urllib.request.urlopen(req, timeout=30)

def leer_estado() -> dict:
    with _gh(urllib.request.Request(API_GIST)) as r:
        g = json.load(r)
    try:
        return json.loads(g["files"]["estado.json"]["content"])
    except (KeyError, json.JSONDecodeError):
        return {}

def guardar_estado(st: dict):
    body = json.dumps({"files": {"estado.json":
                       {"content": json.dumps(st, indent=1)}}}).encode()
    req = urllib.request.Request(API_GIST, data=body, method="PATCH")
    with _gh(req) as r:
        r.read()


# ---------- Mercado (Kraken) ----------

def get_closes() -> list:
    """Cierres de las últimas ~SMA_SLOW+2 velas de 1h de BTC/USD."""
    since = int(time.time()) - (SMA_SLOW + 3) * 3600
    url = f"https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=60&since={since}"
    with urllib.request.urlopen(url, timeout=20) as r:
        j = json.load(r)
    if j.get("error"):
        raise RuntimeError(f"Kraken: {j['error']}")
    key = next(k for k in j["result"] if k != "last")
    return [float(c[4]) for c in j["result"][key]]


# ---------- Un ciclo ----------

def ciclo():
    closes = get_closes()
    precio = closes[-1]
    cerradas = closes[:-1]  # la última vela aún no cierra
    señal = 1 if (sum(cerradas[-SMA_FAST:]) / SMA_FAST >
                  sum(cerradas[-SMA_SLOW:]) / SMA_SLOW) else 0

    st = leer_estado()
    if not st:
        st = {"usd": CAPITAL, "btc": 0.0, "posicion": 0, "trades": [],
              "historia": [], "creado": datetime.now(timezone.utc).isoformat()}

    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    accion = "esperar"
    if señal == 1 and st["posicion"] == 0:
        st["btc"] = (st["usd"] * (1 - FEE)) / precio
        st["usd"] = 0.0
        st["posicion"] = 1
        accion = "COMPRA"
    elif señal == 0 and st["posicion"] == 1:
        st["usd"] = st["btc"] * precio * (1 - FEE)
        st["btc"] = 0.0
        st["posicion"] = 0
        accion = "VENTA"

    equity = st["usd"] + st["btc"] * precio
    if accion != "esperar":
        st["trades"].append({"t": ahora, "a": accion,
                             "p": round(precio, 2), "eq": round(equity, 4)})
        st["trades"] = st["trades"][-50:]

    st["historia"].append({"t": ahora, "eq": round(equity, 4)})
    st["historia"] = st["historia"][-2000:]
    st.update({"precio": round(precio, 2), "senal": señal,
               "equity": round(equity, 4), "capital_inicial": CAPITAL,
               "ultima_revision": ahora})
    guardar_estado(st)

    pnl = (equity / CAPITAL - 1) * 100
    print(f"[{ahora}] BTC ${precio:,.0f} | señal={'alcista' if señal else 'bajista'} "
          f"| {'COMPRADO' if st['posicion'] else 'FUERA'} | acción: {accion} "
          f"| equity ${equity:.2f} ({pnl:+.2f}%) | trades: {len(st['trades'])}")


if __name__ == "__main__":
    ciclo()
