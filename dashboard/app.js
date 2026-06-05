const WORKER_URL      = "https://etl-b3-pipeline.vitorcorrea805.workers.dev";
const ACOES           = ["PETR4", "VALE3", "ITUB4", "BBDC4", "MGLU3"];
const FIIS            = ["MXRF11", "HGLG11", "KNRI11"];
const REFRESH_SEG     = 5 * 60;

let chart         = null;
let countdown     = REFRESH_SEG;
let countdownTimer = null;

// ── Formatadores ─────────────────────────────────────────────

function fmtBRL(v) {
  if (v == null) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
}

function fmtPct(v) {
  if (v == null) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}

function fmtVolume(v) {
  if (v == null) return "—";
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K`;
  return v.toLocaleString("pt-BR");
}

function fmtMarketCap(v) {
  if (v == null) return "—";
  if (v >= 1e12) return `R$ ${(v / 1e12).toFixed(1)} tri`;
  if (v >= 1e9)  return `R$ ${(v / 1e9).toFixed(1)} bi`;
  return `R$ ${(v / 1e6).toFixed(1)} mi`;
}

function fmtBRT(utcStr, opcoes) {
  // O banco armazena sem TZ — adiciona Z para forçar leitura como UTC
  return new Date(utcStr + "Z").toLocaleString("pt-BR", {
    timeZone: "America/Sao_Paulo",
    ...opcoes,
  });
}

// ── Fetch ─────────────────────────────────────────────────────

async function fetchComRetry(url, tentativas = 3) {
  for (let i = 0; i < tentativas; i++) {
    try {
      const res = await fetch(url);
      if (res.ok) return res.json();
    } catch (_) {}
    if (i < tentativas - 1) await new Promise(r => setTimeout(r, 1500));
  }
  throw new Error(`Falha após ${tentativas} tentativas: ${url}`);
}

async function fetchCotacoes() {
  return fetchComRetry(`${WORKER_URL}/cotacoes`);
}

async function fetchHistorico(symbol, dias) {
  return fetchComRetry(`${WORKER_URL}/historico?symbol=${symbol}&dias=${dias}`);
}

// ── Cards ─────────────────────────────────────────────────────

function renderCards(data, containerId, tickers) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  tickers.forEach(ticker => {
    const item = data.find(d => d.symbol === ticker);
    if (!item) return;

    const pos  = item.change_pct >= 0;
    const cor  = pos ? "positivo" : "negativo";
    const seta = pos ? "▲" : "▼";

    container.innerHTML += `
      <div class="card">
        <div class="card-symbol">${item.symbol}</div>
        <div class="card-price">${fmtBRL(item.price)}</div>
        <div class="card-change ${cor}">${seta} ${fmtPct(item.change_pct)}</div>
        <div class="card-change-abs ${cor}">${fmtBRL(item.change)}</div>
      </div>`;
  });
}

// ── Tabela ────────────────────────────────────────────────────

function renderTabela(data) {
  const tbody = document.querySelector("#tabela-ativos tbody");
  tbody.innerHTML = "";

  data.forEach(item => {
    const pos  = item.change_pct >= 0;
    const cor  = pos ? "positivo" : "negativo";
    const seta = pos ? "▲" : "▼";

    tbody.innerHTML += `
      <tr>
        <td><strong>${item.symbol}</strong></td>
        <td>${fmtBRL(item.price)}</td>
        <td class="${cor}">${seta} ${fmtPct(item.change_pct)}</td>
        <td>${fmtVolume(item.volume)}</td>
        <td>${fmtMarketCap(item.market_cap)}</td>
        <td class="ts">${fmtBRT(item.collected_at, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</td>
      </tr>`;
  });
}

// ── Gráfico ───────────────────────────────────────────────────

async function renderGrafico(symbol, dias) {
  const data = await fetchHistorico(symbol, dias);

  const labels = data.map(d =>
    fmtBRT(d.collected_at, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })
  );
  const precos = data.map(d => d.price);

  if (chart) chart.destroy();

  chart = new Chart(document.getElementById("chart-preco"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: symbol,
        data: precos,
        borderColor: "#3B82F6",
        backgroundColor: "rgba(59,130,246,0.08)",
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        tension: 0.3,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => fmtBRL(ctx.parsed.y) } },
      },
      scales: {
        x: {
          ticks: { color: "#94A3B8", maxTicksLimit: 8, maxRotation: 0 },
          grid:  { color: "#1E293B" },
        },
        y: {
          ticks: { color: "#94A3B8", callback: v => fmtBRL(v) },
          grid:  { color: "#334155" },
        },
      },
    },
  });
}

// ── Countdown ─────────────────────────────────────────────────

function startCountdown() {
  countdown = REFRESH_SEG;
  clearInterval(countdownTimer);

  countdownTimer = setInterval(() => {
    countdown--;
    const m = String(Math.floor(countdown / 60)).padStart(2, "0");
    const s = String(countdown % 60).padStart(2, "0");
    document.getElementById("countdown").textContent = `${m}:${s}`;
    if (countdown <= 0) init(false);
  }, 1000);
}

// ── Init ──────────────────────────────────────────────────────

async function init(reiniciarCountdown = true) {
  document.getElementById("status").textContent = "Atualizando...";

  try {
    const data = await fetchCotacoes();

    renderCards(data, "cards-acoes", ACOES);
    renderCards(data, "cards-fiis",  FIIS);
    renderTabela(data);

    const symbol = document.getElementById("select-ativo").value;
    const dias   = parseInt(document.querySelector(".btn-periodo.ativo").dataset.dias);
    await renderGrafico(symbol, dias);

    const latest = data.reduce((a, b) => a.collected_at > b.collected_at ? a : b);
    document.getElementById("ultima-atualizacao").textContent =
      `Última atualização: ${fmtBRT(latest.collected_at, { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" })}`;

    document.getElementById("status").textContent = "";
    if (reiniciarCountdown) startCountdown();

  } catch (e) {
    document.getElementById("status").textContent = "Erro ao carregar dados. Tentando novamente em breve.";
    console.error(e);
  }
}

// ── Event listeners ───────────────────────────────────────────

document.getElementById("select-ativo").addEventListener("change", e => {
  const dias = parseInt(document.querySelector(".btn-periodo.ativo").dataset.dias);
  renderGrafico(e.target.value, dias);
});

document.querySelectorAll(".btn-periodo").forEach(btn => {
  btn.addEventListener("click", e => {
    document.querySelectorAll(".btn-periodo").forEach(b => b.classList.remove("ativo"));
    e.target.classList.add("ativo");
    const symbol = document.getElementById("select-ativo").value;
    renderGrafico(symbol, parseInt(e.target.dataset.dias));
  });
});

// ── Start ─────────────────────────────────────────────────────
init();
