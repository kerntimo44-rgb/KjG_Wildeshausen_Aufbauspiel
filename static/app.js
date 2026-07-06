const socket = io();

let clientId = null;
let state = null;
let view = { type: "lobby" };
let orgaGranted = true;
let stopwatches = {};

const app = document.getElementById("app");

function fmt(sec) {
  sec = Math.max(0, Math.floor(sec || 0));
  return `${String(Math.floor(sec / 60)).padStart(2, "0")}:${String(sec % 60).padStart(2, "0")}`;
}

function timerClass(sec) {
  return Number(sec) > 0 && Number(sec) <= 5 ? "timer danger-timer" : "timer";
}

function stopwatchClass(sec) {
  return Number(sec) > 0 && Number(sec) <= 5 ? "stopwatch-time danger-timer" : "stopwatch-time";
}

let lastRoundTick = Date.now();

function updateRoundTimerDom() {
  if (!state) return;

  document.querySelectorAll("[data-round-timer]").forEach(el => {
    el.textContent = fmt(state.roundRemainingSec);
    el.className = timerClass(state.roundRemainingSec) + (el.classList.contains("big-timer") ? " big-timer" : "");
  });

  document.querySelectorAll("[data-round-status]").forEach(el => {
    el.textContent = state.roundRunning ? "Die Welle läuft" : "Die Welle ruht";
  });
}

setInterval(() => {
  if (!state || !state.roundRunning) {
    lastRoundTick = Date.now();
    return;
  }

  const now = Date.now();
  const delta = Math.floor((now - lastRoundTick) / 1000);
  if (delta <= 0) return;

  lastRoundTick += delta * 1000;
  state.roundRemainingSec = Math.max(0, Number(state.roundRemainingSec) - delta);
  if (state.roundRemainingSec <= 0) state.roundRunning = false;

  updateRoundTimerDom();
}, 250);

function parseTime(value, fallback) {
  const match = String(value || "").trim().match(/^(\d{1,3})(?::([0-5]?\d))?$/);
  if (!match) return fallback;
  return Number(match[1]) * 60 + Number(match[2] || 0);
}

function timeInput(sec) {
  return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}`;
}

function stationName(stationId) {
  return state.stations[String(stationId)]?.name || `Station ${stationId}`;
}

function teamName(teamId) {
  return state.teams[String(teamId)]?.name || `Team ${teamId}`;
}

function teamEmoji(teamId) {
  const icons = ["🐟", "⛵", "🌊", "🐚", "🌀", "🛶", "🐠", "🌺", "🌴", "⭐"];
  return icons[(Number(teamId) - 1) % icons.length];
}

function helpStatusFor(kind, id) {
  const req = (state.helpRequests || []).find(item => item.kind === kind && String(item.id) === String(id));
  return req ? req.status : null;
}

function helpClass(kind, id) {
  const status = helpStatusFor(kind, id);
  if (status === "red") return " help-active-red";
  if (status === "yellow") return " help-active-yellow";
  return "";
}

function clans() {
  return state.clans || [];
}

function clanById(clanId) {
  return clans().find(clan => clan.id === clanId);
}

function clanImg(teamId) {
  const clan = clanById(state.teams[String(teamId)]?.clan);
  return clan ? `<img class="clan-icon" src="/static/clans/${clan.file}" alt="${escapeHtml(clan.name)}">` : `<span class="clan-placeholder">${teamEmoji(teamId)}</span>`;
}

function usedClanIds(exceptTeamId = null) {
  return new Set(Object.entries(state.teams || {})
    .filter(([id]) => String(id) !== String(exceptTeamId))
    .map(([, team]) => team.clan)
    .filter(Boolean));
}

function clanSelectOptions(teamId) {
  const used = usedClanIds(teamId);
  const current = state.teams[String(teamId)]?.clan || "";
  let html = `<option value="">Kein Wappen</option>`;
  for (const clan of clans()) {
    const disabled = used.has(clan.id) ? "disabled" : "";
    const selected = current === clan.id ? "selected" : "";
    html += `<option value="${clan.id}" ${selected} ${disabled}>${clan.name} (${clan.label})${disabled ? " – vergeben" : ""}</option>`;
  }
  return html;
}

function helpOverviewHtml() {
  const requests = [...(state.helpRequests || [])].sort((a, b) => Number(a.createdAt || 0) - Number(b.createdAt || 0));
  if (!requests.length) {
    return `<div class="card empty-help"><h2>Keine Hilferufe</h2><p>Wenn ein Team oder eine Station Hilfe ruft, erscheint es hier.</p></div>`;
  }
  return requests.map(req => {
    const cls = req.status === "yellow" ? "help-button-yellow" : "help-button-red";
    const prefix = req.kind === "team" ? "Team" : "Station";
    return `<button class="${cls}" onclick="helperToggleHelp('${req.kind}', '${req.id}')">${prefix}: ${escapeHtml(req.label)}</button>`;
  }).join("");
}


function points(team) {
  return team.villages + team.towns * 2 + team.cities * 3;
}

function button(label, onclick, cls = "", disabled = false) {
  return `<button class="${cls}" ${disabled ? "disabled" : ""} onclick="${onclick}">${label}</button>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function roundHeader() {
  return `
    <div class="card round">
      <div class="label">🌊 Aktive Runde</div>
      <div class="round-number">${state.activeRound} / ${state.roundCount}</div>
      <div class="${timerClass(state.roundRemainingSec)}" data-round-timer>${fmt(state.roundRemainingSec)}</div>
      <div class="label" data-round-status>${state.roundRunning ? "Die Welle läuft" : "Die Welle ruht"}</div>
    </div>
  `;
}

function go(next) {
  if (view.type === "orga" && next.type !== "orga") socket.emit("leave_orga");
  if (view.type === "station" || view.type === "team") socket.emit("leave_slot");
  view = next;
  if (next.type === "orga") {
    socket.emit("request_orga");
  }
  render();
}

function render() {
  if (!state) return;
  if (view.type === "lobby") return renderLobby();
  if (view.type === "orga") return renderOrga();
  if (view.type === "ranking") return renderRanking(false);
  if (view.type === "timer") return renderBigTimer();
  if (view.type === "station") return renderStation();
  if (view.type === "team") return renderTeam();
  if (view.type === "helper") return renderHelper();
}

function renderLobby() {
  let stations = "";
  for (let s = 1; s <= state.stationCount; s++) {
    const station = state.stations[String(s)];
    const occupied = !!station?.occupiedBy;
    stations += `
      <div class="station-box">
        <div>
          <div class="station-title">🌺 ${escapeHtml(stationName(s))}</div>
        </div>
        ${button(`${occupied ? "🔒 Belegt" : "Betreten"}`, `joinStation(${s})`, occupied ? "secondary" : "", occupied)}
      </div>
    `;
  }

  let teams = "";
  for (let t = 1; t <= state.teamCount; t++) {
    const occupied = !!state.teams[String(t)]?.occupiedBy;
    teams += `
      <div class="station-box">
        <div>
          <div class="station-title">${clanImg(t)} ${escapeHtml(teamName(t))}</div>
        </div>
        ${button(`${occupied ? "🔒 Belegt" : "Betreten"}`, `joinTeam(${t})`, occupied ? "secondary" : "", occupied)}
      </div>
    `;
  }

  let helpers = `
    <div class="station-box">
      <div>
        <div class="station-title">Helfer</div>
      </div>
      ${button("Betreten", "go({type:'helper'})")}
    </div>
  `;

  app.innerHTML = `
    <main class="page">
      <div class="topbar">
        <div><h1>KjG-Aufbauspiel</h1><p>Stationen und Teams betreten.</p></div>
        ${button("💻 Orga-View", "go({type:'orga'})")}
      </div>
      <div class="grid two">
        <section class="card lobby-section"><h2>🌴 Stationen</h2><div class="grid">${stations}</div></section>
        <section class="card lobby-section"><h2>🛶 Teams</h2><div class="grid">${teams}</div></section>
        <section class="card lobby-section full"><h2>🛟 Helfer</h2><div class="grid">${helpers}</div></section>
      </div>
    </main>
  `;
}

function joinStation(station) {
  socket.emit("join_station", { station });
  view = { type: "station", station };
  render();
}

function joinTeam(team) {
  socket.emit("join_team", { team });
  view = { type: "team", team };
  render();
}

function renderOrga() {
  let helpers = `
    <div class="station-box">
      <div>
        <div class="station-title">Helfer</div>
      </div>
      ${button("Betreten", "go({type:'helper'})")}
    </div>
  `;

  app.innerHTML = `
    <main class="page">
      <div class="topbar">
        <div><h1>Orga-View</h1></div>
        ${button("🏠 Lobby", "go({type:'lobby'})", "secondary")}
      </div>
      <div class="grid orga-grid">
        <section class="card">
          <h2>⚙️ Einstellungen</h2>
          <div class="config">
            <label>Anzahl Stationen<input id="stationCount" type="number" min="1" value="${state.stationCount}"></label>
            <label>Spiele pro Station<input id="gamesPerStation" type="number" min="1" value="${state.gamesPerStation}"></label>
            <label>Anzahl Teams<input id="teamCount" type="number" min="1" value="${state.teamCount}"></label>
            <label>Anzahl Runden<input id="roundCount" type="number" min="1" value="${state.roundCount}"></label>
            <label>Dauer pro Runde, MM:SS<input id="roundDurationSec" value="${timeInput(state.roundDurationSec)}"></label>
            <label>Dauer der Spiele in der Station, MM:SS<input id="gameDurationSec" value="${timeInput(state.gameDurationSec)}"></label>
          </div>
          <div class="actions">
            ${button(state.roundRunning ? "⏸ Pause" : "▶ Runde starten", "toggleRound()")}
            ${button("⏭ Nächste Runde", "nextRound()", "secondary")}
            ${button("⏱ Timer zurücksetzen", "resetRoundTimer()", "secondary full")}
            ${button("🔄 Alles zurücksetzen", "resetGame()", "danger full")}
            ${button("🏆 Team-Ranking", "go({type:'ranking'})", "secondary")}
            ${button("⏱ Timer", "go({type:'timer'})", "secondary")}
          </div>
          <div class="manual-round-box">
            <label>Aktive Runde überschreiben</label>
            <div class="manual-round-row">
              <input id="manualRound" type="number" min="1" max="${state.roundCount}" value="${state.activeRound}">
              ${button("Setzen", "setActiveRound()", "secondary")}
            </div>
          </div>
        </section>
        <section class="grid">
          ${roundHeader()}
          <div class="card">
            <h2>🛟 Hilferufe</h2>
            <section class="grid help-list">${helpOverviewHtml()}</section>
          </div>
          ${rankingHtml(true)}
          <div class="card">
            <h2>🌴 Stationsnamen</h2>
            <div class="grid station-name-grid">
              ${stationNameInputs()}
            </div>
          </div>
          <div class="card">
            <h2>🛶 Teamnamen</h2>
            <div class="grid station-name-grid">
              ${teamNameInputs()}
            </div>
          </div>
        </section>
      </div>
    </main>
  `;

  ["stationCount", "gamesPerStation", "teamCount", "roundCount"].forEach(id => {
    document.getElementById(id).addEventListener("change", e => {
      socket.emit("update_config", { [id]: Number(e.target.value) });
    });
  });
  document.getElementById("roundDurationSec").addEventListener("change", e => {
    socket.emit("update_config", { roundDurationSec: parseTime(e.target.value, state.roundDurationSec) });
  });
  document.getElementById("gameDurationSec").addEventListener("change", e => {
    socket.emit("update_config", { gameDurationSec: parseTime(e.target.value, state.gameDurationSec) });
  });

  for (let s = 1; s <= state.stationCount; s++) {
    const input = document.getElementById(`stationName-${s}`);
    input.addEventListener("change", e => {
      socket.emit("update_station_name", { station: s, name: e.target.value });
    });
  }

  for (let t = 1; t <= state.teamCount; t++) {
    const input = document.getElementById(`teamName-${t}`);
    input.addEventListener("change", e => {
      socket.emit("update_team_name", { team: t, name: e.target.value });
    });

    const clan = document.getElementById(`teamClan-${t}`);
    clan.addEventListener("change", e => {
      socket.emit("update_team_clan", { team: t, clan: e.target.value });
    });
  }
}

function stationNameInputs() {
  let html = "";
  for (let s = 1; s <= state.stationCount; s++) {
    html += `
      <label class="station-name-row">
        <strong>Station ${s}</strong>
        <input id="stationName-${s}" value="${escapeHtml(stationName(s))}" placeholder="Name der Station">
      </label>
    `;
  }
  return html;
}

function teamNameInputs() {
  let html = "";
  for (let t = 1; t <= state.teamCount; t++) {
    html += `
      <div class="team-settings-row">
        <label class="station-name-row">
          <strong>Team ${t}</strong>
          <input id="teamName-${t}" value="${escapeHtml(teamName(t))}" placeholder="Name des Teams">
        </label>
        <label class="station-name-row clan-select-row">
          <strong>Wappen</strong>
          <select id="teamClan-${t}">
            ${clanSelectOptions(t)}
          </select>
        </label>
      </div>
    `;
  }
  return html;
}

function toggleRound() { socket.emit("toggle_round"); }
function nextRound() { socket.emit("next_round"); }
function resetRoundTimer() { socket.emit("reset_round_timer"); }
function setActiveRound() {
  const input = document.getElementById("manualRound");
  socket.emit("set_active_round", { round: Number(input?.value || state.activeRound) });
}
function resetGame() { if (confirm("Wirklich alles auf Spielstart zurücksetzen? Stationsnamen werden ebenfalls zurückgesetzt.")) socket.emit("reset_game"); }

function rankingHtml() {
  const rows = Object.entries(state.teams).map(([id, team]) => ({ id, ...team, pts: points(team) })).sort((a,b) => b.pts - a.pts);
  const max = Math.max(1, ...rows.map(r => r.pts));
  return `
    <div class="card">
      <h2>🏆 Team-Ranking</h2>
      ${rows.map((row, idx) => `
        <div class="ranking-row">
          <strong>#${idx + 1} ${escapeHtml(teamName(row.id))}</strong>
          <div class="bar-bg"><div class="bar" style="width:${row.pts / max * 100}%"></div></div>
          <div class="points">${row.pts}</div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderRanking() {
  app.innerHTML = `
    <main class="page page-with-corner-button">
      ${rankingHtml(false)}
      <button class="secondary corner-back-button" onclick="go({type:'orga'})">Zur Orga-View</button>
    </main>
  `;
}

function renderBigTimer() {
  app.innerHTML = `
    <main class="big-timer-page">
      <div>
        <h1>Runde ${state.activeRound} / ${state.roundCount}</h1>
        <div class="${timerClass(state.roundRemainingSec)} big-timer" data-round-timer>${fmt(state.roundRemainingSec)}</div>
      </div>
      <button class="secondary corner-back-button" onclick="go({type:'orga'})">Zur Orga-View</button>
    </main>
  `;
}


function renderHelper() {
  app.innerHTML = `
    <main class="station-view helper-view">
      ${button("🏠 Lobby", "go({type:'lobby'})", "ghost")}
      <div class="top-spacer"></div>
      ${roundHeader()}
      <section class="grid help-list">${helpOverviewHtml()}</section>
    </main>
  `;
}

function helperToggleHelp(kind, id) {
  socket.emit("helper_toggle_help", { kind, id });
}

function toggleHelp(kind, id) {
  socket.emit("toggle_help_request", { kind, id });
}


function renderStation() {
  const { station } = view;
  let watches = "";
  for (let w = 1; w <= state.gamesPerStation; w++) {
    const key = `${station}:${w}`;
    const sw = stopwatches[key] || { remaining: state.gameDurationSec, running: false };
    watches += `
      <div class="card stopwatch">
        <h2>🐚 Spiel ${w}</h2>
        <div class="${stopwatchClass(sw.remaining)}">${fmt(sw.remaining)}</div>
        <div class="stopwatch-actions">
          ${button(sw.running ? "Stop" : "Start", `toggleStopwatch(${w})`)}
          ${button("Reset", `resetStopwatch(${w})`, "secondary")}
        </div>
      </div>
    `;
  }

  app.innerHTML = `
    <main class="station-view${helpClass('station', station)}">
      <div class="view-topline">
        ${button("🏠 Lobby", "go({type:'lobby'})", "ghost")}
        <div class="inline-view-title">🌺 ${escapeHtml(stationName(station))}</div>
      </div>
      <div class="top-spacer"></div>
      ${roundHeader()}
      <section class="grid station-stopwatches">${watches}</section>
      <button class="help-call-button" onclick="toggleHelp('station', '${station}')">Hilfe</button>
    </main>
  `;
}

function toggleStopwatch(watch) {
  socket.emit("toggle_stopwatch", { station: view.station, watch });
}

function resetStopwatch(watch) {
  socket.emit("reset_stopwatch", { station: view.station, watch });
}

function renderTeam() {
  const teamId = String(view.team);
  const team = state.teams[teamId] || { villages: 0, towns: 0, cities: 0, name: `Team ${teamId}` };

  app.innerHTML = `
    <main class="team-layout${helpClass('team', teamId)}">
      <section>
        <div class="view-topline">
          ${button("🏠 Lobby", "go({type:'lobby'})", "ghost")}
          <div class="inline-view-title">${clanImg(teamId)} ${escapeHtml(teamName(teamId))}</div>
        </div>
        <div class="top-spacer"></div>
        ${roundHeader()}
        <div class="card round team-points-card" style="margin-top:12px">
          <div class="label">🛶 ${escapeHtml(teamName(teamId))} Punkte</div>
          <div class="timer">${points(team)}</div>
        </div>
      </section>
      <section class="grid team-counter-section">
        ${counterRow("Dörfer", team.villages, "village_minus", "village_plus")}
        ${counterRow("Städte", team.towns, "town_minus", "town_plus")}
        ${counterRow("Großstädte", team.cities, "city_minus", "city_plus")}
        <button class="help-call-button" onclick="toggleHelp('team', '${teamId}')">Hilfe</button>
      </section>
    </main>
  `;
}

function counterRow(name, value, minus, plus) {
  return `
    <div class="card counter-row">
      <div class="counter-name">${name}</div>
      ${button("-1", `teamAction('${minus}')`, "secondary")}
      <div class="counter-value">${value}</div>
      ${button("+1", `teamAction('${plus}')`)}
    </div>
  `;
}

function teamAction(action) {
  socket.emit("update_team", { team: view.team, action });
}

socket.on("client_id", id => { clientId = id; });
socket.on("state", next => { state = next; lastRoundTick = Date.now(); render(); });
socket.on("orga_granted", granted => { orgaGranted = granted; render(); });
socket.on("stopwatches", next => { stopwatches = next; if (view.type === "station" || view.type === "helper") render(); });

setInterval(() => socket.emit("get_stopwatches"), 1000);
