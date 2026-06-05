const TICKERS_VALIDOS = ["PETR4", "VALE3", "ITUB4", "BBDC4", "MGLU3", "MXRF11", "HGLG11", "KNRI11"];

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Content-Type": "application/json",
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // GET /cotacoes — última cotação de cada ativo (via view ultima_cotacao)
    if (path === "/cotacoes") {
      return await fetchSupabase(
        `${env.SUPABASE_URL}/rest/v1/ultima_cotacao?select=*&order=symbol.asc`,
        env.SUPABASE_KEY
      );
    }

    // GET /historico?symbol=PETR4&dias=30 — histórico de preço de um ativo
    if (path === "/historico") {
      const symbol = url.searchParams.get("symbol") || "PETR4";
      const dias   = parseInt(url.searchParams.get("dias") || "30");

      if (!TICKERS_VALIDOS.includes(symbol)) {
        return json({ error: `Ativo inválido. Permitidos: ${TICKERS_VALIDOS.join(", ")}` }, 400);
      }

      const diasValidos = [7, 30, 90];
      const periodo = diasValidos.includes(dias) ? dias : 30;

      return await fetchSupabase(
        `${env.SUPABASE_URL}/rest/v1/cotacoes` +
        `?symbol=eq.${symbol}` +
        `&collected_at=gte.${diasAtras(periodo)}` +
        `&order=collected_at.asc` +
        `&select=price,change_pct,collected_at`,
        env.SUPABASE_KEY
      );
    }

    return json({ error: "Rota não encontrada", rotas: ["/cotacoes", "/historico?symbol=PETR4&dias=30"] }, 404);
  },
};

async function fetchSupabase(url, key) {
  try {
    const res = await fetch(url, {
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
      },
    });

    if (!res.ok) {
      const erro = await res.text();
      return json({ error: "Erro ao consultar Supabase", detalhe: erro }, 502);
    }

    const data = await res.json();
    return json(data, 200);
  } catch (e) {
    return json({ error: "Falha na conexão com o banco de dados" }, 503);
  }
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: CORS });
}

function diasAtras(dias) {
  const d = new Date();
  d.setDate(d.getDate() - dias);
  return d.toISOString().split("T")[0]; // "YYYY-MM-DD"
}
