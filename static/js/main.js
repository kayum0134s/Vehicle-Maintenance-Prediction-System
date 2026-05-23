// VMPS Main Application Logic
let vehicles = [];
let activeVehicle = null;
let activeVehicleId = null;
let lastPrediction = null;

// ─── Utils ───────────────────────────────────────────────
function showLoading(msg) {
  const ov = document.getElementById('loading-overlay');
  document.getElementById('loading-text').textContent = msg || 'PROCESSING...';
  ov.classList.add('active');
}
function hideLoading() { document.getElementById('loading-overlay').classList.remove('active'); }

function toast(msg, type = 'info') {
  const tc = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  tc.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

function showSection(name) {
  ['dashboard','predict','analytics','vehicles','recommendations','history'].forEach(s => {
    const el = document.getElementById(`section-${s}`);
    if (el) el.style.display = s === name ? '' : 'none';
    const nav = document.getElementById(`nav-${s}`);
    if (nav) nav.classList.toggle('active', s === name);
  });
  if (name === 'analytics') loadAnalytics();
  if (name === 'vehicles') renderVehiclesGrid();
  if (name === 'history') loadHistory();
}

function setGauge(fillId, valId, pct, color) {
  const fill = document.getElementById(fillId);
  const val = document.getElementById(valId);
  if (!fill || !val) return;
  const circ = 2 * Math.PI * 65;
  const offset = circ - (pct / 100) * circ;
  fill.style.strokeDashoffset = offset;
  fill.style.stroke = pct >= 70 ? '#06ffa5' : pct >= 40 ? '#ffa502' : '#ff4757';
  val.textContent = pct + '%';
  val.style.color = pct >= 70 ? '#06ffa5' : pct >= 40 ? '#ffa502' : '#ff4757';
}

function riskBadgeHtml(level) {
  return `<span class="risk-badge risk-${level}">${level}</span>`;
}

function progressBarHtml(name, value, max, dangerThreshold, warnThreshold) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  let cls = 'good';
  if (value <= dangerThreshold) cls = 'danger';
  else if (value <= warnThreshold) cls = 'warning';
  return `
    <div class="progress-wrap">
      <div class="progress-header"><span class="progress-name">${name}</span><span class="progress-val">${value}</span></div>
      <div class="progress-track"><div class="progress-fill ${cls}" style="width:${pct}%"></div></div>
    </div>`;
}

// ─── Auth ────────────────────────────────────────────────
async function doLogout() {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
  window.location.href = '/login';
}

// ─── Dark Mode ───────────────────────────────────────────
let isDark = true;
function toggleDark() {
  isDark = !isDark;
  document.body.classList.toggle('light-mode', !isDark);
  document.getElementById('dark-toggle-btn').textContent = isDark ? '🌙 Dark' : '☀️ Light';
}

// ─── Alerts ──────────────────────────────────────────────
function toggleAlerts() {
  const panel = document.getElementById('alert-panel');
  panel.classList.toggle('open');
  if (panel.classList.contains('open')) loadAlerts();
}

async function loadAlerts() {
  try {
    const res = await fetch('/api/alerts', { credentials: 'include' });
    const data = await res.json();
    const alerts = data.alerts || [];
    const badge = document.getElementById('alert-count');
    const unread = alerts.filter(a => !a.is_read).length;
    badge.textContent = unread;
    badge.style.display = unread > 0 ? 'flex' : 'none';

    const list = document.getElementById('alerts-list');
    if (!alerts.length) { list.innerHTML = '<div style="color:var(--text-secondary);font-size:0.82rem;text-align:center;padding:20px;">No alerts</div>'; return; }
    list.innerHTML = alerts.map(a => `
      <div class="alert-item alert-${a.severity}">
        <div class="alert-msg">${a.message}</div>
        <div class="alert-time">${new Date(a.created_at).toLocaleString()}</div>
      </div>`).join('');
  } catch(e) { console.error('loadAlerts', e); }
}

// ─── Dashboard ───────────────────────────────────────────
async function loadDashboard() {
  showLoading('LOADING DASHBOARD...');
  try {
    const [dashRes, vRes] = await Promise.all([
      fetch('/api/dashboard', { credentials: 'include' }),
      fetch('/api/vehicles', { credentials: 'include' })
    ]);
    const dashData = await dashRes.json();
    const vData = await vRes.json();
    vehicles = vData.vehicles || [];

    document.getElementById('stat-total').textContent = dashData.total_vehicles;
    document.getElementById('stat-health').textContent = dashData.avg_health + '%';
    document.getElementById('stat-critical').textContent = dashData.critical_count;
    document.getElementById('stat-ok').textContent = dashData.ok_count;

    renderDashboardCharts(dashData.trend, dashData.risk_distribution);
    renderFleetChips();
    loadAlerts();
  } catch(e) { toast('Failed to load dashboard', 'error'); console.error(e); }
  finally { hideLoading(); }
}

function renderFleetChips() {
  const el = document.getElementById('fleet-chips');
  if (!vehicles.length) {
    el.innerHTML = '<div style="color:var(--text-secondary);font-size:0.82rem;padding:8px 0;">No vehicles yet. <a href="#" onclick="showSection(\'predict\')" style="color:var(--neon-blue);">Add your first vehicle →</a></div>';
    return;
  }
  el.innerHTML = vehicles.map(v => {
    const dot = v._health ? (v._health >= 70 ? '#06ffa5' : v._health >= 40 ? '#ffa502' : '#ff4757') : '#7a9bc0';
    return `<div class="vehicle-chip ${activeVehicleId === v.id ? 'active' : ''}" id="chip-${v.id}" onclick="selectVehicle(${v.id})">
      <div class="chip-dot" style="background:${dot}"></div>${v.vehicle_number}<br/><small style="color:var(--text-secondary)">${v.manufacturer} ${v.vehicle_model}</small>
    </div>`;
  }).join('');
}

async function selectVehicle(id) {
  activeVehicleId = id;
  activeVehicle = vehicles.find(v => v.id === id);
  if (!activeVehicle) return;

  // Update chips
  document.querySelectorAll('.vehicle-chip').forEach(c => c.classList.remove('active'));
  const chip = document.getElementById(`chip-${id}`);
  if (chip) chip.classList.add('active');

  // Update sidebar info
  document.getElementById('sidebar-vehicle-info').style.display = 'block';
  document.getElementById('sv-number').textContent = activeVehicle.vehicle_number;
  document.getElementById('sv-model').textContent = `${activeVehicle.manufacturer} ${activeVehicle.vehicle_model}`;

  // Load latest prediction
  try {
    const res = await fetch(`/api/vehicles/${id}/predictions`, { credentials: 'include' });
    const data = await res.json();
    const pred = (data.predictions || [])[0];
    if (pred) {
      document.getElementById('fleet-detail').style.display = 'block';
      setGauge('fleet-gauge-fill', 'fleet-gauge-value', pred.health_score);
      document.getElementById('fleet-risk-badge').innerHTML = riskBadgeHtml(pred.risk_level);
      document.getElementById('fleet-urgency').textContent = `Urgency: ${pred.urgency}`;
      document.getElementById('sv-health').innerHTML = `Health: <strong style="color:${pred.health_score>=70?'#06ffa5':pred.health_score>=40?'#ffa502':'#ff4757'}">${pred.health_score}%</strong>`;

      const v = activeVehicle;
      document.getElementById('fleet-sensor-bars').innerHTML = `
        ${progressBarHtml('Oil Quality', v.oil_quality, 100, 30, 50)}
        ${progressBarHtml('Brake Condition', v.brake_condition, 100, 30, 55)}
        ${progressBarHtml('Battery Health', v.battery_health, 100, 25, 50)}
        ${progressBarHtml('Fuel Efficiency', v.fuel_efficiency, 50, 10, 20)}`;

      document.getElementById('fleet-status-info').innerHTML = `
        <div class="result-row"><span class="result-key">Component</span><span class="result-val">${(pred.failure_components||['None'])[0]}</span></div>
        <div class="result-row" style="margin-top:6px;"><span class="result-key">Est. Cost</span><span class="result-val" style="color:#06ffa5;">$${pred.estimated_cost?.toFixed(0)||0}</span></div>`;

      lastPrediction = pred;
    }
  } catch(e) { console.error('selectVehicle', e); }
}

async function runPredictionForSelected() {
  if (!activeVehicleId) { toast('Select a vehicle first', 'info'); return; }
  showLoading('RUNNING AI ANALYSIS...');
  try {
    const res = await fetch(`/api/vehicles/${activeVehicleId}/predict`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify(activeVehicle), credentials: 'include'
    });
    const data = await res.json();
    const pred = data.prediction;
    toast(`Analysis complete — Health: ${pred.health_score}%`, 'success');
    setGauge('fleet-gauge-fill', 'fleet-gauge-value', pred.health_score);
    document.getElementById('fleet-risk-badge').innerHTML = riskBadgeHtml(pred.risk_level);
    lastPrediction = pred;
    loadAlerts();
    loadDashboard();
  } catch(e) { toast('Prediction failed', 'error'); } finally { hideLoading(); }
}

function deleteSelected() {
  if (!activeVehicleId) { toast('Select a vehicle first', 'info'); return; }
  if (!confirm(`Delete vehicle ${activeVehicle?.vehicle_number}?`)) return;
  fetch(`/api/vehicles/${activeVehicleId}`, { method: 'DELETE', credentials: 'include' })
    .then(() => { toast('Vehicle deleted', 'success'); activeVehicleId = null; activeVehicle = null; document.getElementById('fleet-detail').style.display = 'none'; loadDashboard(); })
    .catch(() => toast('Delete failed', 'error'));
}

function exportSelectedReport() {
  if (!activeVehicleId) { toast('Select a vehicle first', 'info'); return; }
  window.open(`/api/vehicles/${activeVehicleId}/report`, '_blank');
}

function exportCurrentReport() {
  if (!activeVehicleId) { toast('Select a vehicle first', 'info'); return; }
  exportSelectedReport();
}

// ─── Prediction Form ─────────────────────────────────────
function fillSample(type) {
  if (type === 'good') {
    document.getElementById('f-number').value = 'MH-01-AA-0001';
    document.getElementById('f-model').value = 'Model 3';
    document.getElementById('f-manufacturer').value = 'Tesla';
    document.getElementById('f-mileage').value = 25000;
    document.getElementById('f-engine-temp').value = 88;
    document.getElementById('f-oil').value = 85;
    document.getElementById('f-tire').value = 33;
    document.getElementById('f-brake').value = 88;
    document.getElementById('f-battery').value = 92;
    document.getElementById('f-fuel').value = 38;
    document.getElementById('f-service-hist').value = 3;
    document.getElementById('f-last-service').value = new Date(Date.now()-90*864e5).toISOString().split('T')[0];
  } else {
    document.getElementById('f-number').value = 'DL-02-ZZ-9999';
    document.getElementById('f-model').value = 'F-150';
    document.getElementById('f-manufacturer').value = 'Ford';
    document.getElementById('f-mileage').value = 190000;
    document.getElementById('f-engine-temp').value = 122;
    document.getElementById('f-oil').value = 8;
    document.getElementById('f-tire').value = 22;
    document.getElementById('f-brake').value = 12;
    document.getElementById('f-battery').value = 15;
    document.getElementById('f-fuel').value = 8;
    document.getElementById('f-service-hist').value = 15;
    document.getElementById('f-last-service').value = new Date(Date.now()-600*864e5).toISOString().split('T')[0];
  }
}

function resetForm() {
  ['f-number','f-model','f-mileage','f-engine-temp','f-oil','f-tire','f-brake','f-battery','f-fuel','f-service-hist','f-last-service'].forEach(id => {
    document.getElementById(id).value = '';
  });
  document.getElementById('f-manufacturer').value = '';
}

async function submitPrediction() {
  const number = document.getElementById('f-number').value.trim();
  const model = document.getElementById('f-model').value.trim();
  const manufacturer = document.getElementById('f-manufacturer').value;
  if (!number || !model || !manufacturer) { toast('Please fill Vehicle Number, Model and Manufacturer', 'error'); return; }

  const payload = {
    vehicle_number: number, vehicle_model: model, manufacturer,
    mileage: +document.getElementById('f-mileage').value || 50000,
    engine_temp: +document.getElementById('f-engine-temp').value || 90,
    oil_quality: +document.getElementById('f-oil').value || 75,
    tire_pressure: +document.getElementById('f-tire').value || 32,
    brake_condition: +document.getElementById('f-brake').value || 75,
    battery_health: +document.getElementById('f-battery').value || 80,
    fuel_efficiency: +document.getElementById('f-fuel').value || 28,
    service_history: +document.getElementById('f-service-hist').value || 2,
    last_service_date: document.getElementById('f-last-service').value
  };

  showLoading('RUNNING ML PREDICTION...');
  try {
    const res = await fetch('/api/predict/quick', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload), credentials: 'include'
    });
    const data = await res.json();
    const pred = data.prediction;
    lastPrediction = pred;
    activeVehicleId = data.vehicle_id;
    activeVehicle = data.vehicle;

    vehicles.push(data.vehicle);
    showPredictionResult(pred);
    loadDashboard();
    toast(`AI Analysis complete — ${pred.health_score}% health`, 'success');
    loadAlerts();
  } catch(e) { toast('Prediction failed. Check connection.', 'error'); console.error(e); }
  finally { hideLoading(); }
}

function showPredictionResult(pred) {
  document.getElementById('prediction-placeholder').style.display = 'none';
  document.getElementById('prediction-output').style.display = 'block';

  setGauge('pred-gauge-fill', 'pred-health-val', pred.health_score);

  document.getElementById('result-list').innerHTML = `
    <div class="result-row"><span class="result-key">Maintenance Required</span><span class="result-val" style="color:${pred.maintenance_required?'#ff4757':'#06ffa5'}">${pred.maintenance_required?'YES ⚠️':'NO ✅'}</span></div>
    <div class="result-row"><span class="result-key">Risk Level</span>${riskBadgeHtml(pred.risk_level)}</div>
    <div class="result-row"><span class="result-key">Service Urgency</span><span class="result-val">${pred.urgency}</span></div>
    <div class="result-row"><span class="result-key">Failure Component</span><span class="result-val" style="color:#ffa502">${pred.failure_component}</span></div>
    <div class="result-row"><span class="result-key">Est. Cost</span><span class="result-val" style="color:#06ffa5">$${pred.estimated_cost?.toFixed(0)}</span></div>
    <div class="result-row"><span class="result-key">Accuracy</span><span class="result-val">${pred.accuracy}%</span></div>
    <div class="result-row"><span class="result-key">Models Used</span><span class="result-val" style="font-size:0.75rem;color:var(--text-secondary)">${(pred.models_used||[]).join(' · ')}</span></div>`;

  const recs = pred.recommendations || [];
  document.getElementById('rec-list').innerHTML = recs.length
    ? recs.map(r => `<div class="rec-card ${r.priority}">
        <div class="rec-action">${r.icon||'🔧'} ${r.action}</div>
        <div class="rec-meta"><span class="risk-badge risk-${r.priority}" style="font-size:0.65rem;padding:2px 8px;">${r.priority}</span><span class="rec-cost">$${r.cost}</span></div>
      </div>`).join('')
    : '<div style="color:var(--text-secondary);font-size:0.82rem;">No recommendations at this time.</div>';
}

// ─── Analytics ───────────────────────────────────────────
async function loadAnalytics() {
  try {
    const res = await fetch('/api/dashboard', { credentials: 'include' });
    const data = await res.json();
    renderAnalyticsCharts(data.trend);
    renderTimeline();
  } catch(e) { console.error('loadAnalytics', e); }
}

function renderTimeline() {
  const events = [
    { date: '2025-11-15', text: 'Tesla Model S — Full service completed', dot: '#06ffa5' },
    { date: '2025-09-10', text: 'Honda Civic — Oil change', dot: '#00d4ff' },
    { date: '2025-05-20', text: 'BMW 5 Series — Brake inspection', dot: '#ffa502' },
    { date: '2024-09-01', text: 'Ford F-150 — CRITICAL: Multiple failures detected', dot: '#ff4757' },
    { date: '2024-06-12', text: 'Tesla Model S — Tire rotation', dot: '#8b5cf6' },
  ];
  document.getElementById('analytics-timeline').innerHTML = events.map(e =>
    `<div class="timeline-item">
      <div class="timeline-dot" style="background:${e.dot};box-shadow:0 0 8px ${e.dot}"></div>
      <div class="timeline-content">
        <div class="timeline-date">${e.date}</div>
        <div class="timeline-text">${e.text}</div>
      </div>
    </div>`).join('');
}

// ─── Vehicles Grid ───────────────────────────────────────
function renderVehiclesGrid() {
  const el = document.getElementById('vehicles-grid');
  if (!vehicles.length) { el.innerHTML = '<div style="color:var(--text-secondary);font-size:0.85rem;padding:20px;grid-column:1/-1;">No vehicles yet.</div>'; return; }
  el.innerHTML = vehicles.map(v => `
    <div class="glass-card" style="padding:20px;cursor:pointer;" onclick="showSection('dashboard');selectVehicle(${v.id})">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
        <div>
          <div style="font-family:'Orbitron',monospace;font-size:0.85rem;color:var(--neon-blue);">${v.vehicle_number}</div>
          <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:2px;">${v.manufacturer} ${v.vehicle_model}</div>
        </div>
        <span style="font-size:1.5rem;">🚗</span>
      </div>
      ${progressBarHtml('Oil', v.oil_quality, 100, 30, 50)}
      ${progressBarHtml('Battery', v.battery_health, 100, 25, 50)}
      ${progressBarHtml('Brakes', v.brake_condition, 100, 30, 55)}
      <div style="display:flex;justify-content:space-between;margin-top:10px;font-size:0.78rem;color:var(--text-secondary);">
        <span>🌡️ ${v.engine_temp}°C</span>
        <span>⛽ ${v.fuel_efficiency} km/L</span>
        <span>📏 ${Number(v.mileage).toLocaleString()} km</span>
      </div>
    </div>`).join('');
}

// ─── History ─────────────────────────────────────────────
async function loadHistory() {
  if (!activeVehicleId) {
    document.getElementById('history-list').innerHTML = '<div style="color:var(--text-secondary);font-size:0.82rem;text-align:center;padding:30px;">Select a vehicle from the Dashboard first.</div>';
    return;
  }
  try {
    const res = await fetch(`/api/vehicles/${activeVehicleId}/predictions`, { credentials: 'include' });
    const data = await res.json();
    const preds = data.predictions || [];
    document.getElementById('history-list').innerHTML = preds.length
      ? `<table style="width:100%;border-collapse:collapse;font-size:0.82rem;">
          <thead><tr style="color:var(--text-secondary);border-bottom:1px solid var(--glass-border);">
            <th style="text-align:left;padding:8px;">Date</th>
            <th style="text-align:left;padding:8px;">Health</th>
            <th style="text-align:left;padding:8px;">Risk</th>
            <th style="text-align:left;padding:8px;">Urgency</th>
            <th style="text-align:left;padding:8px;">Cost</th>
          </tr></thead>
          <tbody>${preds.map(p => `<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
            <td style="padding:8px;color:var(--text-secondary);">${new Date(p.created_at).toLocaleDateString()}</td>
            <td style="padding:8px;color:${p.health_score>=70?'#06ffa5':p.health_score>=40?'#ffa502':'#ff4757'};font-weight:600;">${p.health_score}%</td>
            <td style="padding:8px;">${riskBadgeHtml(p.risk_level)}</td>
            <td style="padding:8px;color:var(--text-primary);">${p.urgency}</td>
            <td style="padding:8px;color:#06ffa5;">$${p.estimated_cost?.toFixed(0)||0}</td>
          </tr>`).join('')}</tbody>
        </table>`
      : '<div style="color:var(--text-secondary);text-align:center;padding:30px;">No predictions yet.</div>';
  } catch(e) { console.error('loadHistory', e); }
}

// ─── Chatbot ─────────────────────────────────────────────
function toggleChatbot() {
  document.getElementById('chatbot-window').classList.toggle('open');
}

async function sendChat() {
  const input = document.getElementById('chatbot-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';

  const msgs = document.getElementById('chatbot-messages');
  msgs.innerHTML += `<div class="msg msg-user">${msg}</div>`;
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const res = await fetch('/api/chatbot', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ message: msg }), credentials: 'include'
    });
    const data = await res.json();
    msgs.innerHTML += `<div class="msg msg-bot">${data.reply}</div>`;
    msgs.scrollTop = msgs.scrollHeight;
  } catch(e) {
    msgs.innerHTML += `<div class="msg msg-bot">Sorry, I'm having trouble connecting right now.</div>`;
  }
}

// ─── Voice Input ─────────────────────────────────────────
let recognition = null;
let isListening = false;

function toggleVoice() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    toast('Voice input not supported in this browser. Try Chrome.', 'error'); return;
  }
  if (isListening) {
    recognition.stop(); isListening = false;
    document.getElementById('voice-btn').classList.remove('listening');
    document.getElementById('voice-btn').textContent = '🎤 Voice';
    return;
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.lang = 'en-US';
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript.toLowerCase();
    toast(`Voice: "${transcript}"`, 'info');
    parseVoiceInput(transcript);
    isListening = false;
    document.getElementById('voice-btn').classList.remove('listening');
    document.getElementById('voice-btn').textContent = '🎤 Voice';
  };
  recognition.onerror = () => {
    toast('Voice recognition error', 'error');
    isListening = false;
    document.getElementById('voice-btn').classList.remove('listening');
    document.getElementById('voice-btn').textContent = '🎤 Voice';
  };
  recognition.start();
  isListening = true;
  document.getElementById('voice-btn').classList.add('listening');
  document.getElementById('voice-btn').textContent = '🔴 Listening...';
}

function parseVoiceInput(text) {
  const mileMatch = text.match(/(\d+)\s*(thousand|k)?\s*(?:kilo(?:meters?)?|km|miles?)/i);
  if (mileMatch) {
    let val = parseInt(mileMatch[1]);
    if (mileMatch[2]) val *= 1000;
    document.getElementById('f-mileage').value = val;
    toast(`Mileage set to ${val} km`, 'success');
  }
  const tempMatch = text.match(/(?:engine|temperature|temp)\s*(?:is|at|:)?\s*(\d+)/i);
  if (tempMatch) {
    document.getElementById('f-engine-temp').value = parseInt(tempMatch[1]);
    toast(`Engine temp set to ${tempMatch[1]}°C`, 'success');
  }
  const oilMatch = text.match(/oil\s*(?:quality|level)?\s*(?:is|at|:)?\s*(\d+)/i);
  if (oilMatch) {
    document.getElementById('f-oil').value = parseInt(oilMatch[1]);
    toast(`Oil quality set to ${oilMatch[1]}%`, 'success');
  }
}

// ─── Init ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  showSection('dashboard');
  // Set default date
  document.getElementById('f-last-service').value = new Date(Date.now()-180*864e5).toISOString().split('T')[0];
});
