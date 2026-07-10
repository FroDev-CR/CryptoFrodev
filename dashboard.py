"""
Dashboard local del bot. Solo librería estándar, cero dependencias.

    python dashboard.py    ->  abre http://localhost:8000

Lee state.json y los logs que escribe bot.py. El precio en vivo lo trae
tu navegador directo de Binance. Corre en paralelo al bot (dos terminales).
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8000


def leer_datos():
    datos = {"state": None, "trades": [], "equity": [], "config": {}}
    cfg = json.load(open(os.path.join(HERE, "config.json")))
    datos["config"] = {"mode": cfg["mode"], "symbol": cfg["symbol"],
                       "interval": cfg["interval"], "strategy": cfg["strategy"],
                       "capital_inicial": cfg["paper"]["capital_inicial_usd"]}
    sf = os.path.join(HERE, "state.json")
    if os.path.exists(sf):
        datos["state"] = json.load(open(sf))
    tf = os.path.join(HERE, "results", "trades_log.csv")
    if os.path.exists(tf):
        lineas = open(tf).read().strip().split("\n")[1:]
        datos["trades"] = [dict(zip(["fecha", "modo", "accion", "precio", "equity"],
                                    l.split(","))) for l in lineas][-20:]
    ef = os.path.join(HERE, "results", "equity_log.csv")
    if os.path.exists(ef):
        lineas = open(ef).read().strip().split("\n")[1:]
        puntos = [l.split(",") for l in lineas][-500:]
        datos["equity"] = [{"t": p[0], "precio": float(p[1]), "eq": float(p[2]),
                            "pos": int(p[3]), "senal": int(p[4])} for p in puntos]
    return datos


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, contenido, tipo="text/html"):
        self.send_response(200)
        self.send_header("Content-Type", f"{tipo}; charset=utf-8")
        self.end_headers()
        self.wfile.write(contenido.encode())

    def do_GET(self):
        if self.path == "/api/datos":
            self._send(json.dumps(leer_datos()), "application/json")
        else:
            self._send(HTML)


HTML = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CryptoBot</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root { --bg:#0d1117; --card:#161b22; --border:#30363d; --txt:#e6edf3;
          --mut:#8b949e; --verde:#3fb950; --rojo:#f85149; --azul:#58a6ff; --ambar:#d29922; }
  * { margin:0; box-sizing:border-box; font-family:'Segoe UI',system-ui,sans-serif; }
  body { background:var(--bg); color:var(--txt); padding:24px; max-width:960px; margin:auto; }
  h1 { font-size:20px; font-weight:600; display:flex; align-items:center; gap:10px; }
  .badge { font-size:11px; padding:3px 10px; border-radius:20px; font-weight:600; }
  .paper { background:#1f6feb33; color:var(--azul); }
  .live  { background:#f8514933; color:var(--rojo); }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin:20px 0; }
  .card { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px; }
  .card .lbl { font-size:12px; color:var(--mut); margin-bottom:6px; }
  .card .val { font-size:24px; font-weight:600; }
  .verde { color:var(--verde); } .rojo { color:var(--rojo); } .ambar { color:var(--ambar); }
  .chartbox { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px; margin-bottom:20px; height:280px; position:relative; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th { text-align:left; color:var(--mut); font-weight:500; padding:8px; border-bottom:1px solid var(--border); }
  td { padding:8px; border-bottom:1px solid var(--border); }
  .mut { color:var(--mut); font-size:12px; margin-top:16px; text-align:center; }
</style></head><body>
<h1>CryptoBot <span id="modo" class="badge paper">paper</span>
    <span id="estado" class="badge" style="background:#23863633;color:var(--verde)">conectando...</span></h1>

<div class="grid">
  <div class="card"><div class="lbl">BTC ahora</div><div class="val" id="precio">—</div></div>
  <div class="card"><div class="lbl">Tu equity</div><div class="val" id="equity">—</div></div>
  <div class="card"><div class="lbl">Ganancia/pérdida</div><div class="val" id="pnl">—</div></div>
  <div class="card"><div class="lbl">Posición</div><div class="val" id="pos">—</div></div>
  <div class="card"><div class="lbl">Señal</div><div class="val" id="senal">—</div></div>
  <div class="card"><div class="lbl">Trades</div><div class="val" id="trades">—</div></div>
</div>

<div class="chartbox"><canvas id="chart"></canvas></div>

<div class="card">
  <div class="lbl" style="margin-bottom:10px">Últimas operaciones</div>
  <table><thead><tr><th>Fecha</th><th>Modo</th><th>Acción</th><th>Precio</th><th>Equity</th></tr></thead>
  <tbody id="tbody"><tr><td colspan="5" style="color:var(--mut)">Sin operaciones todavía — el bot está esperando su momento.</td></tr></tbody></table>
</div>
<p class="mut">Se actualiza cada 10 s · el bot decide según config.json · esto no es asesoría financiera</p>

<script>
let chart;
const fmt = n => '$' + n.toLocaleString('en-US', {maximumFractionDigits: 2});

async function precioVivo() {
  try {
    const r = await fetch('https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT');
    const j = await r.json();
    document.getElementById('precio').textContent = fmt(parseFloat(j.price));
  } catch(e) {}
}

async function refrescar() {
  try {
    const d = await (await fetch('/api/datos')).json();
    const m = document.getElementById('modo');
    m.textContent = d.config.mode; m.className = 'badge ' + d.config.mode;
    document.getElementById('estado').textContent = d.state ? 'bot activo' : 'bot sin arrancar';

    if (d.state) {
      const ult = d.equity.length ? d.equity[d.equity.length-1] : null;
      const eq = ult ? ult.eq : d.state.usd;
      const ini = d.config.capital_inicial;
      const pnl = (eq/ini - 1) * 100;
      document.getElementById('equity').textContent = fmt(eq);
      const p = document.getElementById('pnl');
      p.textContent = (pnl>=0?'+':'') + pnl.toFixed(2) + '%';
      p.className = 'val ' + (pnl>=0?'verde':'rojo');
      const pos = document.getElementById('pos');
      pos.textContent = d.state.posicion ? 'COMPRADO' : 'FUERA';
      pos.className = 'val ' + (d.state.posicion?'verde':'ambar');
      if (ult) {
        const s = document.getElementById('senal');
        s.textContent = ult.senal ? 'alcista' : 'bajista';
        s.className = 'val ' + (ult.senal?'verde':'rojo');
      }
      document.getElementById('trades').textContent = d.state.trades;
    }

    if (d.trades.length) {
      document.getElementById('tbody').innerHTML = d.trades.slice().reverse().map(t =>
        `<tr><td>${t.fecha.slice(0,16).replace('T',' ')}</td><td>${t.modo}</td>
         <td class="${t.accion==='COMPRA'?'verde':'rojo'}">${t.accion}</td>
         <td>${fmt(parseFloat(t.precio))}</td><td>${fmt(parseFloat(t.equity))}</td></tr>`).join('');
    }

    if (d.equity.length > 1) {
      const labels = d.equity.map(p => p.t.slice(5,16).replace('T',' '));
      const data = d.equity.map(p => p.eq);
      if (!chart) {
        chart = new Chart(document.getElementById('chart'), {
          type:'line',
          data:{ labels, datasets:[{ label:'Equity', data, borderColor:'#58a6ff',
                 borderWidth:2, pointRadius:0, tension:0.3, fill:true,
                 backgroundColor:'#58a6ff1a' }]},
          options:{ responsive:true, maintainAspectRatio:false,
            plugins:{ legend:{display:false} },
            scales:{ x:{ ticks:{color:'#8b949e', maxTicksLimit:8}, grid:{display:false} },
                     y:{ ticks:{color:'#8b949e', callback:v=>'$'+v.toFixed(2)}, grid:{color:'#30363d55'} } } }
        });
      } else {
        chart.data.labels = labels; chart.data.datasets[0].data = data; chart.update('none');
      }
    }
  } catch(e) {}
}

precioVivo(); refrescar();
setInterval(precioVivo, 10000); setInterval(refrescar, 10000);
</script></body></html>"""


if __name__ == "__main__":
    print(f"Dashboard en http://localhost:{PORT}  (Ctrl+C para salir)")
    HTTPServer(("localhost", PORT), Handler).serve_forever()
