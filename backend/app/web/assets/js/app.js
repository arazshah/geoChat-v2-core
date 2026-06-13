const DEFAULT_CENTER = [37.5527, 45.0761]; // Urmia
const DEFAULT_ZOOM = 13;

const state = {
  map: null,
  resultLayer: null,
  markers: [],
};

const els = {
  queryInput: document.getElementById("queryInput"),
  datasetInput: document.getElementById("datasetInput"),
  languageInput: document.getElementById("languageInput"),
  searchButton: document.getElementById("searchButton"),
  statusText: document.getElementById("statusText"),
  answerBox: document.getElementById("answerBox"),
  resultsList: document.getElementById("resultsList"),
  resultCount: document.getElementById("resultCount"),
  pluginHealthButton: document.getElementById("pluginHealthButton"),
  pluginHealthBox: document.getElementById("pluginHealthBox"),
};

function setStatus(text, type = "normal") {
  els.statusText.textContent = text;

  if (type === "error") {
    els.statusText.style.color = "#dc2626";
  } else if (type === "success") {
    els.statusText.style.color = "#16a34a";
  } else {
    els.statusText.style.color = "#172033";
  }
}

function initMap() {
  state.map = L.map("map", {
    zoomControl: true,
    preferCanvas: true,
  }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(state.map);

  state.resultLayer = L.layerGroup().addTo(state.map);

  // Prevent broken/tiled map rendering after layout changes.
  setTimeout(() => {
    state.map.invalidateSize();
  }, 250);
}

function normalizeText(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  return String(value);
}

function getName(item) {
  const candidates = [
    item?.display_name,
    item?.name,
    item?.title,
    item?.label,
    item?.properties?.display_name,
    item?.properties?.name,
    item?.properties?.title,
    item?.properties?.label,
    item?.names?.fa,
    item?.names?.en,
    item?.properties?.names?.fa,
    item?.properties?.names?.en,
  ];

  return normalizeText(candidates.find(Boolean), "بدون نام");
}

function getCategory(item) {
  const candidates = [
    item?.category,
    item?.kind,
    item?.type,
    item?.properties?.category,
    item?.properties?.kind,
    item?.properties?.type,
    item?.poi_category,
    item?.properties?.poi_category,
  ];

  return normalizeText(candidates.find(Boolean), "مکان");
}

function getDistanceText(item) {
  const distance =
    item?.distance_m ??
    item?.spatial_metrics?.distance_m ??
    item?.properties?.distance_m ??
    item?.properties?.spatial_metrics?.distance_m;

  if (distance === null || distance === undefined || Number.isNaN(Number(distance))) {
    return "";
  }

  const meters = Math.round(Number(distance));

  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(1)} کیلومتر`;
  }

  return `${meters} متر`;
}

function extractLatLonFromObject(obj) {
  if (!obj || typeof obj !== "object") return null;

  const lat =
    obj.lat ??
    obj.latitude ??
    obj.y ??
    obj.properties?.lat ??
    obj.properties?.latitude ??
    obj.properties?.y;

  const lon =
    obj.lon ??
    obj.lng ??
    obj.longitude ??
    obj.x ??
    obj.properties?.lon ??
    obj.properties?.lng ??
    obj.properties?.longitude ??
    obj.properties?.x;

  if (lat !== undefined && lon !== undefined) {
    const latNum = Number(lat);
    const lonNum = Number(lon);

    if (Number.isFinite(latNum) && Number.isFinite(lonNum)) {
      return [latNum, lonNum];
    }
  }

  const centroid = obj.centroid ?? obj.properties?.centroid;
  if (centroid && typeof centroid === "object") {
    return extractLatLonFromObject(centroid);
  }

  const center = obj.center ?? obj.properties?.center;
  if (center && typeof center === "object") {
    return extractLatLonFromObject(center);
  }

  return null;
}

function geoJsonToLatLng(geometry) {
  if (!geometry || typeof geometry !== "object") return null;

  if (geometry.type === "Point" && Array.isArray(geometry.coordinates)) {
    const [lon, lat] = geometry.coordinates;
    if (Number.isFinite(Number(lat)) && Number.isFinite(Number(lon))) {
      return [Number(lat), Number(lon)];
    }
  }

  if (geometry.type === "Feature" && geometry.geometry) {
    return geoJsonToLatLng(geometry.geometry);
  }

  return null;
}

function getGeometry(item) {
  return (
    item?.geometry ??
    item?.geojson ??
    item?.properties?.geometry ??
    item?.properties?.geojson ??
    null
  );
}

function getLatLng(item) {
  const geometry = getGeometry(item);
  const fromGeometry = geoJsonToLatLng(geometry);

  if (fromGeometry) return fromGeometry;

  return extractLatLonFromObject(item);
}

function extractFeatures(responsePayload) {
  const root = responsePayload?.data ?? responsePayload ?? {};

  const candidates = [
    root.features,
    root.results,
    root.items,
    root.geo_features,
    root.data?.features,
    root.data?.results,
    root.data?.items,
    root.payload?.features,
    root.payload?.results,
  ];

  const found = candidates.find(Array.isArray);
  return found ?? [];
}

function extractAnswer(responsePayload) {
  const root = responsePayload?.data ?? responsePayload ?? {};

  const candidates = [
    root.answer,
    root.text,
    root.message,
    root.summary,
    root.response_text,
    root.natural_language_response,
    root.data?.answer,
    root.data?.text,
  ];

  return normalizeText(candidates.find(Boolean), "پاسخی برای نمایش وجود ندارد.");
}

function clearMap() {
  state.resultLayer.clearLayers();
  state.markers = [];
}

function iconForCategory(category) {
  const normalized = category.toLowerCase();

  if (normalized.includes("bank") || category.includes("بانک")) return "🏦";
  if (normalized.includes("restaurant") || category.includes("رستوران")) return "🍽️";
  if (normalized.includes("cafe") || category.includes("کافه")) return "☕";
  if (normalized.includes("pharmacy") || category.includes("داروخانه")) return "💊";
  if (normalized.includes("fuel") || category.includes("پمپ")) return "⛽";
  if (normalized.includes("university") || category.includes("دانشگاه")) return "🎓";
  if (normalized.includes("hospital") || category.includes("بیمارستان")) return "🏥";
  if (normalized.includes("fire") || category.includes("آتش")) return "🚒";

  return "📍";
}

function addFeaturesToMap(features) {
  clearMap();

  const bounds = [];

  features.forEach((item, index) => {
    const latLng = getLatLng(item);
    if (!latLng) return;

    const name = getName(item);
    const category = getCategory(item);
    const distanceText = getDistanceText(item);
    const icon = iconForCategory(category);

    const marker = L.marker(latLng)
      .bindPopup(`
        <strong>${icon} ${escapeHtml(name)}</strong>
        <br />
        <span>${escapeHtml(category)}</span>
        ${distanceText ? `<br /><span>${escapeHtml(distanceText)}</span>` : ""}
      `)
      .addTo(state.resultLayer);

    marker.__resultIndex = index;
    state.markers[index] = marker;
    bounds.push(latLng);
  });

  if (bounds.length === 1) {
    state.map.setView(bounds[0], 16);
  } else if (bounds.length > 1) {
    state.map.fitBounds(bounds, {
      padding: [40, 40],
      maxZoom: 16,
    });
  }

  setTimeout(() => {
    state.map.invalidateSize();
  }, 100);
}

function renderResults(features) {
  els.resultCount.textContent = `${features.length.toLocaleString("fa-IR")} مورد`;

  if (!features.length) {
    els.resultsList.innerHTML = `
      <div class="empty-state">
        نتیجه‌ای برای نمایش وجود ندارد.
      </div>
    `;
    return;
  }

  els.resultsList.innerHTML = "";

  features.forEach((item, index) => {
    const name = getName(item);
    const category = getCategory(item);
    const distanceText = getDistanceText(item);
    const icon = iconForCategory(category);
    const latLng = getLatLng(item);

    const div = document.createElement("div");
    div.className = "result-item";
    div.innerHTML = `
      <div class="result-title">
        <span>${icon}</span>
        <span>${escapeHtml(name)}</span>
      </div>
      <div class="result-meta">
        ${escapeHtml(category)}
        ${distanceText ? ` · ${escapeHtml(distanceText)}` : ""}
        ${latLng ? ` · ${latLng[0].toFixed(5)}, ${latLng[1].toFixed(5)}` : ""}
      </div>
    `;

    div.addEventListener("click", () => {
      const marker = state.markers[index];
      if (marker) {
        state.map.setView(marker.getLatLng(), 17);
        marker.openPopup();
      }
    });

    els.resultsList.appendChild(div);
  });
}

async function runQuery() {
  const text = els.queryInput.value.trim();
  const datasetId = els.datasetInput.value.trim() || "urmia";
  const language = els.languageInput.value.trim() || "fa";

  if (!text) {
    setStatus("پرسش خالی است", "error");
    els.queryInput.focus();
    return;
  }

  els.searchButton.disabled = true;
  setStatus("در حال جستجو...", "normal");

  try {
    const response = await fetch("/api/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        dataset_id: datasetId,
        language,
        metadata: {},
      }),
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload?.detail || "خطا در دریافت پاسخ از API");
    }

    const features = extractFeatures(payload);
    const answer = extractAnswer(payload);

    els.answerBox.textContent = answer;

    renderResults(features);
    addFeaturesToMap(features);

    setStatus("انجام شد", "success");
  } catch (error) {
    console.error(error);
    setStatus("خطا", "error");
    els.answerBox.textContent = error?.message || "خطای ناشناخته رخ داد.";
    renderResults([]);
    clearMap();
  } finally {
    els.searchButton.disabled = false;
  }
}

async function checkPluginHealth() {
  try {
    setStatus("در حال بررسی پلاگین‌ها...", "normal");

    const response = await fetch("/api/plugins/health");
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload?.detail || "خطا در بررسی پلاگین‌ها");
    }

    els.pluginHealthBox.classList.remove("hidden");
    els.pluginHealthBox.textContent = JSON.stringify(payload, null, 2);

    setStatus("پلاگین‌ها بررسی شدند", "success");
  } catch (error) {
    console.error(error);
    els.pluginHealthBox.classList.remove("hidden");
    els.pluginHealthBox.textContent = error?.message || "خطای ناشناخته";
    setStatus("خطا در پلاگین‌ها", "error");
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function bindEvents() {
  els.searchButton.addEventListener("click", runQuery);
  els.pluginHealthButton.addEventListener("click", checkPluginHealth);

  els.queryInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      runQuery();
    }
  });

  document.querySelectorAll("[data-query]").forEach((button) => {
    button.addEventListener("click", () => {
      els.queryInput.value = button.dataset.query || "";
      els.queryInput.focus();
    });
  });

  window.addEventListener("resize", () => {
    if (state.map) {
      state.map.invalidateSize();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  bindEvents();
});
