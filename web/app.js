const statusPill = document.getElementById("statusPill");
const statusDot = document.getElementById("statusDot");
const statusLabel = document.getElementById("statusLabel");

const statAccess = document.getElementById("statAccess");
const statMatches = document.getElementById("statMatches");
const statUptime = document.getElementById("statUptime");
const statMatchDur = document.getElementById("statMatchDur");

const toggleBtn = document.getElementById("toggleBtn");
const btnIconWrap = document.getElementById("btnIconWrap");
const btnText = document.getElementById("btnText");

const snipBtn = document.getElementById("snipBtn");
const testBtn = document.getElementById("testBtn");
const resetBtn = document.getElementById("resetBtn");
const clearLogBtn = document.getElementById("clearLogBtn");
const saveSettingsBtn = document.getElementById("saveSettingsBtn");

const inputInterval = document.getElementById("inputInterval");
const valInterval = document.getElementById("valInterval");
const inputConf = document.getElementById("inputConf");
const valConf = document.getElementById("valConf");
const checkAfk = document.getElementById("checkAfk");
const checkWSpace = document.getElementById("checkWSpace");
const logContainer = document.getElementById("logContainer");

let isRunning = false;
let uptimeSeconds = 0;
let matchSeconds = 0;
let tickerTimer = null;

function formatHHMMSS(sec) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function formatMMSS(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function updateStatusUI(status) {
  statusLabel.innerText = status;
  const pulseBeacon = document.getElementById("pulseBeacon");

  if (status === "IDLE") {
    statusDot.style.background = "#64748b";
    statusDot.style.boxShadow = "none";
    statusPill.style.borderColor = "var(--fn-border-card)";
    if (pulseBeacon) pulseBeacon.style.background = "transparent";
  } else if (status === "IN MATCH") {
    statusDot.style.background = "var(--fn-green)";
    statusDot.style.boxShadow = "0 0 14px var(--fn-green-glow)";
    statusPill.style.borderColor = "rgba(16, 185, 129, 0.6)";
    if (pulseBeacon) pulseBeacon.style.background = "var(--fn-green)";
  } else if (status === "ELIMINATED") {
    statusDot.style.background = "var(--fn-red)";
    statusDot.style.boxShadow = "0 0 14px rgba(255, 42, 95, 0.6)";
    statusPill.style.borderColor = "rgba(255, 42, 95, 0.6)";
    if (pulseBeacon) pulseBeacon.style.background = "var(--fn-red)";
  } else if (status === "CLICKING PLAY AGAIN") {
    statusDot.style.background = "var(--fn-yellow)";
    statusDot.style.boxShadow = "0 0 14px var(--fn-gold-glow)";
    statusPill.style.borderColor = "rgba(255, 190, 11, 0.6)";
    if (pulseBeacon) pulseBeacon.style.background = "var(--fn-yellow)";
  } else if (status === "MATCHMAKING") {
    statusDot.style.background = "var(--fn-purple)";
    statusDot.style.boxShadow = "0 0 14px var(--fn-purple-glow)";
    statusPill.style.borderColor = "rgba(192, 132, 252, 0.6)";
    if (pulseBeacon) pulseBeacon.style.background = "var(--fn-purple)";
  } else {
    statusDot.style.background = "var(--fn-cyan)";
    statusDot.style.boxShadow = "0 0 14px var(--fn-cyan-glow)";
    statusPill.style.borderColor = "rgba(0, 240, 255, 0.6)";
    if (pulseBeacon) pulseBeacon.style.background = "var(--fn-cyan)";
  }
}

function setRunningState(running) {
  isRunning = running;
  const subLabel = document.querySelector(".fn-btn-sub");
  if (running) {
    toggleBtn.className = "fortnite-play-btn btn-play-stop";
    if (btnIconWrap) {
      btnIconWrap.innerHTML = '<svg viewBox="0 0 24 24" class="cta-play-svg"><rect x="5" y="5" width="14" height="14" rx="2" fill="currentColor"/></svg>';
    }
    btnText.innerText = "STOP AUTOMATION";
    if (subLabel) subLabel.innerText = "PAUSE AUTO-CYCLE ENGINE";
  } else {
    toggleBtn.className = "fortnite-play-btn btn-play-ready";
    if (btnIconWrap) {
      btnIconWrap.innerHTML = '<svg viewBox="0 0 24 24" class="cta-play-svg"><polygon points="6 3 20 12 6 21 6 3" fill="currentColor"/></svg>';
    }
    btnText.innerText = "START AUTOMATION";
    if (subLabel) subLabel.innerText = "READY UP & AUTO-CYCLE LOOP";
  }
}

function appendLogEntry(entry) {
  const row = document.createElement("div");
  row.className = "log-row";

  const timeSpan = document.createElement("span");
  timeSpan.className = "log-time";
  timeSpan.innerText = `[${entry.time}]`;

  const tagSpan = document.createElement("span");
  const levelClass = entry.level ? `tag-${entry.level}` : "tag-info";
  tagSpan.className = `log-tag ${levelClass}`;
  tagSpan.innerText = (entry.level || "info").toUpperCase();

  const msgSpan = document.createElement("span");
  msgSpan.className = "log-msg";
  msgSpan.innerText = entry.text;

  row.appendChild(timeSpan);
  row.appendChild(tagSpan);
  row.appendChild(msgSpan);

  logContainer.appendChild(row);
  logContainer.scrollTop = logContainer.scrollHeight;
}

eel.expose(js_update_state);
function js_update_state(data) {
  setRunningState(data.running);
  updateStatusUI(data.status);
  statMatches.innerText = data.matches;
  statAccess.innerText = data.access_found || 0;
  uptimeSeconds = data.uptime || 0;
  matchSeconds = data.match_duration || 0;
  statUptime.innerText = formatHHMMSS(uptimeSeconds);
  statMatchDur.innerText = formatMMSS(matchSeconds);
}

eel.expose(js_add_log);
function js_add_log(entry) {
  appendLogEntry(entry);
}

toggleBtn.addEventListener("click", () => {
  eel.toggle_macro()();
});

snipBtn.addEventListener("click", () => {
  appendLogEntry({
    time: new Date().toTimeString().split(" ")[0],
    level: "action",
    text: "Opening screen snip overlay. Click and drag a box around button. Press Esc to cancel."
  });
  eel.trigger_snip()();
});

testBtn.addEventListener("click", () => {
  eel.test_screen_detection()();
});

resetBtn.addEventListener("click", () => {
  eel.reset_counters()();
});

clearLogBtn.addEventListener("click", () => {
  logContainer.innerHTML = "";
  eel.clear_logs()();
});

inputInterval.addEventListener("input", (e) => {
  valInterval.innerText = `${parseFloat(e.target.value).toFixed(1)}s`;
});

inputConf.addEventListener("input", (e) => {
  valConf.innerText = `${e.target.value}%`;
});

function saveCurrentSettings() {
  const interval = parseFloat(inputInterval.value);
  const conf = parseFloat(inputConf.value) / 100.0;
  const afk = checkAfk.checked;
  const wSpace = checkWSpace.checked;
  eel.update_settings(interval, conf, afk, wSpace)();
}

saveSettingsBtn.addEventListener("click", saveCurrentSettings);
checkWSpace.addEventListener("change", saveCurrentSettings);
checkAfk.addEventListener("change", saveCurrentSettings);

if (!tickerTimer) {
  tickerTimer = setInterval(() => {
    if (isRunning) {
      uptimeSeconds++;
      matchSeconds++;
      statUptime.innerText = formatHHMMSS(uptimeSeconds);
      statMatchDur.innerText = formatMMSS(matchSeconds);
    }
  }, 1000);
}

window.addEventListener("DOMContentLoaded", () => {
  if (window.eel) {
    eel.get_initial_data()().then((data) => {
      setRunningState(data.running);
      updateStatusUI(data.status);
      statMatches.innerText = data.matches;
      statAccess.innerText = data.access_found || 0;
      uptimeSeconds = data.uptime || 0;
      matchSeconds = data.match_duration || 0;
      statUptime.innerText = formatHHMMSS(uptimeSeconds);
      statMatchDur.innerText = formatMMSS(matchSeconds);

      inputInterval.value = data.check_interval;
      valInterval.innerText = `${parseFloat(data.check_interval).toFixed(1)}s`;

      inputConf.value = Math.round(data.confidence * 100);
      valConf.innerText = `${Math.round(data.confidence * 100)}%`;

      checkAfk.checked = data.anti_afk;
      checkWSpace.checked = !!data.w_space;

      if (data.logs && data.logs.length) {
        logContainer.innerHTML = "";
        data.logs.forEach(appendLogEntry);
      }
    }).catch(() => {});
  }
});
