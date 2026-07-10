// Función serverless de Vercel: el cerebro del FRODEV-3000.
// La GEMINI_API_KEY vive como variable de entorno en Vercel, nunca en el navegador.
// Intenta con un modelo rápido y si está saturado reintenta con otro.

const MODELOS = [
  process.env.GEMINI_MODEL || "gemini-3.1-flash-lite",
  "gemini-flash-latest",
];

async function llamarGemini(model, key, system, contents) {
  const r = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${key}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: system }] },
        contents,
        generationConfig: { maxOutputTokens: 1024, temperature: 0.8 },
      }),
    }
  );
  const j = await r.json();
  if (j?.error) return { error: j.error.message || j.error.status };
  const text = j?.candidates?.[0]?.content?.parts?.map(p => p.text).join("") || "";
  return text ? { text } : { error: "respuesta vacia" };
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "solo POST" });
  }
  const key = process.env.GEMINI_API_KEY;
  if (!key) {
    return res.status(200).json({ text: "[ERROR] Falta GEMINI_API_KEY en las variables de entorno de Vercel." });
  }

  const { messages = [], contexto = {} } = req.body || {};

  const system = `Eres FRODEV-3000, un asistente robot retro-futurista del año 2000 que vive
en una pagina de trading llamada CryptoFroDev. Personalidad: hablas como robot ochentero-noventero
simpatico, con toques ticos sutiles (mae, tuanis) y ocasionales PALABRAS EN MAYUSCULA estilo
terminal. Respuestas CORTAS: maximo 60 palabras.

Contexto en vivo de la pagina: ${JSON.stringify(contexto)}.
La pagina muestra: velas de BTC/USDT de 1 hora, dos medias moviles (SMA 20 cian, SMA 60 magenta),
y una ventana NUBE.EXE con el bot 24/7 que corre en GitHub Actions cada 15 min: un portafolio
compartido de $15 ficticios con su grafica de equity historica. Compra cuando la SMA 20 cruza
arriba de la SMA 60 y vende al cruce contrario (comision simulada 0.1%).

Reglas estrictas:
- Explicas conceptos de trading y que hace el bot, con datos del contexto.
- JAMAS des consejos de inversion ni digas si comprar o vender. Si te lo piden, recuerda
  que eres un robot demo y que nada aqui es asesoria financiera.
- Si preguntan algo fuera de tema, responde breve y regresa al trading.`;

  const contents = messages.slice(-8).map((m) => ({
    role: m.role === "user" ? "user" : "model",
    parts: [{ text: String(m.text || "").slice(0, 500) }],
  }));

  try {
    let ultimo = "";
    for (const model of MODELOS) {
      const r = await llamarGemini(model, key, system, contents);
      if (r.text) return res.status(200).json({ text: r.text });
      ultimo = r.error;
    }
    return res.status(200).json({ text: `[ERROR DE GOOGLE] ${ultimo}` });
  } catch (e) {
    return res.status(200).json({ text: `[FALLO DE ENLACE] ${e.message || "mi cerebro no responde"}` });
  }
}
