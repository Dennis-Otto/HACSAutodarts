/*
 * Autodarts cards for Home Assistant, served by the Autodarts integration.
 *
 * - autodarts-card: the current visit on a dartboard drawn with the geometry of
 *   the Autodarts Board Manager. Hit beds blink, darts appear at their detected
 *   position and the board glows in the detection status colour.
 * - autodarts-training-card: the local training session with a hit heatmap,
 *   statistics, the most hit beds and the recent visits.
 * - autodarts-status-card: detection, connections, cameras, the board PC and
 *   maintenance controls at a glance.
 */

const CARD_TYPE = "autodarts-card";
const EDITOR_TYPE = "autodarts-card-editor";
const TRAINING_TYPE = "autodarts-training-card";
const TRAINING_EDITOR_TYPE = "autodarts-training-card-editor";
const STATUS_TYPE = "autodarts-status-card";
const STATUS_EDITOR_TYPE = "autodarts-status-card-editor";
const DOCS = "https://github.com/Dennis-Otto/HACSAutodarts#dashboard-cards";

// Board Manager geometry in millimetres; dart coordinates are normalised to
// the outer edge of the double ring (170 mm) with y pointing to the 20.
const NORM = 170;
const R = {
  bull: 7,
  outerBull: 17,
  trebleIn: 97,
  trebleOut: 107,
  doubleIn: 160,
  doubleOut: 170,
  numbers: 197,
  board: 225,
};
const NUMBERS = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5];
const BEDS = {
  SI: [R.outerBull, R.trebleIn],
  T: [R.trebleIn, R.trebleOut],
  SO: [R.trebleOut, R.doubleIn],
  D: [R.doubleIn, R.doubleOut],
  M: [R.doubleOut, R.board],
};

const STYLES = {
  autodarts: {
    black: "#212121",
    white: "#fffde7",
    red: "#ef5350",
    green: "#66bb6a",
    surround: "#212121",
    wire: "none",
    numbers: "#ffffff",
  },
  classic: {
    black: "#1b1b1b",
    white: "#f1e4c3",
    red: "#d42f2f",
    green: "#1d9150",
    surround: "#101010",
    wire: "#b8bcc2",
    numbers: "#f5f5f5",
  },
  // A quiet board that lets a heatmap stand out.
  muted: {
    black: "#2a2d33",
    white: "#3b3f47",
    red: "#34373e",
    green: "#303339",
    surround: "#1c1e22",
    wire: "#4f545d",
    numbers: "#d6d9de",
  },
};

const STATUS_COLORS = {
  ready: "#43a047",
  takeout: "#fbc02d",
  stopped: "#fb8c00",
  calibrating: "#8e24aa",
  problem: "#e53935",
  offline: "#e53935",
};

const VISIT_COLORS = {
  max: "#ffd60a",
  high: "#ff8c42",
  ton: "#43b581",
  good: "var(--ad-accent)",
  low: "#8a8f98",
};

const TEXT = {
  en: {
    visit: "Current visit",
    points: "points",
    dart: "Dart",
    of: "of",
    miss: "Miss",
    session: "Training session",
    since: "since",
    darts: "Darts",
    average: "3-dart avg.",
    triples: "Triples",
    bulls: "Bulls",
    max: "180s",
    board: "Board Manager",
    realtime: "Realtime",
    cameras: "Cameras",
    camera_problem: "Check cameras",
    start: "Start detection",
    stop: "Stop detection",
    reset: "Reset detection",
    calibrate: "Calibrate",
    confirm: "Confirm?",
    status_offline: "Board unreachable",
    status_calibrating: "Calibrating",
    status_problem: "Check cameras",
    status_starting: "Starting detection",
    status_stopping: "Stopping detection",
    status_stopped: "Detection stopped",
    status_takeout: "Removing darts",
    status_hand: "Hand at the board",
    status_full: "Remove your darts",
    status_ready: "Ready – throw!",
    no_board: "No Autodarts board found. Select a device in the card settings.",
    board_label: "Dartboard with the current visit",
    device_id: "Board",
    device_helper: "Optional. Without a selection, the card uses the first Autodarts board.",
    title: "Title",
    layout: "Layout",
    layout_auto: "Automatic",
    layout_horizontal: "Board on the right",
    layout_vertical: "Board below",
    layout_board: "Board only",
    board_style: "Board style",
    style_classic: "Classic",
    style_autodarts: "Autodarts",
    style_muted: "Muted",
    highlight: "Highlight",
    highlight_visit: "All darts of the visit",
    highlight_last: "Last dart only",
    highlight_none: "Off",
    blink: "Blink hit beds",
    show_markers: "Show dart positions",
    show_numbers: "Show numbers",
    show_stats: "Show training statistics",
    show_connection: "Show connection status",
    show_controls: "Show controls",
    // Training card
    training: "Training",
    average_long: "3-dart average",
    visits: "Visits",
    highest: "Highest visit",
    scores_100: "100+",
    scores_140: "140+",
    doubles: "Doubles",
    misses: "Misses",
    triple_rate: "Triple rate",
    heatmap: "Hit map",
    heatmap_label: "Dartboard coloured by how often each bed was hit",
    top: "Most hit",
    history: "Recent visits",
    history_empty: "Completed visits appear here.",
    no_darts: "No darts in this session yet. Start throwing!",
    new_session: "New session",
    hits: "hits",
    mode: "Heatmap",
    mode_beds: "Beds",
    mode_numbers: "Numbers",
    show_heatmap: "Show heatmap",
    show_top: "Show most hit beds",
    show_history: "Show recent visits",
    show_reset: "Show new session button",
    history_size: "Visits in the history",
    // Status card
    status: "Board status",
    detection: "Detection",
    on: "On",
    off: "Off",
    connections: "Connections",
    cloud: "Cloud",
    version: "Version",
    update_available: "Update to",
    up_to_date: "Up to date",
    system: "Board PC",
    cpu: "CPU",
    memory: "Memory",
    detection_fps: "Detection",
    camera: "Camera",
    camera_ok: "OK",
    camera_failure: "Problem",
    restart: "Restart",
    show_cameras: "Show cameras",
    show_system: "Show board PC",
    unknown: "unknown",
  },
  de: {
    visit: "Aktuelle Aufnahme",
    points: "Punkte",
    dart: "Dart",
    of: "von",
    miss: "Miss",
    session: "Trainingssession",
    since: "seit",
    darts: "Darts",
    average: "3-Dart-Schnitt",
    triples: "Triple",
    bulls: "Bulls",
    max: "180er",
    board: "Board Manager",
    realtime: "Echtzeit",
    cameras: "Kameras",
    camera_problem: "Kameras prüfen",
    start: "Erkennung starten",
    stop: "Erkennung stoppen",
    reset: "Erkennung zurücksetzen",
    calibrate: "Kalibrieren",
    confirm: "Bestätigen?",
    status_offline: "Board nicht erreichbar",
    status_calibrating: "Kalibrierung läuft",
    status_problem: "Kameras prüfen",
    status_starting: "Erkennung startet",
    status_stopping: "Erkennung stoppt",
    status_stopped: "Erkennung gestoppt",
    status_takeout: "Darts werden entnommen",
    status_hand: "Hand am Board",
    status_full: "Darts entnehmen",
    status_ready: "Bereit – wirf!",
    no_board: "Kein Autodarts-Board gefunden. Wähle ein Gerät in den Karteneinstellungen.",
    board_label: "Dartscheibe mit der aktuellen Aufnahme",
    device_id: "Board",
    device_helper: "Optional. Ohne Auswahl nutzt die Karte das erste Autodarts-Board.",
    title: "Titel",
    layout: "Anordnung",
    layout_auto: "Automatisch",
    layout_horizontal: "Scheibe rechts",
    layout_vertical: "Scheibe unten",
    layout_board: "Nur Scheibe",
    board_style: "Scheibenstil",
    style_classic: "Klassisch",
    style_autodarts: "Autodarts",
    style_muted: "Dezent",
    highlight: "Hervorhebung",
    highlight_visit: "Alle Darts der Aufnahme",
    highlight_last: "Nur letzter Dart",
    highlight_none: "Aus",
    blink: "Getroffene Felder blinken",
    show_markers: "Dart-Positionen anzeigen",
    show_numbers: "Zahlen anzeigen",
    show_stats: "Trainingsstatistik anzeigen",
    show_connection: "Verbindungsstatus anzeigen",
    show_controls: "Steuerung anzeigen",
    training: "Training",
    average_long: "3-Dart-Average",
    visits: "Aufnahmen",
    highest: "Beste Aufnahme",
    scores_100: "100+",
    scores_140: "140+",
    doubles: "Doubles",
    misses: "Fehlwürfe",
    triple_rate: "Triple-Quote",
    heatmap: "Trefferbild",
    heatmap_label: "Dartscheibe, eingefärbt nach Trefferhäufigkeit je Feld",
    top: "Häufigste Felder",
    history: "Letzte Aufnahmen",
    history_empty: "Abgeschlossene Aufnahmen erscheinen hier.",
    no_darts: "Noch keine Darts in dieser Session. Leg los!",
    new_session: "Neue Session",
    hits: "Treffer",
    mode: "Heatmap",
    mode_beds: "Felder",
    mode_numbers: "Zahlen",
    show_heatmap: "Heatmap anzeigen",
    show_top: "Häufigste Felder anzeigen",
    show_history: "Letzte Aufnahmen anzeigen",
    show_reset: "Schaltfläche für neue Session anzeigen",
    history_size: "Aufnahmen im Verlauf",
    status: "Board-Status",
    detection: "Erkennung",
    on: "An",
    off: "Aus",
    connections: "Verbindungen",
    cloud: "Cloud",
    version: "Version",
    update_available: "Update auf",
    up_to_date: "Aktuell",
    system: "Board-PC",
    cpu: "CPU",
    memory: "Speicher",
    detection_fps: "Erkennung",
    camera: "Kamera",
    camera_ok: "OK",
    camera_failure: "Störung",
    restart: "Neu starten",
    show_cameras: "Kameras anzeigen",
    show_system: "Board-PC anzeigen",
    unknown: "unbekannt",
  },
};

const DEFAULTS = {
  layout: "auto",
  board_style: "classic",
  highlight: "visit",
  blink: true,
  show_markers: true,
  show_numbers: true,
  show_stats: true,
  show_connection: true,
  show_controls: true,
};

const TRAINING_DEFAULTS = {
  mode: "beds",
  board_style: "muted",
  show_heatmap: true,
  show_stats: true,
  show_top: true,
  show_history: true,
  show_reset: true,
  history_size: 20,
};

const STATUS_DEFAULTS = {
  show_connection: true,
  show_cameras: true,
  show_system: true,
  show_controls: true,
};

// Entities a card reads, by domain and translation key of the integration.
const BOARD_KEYS = {
  status: "sensor.local_status",
  numThrows: "sensor.num_throws",
  connected: "binary_sensor.local_connected",
  realtime: "binary_sensor.realtime_connected",
  cameras: "binary_sensor.cameras_active",
  calibrating: "binary_sensor.calibrating",
  cameraProblem: "binary_sensor.camera_problem",
  hand: "binary_sensor.hand_detected",
  takeoutPartial: "binary_sensor.takeout_partial",
  detection: "switch.detection",
  start: "button.start",
  stop: "button.stop",
  reset: "button.reset",
  calibrate: "button.calibrate",
};

const KEYS = {
  ...BOARD_KEYS,
  visit: "sensor.local_visit_score",
  lastThrow: "sensor.last_throw",
  darts: "sensor.training_darts",
  points: "sensor.training_points",
  average: "sensor.training_average",
  triples: "sensor.training_triples",
  bulls: "sensor.training_bulls",
  max: "sensor.training_scores_180",
  started: "sensor.training_started",
};

const TRAINING_KEYS = {
  darts: "sensor.training_darts",
  points: "sensor.training_points",
  average: "sensor.training_average",
  visits: "sensor.training_visits",
  highest: "sensor.training_highest_visit",
  scores_100: "sensor.training_scores_100",
  scores_140: "sensor.training_scores_140",
  max: "sensor.training_scores_180",
  triples: "sensor.training_triples",
  doubles: "sensor.training_doubles",
  bulls: "sensor.training_bulls",
  misses: "sensor.training_misses",
  started: "sensor.training_started",
  events: "event.board_events",
  newSession: "button.reset_training",
};

const STATUS_KEYS = {
  ...BOARD_KEYS,
  restart: "button.restart",
  cloudLink: "binary_sensor.cloud_link",
  upstream: "switch.upstream",
  cpu: "sensor.cpu_usage",
  memory: "sensor.memory_usage",
  fps: "sensor.detection_fps",
  update: "update.board_software",
};

// Per-camera entities carry their camera number as an attribute.
const CAMERA_KEYS = {
  problem: "binary_sensor.individual_camera_problem",
  fps: "sensor.camera_fps",
  calibrate: "button.calibrate_camera",
  image: "camera.board_camera",
};

const language = (hass) =>
  String(hass?.locale?.language || hass?.language || "en").startsWith("de") ? "de" : "en";

const translate = (hass, key) => TEXT[language(hass)][key] ?? TEXT.en[key] ?? key;

const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`);

const usable = (state) => state && !["unknown", "unavailable"].includes(state.state);

// Entity lookup ------------------------------------------------------------

// hass.entities is replaced whenever the registry changes, so it keys a cache
// that spares every card from scanning all entities on each state update.
const deviceCache = new WeakMap();
const indexCache = new WeakMap();

function autodartsDevices(hass) {
  const entities = hass?.entities || {};
  let devices = deviceCache.get(entities);
  if (!devices) {
    const found = new Set();
    for (const entity of Object.values(entities)) {
      if (entity.platform === "autodarts" && entity.device_id) found.add(entity.device_id);
    }
    devices = [...found];
    deviceCache.set(entities, devices);
  }
  return devices;
}

function entityIndex(hass, deviceId) {
  const entities = hass?.entities || {};
  let byDevice = indexCache.get(entities);
  if (!byDevice) {
    byDevice = new Map();
    indexCache.set(entities, byDevice);
  }
  let index = byDevice.get(deviceId);
  if (!index) {
    index = {};
    for (const entity of Object.values(entities)) {
      if (entity.platform !== "autodarts" || entity.device_id !== deviceId) continue;
      if (!entity.translation_key) continue;
      const key = `${entity.entity_id.split(".")[0]}.${entity.translation_key}`;
      (index[key] ||= []).push(entity.entity_id);
    }
    byDevice.set(deviceId, index);
  }
  return index;
}

function resolveKeys(index, keys) {
  return Object.fromEntries(Object.entries(keys).map(([name, key]) => [name, index[key]?.[0]]));
}

function cameraEntities(hass, index) {
  const cameras = new Map();
  for (const [role, key] of Object.entries(CAMERA_KEYS)) {
    for (const id of index[key] || []) {
      const number = Number(hass.states[id]?.attributes?.camera);
      if (!Number.isInteger(number) || number < 1) continue;
      if (!cameras.has(number)) cameras.set(number, { number });
      cameras.get(number)[role] ??= id;
    }
  }
  return [...cameras.values()].sort((a, b) => a.number - b.number);
}

// Geometry ----------------------------------------------------------------

function point(radius, degrees) {
  const angle = (degrees * Math.PI) / 180;
  return [radius * Math.sin(angle), -radius * Math.cos(angle)];
}

const fmt = (value) => Number(value.toFixed(2));

function sectorPath(inner, outer, start, end) {
  const [x1, y1] = point(outer, start);
  const [x2, y2] = point(outer, end);
  const [x3, y3] = point(inner, end);
  const [x4, y4] = point(inner, start);
  return (
    `M${fmt(x1)} ${fmt(y1)}A${outer} ${outer} 0 0 1 ${fmt(x2)} ${fmt(y2)}` +
    `L${fmt(x3)} ${fmt(y3)}A${inner} ${inner} 0 0 0 ${fmt(x4)} ${fmt(y4)}Z`
  );
}

function ringPath(inner, outer) {
  const circle = (r) => `M${r} 0A${r} ${r} 0 1 0 ${-r} 0A${r} ${r} 0 1 0 ${r} 0Z`;
  return inner > 0 ? circle(outer) + circle(inner) : circle(outer);
}

function bedPath(id) {
  if (id === "Bull") return ringPath(0, R.bull);
  if (id === "25") return ringPath(R.bull, R.outerBull);
  if (id === "Miss") return ringPath(R.doubleOut, R.board);
  const match = /^(SI|SO|T|D|M)(\d+)$/.exec(id);
  const index = match ? NUMBERS.indexOf(Number(match[2])) : -1;
  if (index < 0) return null;
  const [inner, outer] = BEDS[match[1]];
  return sectorPath(inner, outer, index * 18 - 9, index * 18 + 9);
}

function sectorAt(dart) {
  if (!Number.isFinite(dart.x) || !Number.isFinite(dart.y)) return null;
  const degrees = (Math.atan2(dart.x, dart.y) * 180) / Math.PI;
  return NUMBERS[((Math.round(degrees / 18) % 20) + 20) % 20];
}

function beds(dart) {
  const { number, multiplier, bed } = dart;
  if (number === 25) return [multiplier >= 2 ? "Bull" : "25"];
  if (multiplier === 0 || bed === "Outside") {
    const sector = NUMBERS.includes(number) ? number : sectorAt(dart);
    return [sector ? `M${sector}` : "Miss"];
  }
  if (!NUMBERS.includes(number)) return [];
  if (bed === "Triple" || multiplier === 3) return [`T${number}`];
  if (bed === "Double" || multiplier === 2) return [`D${number}`];
  if (bed === "SingleInner") return [`SI${number}`];
  if (bed === "SingleOuter") return [`SO${number}`];
  if (Number.isFinite(dart.x) && Number.isFinite(dart.y)) {
    return [Math.hypot(dart.x, dart.y) * NORM < R.trebleIn ? `SI${number}` : `SO${number}`];
  }
  return [`SI${number}`, `SO${number}`];
}

function kind(dart) {
  if (dart.number === 25) return dart.multiplier >= 2 ? "bull" : "outer-bull";
  if (dart.multiplier === 0 || dart.bed === "Outside") return "miss";
  return { 3: "triple", 2: "double" }[dart.multiplier] || "single";
}

function label(hass, dart) {
  if (dart.number === 25) return dart.multiplier >= 2 ? "Bull" : "25";
  if (kind(dart) === "miss") return translate(hass, "miss");
  return `${{ 3: "T", 2: "D" }[dart.multiplier] || "S"}${dart.number}`;
}

function parseSegment(name) {
  // Fallback for integrations without dart details: the last segment name only.
  const text = String(name || "").trim();
  if (/^(bull|db|d25)$/i.test(text)) return { number: 25, multiplier: 2 };
  if (text === "25" || /^s25$/i.test(text)) return { number: 25, multiplier: 1 };
  const match = /^([SDTM])(\d{1,2})$/i.exec(text);
  if (!match) return null;
  const multiplier = { S: 1, D: 2, T: 3, M: 0 }[match[1].toUpperCase()];
  return { number: Number(match[2]), multiplier };
}

function boardSvg(style) {
  const colors = STYLES[style] || STYLES.classic;
  const wire = colors.wire === "none" ? "" : ` stroke="${colors.wire}" stroke-width="0.7"`;
  const parts = [`<circle r="${R.board}" fill="${colors.surround}"/>`];
  NUMBERS.forEach((number, index) => {
    const even = index % 2 === 0;
    const single = even ? colors.black : colors.white;
    const ring = even ? colors.red : colors.green;
    const start = index * 18 - 9;
    for (const [bed, fill] of [["SI", single], ["T", ring], ["SO", single], ["D", ring]]) {
      const [inner, outer] = BEDS[bed];
      parts.push(`<path d="${sectorPath(inner, outer, start, start + 18)}" fill="${fill}"${wire}/>`);
    }
  });
  parts.push(`<circle r="${R.outerBull}" fill="${colors.green}"${wire}/>`);
  parts.push(`<circle r="${R.bull}" fill="${colors.red}"${wire}/>`);
  if (colors.wire !== "none") {
    parts.push(
      `<circle r="${R.doubleOut}" fill="none" stroke="${colors.wire}" stroke-width="1.2"/>`
    );
  }
  return parts.join("");
}

function numbersSvg(style) {
  // Drawn above highlights, so a hit outside the double ring keeps its number readable.
  const color = (STYLES[style] || STYLES.classic).numbers;
  return NUMBERS.map((number, index) => {
    const [x, y] = point(R.numbers, index * 18);
    return `<text x="${fmt(x)}" y="${fmt(y)}" fill="${color}" class="number">${number}</text>`;
  }).join("");
}

// Training analytics ------------------------------------------------------

// Hits are counted per bed as S20, D16, T19, 25, BULL or MISS by the integration.
function hitBeds(key) {
  const text = String(key);
  if (text === "BULL") return ["Bull"];
  if (text === "25") return ["25"];
  const match = /^([SDT])(\d{1,2})$/.exec(text);
  if (!match || !NUMBERS.includes(Number(match[2]))) return [];
  const number = match[2];
  return { S: [`SI${number}`, `SO${number}`], D: [`D${number}`], T: [`T${number}`] }[match[1]];
}

function validHits(hits) {
  return Object.entries(hits && typeof hits === "object" ? hits : {})
    .map(([key, count]) => [key, Number(count)])
    .filter(([key, count]) => Number.isInteger(count) && count > 0 && (key === "MISS" || hitBeds(key).length));
}

function heatLevels(hits, mode = "beds") {
  const levels = new Map();
  const add = (bed, count) => levels.set(bed, (levels.get(bed) || 0) + count);
  for (const [key, count] of validHits(hits)) {
    const beds = hitBeds(key);
    if (mode !== "numbers") {
      beds.forEach((bed) => add(bed, count));
      continue;
    }
    // Numbers mode sums singles, doubles and triples of a sector.
    const number = /^[SDT](\d{1,2})$/.exec(key)?.[1];
    const group = number ? ["SI", "T", "SO", "D"].map((bed) => `${bed}${number}`) : beds.length ? ["Bull", "25"] : [];
    group.forEach((bed) => add(bed, count));
  }
  return levels;
}

function heatRatio(count, max) {
  return max > 1 ? Math.min(1, Math.max(0, (count - 1) / (max - 1))) : 1;
}

function heatColor(ratio) {
  // Thermal scale from blue (rarely hit) through green and yellow to red (most hit).
  const value = Math.min(1, Math.max(0, Number(ratio) || 0));
  return `hsl(${Math.round(220 * (1 - value))}, 90%, 55%)`;
}

function topHits(hits, limit = 5) {
  return validHits(hits)
    .filter(([key]) => key !== "MISS")
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, limit);
}

function hitLabel(hass, key) {
  if (key === "BULL") return "Bull";
  if (key === "MISS") return translate(hass, "miss");
  return key;
}

function visitBucket(score) {
  if (score >= 180) return "max";
  if (score >= 140) return "high";
  if (score >= 100) return "ton";
  if (score >= 60) return "good";
  return "low";
}

// Rows of history/history_during_period for the board events entity.
function visitsFromHistory(rows, since = 0) {
  const visits = [];
  for (const row of Array.isArray(rows) ? rows : []) {
    const attributes = row?.a || row?.attributes;
    if (attributes?.event_type !== "visit_completed") continue;
    const time = Date.parse(row.s ?? row.state);
    const score = Number(attributes.score);
    if (!Number.isFinite(time) || !Number.isFinite(score) || time < since) continue;
    visits.push({
      time,
      score,
      darts: Number(attributes.darts) || 0,
      segments: Array.isArray(attributes.segments) ? attributes.segments.map(String) : [],
    });
  }
  return visits;
}

// Board status shared by the live and status cards.
function boardStatus(stateOf) {
  const on = (name) => stateOf(name)?.state === "on";
  const connected = stateOf("connected");
  const detection = stateOf("detection")?.state;
  const status = String(stateOf("status")?.state || "").toLowerCase();
  if (!connected || connected.state !== "on") return ["offline", "status_offline"];
  if (on("calibrating") || status === "calibrating") return ["calibrating", "status_calibrating"];
  if (on("cameraProblem")) return ["problem", "status_problem"];
  if (status === "starting") return ["stopped", "status_starting"];
  if (status === "stopping") return ["stopped", "status_stopping"];
  if (detection === "off" || status === "stopped") return ["stopped", "status_stopped"];
  if (status.includes("takeout") || on("takeoutPartial")) return ["takeout", "status_takeout"];
  if (on("hand")) return ["takeout", "status_hand"];
  if (Number(stateOf("numThrows")?.state) >= 3) return ["takeout", "status_full"];
  return ["ready", "status_ready"];
}

// Styles ----------------------------------------------------------------------

const BASE_CSS = `
  :host { display: block; }
  ha-card { overflow: hidden; height: 100%; }
  .root { container-type: inline-size; height: 100%; }
  header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .title {
    font-size: 16px; font-weight: 600; color: var(--primary-text-color);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .pill {
    display: inline-flex; align-items: center; gap: 8px; flex-shrink: 0;
    padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 600;
    color: var(--ad-status); background: color-mix(in srgb, var(--ad-status) 14%, transparent);
    transition: color .4s, background .4s;
  }
  .pill::before {
    content: ""; width: 8px; height: 8px; border-radius: 50%;
    background: var(--ad-status); box-shadow: 0 0 8px var(--ad-status);
  }
  .section-label {
    font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
    color: var(--ad-accent);
  }
  .muted { font-size: 11px; color: var(--secondary-text-color); }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip {
    display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 999px;
    font: inherit; font-size: 12px; color: var(--secondary-text-color); cursor: pointer;
    border: 1px solid var(--divider-color, rgba(127,127,127,.25)); background: none;
  }
  .chip::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--chip, #9e9e9e); }
  .chip.on { --chip: ${STATUS_COLORS.ready}; }
  .chip.off { --chip: #9e9e9e; }
  .chip.alert { --chip: ${STATUS_COLORS.problem}; color: ${STATUS_COLORS.problem}; }
  .controls { display: flex; flex-wrap: wrap; gap: 8px; }
  .controls button, button.action {
    flex: 1 1 auto; min-height: 40px; padding: 0 14px; border-radius: 12px; cursor: pointer;
    font: inherit; font-size: 13px; font-weight: 600; color: var(--primary-text-color);
    border: 1px solid var(--divider-color, rgba(127,127,127,.3)); background: none;
    transition: background .2s, border-color .2s, color .2s;
  }
  :is(.controls button, button.action):hover { background: color-mix(in srgb, var(--primary-text-color) 6%, transparent); }
  :is(.controls button, button.action).primary {
    color: var(--text-primary-color, #fff); background: var(--ad-accent); border-color: var(--ad-accent);
  }
  :is(.controls button, button.action).primary.stop { background: none; color: var(--ad-accent); }
  :is(.controls button, button.action).confirm {
    color: #fff; background: ${STATUS_COLORS.problem}; border-color: ${STATUS_COLORS.problem};
  }
  :is(.controls button, button.action):disabled { opacity: .45; cursor: default; }
  :is(button, [tabindex]):focus-visible { outline: 2px solid var(--ad-accent); outline-offset: 2px; }
  svg { display: block; width: 100%; height: 100%; overflow: visible; }
  .number {
    font: 700 22px/1 Roboto, Arial, sans-serif; text-anchor: middle; dominant-baseline: central;
    pointer-events: none;
  }
  .message { padding: 18px; color: var(--secondary-text-color); }
`;

const CSS = `${BASE_CSS}
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    grid-template-areas: "header board" "visit board" "session board" "footer board";
    align-content: center;
    column-gap: 24px;
    row-gap: 16px;
    padding: 18px;
    box-sizing: border-box;
    height: 100%;
  }
  .layout.vertical {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas: "header" "visit" "board" "session" "footer";
  }
  .layout.board-only { grid-template-columns: minmax(0, 1fr); grid-template-areas: "header" "board"; }
  .layout.board-only :is(.visit, .session, .footer) { display: none; }
  @container (max-width: 520px) {
    .layout.auto {
      grid-template-columns: minmax(0, 1fr);
      grid-template-areas: "header" "visit" "board" "session" "footer";
    }
  }
  header { grid-area: header; }
  .visit { grid-area: visit; display: flex; flex-direction: column; gap: 12px; min-width: 0; }
  .session { grid-area: session; min-width: 0; }
  .footer { grid-area: footer; display: flex; flex-direction: column; gap: 12px; min-width: 0; }
  .board { grid-area: board; align-self: center; }
  .visit-label {
    font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
    color: var(--ad-accent);
  }
  .score-row { display: flex; align-items: baseline; gap: 10px; margin-top: 2px; }
  .score {
    font-size: clamp(48px, 16cqw, 84px); font-weight: 800; line-height: 1;
    letter-spacing: -0.04em; color: var(--primary-text-color); font-variant-numeric: tabular-nums;
  }
  .score-unit { font-size: 14px; color: var(--secondary-text-color); }
  .progress { margin-left: auto; font-size: 12px; color: var(--secondary-text-color); white-space: nowrap; }
  .slots { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
  .slot {
    position: relative; padding: 10px 8px 9px; border-radius: 14px; text-align: center;
    border: 1px solid var(--divider-color, rgba(127,127,127,.25));
    background: color-mix(in srgb, var(--primary-text-color) 4%, transparent);
    transition: border-color .3s, box-shadow .3s, background .3s;
  }
  .slot.empty { border-style: dashed; background: none; }
  .slot.latest {
    border-color: var(--ad-highlight);
    box-shadow: 0 0 0 1px var(--ad-highlight), 0 0 18px color-mix(in srgb, var(--ad-highlight) 35%, transparent);
  }
  .slot .index { font-size: 11px; color: var(--secondary-text-color); }
  .slot .segment { font-size: 22px; font-weight: 800; margin: 2px 0; color: var(--primary-text-color); }
  .slot .value { font-size: 12px; color: var(--secondary-text-color); font-variant-numeric: tabular-nums; }
  .slot.triple .segment { color: #ef6c57; }
  .slot.double .segment { color: #43b581; }
  .slot.bull .segment, .slot.outer-bull .segment { color: #e5484d; }
  .slot.miss .segment { color: var(--secondary-text-color); }
  .stats { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 6px; margin-top: 8px; }
  .stat { min-width: 0; }
  .stat .value {
    font-size: 18px; font-weight: 700; color: var(--primary-text-color);
    font-variant-numeric: tabular-nums; white-space: nowrap;
  }
  .stat .name {
    font-size: 11px; color: var(--secondary-text-color);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .section-head { display: flex; justify-content: space-between; gap: 8px; }
  .since { font-size: 11px; color: var(--secondary-text-color); }
  .board { display: flex; justify-content: center; }
  .board-frame {
    width: clamp(180px, 42cqw, 380px); aspect-ratio: 1; border-radius: 50%;
    box-shadow: 0 0 42px 4px color-mix(in srgb, var(--ad-status) 55%, transparent);
    transition: box-shadow .5s;
  }
  .board-frame svg { cursor: pointer; border-radius: 50%; }
  .layout.vertical .board-frame, .layout.board-only .board-frame { width: min(100%, 420px); }
  @container (max-width: 520px) {
    .layout.auto .board-frame { width: min(100%, 360px); }
    .stats { grid-template-columns: repeat(3, minmax(0, 1fr)); row-gap: 12px; }
  }
  .hit { fill: var(--ad-highlight); opacity: .88; pointer-events: none; }
  .blink .hit { animation: ad-blink .8s ease-in-out infinite alternate; }
  .dart .pin { fill: #3182ce; stroke: #fff; stroke-width: 2; }
  .dart text { font: 700 11px/1 Roboto, Arial, sans-serif; fill: #fff; text-anchor: middle; dominant-baseline: central; }
  .dart.latest .halo { fill: none; stroke: var(--ad-highlight); stroke-width: 2; animation: ad-pulse 1.6s ease-out infinite; transform-box: fill-box; transform-origin: center; }
  @keyframes ad-blink { from { opacity: .18; } to { opacity: .95; } }
  @keyframes ad-pulse { from { opacity: .9; transform: scale(.7); } to { opacity: 0; transform: scale(1.8); } }
  @media (prefers-reduced-motion: reduce) {
    .blink .hit, .dart.latest .halo { animation: none; }
  }
`;

const TRAINING_CSS = `${BASE_CSS}
  .training { display: flex; flex-direction: column; gap: 18px; padding: 18px; box-sizing: border-box; }
  .hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
  .average {
    font-size: clamp(44px, 14cqw, 72px); font-weight: 800; line-height: 1; letter-spacing: -0.04em;
    color: var(--primary-text-color); font-variant-numeric: tabular-nums;
  }
  .average-label { font-size: 12px; color: var(--secondary-text-color); margin-top: 4px; }
  .totals { display: flex; gap: 18px; }
  .total .value { font-size: 22px; font-weight: 700; color: var(--primary-text-color); font-variant-numeric: tabular-nums; text-align: right; }
  .total .name { font-size: 11px; color: var(--secondary-text-color); text-align: right; }
  .body { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 20px; align-items: start; }
  .body.single { grid-template-columns: minmax(0, 1fr); }
  @container (max-width: 560px) { .body { grid-template-columns: minmax(0, 1fr); } }
  .heat { display: flex; flex-direction: column; align-items: center; gap: 10px; }
  .heat-frame { width: min(100%, 380px); aspect-ratio: 1; }
  .heat-bed { stroke: rgba(0,0,0,.25); stroke-width: .6; }
  .legend { width: min(100%, 320px); display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 8px; }
  .legend-bar { height: 8px; border-radius: 999px; }
  .side { display: flex; flex-direction: column; gap: 18px; min-width: 0; }
  .tiles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
  .tile {
    min-width: 0; padding: 10px 8px; border-radius: 14px; text-align: center;
    background: color-mix(in srgb, var(--primary-text-color) 5%, transparent);
  }
  .tile .value { font-size: 20px; font-weight: 800; color: var(--primary-text-color); font-variant-numeric: tabular-nums; white-space: nowrap; }
  .tile .name { font-size: 11px; color: var(--secondary-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .tile.hot .value { color: ${VISIT_COLORS.max}; }
  @container (max-width: 380px) { .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
  .top { display: flex; flex-direction: column; gap: 6px; }
  .top-row { display: grid; grid-template-columns: 3.2em 1fr auto; align-items: center; gap: 10px; font-size: 13px; }
  .top-row .key { font-weight: 800; color: var(--primary-text-color); }
  .top-row .bar { height: 8px; border-radius: 999px; background: color-mix(in srgb, var(--primary-text-color) 8%, transparent); overflow: hidden; }
  .top-row .fill { height: 100%; border-radius: inherit; }
  .top-row .count { color: var(--secondary-text-color); font-variant-numeric: tabular-nums; white-space: nowrap; }
  .history-chart { position: relative; height: 104px; display: flex; align-items: stretch; gap: 4px; margin-top: 8px; }
  .visit-bar {
    flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; justify-content: flex-end; align-items: center;
  }
  .visit-bar .fill {
    width: 100%; max-width: 30px; min-height: 3px; border-radius: 5px 5px 2px 2px;
    height: calc((100% - 16px) * var(--height));
  }
  .visit-bar .label {
    font-size: 10px; font-weight: 700; line-height: 14px; margin-bottom: 2px;
    color: var(--secondary-text-color); font-variant-numeric: tabular-nums; white-space: nowrap;
  }
  .visit-bar.empty .fill { background: color-mix(in srgb, var(--primary-text-color) 7%, transparent); height: 3px; }
  .average-line {
    position: absolute; left: 0; right: 0; bottom: calc((100% - 16px) * var(--height));
    border-top: 1px dashed var(--secondary-text-color); opacity: .55; pointer-events: none;
  }
  .footer-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .footer-row button.action { flex: 0 0 auto; }
  .empty-hint { font-size: 13px; color: var(--secondary-text-color); text-align: center; padding: 8px 0; }
`;

const STATUS_CSS = `${BASE_CSS}
  .status-card { display: flex; flex-direction: column; gap: 16px; padding: 18px; box-sizing: border-box; }
  .detection {
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    padding: 12px 14px; border-radius: 16px;
    background: color-mix(in srgb, var(--ad-status) 10%, transparent);
  }
  .detection .name { font-weight: 700; color: var(--primary-text-color); }
  .detection .state { font-size: 12px; color: var(--secondary-text-color); }
  .toggle {
    position: relative; width: 52px; height: 30px; flex-shrink: 0; border-radius: 999px; cursor: pointer;
    border: none; background: color-mix(in srgb, var(--primary-text-color) 20%, transparent); transition: background .2s;
  }
  .toggle::after {
    content: ""; position: absolute; top: 3px; left: 3px; width: 24px; height: 24px; border-radius: 50%;
    background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.3); transition: transform .2s;
  }
  .toggle[aria-checked="true"] { background: var(--ad-accent); }
  .toggle[aria-checked="true"]::after { transform: translateX(22px); }
  .toggle:disabled { opacity: .45; cursor: default; }
  .info { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; }
  .info-tile {
    display: flex; flex-direction: column; gap: 6px; min-width: 0; padding: 12px; border-radius: 14px;
    background: color-mix(in srgb, var(--primary-text-color) 5%, transparent);
  }
  .info-tile .value { font-size: 15px; font-weight: 700; color: var(--primary-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .info-tile .badge {
    align-self: flex-start; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; cursor: pointer;
    border: none; font-family: inherit;
    color: ${STATUS_COLORS.takeout}; background: color-mix(in srgb, ${STATUS_COLORS.takeout} 16%, transparent);
  }
  .info-tile .badge.ok { color: ${STATUS_COLORS.ready}; background: color-mix(in srgb, ${STATUS_COLORS.ready} 14%, transparent); cursor: default; }
  .metrics { display: flex; gap: 14px; flex-wrap: wrap; }
  .metric .value { font-size: 15px; font-weight: 700; font-variant-numeric: tabular-nums; }
  .metric .name { font-size: 11px; color: var(--secondary-text-color); }
  .camera-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 8px; }
  .camera {
    display: flex; flex-direction: column; gap: 8px; padding: 12px; border-radius: 14px;
    border: 1px solid var(--divider-color, rgba(127,127,127,.25));
  }
  .camera.problem { border-color: ${STATUS_COLORS.problem}; background: color-mix(in srgb, ${STATUS_COLORS.problem} 8%, transparent); }
  .camera-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .camera-name { font-weight: 700; color: var(--primary-text-color); background: none; border: none; padding: 0; font: inherit; font-weight: 700; cursor: pointer; }
  .dot { width: 9px; height: 9px; border-radius: 50%; background: ${STATUS_COLORS.ready}; box-shadow: 0 0 6px ${STATUS_COLORS.ready}; }
  .camera.problem .dot { background: ${STATUS_COLORS.problem}; box-shadow: 0 0 6px ${STATUS_COLORS.problem}; }
  .camera .fps { font-size: 12px; color: var(--secondary-text-color); font-variant-numeric: tabular-nums; }
  .camera button.action { min-height: 32px; font-size: 12px; }
`;

// Elements ------------------------------------------------------------------

// Elements are created on demand: Home Assistant replaces HTMLElement while it boots.
function createElements(Base) {
  class CardBase extends Base {
    static keys = {};

    static defaults = {};

    static getStubConfig(hass) {
      const [deviceId] = autodartsDevices(hass);
      return deviceId ? { device_id: deviceId } : {};
    }

    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._watchedStates = [];
      this._confirm = null;
    }

    setConfig(config) {
      if (!config || typeof config !== "object") throw new Error("Invalid configuration");
      this._config = { ...this.constructor.defaults, ...config };
      this._built = false;
      this._watchedStates = [];
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      this._render();
    }

    // Home Assistant sets this in the card editor and picker, where taps must not act.
    set preview(value) {
      this._preview = Boolean(value);
    }

    get preview() {
      return Boolean(this._preview);
    }

    disconnectedCallback() {
      clearTimeout(this._confirmTimer);
      this._confirm = null;
    }

    getGridOptions() {
      return { columns: 12, min_columns: 6 };
    }

    _css() {
      return BASE_CSS;
    }

    // Entity ids whose state changes redraw the card.
    _watched() {
      return Object.values(this._ids);
    }

    _render() {
      if (!this._config || !this._hass) return;
      const hass = this._hass;
      const deviceId = this._config.device_id || autodartsDevices(hass)[0];
      // A deleted device must not be mistaken for an unreachable board.
      const known = !this._config.device_id || !hass.devices || hass.devices[deviceId];
      if (!deviceId || !known) {
        this.shadowRoot.innerHTML = `<style>${this._css()}</style><ha-card><div class="message">${escapeHtml(
          translate(hass, "no_board")
        )}</div></ha-card>`;
        this._built = false;
        return;
      }
      this._index = entityIndex(hass, deviceId);
      this._ids = resolveKeys(this._index, this.constructor.keys);
      const states = this._watched().map((id) => (id ? hass.states[id] : undefined));
      const lang = language(hass);
      const rebuild = !this._built || this._language !== lang || this._deviceId !== deviceId;
      if (
        !rebuild &&
        states.length === this._watchedStates.length &&
        states.every((state, index) => state === this._watchedStates[index])
      ) {
        return;
      }
      if (rebuild) {
        this._language = lang;
        this._deviceId = deviceId;
        this._build();
        this._built = true;
      }
      this._watchedStates = states;
      this._update();
    }

    _t(key) {
      return translate(this._hass, key);
    }

    _state(name) {
      const id = this._ids?.[name];
      return id ? this._hass.states[id] : undefined;
    }

    _number(name) {
      const state = this._state(name);
      const value = usable(state) ? Number(state.state) : NaN;
      return Number.isFinite(value) ? value : null;
    }

    _format(value, digits = 0) {
      if (value === null || value === undefined || !Number.isFinite(value)) return "–";
      return new Intl.NumberFormat(this._hass.locale?.language || this._hass.language, {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }).format(value);
    }

    _since() {
      const started = this._state("started");
      const date = usable(started) ? new Date(started.state) : null;
      if (!date || Number.isNaN(date.getTime())) return "";
      return `${this._t("since")} ${new Intl.DateTimeFormat(this._hass.locale?.language || this._hass.language, {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      }).format(date)}`;
    }

    _deviceName() {
      const device = this._hass.devices?.[this._deviceId];
      return this._config.title || device?.name_by_user || device?.name || "Autodarts";
    }

    _call(domain, service, data) {
      // Home Assistant already shows failures as a toast.
      Promise.resolve(this._hass.callService(domain, service, data)).catch(() => {});
    }

    _press(id) {
      if (id) this._call("button", "press", { entity_id: id });
    }

    // Destructive actions need a second tap within a few seconds.
    _confirmed(action) {
      if (this._confirm === action) {
        this._confirm = null;
        clearTimeout(this._confirmTimer);
        return true;
      }
      this._confirm = action;
      clearTimeout(this._confirmTimer);
      this._confirmTimer = setTimeout(() => {
        this._confirm = null;
        this._confirmChanged();
      }, 4000);
      return false;
    }

    _confirmChanged() {}

    _moreInfo(entityId) {
      if (!entityId || this.preview) return;
      this.dispatchEvent(
        new CustomEvent("hass-more-info", { bubbles: true, composed: true, detail: { entityId } })
      );
    }

    // Replace markup only when it changes, so animations and focus survive updates.
    _setHtml(element, html) {
      if (element && element._adHtml !== html) {
        element.innerHTML = html;
        element._adHtml = html;
      }
    }
  }

  // Live visit card ------------------------------------------------------------

  class AutodartsCard extends CardBase {
    static keys = KEYS;

    static defaults = DEFAULTS;

    static getConfigElement() {
      return document.createElement(EDITOR_TYPE);
    }

    getCardSize() {
      return this._config?.layout === "vertical" ? 10 : 7;
    }

    _css() {
      return CSS;
    }

    _build() {
      const c = this._config;
      const t = (key) => escapeHtml(this._t(key));
      const layout = c.layout === "board" ? "board-only" : c.layout;
      this.shadowRoot.innerHTML = `
        <style>${CSS}</style>
        <ha-card>
          <div class="root">
            <div class="layout ${escapeHtml(layout)}">
              <header>
                <div class="title"></div>
                <div class="pill" role="status"></div>
              </header>
              <div class="visit">
                <div>
                  <div class="visit-label">${t("visit")}</div>
                  <div class="score-row">
                    <span class="score">–</span>
                    <span class="score-unit">${t("points")}</span>
                    <span class="progress"></span>
                  </div>
                </div>
                <div class="slots">
                  ${[1, 2, 3]
                    .map(
                      (n) =>
                        `<div class="slot empty"><div class="index">${t("dart")} ${n}</div>` +
                        `<div class="segment">–</div><div class="value">&nbsp;</div></div>`
                    )
                    .join("")}
                </div>
              </div>
              <div class="board">
                <div class="board-frame">
                  <svg viewBox="-230 -230 460 460" role="button" tabindex="0" aria-label="${t("board_label")}">
                    <g class="face">${boardSvg(c.board_style)}</g>
                    <g class="hits${c.blink ? " blink" : ""}"></g>
                    ${c.show_numbers ? `<g class="numbers">${numbersSvg(c.board_style)}</g>` : ""}
                    <g class="darts"></g>
                  </svg>
                </div>
              </div>
              ${
                c.show_stats
                  ? `<div class="session">
                      <div class="section-head">
                        <span class="section-label">${t("session")}</span>
                        <span class="since"></span>
                      </div>
                      <div class="stats">
                        ${["darts", "average", "triples", "bulls", "max"]
                          .map(
                            (key) =>
                              `<div class="stat" data-stat="${key}"><div class="value">–</div>` +
                              `<div class="name">${t(key)}</div></div>`
                          )
                          .join("")}
                      </div>
                    </div>`
                  : ""
              }
              ${
                c.show_connection || c.show_controls
                  ? `<div class="footer">
                      ${c.show_connection ? `<div class="chips"></div>` : ""}
                      ${
                        c.show_controls
                          ? `<div class="controls">
                              <button class="primary" data-action="toggle"></button>
                              <button data-action="reset">${t("reset")}</button>
                              <button data-action="calibrate">${t("calibrate")}</button>
                            </div>`
                          : ""
                      }
                    </div>`
                  : ""
              }
            </div>
          </div>
        </ha-card>`;
      const root = this.shadowRoot;
      this._el = {
        title: root.querySelector(".title"),
        pill: root.querySelector(".pill"),
        score: root.querySelector(".score"),
        progress: root.querySelector(".progress"),
        slots: [...root.querySelectorAll(".slot")],
        since: root.querySelector(".since"),
        stats: Object.fromEntries(
          [...root.querySelectorAll(".stat")].map((el) => [el.dataset.stat, el.querySelector(".value")])
        ),
        chips: root.querySelector(".chips"),
        controls: root.querySelector(".controls"),
        hits: root.querySelector(".hits"),
        darts: root.querySelector(".darts"),
        svg: root.querySelector("svg"),
      };
      this._el.controls?.addEventListener("click", (event) => this._onControl(event));
      this._el.chips?.addEventListener("click", (event) => {
        const id = event.target.closest(".chip")?.dataset.entity;
        if (id) this._moreInfo(id);
      });
      this._el.svg.addEventListener("click", () => this._moreInfo(this._ids.visit));
      this._el.svg.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        this._moreInfo(this._ids.visit);
      });
    }

    _darts() {
      const visit = this._state("visit");
      const throws = visit?.attributes?.throws;
      if (Array.isArray(throws)) {
        return throws.filter(
          (dart) => dart && Number.isInteger(dart.number) && Number.isInteger(dart.multiplier)
        );
      }
      // Older integration versions only report the last segment.
      const last = this._state("lastThrow");
      const count = Number(this._state("numThrows")?.state);
      const parsed = usable(last) ? parseSegment(last.state) : null;
      if (!parsed || !(count > 0)) return [];
      return [...Array(Math.min(count, 3) - 1).fill(null), parsed];
    }

    _status() {
      return boardStatus((name) => this._state(name));
    }

    _update() {
      const hass = this._hass;
      const c = this._config;
      const el = this._el;
      const t = (key) => this._t(key);
      el.title.textContent = this._deviceName();

      const [status, statusText] = this._status();
      this.style.setProperty("--ad-status", STATUS_COLORS[status]);
      this.style.setProperty("--ad-accent", c.accent_color || "var(--primary-color)");
      this.style.setProperty("--ad-highlight", c.highlight_color || "#ffd60a");
      el.pill.textContent = t(statusText);

      const darts = this._darts();
      const known = darts.filter(Boolean);
      const visit = this._state("visit");
      const total = usable(visit)
        ? visit.state
        : known.reduce((sum, dart) => sum + dart.number * dart.multiplier, 0);
      el.score.textContent = darts.length || usable(visit) ? total : "–";
      el.progress.textContent = darts.length ? `${t("dart")} ${darts.length} ${t("of")} 3` : "";

      el.slots.forEach((slot, index) => {
        const dart = darts[index];
        const [segment, value] = [slot.querySelector(".segment"), slot.querySelector(".value")];
        if (!dart) {
          slot.className = `slot ${index < darts.length ? "unknown" : "empty"}`;
          segment.textContent = index < darts.length ? "?" : "–";
          value.innerHTML = "&nbsp;";
          return;
        }
        slot.className = `slot ${kind(dart)}${index === darts.length - 1 ? " latest" : ""}`;
        segment.textContent = label(hass, dart);
        value.textContent = `${dart.number * dart.multiplier} ${t("points")}`;
      });

      this._updateBoard(darts);
      this._updateStats();
      this._updateChips();
      this._updateControls(status);
    }

    _updateBoard(darts) {
      const c = this._config;
      const latest = darts.length - 1;
      const highlighted =
        c.highlight === "none"
          ? []
          : darts
              .map((dart, index) => (dart && (c.highlight !== "last" || index === latest) ? dart : null))
              .filter(Boolean);
      const paths = new Set(highlighted.flatMap(beds));
      this._setHtml(
        this._el.hits,
        [...paths]
          .map((id) => bedPath(id))
          .filter(Boolean)
          .map((d) => `<path class="hit" d="${d}"/>`)
          .join("")
      );

      this._setHtml(
        this._el.darts,
        c.show_markers
          ? darts
              .map((dart, index) => {
                if (!dart || !Number.isFinite(dart.x) || !Number.isFinite(dart.y)) return "";
                const radius = Math.hypot(dart.x, dart.y) * NORM;
                const scale = radius > R.board - 4 ? (R.board - 4) / radius : 1;
                const x = fmt(dart.x * NORM * scale);
                const y = fmt(-dart.y * NORM * scale);
                return (
                  `<g class="dart${index === latest ? " latest" : ""}" transform="translate(${x} ${y})">` +
                  `<circle class="halo" r="11"/><circle class="pin" r="9.5"/><text>${index + 1}</text></g>`
                );
              })
              .join("")
          : ""
      );
      const summary = darts
        .filter(Boolean)
        .map((dart) => label(this._hass, dart))
        .join(", ");
      this._el.svg.setAttribute(
        "aria-label",
        summary ? `${this._t("board_label")}: ${summary}` : this._t("board_label")
      );
    }

    _updateStats() {
      const stats = this._el.stats;
      if (!stats.darts) return;
      const darts = this._number("darts");
      const points = this._number("points");
      // Older integration versions have no average sensor.
      const average = this._ids.average
        ? this._number("average")
        : darts > 0 && points !== null
          ? (points / darts) * 3
          : null;
      stats.darts.textContent = this._format(darts);
      stats.average.textContent = this._format(average, 1);
      stats.triples.textContent = this._format(this._number("triples"));
      stats.bulls.textContent = this._format(this._number("bulls"));
      stats.max.textContent = this._format(this._number("max"));
      this._el.since.textContent = this._since();
    }

    _updateChips() {
      if (!this._el.chips) return;
      const t = (key) => escapeHtml(this._t(key));
      const chip = (name, text, alert = false) => {
        const id = this._ids[name];
        if (!id) return "";
        const state = this._hass.states[id]?.state;
        const cls = alert ? "alert" : state === "on" ? "on" : "off";
        return `<button class="chip ${cls}" data-entity="${escapeHtml(id)}">${text}</button>`;
      };
      const problem = this._state("cameraProblem")?.state === "on";
      this._setHtml(
        this._el.chips,
        [
          chip("connected", t("board")),
          chip("realtime", t("realtime")),
          problem ? chip("cameraProblem", t("camera_problem"), true) : chip("cameras", t("cameras")),
        ].join("")
      );
    }

    _updateControls(status) {
      const controls = this._el.controls;
      if (!controls) return;
      const running = this._state("detection")?.state === "on";
      const toggle = controls.querySelector('[data-action="toggle"]');
      toggle.textContent = this._t(running ? "stop" : "start");
      toggle.classList.toggle("stop", running);
      toggle.disabled = status === "offline" || !(this._ids.detection || this._ids.start);
      for (const action of ["reset", "calibrate"]) {
        const button = controls.querySelector(`[data-action="${action}"]`);
        const confirming = this._confirm === action;
        button.textContent = this._t(confirming ? "confirm" : action);
        button.classList.toggle("confirm", confirming);
        button.disabled = status === "offline" || !this._ids[action];
      }
    }

    _confirmChanged() {
      if (this._el) this._updateControls(this._status()[0]);
    }

    _onControl(event) {
      const action = event.target.closest("button")?.dataset.action;
      if (!action || this.preview) return;
      if (action === "toggle") {
        const running = this._state("detection")?.state === "on";
        if (this._ids.detection) {
          this._call("switch", running ? "turn_off" : "turn_on", { entity_id: this._ids.detection });
        } else {
          this._press(this._ids[running ? "stop" : "start"]);
        }
        return;
      }
      // Reset and calibration discard detected darts, so they need a second tap.
      if (this._confirmed(action)) this._press(this._ids[action]);
      this._confirmChanged();
    }
  }

  // Training card ---------------------------------------------------------------

  class AutodartsTrainingCard extends CardBase {
    static keys = TRAINING_KEYS;

    static defaults = TRAINING_DEFAULTS;

    static getConfigElement() {
      return document.createElement(TRAINING_EDITOR_TYPE);
    }

    constructor() {
      super();
      this._visits = [];
      this._seen = new Set();
    }

    getCardSize() {
      return 9;
    }

    _css() {
      return TRAINING_CSS;
    }

    _build() {
      const c = this._config;
      const t = (key) => escapeHtml(this._t(key));
      const side = c.show_stats || c.show_top;
      const tiles = [
        ["highest", "highest"],
        ["scores_100", "scores_100"],
        ["scores_140", "scores_140"],
        ["max", "max"],
        ["triple_rate", "triple_rate"],
        ["doubles", "doubles"],
        ["bulls", "bulls"],
        ["misses", "misses"],
      ];
      this.shadowRoot.innerHTML = `
        <style>${TRAINING_CSS}</style>
        <ha-card>
          <div class="root">
            <div class="training">
              <header>
                <div class="title"></div>
                <div class="muted since"></div>
              </header>
              <div class="hero">
                <div>
                  <div class="average">–</div>
                  <div class="average-label">${t("average_long")}</div>
                </div>
                <div class="totals">
                  <div class="total"><div class="value" data-total="darts">–</div><div class="name">${t("darts")}</div></div>
                  <div class="total"><div class="value" data-total="visits">–</div><div class="name">${t("visits")}</div></div>
                </div>
              </div>
              <div class="empty-hint" hidden>${t("no_darts")}</div>
              ${
                c.show_heatmap || side
                  ? `<div class="body${c.show_heatmap && side ? "" : " single"}">
                      ${
                        c.show_heatmap
                          ? `<div class="heat">
                              <div class="section-label">${t("heatmap")}</div>
                              <div class="heat-frame">
                                <svg viewBox="-230 -230 460 460" role="img" aria-label="${t("heatmap_label")}">
                                  <g class="face">${boardSvg(c.board_style)}</g>
                                  <g class="heat-layer"></g>
                                  <g class="numbers">${numbersSvg(c.board_style)}</g>
                                </svg>
                              </div>
                              <div class="legend">
                                <span class="muted">1</span>
                                <div class="legend-bar" style="background: linear-gradient(90deg, ${[0, 0.25, 0.5, 0.75, 1]
                                  .map(heatColor)
                                  .join(", ")})"></div>
                                <span class="muted legend-max">–</span>
                              </div>
                            </div>`
                          : ""
                      }
                      ${
                        side
                          ? `<div class="side">
                              ${
                                c.show_stats
                                  ? `<div class="tiles">
                                      ${tiles
                                        .map(
                                          ([key, name]) =>
                                            `<div class="tile" data-tile="${key}">` +
                                            `<div class="value">–</div><div class="name">${t(name)}</div></div>`
                                        )
                                        .join("")}
                                    </div>`
                                  : ""
                              }
                              ${
                                c.show_top
                                  ? `<div class="top-section">
                                      <div class="section-label">${t("top")}</div>
                                      <div class="top"></div>
                                    </div>`
                                  : ""
                              }
                            </div>`
                          : ""
                      }
                    </div>`
                  : ""
              }
              ${
                c.show_history
                  ? `<div class="history">
                      <div class="section-label">${t("history")}</div>
                      <div class="history-chart"></div>
                    </div>`
                  : ""
              }
              ${
                c.show_reset
                  ? `<div class="footer-row">
                      <span class="muted"></span>
                      <button class="action" data-action="new_session">${t("new_session")}</button>
                    </div>`
                  : ""
              }
            </div>
          </div>
        </ha-card>`;
      const root = this.shadowRoot;
      this._el = {
        title: root.querySelector(".title"),
        since: root.querySelector(".since"),
        average: root.querySelector(".average"),
        totals: Object.fromEntries([...root.querySelectorAll("[data-total]")].map((el) => [el.dataset.total, el])),
        empty: root.querySelector(".empty-hint"),
        heat: root.querySelector(".heat-layer"),
        legendMax: root.querySelector(".legend-max"),
        tiles: Object.fromEntries(
          [...root.querySelectorAll("[data-tile]")].map((el) => [el.dataset.tile, el.querySelector(".value")])
        ),
        top: root.querySelector(".top"),
        history: root.querySelector(".history-chart"),
        newSession: root.querySelector('[data-action="new_session"]'),
      };
      this._el.newSession?.addEventListener("click", () => {
        if (this.preview) return;
        if (this._confirmed("new_session")) this._press(this._ids.newSession);
        this._confirmChanged();
      });
      root.querySelector(".tiles")?.addEventListener("click", () => this._moreInfo(this._ids.darts));
      this._historyFor = null;
    }

    _confirmChanged() {
      const button = this._el?.newSession;
      if (!button) return;
      const confirming = this._confirm === "new_session";
      button.textContent = this._t(confirming ? "confirm" : "new_session");
      button.classList.toggle("confirm", confirming);
      button.disabled = !this._ids.newSession;
    }

    _update() {
      const c = this._config;
      const el = this._el;
      this.style.setProperty("--ad-accent", c.accent_color || "var(--primary-color)");
      el.title.textContent = c.title || `${this._t("training")} · ${this._deviceName()}`;
      el.since.textContent = this._since();

      const darts = this._number("darts");
      const points = this._number("points");
      const average = this._ids.average
        ? this._number("average")
        : darts > 0 && points !== null
          ? (points / darts) * 3
          : null;
      el.average.textContent = this._format(average, 1);
      el.totals.darts.textContent = this._format(darts);
      el.totals.visits.textContent = this._format(this._number("visits"));
      el.empty.hidden = darts > 0;

      const tiles = el.tiles;
      if (tiles.highest) {
        for (const key of ["highest", "scores_100", "scores_140", "max", "doubles", "bulls", "misses"]) {
          tiles[key].textContent = this._format(this._number(key));
        }
        tiles.max.parentElement.classList.toggle("hot", this._number("max") > 0);
        const triples = this._number("triples");
        tiles.triple_rate.textContent =
          darts > 0 && triples !== null ? `${this._format((triples / darts) * 100, 1)} %` : "–";
      }

      const hits = this._state("darts")?.attributes?.hits;
      this._updateHeat(hits);
      this._updateTop(hits, darts);
      this._updateHistory();
      this._confirmChanged();
    }

    _updateHeat(hits) {
      if (!this._el.heat) return;
      const levels = heatLevels(hits, this._config.mode);
      const max = Math.max(0, ...levels.values());
      const counts = new Map(validHits(hits));
      const total = [...counts.values()].reduce((sum, count) => sum + count, 0);
      const describe = (bed) => {
        // Tooltips name the scoring bed; singles cover both single areas.
        const key = bed === "Bull" ? "BULL" : bed.replace(/^S[IO]/, "S");
        const count = this._config.mode === "numbers" ? levels.get(bed) : counts.get(key) || 0;
        const name = this._config.mode === "numbers" ? (bed === "Bull" || bed === "25" ? "Bull" : bed.replace(/^\D+/, "")) : hitLabel(this._hass, key);
        const share = total ? ` · ${this._format((count / total) * 100, 1)} %` : "";
        return `${name}: ${count} ${this._t("hits")}${share}`;
      };
      const markup = [...levels.entries()]
        .map(([bed, count]) => {
          const path = bedPath(bed);
          if (!path || !max) return "";
          const ratio = heatRatio(count, max);
          return (
            `<path class="heat-bed" d="${path}" fill="${heatColor(ratio)}" fill-opacity="${fmt(0.6 + 0.35 * ratio)}">` +
            `<title>${escapeHtml(describe(bed))}</title></path>`
          );
        })
        .join("");
      this._setHtml(this._el.heat, markup);
      if (this._el.legendMax) this._el.legendMax.textContent = max ? this._format(max) : "–";
    }

    _updateTop(hits, darts) {
      if (!this._el.top) return;
      const top = topHits(hits, 5);
      const most = top[0]?.[1] || 0;
      this._setHtml(
        this._el.top,
        top.length
          ? top
              .map(([key, count]) => {
                const width = most ? count / most : 0;
                const share = darts > 0 ? ` · ${this._format((count / darts) * 100, 0)} %` : "";
                return (
                  `<div class="top-row"><span class="key">${escapeHtml(hitLabel(this._hass, key))}</span>` +
                  `<div class="bar"><div class="fill" style="width:${fmt(width * 100)}%;background:${heatColor(heatRatio(count, most))}"></div></div>` +
                  `<span class="count">${this._format(count)}×${share}</span></div>`
                );
              })
              .join("")
          : `<div class="empty-hint">–</div>`
      );
    }

    _sessionStart() {
      const started = Date.parse(this._state("started")?.state);
      return Number.isFinite(started) ? started : 0;
    }

    _updateHistory() {
      if (!this._el.history) return;
      const since = this._sessionStart();
      const key = `${this._ids.events}|${since}`;
      if (this._historyFor !== key) {
        // A new session or board starts an empty history.
        this._historyFor = key;
        this._visits = [];
        this._seen = new Set();
        this._loadHistory(since, key);
      }
      const event = this._state("events");
      if (event?.attributes?.event_type === "visit_completed") {
        this._addVisits(visitsFromHistory([event], since));
      }
      this._drawHistory();
    }

    async _loadHistory(since, key) {
      const id = this._ids.events;
      if (!id || typeof this._hass.callWS !== "function") return;
      // The recorder keeps ten days by default; older visits are not needed.
      const start = Math.max(since, Date.now() - 7 * 86400000);
      try {
        const result = await this._hass.callWS({
          type: "history/history_during_period",
          start_time: new Date(start).toISOString(),
          entity_ids: [id],
          minimal_response: false,
          no_attributes: false,
          significant_changes_only: false,
        });
        if (this._historyFor !== key) return;
        this._addVisits(visitsFromHistory(result?.[id], since));
        this._drawHistory();
      } catch (error) {
        // Without the recorder, visits of the open dashboard still appear.
      }
    }

    _addVisits(visits) {
      for (const visit of visits) {
        if (this._seen.has(visit.time)) continue;
        this._seen.add(visit.time);
        this._visits.push(visit);
      }
      this._visits.sort((a, b) => a.time - b.time);
      const size = Math.min(60, Math.max(5, Number(this._config.history_size) || 20));
      if (this._visits.length > size) this._visits = this._visits.slice(-size);
    }

    _drawHistory() {
      const chart = this._el.history;
      if (!chart) return;
      const visits = this._visits;
      if (!visits.length) {
        chart.removeAttribute("role");
        chart.removeAttribute("aria-label");
        this._setHtml(chart, `<div class="empty-hint">${escapeHtml(this._t("history_empty"))}</div>`);
        return;
      }
      const size = Math.min(60, Math.max(5, Number(this._config.history_size) || 20));
      const labels = size <= 30;
      const share = (score) => fmt(Math.min(180, Math.max(0, score)) / 180);
      const bars = visits.map((visit) => {
        const tip = `${visit.segments.join(" · ")}${visit.segments.length ? " = " : ""}${visit.score}`;
        return (
          `<div class="visit-bar" title="${escapeHtml(tip)}">` +
          (labels ? `<span class="label">${visit.score}</span>` : "") +
          `<div class="fill" style="--height:${share(visit.score)};background:${VISIT_COLORS[visitBucket(visit.score)]}"></div></div>`
        );
      });
      // Empty slots keep the bar width steady while the session fills the chart.
      for (let index = visits.length; index < size; index += 1) {
        bars.push(`<div class="visit-bar empty"><div class="fill"></div></div>`);
      }
      const average = this._number("average");
      const line =
        average !== null
          ? `<div class="average-line" style="--height:${share(average)}" title="${escapeHtml(
              `${this._t("average_long")}: ${this._format(average, 1)}`
            )}"></div>`
          : "";
      chart.setAttribute("role", "img");
      chart.setAttribute(
        "aria-label",
        `${this._t("history")}: ${visits.map((visit) => visit.score).join(", ")}`
      );
      this._setHtml(chart, line + bars.join(""));
    }
  }

  // Status card -----------------------------------------------------------------

  class AutodartsStatusCard extends CardBase {
    static keys = STATUS_KEYS;

    static defaults = STATUS_DEFAULTS;

    static getConfigElement() {
      return document.createElement(STATUS_EDITOR_TYPE);
    }

    getCardSize() {
      return 7;
    }

    _css() {
      return STATUS_CSS;
    }

    _watched() {
      const cameras = Object.values(CAMERA_KEYS).flatMap((key) => this._index[key] || []);
      return [...Object.values(this._ids), ...cameras];
    }

    _build() {
      const c = this._config;
      const t = (key) => escapeHtml(this._t(key));
      this.shadowRoot.innerHTML = `
        <style>${STATUS_CSS}</style>
        <ha-card>
          <div class="root">
            <div class="status-card">
              <header>
                <div class="title"></div>
                <div class="pill" role="status"></div>
              </header>
              <div class="detection">
                <div>
                  <div class="name">${t("detection")}</div>
                  <div class="state"></div>
                </div>
                <button class="toggle" role="switch" aria-checked="false" aria-label="${t("detection")}"></button>
              </div>
              <div class="info">
                <div class="info-tile board-tile">
                  <span class="section-label">${t("board")}</span>
                  <span class="value version">–</span>
                  <button class="badge update-badge"></button>
                </div>
                ${
                  c.show_connection
                    ? `<div class="info-tile">
                        <span class="section-label">${t("connections")}</span>
                        <div class="chips"></div>
                      </div>`
                    : ""
                }
                ${
                  c.show_system
                    ? `<div class="info-tile system-tile" hidden>
                        <span class="section-label">${t("system")}</span>
                        <div class="metrics"></div>
                      </div>`
                    : ""
                }
              </div>
              ${
                c.show_cameras
                  ? `<div class="cameras-section" hidden>
                      <div class="section-label">${t("cameras")}</div>
                      <div class="camera-grid"></div>
                    </div>`
                  : ""
              }
              ${
                c.show_controls
                  ? `<div class="controls">
                      <button data-action="calibrate">${t("calibrate")}</button>
                      <button data-action="reset">${t("reset")}</button>
                      <button data-action="restart">${t("restart")}</button>
                    </div>`
                  : ""
              }
            </div>
          </div>
        </ha-card>`;
      const root = this.shadowRoot;
      this._el = {
        title: root.querySelector(".title"),
        pill: root.querySelector(".pill"),
        detectionState: root.querySelector(".detection .state"),
        toggle: root.querySelector(".toggle"),
        version: root.querySelector(".version"),
        update: root.querySelector(".update-badge"),
        chips: root.querySelector(".chips"),
        system: root.querySelector(".system-tile"),
        metrics: root.querySelector(".metrics"),
        camerasSection: root.querySelector(".cameras-section"),
        cameras: root.querySelector(".camera-grid"),
        controls: root.querySelector(".controls"),
      };
      this._el.toggle.addEventListener("click", () => this._toggleDetection());
      this._el.update.addEventListener("click", () => this._moreInfo(this._ids.update));
      this._el.chips?.addEventListener("click", (event) => {
        const id = event.target.closest(".chip")?.dataset.entity;
        if (id) this._moreInfo(id);
      });
      this._el.metrics?.addEventListener("click", (event) => {
        const id = event.target.closest("[data-entity]")?.dataset.entity;
        if (id) this._moreInfo(id);
      });
      this._el.cameras?.addEventListener("click", (event) => {
        const target = event.target.closest("[data-entity], [data-calibrate]");
        if (!target) return;
        if (target.dataset.entity) {
          this._moreInfo(target.dataset.entity);
          return;
        }
        if (this.preview) return;
        const action = `camera:${target.dataset.calibrate}`;
        if (this._confirmed(action)) this._press(target.dataset.calibrate);
        this._confirmChanged();
      });
      this._el.controls?.addEventListener("click", (event) => {
        const action = event.target.closest("button")?.dataset.action;
        if (!action || this.preview) return;
        if (this._confirmed(action)) this._press(this._ids[action]);
        this._confirmChanged();
      });
    }

    _toggleDetection() {
      if (this.preview) return;
      const running = this._state("detection")?.state === "on";
      if (this._ids.detection) {
        this._call("switch", running ? "turn_off" : "turn_on", { entity_id: this._ids.detection });
      } else {
        this._press(this._ids[running ? "stop" : "start"]);
      }
    }

    _confirmChanged() {
      if (!this._el) return;
      const [status] = boardStatus((name) => this._state(name));
      this._updateControls(status);
      this._updateCameras(status);
    }

    _update() {
      const c = this._config;
      const el = this._el;
      const t = (key) => this._t(key);
      el.title.textContent = c.title || this._deviceName();
      const [status, statusText] = boardStatus((name) => this._state(name));
      this.style.setProperty("--ad-status", STATUS_COLORS[status]);
      this.style.setProperty("--ad-accent", c.accent_color || "var(--primary-color)");
      el.pill.textContent = t(statusText);

      const running = this._state("detection")?.state === "on";
      el.toggle.setAttribute("aria-checked", String(running));
      el.toggle.disabled = status === "offline" || !(this._ids.detection || this._ids.start);
      el.detectionState.textContent = t(statusText);

      const device = this._hass.devices?.[this._deviceId];
      el.version.textContent = device?.sw_version ? `${t("version")} ${device.sw_version}` : "–";
      const update = this._state("update");
      if (update?.state === "on") {
        el.update.hidden = false;
        el.update.classList.remove("ok");
        el.update.textContent = `${t("update_available")} ${update.attributes?.latest_version ?? ""}`.trim();
        el.update.disabled = false;
      } else if (update?.state === "off") {
        el.update.hidden = false;
        el.update.classList.add("ok");
        el.update.textContent = t("up_to_date");
        el.update.disabled = true;
      } else {
        el.update.hidden = true;
      }

      this._updateChips();
      this._updateSystem();
      this._updateCameras(status);
      this._updateControls(status);
    }

    _updateChips() {
      if (!this._el.chips) return;
      const chip = (name, text) => {
        const id = this._ids[name];
        if (!id) return "";
        const cls = this._hass.states[id]?.state === "on" ? "on" : "off";
        return `<button class="chip ${cls}" data-entity="${escapeHtml(id)}">${escapeHtml(text)}</button>`;
      };
      this._setHtml(
        this._el.chips,
        [
          chip("connected", this._t("board")),
          chip("realtime", this._t("realtime")),
          this._ids.cloudLink ? chip("cloudLink", this._t("cloud")) : chip("upstream", this._t("cloud")),
        ].join("")
      );
    }

    _updateSystem() {
      if (!this._el.system) return;
      const metric = (name, text, value) =>
        value === null
          ? ""
          : `<div class="metric" data-entity="${escapeHtml(this._ids[name])}"><div class="value">${escapeHtml(value)}</div>` +
            `<div class="name">${escapeHtml(text)}</div></div>`;
      const unit = (name) => this._state(name)?.attributes?.unit_of_measurement || "";
      const value = (name, digits = 0, suffix = "") => {
        const number = this._number(name);
        return number === null ? null : `${this._format(number, digits)}${suffix ? ` ${suffix}` : ""}`;
      };
      const markup = [
        metric("cpu", this._t("cpu"), value("cpu", 0, "%")),
        metric("memory", this._t("memory"), value("memory", 0, unit("memory"))),
        metric("fps", this._t("detection_fps"), value("fps", 1, "fps")),
      ].join("");
      this._el.system.hidden = !markup;
      this._setHtml(this._el.metrics, markup);
    }

    _updateCameras(status) {
      if (!this._el.cameras) return;
      const cameras = cameraEntities(this._hass, this._index);
      this._el.camerasSection.hidden = !cameras.length;
      const markup = cameras
        .map((camera) => {
          const problem = this._hass.states[camera.problem]?.state === "on";
          const fpsState = camera.fps ? this._hass.states[camera.fps] : undefined;
          const fps = usable(fpsState) ? `${this._format(Number(fpsState.state), 1)} fps` : "";
          const target = camera.image || camera.problem || camera.fps;
          const confirming = camera.calibrate && this._confirm === `camera:${camera.calibrate}`;
          const calibrate = camera.calibrate
            ? `<button class="action${confirming ? " confirm" : ""}" data-calibrate="${escapeHtml(camera.calibrate)}"${
                status === "offline" ? " disabled" : ""
              }>${escapeHtml(this._t(confirming ? "confirm" : "calibrate"))}</button>`
            : "";
          return (
            `<div class="camera${problem ? " problem" : ""}">` +
            `<div class="camera-head"><button class="camera-name" data-entity="${escapeHtml(target || "")}">` +
            `${escapeHtml(`${this._t("camera")} ${camera.number}`)}</button><span class="dot" title="${escapeHtml(
              this._t(problem ? "camera_failure" : "camera_ok")
            )}"></span></div>` +
            `<div class="fps">${escapeHtml(problem ? this._t("camera_failure") : fps || this._t("camera_ok"))}</div>` +
            `${calibrate}</div>`
          );
        })
        .join("");
      this._setHtml(this._el.cameras, markup);
    }

    _updateControls(status) {
      const controls = this._el.controls;
      if (!controls) return;
      for (const action of ["calibrate", "reset", "restart"]) {
        const button = controls.querySelector(`[data-action="${action}"]`);
        const confirming = this._confirm === action;
        button.textContent = this._t(confirming ? "confirm" : action);
        button.classList.toggle("confirm", confirming);
        button.hidden = !this._ids[action];
        button.disabled = status === "offline";
      }
    }
  }

  // Editors ---------------------------------------------------------------------

  class CardEditor extends Base {
    static defaults = {};

    setConfig(config) {
      this._config = { ...config };
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      this._render();
    }

    async connectedCallback() {
      if (!customElements.get("ha-form") && window.loadCardHelpers) {
        try {
          // Loading a built-in card editor makes ha-form and its selectors available.
          const helpers = await window.loadCardHelpers();
          const card = await helpers.createCardElement({ type: "entities", entities: [] });
          await card.constructor.getConfigElement?.();
        } catch (error) {
          // The form appears as soon as Home Assistant defines it.
        }
      }
      if (!customElements.get("ha-form")) await customElements.whenDefined("ha-form");
      this._render();
    }

    _options(prefix, values) {
      return values.map((value) => ({ value, label: translate(this._hass, `${prefix}_${value}`) }));
    }

    _schema() {
      return [];
    }

    _render() {
      if (!this._hass || !this._config || !customElements.get("ha-form")) return;
      if (!this._form) {
        this._form = document.createElement("ha-form");
        this._form.computeLabel = (schema) => translate(this._hass, schema.name);
        this._form.computeHelper = (schema) =>
          schema.name === "device_id" ? translate(this._hass, "device_helper") : undefined;
        this._form.addEventListener("value-changed", (event) => {
          const defaults = this.constructor.defaults;
          const config = { ...event.detail.value };
          for (const [key, value] of Object.entries(config)) {
            if (value === "" || value === undefined || defaults[key] === value) delete config[key];
          }
          this._config = { type: this._config.type, ...config };
          this.dispatchEvent(
            new CustomEvent("config-changed", { bubbles: true, composed: true, detail: { config: this._config } })
          );
        });
        this.appendChild(this._form);
      }
      // A new schema object on every update would reset open pickers.
      const lang = language(this._hass);
      if (this._schemaLanguage !== lang) {
        this._schemaLanguage = lang;
        this._form.schema = this._schema();
      }
      this._form.hass = this._hass;
      this._form.data = { ...this.constructor.defaults, ...this._config };
    }
  }

  const device = { name: "device_id", selector: { device: { filter: { integration: "autodarts" } } } };
  const title = { name: "title", selector: { text: {} } };
  const toggles = (names) => ({
    type: "grid",
    name: "",
    schema: names.map((name) => ({ name, selector: { boolean: {} } })),
  });
  const dropdown = (name, options) => ({ name, selector: { select: { mode: "dropdown", options } } });

  class AutodartsCardEditor extends CardEditor {
    static defaults = DEFAULTS;

    _schema() {
      return [
        device,
        title,
        {
          type: "grid",
          name: "",
          schema: [
            dropdown("layout", this._options("layout", ["auto", "horizontal", "vertical", "board"])),
            dropdown("board_style", this._options("style", ["classic", "autodarts"])),
          ],
        },
        dropdown("highlight", this._options("highlight", ["visit", "last", "none"])),
        toggles(["blink", "show_markers", "show_numbers", "show_stats", "show_connection", "show_controls"]),
      ];
    }
  }

  class AutodartsTrainingCardEditor extends CardEditor {
    static defaults = TRAINING_DEFAULTS;

    _schema() {
      return [
        device,
        title,
        {
          type: "grid",
          name: "",
          schema: [
            dropdown("mode", this._options("mode", ["beds", "numbers"])),
            dropdown("board_style", this._options("style", ["muted", "classic", "autodarts"])),
          ],
        },
        { name: "history_size", selector: { number: { min: 5, max: 60, step: 1, mode: "slider" } } },
        toggles(["show_heatmap", "show_stats", "show_top", "show_history", "show_reset"]),
      ];
    }
  }

  class AutodartsStatusCardEditor extends CardEditor {
    static defaults = STATUS_DEFAULTS;

    _schema() {
      return [device, title, toggles(["show_connection", "show_system", "show_cameras", "show_controls"])];
    }
  }

  return {
    [CARD_TYPE]: AutodartsCard,
    [EDITOR_TYPE]: AutodartsCardEditor,
    [TRAINING_TYPE]: AutodartsTrainingCard,
    [TRAINING_EDITOR_TYPE]: AutodartsTrainingCardEditor,
    [STATUS_TYPE]: AutodartsStatusCard,
    [STATUS_EDITOR_TYPE]: AutodartsStatusCardEditor,
  };
}

const CARDS = [
  {
    type: CARD_TYPE,
    name: "Autodarts",
    description:
      "Current visit on a live dartboard with hit beds, dart positions, training statistics and controls.",
  },
  {
    type: TRAINING_TYPE,
    name: "Autodarts training",
    description: "Training session with a hit heatmap, 3-dart average, statistics and recent visits.",
  },
  {
    type: STATUS_TYPE,
    name: "Autodarts board status",
    description: "Detection, connections, cameras, board PC and maintenance controls of an Autodarts board.",
  },
];

function register() {
  const registry = window.customElements;
  for (const [type, element] of Object.entries(createElements(window.HTMLElement))) {
    if (!registry.get(type)) registry.define(type, element);
  }
  window.customCards = window.customCards || [];
  for (const card of CARDS) {
    if (!window.customCards.some((known) => known.type === card.type)) {
      window.customCards.push({ ...card, preview: true, documentationURL: DOCS });
    }
  }
}

async function frontendReady() {
  // Home Assistant loads this module in parallel with its own app, which then swaps in
  // a scoped custom element registry. Elements defined before that swap stay invisible
  // to dashboards, so wait for the app element; other hosts register after a timeout.
  for (let waited = 0; waited < 30000 && !window.customElements.get("home-assistant"); waited += 50) {
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
}

if (globalThis.window?.customElements) frontendReady().then(register);

export {
  bedPath,
  beds,
  boardStatus,
  boardSvg,
  cameraEntities,
  entityIndex,
  escapeHtml,
  heatColor,
  heatLevels,
  heatRatio,
  hitBeds,
  kind,
  label,
  NORM,
  NUMBERS,
  numbersSvg,
  parseSegment,
  R,
  sectorAt,
  topHits,
  visitBucket,
  visitsFromHistory,
};
