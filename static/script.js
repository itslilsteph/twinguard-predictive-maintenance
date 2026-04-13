let xGauge, yGauge, zGauge, magGauge;
let xyzChart, magChart;

function initGauges() {
  xGauge = new JustGage({
    id: "xGauge",
    value: 0,
    min: -500,
    max: 500,
    title: "X",
    label: "",
    levelColors: ["#4CAF50"]
  });

  yGauge = new JustGage({
    id: "yGauge",
    value: 0,
    min: -500,
    max: 500,
    title: "Y",
    label: "",
    levelColors: ["#00BFFF"]
  });

  zGauge = new JustGage({
    id: "zGauge",
    value: 0,
    min: -500,
    max: 500,
    title: "Z",
    label: "",
    levelColors: ["#FF5733"]
  });

  magGauge = new JustGage({
    id: "magGauge",
    value: 0,
    min: -500,
    max: 500,
    title: "Magnitude",
    label: "",
    levelColors: ["#8e44ad"]
  });
}

function initCharts() {
  const xyzCtx = document.getElementById("xyzChart").getContext("2d");
  xyzChart = new Chart(xyzCtx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "X",
          data: [],
          borderColor: "#e74c3c",
          backgroundColor: "rgba(231, 76, 60, 0.1)",
          tension: 0,
          pointRadius: 0,
          borderWidth: 2
        },
        {
          label: "Y",
          data: [],
          borderColor: "#27ae60",
          backgroundColor: "rgba(39, 174, 96, 0.1)",
          tension: 0,
          pointRadius: 0,
          borderWidth: 2
        },
        {
          label: "Z",
          data: [],
          borderColor: "#3498db",
          backgroundColor: "rgba(52, 152, 219, 0.1)",
          tension: 0,
          pointRadius: 0,
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      normalized: true,
      plugins: {
        legend: {
          display: true
        }
      },
      elements: {
        line: {
          tension: 0
        },
        point: {
          radius: 0
        }
      }
    }
  });

  const magCtx = document.getElementById("magChart").getContext("2d");
  magChart = new Chart(magCtx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Magnitude",
          data: [],
          borderColor: "#8e44ad",
          backgroundColor: "rgba(142, 68, 173, 0.1)",
          tension: 0,
          pointRadius: 0,
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      normalized: true,
      plugins: {
        legend: {
          display: true
        }
      },
      elements: {
        line: {
          tension: 0
        },
        point: {
          radius: 0
        }
      }
    }
  });
}

function updateTime() {
  const now = new Date();
  const dayElement = document.getElementById("day");
  const dateElement = document.getElementById("date");
  const timeElement = document.getElementById("time");

  let hours = now.getHours();
  const ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12;
  hours = hours ? hours : 12;
  const minutes = now.getMinutes().toString().padStart(2, "0");

  timeElement.innerText = `${hours}:${minutes} ${ampm}`;

  dayElement.innerText = now.toLocaleDateString("en-US", {
    weekday: "long"
  });

  const day = now.getDate().toString().padStart(2, "0");
  const month = (now.getMonth() + 1).toString().padStart(2, "0");
  const year = now.getFullYear();

  dateElement.innerText = `${day}.${month}.${year}`;
}

function updateInsights(d) {
  const faultLevelEl = document.getElementById("faultLevel");
  const lastFaultEl = document.getElementById("lastFault");
  const faultCountEl = document.getElementById("faultCount");
  const maxDeviationEl = document.getElementById("maxDeviation");

  if (!faultLevelEl || !lastFaultEl || !faultCountEl || !maxDeviationEl) {
    return;
  }

  faultLevelEl.innerText = d.severity ?? "--";
  lastFaultEl.innerText = d.last_fault_time ?? "--";
  faultCountEl.innerText = d.fault_count ?? 0;
  maxDeviationEl.innerText = d.max_deviation_today ?? 0;

  faultLevelEl.className = "insight-value";

  if (d.severity === "None") {
    faultLevelEl.classList.add("fault-normal");
    faultLevelEl.innerText = "Normal";
  } else if (d.severity === "Mild") {
    faultLevelEl.classList.add("fault-mild");
  } else if (d.severity === "Moderate") {
    faultLevelEl.classList.add("fault-moderate");
  } else if (d.severity === "Critical") {
    faultLevelEl.classList.add("fault-critical");
  }
}

async function updateData() {
  const res = await fetch("/data");
  const d = await res.json();

  const x = d.x ?? 0;
  const y = d.y ?? 0;
  const z = d.z ?? 0;
  const rms = d.rms ?? 0;
  const baseline = d.baseline ?? 0;
  const deviation = d.deviation ?? 0;
  const health = d.health ?? "Calibrating...";
  const status = d.status ?? "Waiting...";
  const severity = d.severity ?? "None";
  const temperature = d.temperature !== undefined ? d.temperature : "--";

  const magnitude = Math.sqrt(x * x + y * y + z * z);

  const isError =
    status.toLowerCase().includes("error") ||
    status.toLowerCase().includes("failed");

  if (isError) {
    const statusEl = document.getElementById("systemStatus");
    statusEl.className = "";
    statusEl.classList.add("status-failed");
    statusEl.innerText = "Failed";

    document.getElementById("systemHealth").innerText = "N/A";
    document.getElementById("severityCard").innerText = "N/A";
    document.getElementById("rms").innerText = "N/A";
    document.getElementById("baseline").innerText = "N/A";
    document.getElementById("deviation").innerText = "N/A";
    document.getElementById("temperatureCard").innerText = "N/A";

    const faultLevelEl = document.getElementById("faultLevel");
    const lastFaultEl = document.getElementById("lastFault");
    const faultCountEl = document.getElementById("faultCount");
    const maxDeviationEl = document.getElementById("maxDeviation");

    if (faultLevelEl) faultLevelEl.innerText = "--";
    if (lastFaultEl) lastFaultEl.innerText = "--";
    if (faultCountEl) faultCountEl.innerText = "0";
    if (maxDeviationEl) maxDeviationEl.innerText = "0";

    if (xGauge) xGauge.refresh(0);
    if (yGauge) yGauge.refresh(0);
    if (zGauge) zGauge.refresh(0);
    if (magGauge) magGauge.refresh(0);

    return;
  }

  const statusEl = document.getElementById("systemStatus");
  statusEl.className = "";

  const statusLower = status.toLowerCase();

  if (statusLower.includes("running")) {
    statusEl.innerText = "Running";
    statusEl.classList.add("status-running");
  } else if (statusLower.includes("connecting")) {
    statusEl.innerText = "Connecting";
    statusEl.classList.add("status-connecting");
  } else {
    statusEl.innerText = status;
  }

  document.getElementById("systemHealth").innerText = health;
  document.getElementById("severityCard").innerText = severity;
  document.getElementById("rms").innerText = rms;
  document.getElementById("baseline").innerText = baseline;
  document.getElementById("deviation").innerText = deviation;
  document.getElementById("temperatureCard").innerText =
    temperature === "--" ? "-- °C" : `${temperature} °C`;

  const healthEl = document.getElementById("systemHealth");
  healthEl.className = "";
  if (health.includes("Normal")) healthEl.classList.add("status-normal");
  else if (health.includes("Mild")) healthEl.classList.add("status-mild");
  else if (health.includes("Moderate")) healthEl.classList.add("status-moderate");
  else if (health.includes("Critical") || health.includes("Fault")) healthEl.classList.add("status-critical");
  else healthEl.classList.add("status-cal");

  const severityEl = document.getElementById("severityCard");
  severityEl.className = "";
  if (health.includes("Normal")) severityEl.classList.add("status-normal");
  else if (health.includes("Mild")) severityEl.classList.add("status-mild");
  else if (health.includes("Moderate")) severityEl.classList.add("status-moderate");
  else if (health.includes("Critical") || health.includes("Fault")) severityEl.classList.add("status-critical");
  else severityEl.classList.add("status-cal");

  updateInsights(d);

  if (xGauge) xGauge.refresh(x);
  if (yGauge) yGauge.refresh(y);
  if (zGauge) zGauge.refresh(z);
  if (magGauge) magGauge.refresh(Math.round(magnitude));

  xyzChart.data.labels = (d.history_x || []).map((_, i) => i);
  xyzChart.data.datasets[0].data = d.history_x || [];
  xyzChart.data.datasets[1].data = d.history_y || [];
  xyzChart.data.datasets[2].data = d.history_z || [];
  xyzChart.update();

  magChart.data.labels = (d.history_mag || []).map((_, i) => i);
  magChart.data.datasets[0].data = d.history_mag || [];
  magChart.update();
}

window.onload = function () {
  updateTime();
  setInterval(updateTime, 1000);
  initGauges();
  initCharts();
  updateData();
  setInterval(updateData, 1000);
};