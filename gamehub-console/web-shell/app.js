const clockElement = document.getElementById("live-clock");
const batteryLabel = document.getElementById("battery-label");
const batteryFill = document.getElementById("battery-fill");
const DEFAULT_BATTERY_LEVEL = 87;
const MIN_VISIBLE_FILL = 12;

function formatTime(date) {
  const hours24 = date.getHours();
  const hours12 = ((hours24 + 11) % 12) + 1;
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const suffix = hours24 >= 12 ? "pm" : "am";
  return `${String(hours12).padStart(2, "0")}:${minutes} ${suffix}`;
}

function updateClock() {
  if (!clockElement) {
    return;
  }

  const now = new Date();
  clockElement.textContent = formatTime(now);
  clockElement.dateTime = now.toISOString();
}

function batteryGradient(level) {
  if (level <= 20) {
    return "linear-gradient(90deg, #ff8b8b 0%, #dc2626 100%)";
  }

  if (level <= 45) {
    return "linear-gradient(90deg, #ffd36f 0%, #d99811 100%)";
  }

  return "linear-gradient(90deg, #8bf1b1 0%, #2ad06a 100%)";
}

function setBatteryLevel(level) {
  if (!batteryLabel || !batteryFill) {
    return;
  }

  const safeLevel = Math.max(0, Math.min(100, Math.round(level)));
  batteryLabel.textContent = `${safeLevel}%`;
  batteryFill.style.width = `${Math.max(safeLevel, MIN_VISIBLE_FILL)}%`;
  batteryFill.style.background = batteryGradient(safeLevel);
}

async function initBattery() {
  if (!("getBattery" in navigator)) {
    setBatteryLevel(DEFAULT_BATTERY_LEVEL);
    return;
  }

  try {
    const battery = await navigator.getBattery();
    const applyBatteryState = () => setBatteryLevel(battery.level * 100);

    applyBatteryState();
    battery.addEventListener("levelchange", applyBatteryState);
    battery.addEventListener("chargingchange", applyBatteryState);
  } catch (error) {
    console.warn("Battery API unavailable, using fallback percentage.", error);
    setBatteryLevel(DEFAULT_BATTERY_LEVEL);
  }
}

setBatteryLevel(DEFAULT_BATTERY_LEVEL);
updateClock();
initBattery();
window.setInterval(updateClock, 1000);
