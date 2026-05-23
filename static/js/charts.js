// Chart.js dashboard charts
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const NEON_BLUE = '#00d4ff';
const PURPLE = '#8b5cf6';
const GREEN = '#06ffa5';
const ORANGE = '#ff6b35';

const BASE_CFG = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { enabled: true, backgroundColor: 'rgba(10,15,30,0.9)', titleColor: NEON_BLUE, bodyColor: '#e8f4ff', borderColor: 'rgba(0,212,255,0.3)', borderWidth: 1 } },
  scales: {
    x: { display: true, ticks: { color: '#7a9bc0', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
    y: { display: true, ticks: { color: '#7a9bc0', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } }
  }
};

const chartInstances = {};

function makeLineChart(id, labels, data, color, label) {
  const canvas = document.getElementById(id);
  if (!canvas) return null;
  if (chartInstances[id]) { chartInstances[id].destroy(); }
  const cfg = JSON.parse(JSON.stringify(BASE_CFG));
  chartInstances[id] = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{ label, data, borderColor: color, backgroundColor: color + '18', fill: true, tension: 0.4, pointBackgroundColor: color, pointRadius: 3 }]
    },
    options: cfg
  });
  return chartInstances[id];
}

function makePieChart(id, labels, data, colors) {
  const canvas = document.getElementById(id);
  if (!canvas) return null;
  if (chartInstances[id]) { chartInstances[id].destroy(); }
  chartInstances[id] = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data, backgroundColor: colors, borderColor: 'rgba(10,15,30,0.8)', borderWidth: 2 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '65%',
      plugins: {
        legend: { display: true, position: 'bottom', labels: { color: '#7a9bc0', font: { size: 10 }, padding: 8 } },
        tooltip: { backgroundColor: 'rgba(10,15,30,0.9)', titleColor: NEON_BLUE, bodyColor: '#e8f4ff' }
      }
    }
  });
  return chartInstances[id];
}

function makeBarChart(id, labels, data, color) {
  const canvas = document.getElementById(id);
  if (!canvas) return null;
  if (chartInstances[id]) { chartInstances[id].destroy(); }
  const cfg = JSON.parse(JSON.stringify(BASE_CFG));
  chartInstances[id] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{ data, backgroundColor: color + '88', borderColor: color, borderWidth: 1, borderRadius: 4 }]
    },
    options: cfg
  });
  return chartInstances[id];
}

function renderDashboardCharts(trend, riskDist) {
  const labels = MONTHS.slice(0, trend.health.length);
  makeLineChart('chart-health-trend', labels, trend.health, NEON_BLUE, 'Health %');

  const rd = riskDist || { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
  makePieChart('chart-risk-pie',
    ['Low Risk', 'Medium', 'High', 'Critical'],
    [rd.LOW || 0, rd.MEDIUM || 0, rd.HIGH || 0, rd.CRITICAL || 0],
    [GREEN, '#ffa502', ORANGE, '#ff4757']
  );
}

function renderAnalyticsCharts(trend) {
  const labels = MONTHS.slice(0, trend.health.length);
  makeLineChart('chart-engine', labels, trend.engine, ORANGE, 'Engine Temp °C');
  makeLineChart('chart-battery', labels, trend.battery, GREEN, 'Battery %');
  makeLineChart('chart-fuel', labels, trend.fuel, PURPLE, 'Fuel km/L');

  // Failure probability (simulated)
  const failureProbs = trend.health.map(h => +(100 - h).toFixed(1));
  makeBarChart('chart-failure', labels, failureProbs, '#ff4757');
}
