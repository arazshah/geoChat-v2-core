const DEFAULT_CENTER = [37.5527, 45.0761]; // Urmia
const DEFAULT_ZOOM = 13;

const state = {
  map: null,
  resultLayer: null,
  markers: [],
  anchorMarker: null,
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
    preferCanvas: false,
  }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(state.map);

  state.resultLayer = L.layerGroup().addTo(state.map);

  setTimeout(() => {
    state.map.invalidateSize();
  }, 250);
}

// ------------------------------------------------------------------ //
// Role helpers                                                         //
// ------------------------------------------------------------------ //

function getRole(item) {
  return (
    item?.metadata?.role ||
    item?.properties?.metadata?.role ||
    item?.properties?.role ||
    "target"
  );
}

function isAnchor(item) {
  return getRole(item) === "anchor";
}

// ------------------------------------------------------------------ //
// Text helpers                                                         //
// ------------------------------------------------------------------ //

function normalizeText(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  return String(value);
}

function getName(item) {
  const candidates = [
    item?.display?.label,
    item?.display_name,
    item?.name,
    item?.title,
    item?.label,
    item?.properties?.display_name,
    item?.properties?.name,
    item?.names?.fa,
    item?.names?.en,
  ];
  return normalizeText(candidates.find(Boolean), "بدون نام");
}

function getCategory(item) {
  const candidates = [
    item?.display?.category_label,
    item?.category,
    item?.kind,
    item?.type,
    item?.properties?.category,
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

// ------------------------------------------------------------------ //
// Geometry helpers                                                     //
// ------------------------------------------------------------------ //

function extractLatLonFromObject(obj) {
  if (!obj || typeof obj !== "object") return null;

  const lat =
    obj.lat ?? obj.latitude ?? obj.y ??
    obj.properties?.lat ?? obj.properties?.latitude;

  const lon =
    obj.lon ?? obj.lng ?? obj.longitude ?? obj.x ??
    obj.properties?.lon ?? obj.properties?.lng ?? obj.properties?.longitude;

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
  return item?.geometry ?? item?.geojson ?? item?.properties?.geometry ?? null;
}

function getLatLng(item) {
  const fromGeometry = geoJsonToLatLng(getGeometry(item));
  if (fromGeometry) return fromGeometry;
  return extractLatLonFromObject(item);
}

// ------------------------------------------------------------------ //
// Icons                                                                //
// ------------------------------------------------------------------ //

function iconForCategory(category) {
  const n = (category || "").toLowerCase();
  if (n.includes("bank") || category.includes("بانک")) return "🏦";
  if (n.includes("restaurant") || category.includes("رستوران")) return "🍽️";
  if (n.includes("cafe") || category.includes("کافه")) return "☕";
  if (n.includes("pharmacy") || category.includes("داروخانه")) return "💊";
  if (n.includes("fuel") || category.includes("پمپ")) return "⛽";
  if (n.includes("university") || category.includes("دانشگاه")) return "🎓";
  if (n.includes("hospital") || category.includes("بیمارستان")) return "🏥";
  if (n.includes("school") || category.includes("مدرسه")) return "🏫";
  if (n.includes("park") || category.includes("پارک")) return "🌳";
  if (n.includes("hotel") || category.includes("هتل")) return "🏨";
  if (n.includes("place") || n.includes("square") || category.includes("میدان")) return "🏛️";
  if (n.includes("fire") || category.includes("آتش")) return "🚒";
  return "📍";
}

function getDisplayIcon(item) {
  if (isAnchor(item)) return "🎯";
  const icon = item?.display?.icon;
  if (icon) return icon;
  return iconForCategory(getCategory(item));
}

function makeLeafletIcon(item) {
  const emoji = getDisplayIcon(item);
  const anchor = isAnchor(item);

  const size = anchor ? 44 : 36;
  const bg = anchor ? "#dc2626" : "#2563eb";
  const border = anchor ? "#991b1b" : "#1d4ed8";
  const zIndex = anchor ? 1000 : 500;

  return L.divIcon({
    className: "",
    html: `
      <div style="
        width:${size}px;
        height:${size}px;
        background:${bg};
        border:2px solid ${border};
        border-radius:50%;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:${anchor ? 22 : 18}px;
        box-shadow:0 2px 6px rgba(0,0,0,0.35);
        cursor:pointer;
        z-index:${zIndex};
      ">${emoji}</div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2 + 4)],
  });
}

// ------------------------------------------------------------------ //
// Feature splitting                                                    //
// ------------------------------------------------------------------ //

function splitFeatures(features) {
  const anchors = features.filter(isAnchor);
  const targets = features.filter((f) => !isAnchor(f));
  return { anchors, targets };
}

// ------------------------------------------------------------------ //
// Map rendering                                                        //
// ------------------------------------------------------------------ //

function clearMap() {
  state.resultLayer.clearLayers();
  state.markers = [];
  state.anchorMarker = null;
}

function addFeaturesToMap(features) {
  clearMap();

  const { anchors, targets } = splitFeatures(features);
  const bounds = [];

  // Render anchors first (higher z-index stays on top)
  anchors.forEach((item) => {
    const latLng = getLatLng(item);
    if (!latLng) return;

    const name = getName(item);
    const category = getCategory(item);

    const marker = L.marker(latLng, { icon: makeLeafletIcon(item), zIndexOffset: 1000 })
      .bindPopup(`
        <strong>🎯 ${escapeHtml(name)}</strong>
        <br/>
        <span style="color:#dc2626;font-size:12px">مکان مرجع · ${escapeHtml(category)}</span>
      `)
      .addTo(state.resultLayer);

    state.anchorMarker = marker;
    bounds.push(latLng);
  });

  // Render targets
  targets.forEach((item, index) => {
    const latLng = getLatLng(item);
    if (!latLng) return;

    const name = getName(item);
    const category = getCategory(item);
    const distanceText = getDistanceText(item);
    const icon = getDisplayIcon(item);

    const marker = L.marker(latLng, { icon: makeLeafletIcon(item) })
      .bindPopup(`
        <strong>${escapeHtml(icon)} ${escapeHtml(name)}</strong>
        <br/>
        <span>${escapeHtml(category)}</span>
        ${distanceText ? `<br/><span style="color:#2563eb">📏 ${escapeHtml(distanceText)}</span>` : ""}
      `)
      .addTo(state.resultLayer);

    marker.__resultIndex = index;
    state.markers[index] = marker;
    bounds.push(latLng);
  });

  if (bounds.length === 1) {
    state.map.setView(bounds[0], 16);
  } else if (bounds.length > 1) {
    state.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
  }

  setTimeout(() => state.map.invalidateSize(), 100);
}

// ------------------------------------------------------------------ //
// List rendering                                                       //
// ------------------------------------------------------------------ //

function renderResults(features) {
  const { anchors, targets } = splitFeatures(features);

  // Count label shows only targets (anchor is reference, not a result)
  els.resultCount.textContent = `${targets.length.toLocaleString("fa-IR")} مورد`;

  if (!features.length) {
    els.resultsList.innerHTML = `
      <div class="empty-state">نتیجه‌ای برای نمایش وجود ندارد.</div>
    `;
    return;
  }

  els.resultsList.innerHTML = "";

  // ---- Anchor section ----
  if (anchors.length > 0) {
    const section = document.createElement("div");
    section.className = "results-section";
    section.innerHTML = `<div class="results-section-title">📍 مکان مرجع</div>`;

    anchors.forEach((item) => {
      const name = getName(item);
      const category = getCategory(item);
      const latLng = getLatLng(item);

      const div = document.createElement("div");
      div.className = "result-item result-item--anchor";
      div.innerHTML = `
        <div class="result-title">
          <span>🎯</span>
          <span>${escapeHtml(name)}</span>
        </div>
        <div class="result-meta" style="color:#dc2626">
          ${escapeHtml(category)}
          ${latLng ? ` · ${latLng[0].toFixed(5)}, ${latLng[1].toFixed(5)}` : ""}
        </div>
      `;

      div.addEventListener("click", () => {
        if (state.anchorMarker) {
          state.map.setView(state.anchorMarker.getLatLng(), 17);
          state.anchorMarker.openPopup();
        }
      });

      section.appendChild(div);
    });

    els.resultsList.appendChild(section);

    // Divider
    const divider = document.createElement("div");
    divider.className = "results-divider";
    divider.innerHTML = `<span>نتایج جستجو (${targets.length.toLocaleString("fa-IR")} مورد)</span>`;
    els.resultsList.appendChild(divider);
  }

  // ---- Target section ----
  targets.forEach((item, index) => {
    const name = getName(item);
    const category = getCategory(item);
    const distanceText = getDistanceText(item);
    const icon = getDisplayIcon(item);
    const latLng = getLatLng(item);

    const div = document.createElement("div");
    div.className = "result-item";
    div.innerHTML = `
      <div class="result-title">
        <span>${escapeHtml(icon)}</span>
        <span>${escapeHtml(name)}</span>
      </div>
      <div class="result-meta">
        ${escapeHtml(category)}
        ${distanceText ? ` · <span style="color:#2563eb">📏 ${escapeHtml(distanceText)}</span>` : ""}
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

// ------------------------------------------------------------------ //
// Response parsing                                                     //
// ------------------------------------------------------------------ //

function extractFeatures(responsePayload) {
  const root = responsePayload?.data ?? responsePayload ?? {};
  const candidates = [
    root.features,
    root.results,
    root.items,
    root.geo_features,
    root.data?.features,
    root.payload?.features,
  ];
  return candidates.find(Array.isArray) ?? [];
}

function extractAnswer(responsePayload) {
  const root = responsePayload?.data ?? responsePayload ?? {};
  const candidates = [
    root.user_message?.summary,
    root.answer,
    root.text,
    root.message,
    root.summary,
    root.natural_language_response,
  ];
  return normalizeText(candidates.find(Boolean), "پاسخی برای نمایش وجود ندارد.");
}

// ------------------------------------------------------------------ //
// Query                                                                //
// ------------------------------------------------------------------ //

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
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, dataset_id: datasetId, language, metadata: {} }),
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

    const { anchors, targets } = splitFeatures(features);
    const anchorInfo = anchors.length > 0
      ? ` (مرجع: ${getName(anchors[0])})`
      : "";

    setStatus(
      `${targets.length.toLocaleString("fa-IR")} نتیجه${anchorInfo}`,
      "success"
    );
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

    if (!response.ok) throw new Error(payload?.detail || "خطا در بررسی پلاگین‌ها");

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

// ------------------------------------------------------------------ //
// Utilities                                                            //
// ------------------------------------------------------------------ //

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// ------------------------------------------------------------------ //
// Events & init                                                        //
// ------------------------------------------------------------------ //

function bindEvents() {
  els.searchButton.addEventListener("click", runQuery);
  els.pluginHealthButton.addEventListener("click", checkPluginHealth);

  els.queryInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") runQuery();
  });

  document.querySelectorAll("[data-query]").forEach((button) => {
    button.addEventListener("click", () => {
      els.queryInput.value = button.dataset.query || "";
      els.queryInput.focus();
    });
  });

  window.addEventListener("resize", () => {
    if (state.map) state.map.invalidateSize();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  bindEvents();
});
