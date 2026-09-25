/*
 * Autodarts card for Home Assistant, served by the Autodarts integration.
 *
 * Shows the current visit on a dartboard drawn with the geometry of the
 * Autodarts Board Manager: hit beds blink, darts appear at their detected
 * position and the board glows in the detection status colour.
 */

const CARD_TYPE = "autodarts-card";
const EDITOR_TYPE = "autodarts-card-editor";

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
};

const STATUS_COLORS = {
  ready: "#43a047",
  takeout: "#fbc02d",
  stopped: "#fb8c00",
  calibrating: "#8e24aa",
  problem: "#e53935",
  offline: "#e53935",
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
    reset: "Reset",
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
    reset: "Zurücksetzen",
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

// Entities the card reads, by domain and translation key of the integration.
const KEYS = {
  status: "sensor.local_status",
  visit: "sensor.local_visit_score",
  lastThrow: "sensor.last_throw",
  numThrows: "sensor.num_throws",
  darts: "sensor.training_darts",
  points: "sensor.training_points",
  triples: "sensor.training_triples",
  bulls: "sensor.training_bulls",
  max: "sensor.training_scores_180",
  started: "sensor.training_started",
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

const language = (hass) =>
  String(hass?.locale?.language || hass?.language || "en").startsWith("de") ? "de" : "en";

const translate = (hass, key) => TEXT[language(hass)][key] ?? TEXT.en[key] ?? key;

const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`);

const usable = (state) => state && !["unknown", "unavailable"].includes(state.state);

function autodartsDevices(hass) {
  const devices = new Set();
  for (const entity of Object.values(hass?.entities || {})) {
    if (entity.platform === "autodarts" && entity.device_id) devices.add(entity.device_id);
  }
  return [...devices];
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

// Card ----------------------------------------------------------------------

const CSS = `
  :host { display: block; }
  ha-card { overflow: hidden; height: 100%; }
  .root { container-type: inline-size; height: 100%; }
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
  .visit-label, .section-label {
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
  .controls button {
    flex: 1 1 auto; min-height: 40px; padding: 0 14px; border-radius: 12px; cursor: pointer;
    font: inherit; font-size: 13px; font-weight: 600; color: var(--primary-text-color);
    border: 1px solid var(--divider-color, rgba(127,127,127,.3)); background: none;
    transition: background .2s, border-color .2s, color .2s;
  }
  .controls button:hover { background: color-mix(in srgb, var(--primary-text-color) 6%, transparent); }
  .controls button.primary {
    color: var(--text-primary-color, #fff); background: var(--ad-accent); border-color: var(--ad-accent);
  }
  .controls button.primary.stop { background: none; color: var(--ad-accent); }
  .controls button.confirm { color: #fff; background: ${STATUS_COLORS.problem}; border-color: ${STATUS_COLORS.problem}; }
  .controls button:disabled { opacity: .45; cursor: default; }
  .board { display: flex; justify-content: center; }
  .board-frame {
    width: clamp(180px, 42cqw, 380px); aspect-ratio: 1; border-radius: 50%;
    box-shadow: 0 0 42px 4px color-mix(in srgb, var(--ad-status) 55%, transparent);
    transition: box-shadow .5s;
  }
  .layout.vertical .board-frame, .layout.board-only .board-frame { width: min(100%, 420px); }
  @container (max-width: 520px) {
    .layout.auto .board-frame { width: min(100%, 360px); }
    .stats { grid-template-columns: repeat(3, minmax(0, 1fr)); row-gap: 12px; }
  }
  svg { display: block; width: 100%; height: 100%; overflow: visible; }
  .number {
    font: 700 22px/1 Roboto, Arial, sans-serif; text-anchor: middle; dominant-baseline: central;
    pointer-events: none;
  }
  .hit { fill: var(--ad-highlight); opacity: .88; pointer-events: none; }
  .blink .hit { animation: ad-blink .8s ease-in-out infinite alternate; }
  .dart .pin { fill: #3182ce; stroke: #fff; stroke-width: 2; }
  .dart text { font: 700 11px/1 Roboto, Arial, sans-serif; fill: #fff; text-anchor: middle; dominant-baseline: central; }
  .dart.latest .halo { fill: none; stroke: var(--ad-highlight); stroke-width: 2; animation: ad-pulse 1.6s ease-out infinite; transform-box: fill-box; transform-origin: center; }
  .message { padding: 18px; color: var(--secondary-text-color); }
  @keyframes ad-blink { from { opacity: .18; } to { opacity: .95; } }
  @keyframes ad-pulse { from { opacity: .9; transform: scale(.7); } to { opacity: 0; transform: scale(1.8); } }
  @media (prefers-reduced-motion: reduce) {
    .blink .hit, .dart.latest .halo { animation: none; }
  }
`;

// Elements are created on demand: Home Assistant replaces HTMLElement while it boots.
function createElements(Base) {
  class AutodartsCard extends Base {
    static getConfigElement() {
      return document.createElement(EDITOR_TYPE);
    }

    static getStubConfig(hass) {
      const [deviceId] = autodartsDevices(hass);
      return deviceId ? { device_id: deviceId } : {};
    }

    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._states = [];
      this._confirm = null;
    }

    setConfig(config) {
      if (!config || typeof config !== "object") throw new Error("Invalid configuration");
      this._config = { ...DEFAULTS, ...config };
      this._built = false;
      this._states = [];
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

    getCardSize() {
      return this._config?.layout === "vertical" ? 10 : 7;
    }

    getGridOptions() {
      return { columns: 12, min_columns: 6 };
    }

    _entities() {
      const hass = this._hass;
      const deviceId = this._config.device_id || autodartsDevices(hass)[0];
      const found = {};
      for (const entity of Object.values(hass.entities || {})) {
        if (entity.platform !== "autodarts" || entity.device_id !== deviceId) continue;
        if (!entity.translation_key) continue;
        const key = `${entity.entity_id.split(".")[0]}.${entity.translation_key}`;
        found[key] ??= entity.entity_id;
      }
      const ids = {};
      for (const [name, key] of Object.entries(KEYS)) ids[name] = found[key];
      return { deviceId, ids };
    }

    _render() {
      if (!this._config || !this._hass) return;
      const { deviceId, ids } = this._entities();
      if (!deviceId) {
        this.shadowRoot.innerHTML = `<style>${CSS}</style><ha-card><div class="message">${escapeHtml(
          translate(this._hass, "no_board")
        )}</div></ha-card>`;
        this._built = false;
        return;
      }
      const states = Object.values(ids).map((id) => (id ? this._hass.states[id] : undefined));
      const lang = language(this._hass);
      if (
        this._built &&
        this._language === lang &&
        this._deviceId === deviceId &&
        states.every((state, index) => state === this._states[index])
      ) {
        return;
      }
      if (!this._built || this._language !== lang || this._deviceId !== deviceId) {
        this._build();
        this._language = lang;
        this._deviceId = deviceId;
      }
      this._states = states;
      this._ids = ids;
      this._update();
    }

    _build() {
      const c = this._config;
      const t = (key) => escapeHtml(translate(this._hass, key));
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
                  <svg viewBox="-230 -230 460 460" role="img" aria-label="${t("board_label")}">
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
        layout: root.querySelector(".layout"),
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
      this._built = true;
    }

    _state(name) {
      const id = this._ids[name];
      return id ? this._hass.states[id] : undefined;
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
      const on = (name) => this._state(name)?.state === "on";
      const connected = this._state("connected");
      const detection = this._state("detection")?.state;
      const status = String(this._state("status")?.state || "").toLowerCase();
      if (!connected || connected.state !== "on") return ["offline", "status_offline"];
      if (on("calibrating") || status === "calibrating") return ["calibrating", "status_calibrating"];
      if (on("cameraProblem")) return ["problem", "status_problem"];
      if (status === "starting") return ["stopped", "status_starting"];
      if (status === "stopping") return ["stopped", "status_stopping"];
      if (detection === "off" || status === "stopped") return ["stopped", "status_stopped"];
      if (status.includes("takeout") || on("takeoutPartial")) return ["takeout", "status_takeout"];
      if (on("hand")) return ["takeout", "status_hand"];
      if (Number(this._state("numThrows")?.state) >= 3) return ["takeout", "status_full"];
      return ["ready", "status_ready"];
    }

    _update() {
      const hass = this._hass;
      const c = this._config;
      const el = this._el;
      const t = (key) => translate(hass, key);
      const device = hass.devices?.[this._deviceId];
      el.title.textContent = c.title || device?.name_by_user || device?.name || "Autodarts";

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
        slot.className = "slot";
        const [segment, value] = [slot.querySelector(".segment"), slot.querySelector(".value")];
        if (!dart) {
          slot.classList.add(index < darts.length ? "unknown" : "empty");
          segment.textContent = index < darts.length ? "?" : "–";
          value.innerHTML = "&nbsp;";
          return;
        }
        slot.classList.add(kind(dart));
        if (index === darts.length - 1) slot.classList.add("latest");
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
      this._el.hits.innerHTML = [...paths]
        .map((id) => bedPath(id))
        .filter(Boolean)
        .map((d) => `<path class="hit" d="${d}"/>`)
        .join("");

      this._el.darts.innerHTML = c.show_markers
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
        : "";
      const summary = darts
        .filter(Boolean)
        .map((dart) => label(this._hass, dart))
        .join(", ");
      this._el.svg.setAttribute(
        "aria-label",
        summary ? `${translate(this._hass, "board_label")}: ${summary}` : translate(this._hass, "board_label")
      );
    }

    _updateStats() {
      const stats = this._el.stats;
      if (!stats.darts) return;
      const number = (name) => {
        const state = this._state(name);
        const value = usable(state) ? Number(state.state) : NaN;
        return Number.isFinite(value) ? value : null;
      };
      const locale = this._hass.locale?.language || this._hass.language;
      const format = (value, digits = 0) =>
        value === null
          ? "–"
          : new Intl.NumberFormat(locale, {
              minimumFractionDigits: digits,
              maximumFractionDigits: digits,
            }).format(value);
      const darts = number("darts");
      const points = number("points");
      stats.darts.textContent = format(darts);
      stats.average.textContent = darts > 0 && points !== null ? format((points / darts) * 3, 1) : "–";
      stats.triples.textContent = format(number("triples"));
      stats.bulls.textContent = format(number("bulls"));
      stats.max.textContent = format(number("max"));
      const started = this._state("started");
      const date = usable(started) ? new Date(started.state) : null;
      this._el.since.textContent =
        date && !Number.isNaN(date.getTime())
          ? `${translate(this._hass, "since")} ${new Intl.DateTimeFormat(locale, {
              day: "2-digit",
              month: "2-digit",
              hour: "2-digit",
              minute: "2-digit",
            }).format(date)}`
          : "";
    }

    _updateChips() {
      if (!this._el.chips) return;
      const t = (key) => escapeHtml(translate(this._hass, key));
      const chip = (name, text, alert = false) => {
        const id = this._ids[name];
        if (!id) return "";
        const state = this._hass.states[id]?.state;
        const cls = alert ? "alert" : state === "on" ? "on" : "off";
        return `<button class="chip ${cls}" data-entity="${escapeHtml(id)}">${text}</button>`;
      };
      const problem = this._state("cameraProblem")?.state === "on";
      this._el.chips.innerHTML = [
        chip("connected", t("board")),
        chip("realtime", t("realtime")),
        problem ? chip("cameraProblem", t("camera_problem"), true) : chip("cameras", t("cameras")),
      ].join("");
    }

    _updateControls(status) {
      const controls = this._el.controls;
      if (!controls) return;
      const running = this._state("detection")?.state === "on";
      const toggle = controls.querySelector('[data-action="toggle"]');
      toggle.textContent = translate(this._hass, running ? "stop" : "start");
      toggle.classList.toggle("stop", running);
      toggle.disabled = status === "offline" || !(this._ids.detection || this._ids.start);
      for (const action of ["reset", "calibrate"]) {
        const button = controls.querySelector(`[data-action="${action}"]`);
        const confirming = this._confirm === action;
        button.textContent = translate(this._hass, confirming ? "confirm" : action);
        button.classList.toggle("confirm", confirming);
        button.disabled = status === "offline" || !this._ids[action];
      }
    }

    _onControl(event) {
      const action = event.target.closest("button")?.dataset.action;
      if (!action || this.preview) return;
      if (action === "toggle") {
        const running = this._state("detection")?.state === "on";
        if (this._ids.detection) {
          this._hass.callService("switch", running ? "turn_off" : "turn_on", {
            entity_id: this._ids.detection,
          });
        } else {
          this._press(running ? "stop" : "start");
        }
        return;
      }
      // Reset and calibration discard detected darts, so they need a second tap.
      if (this._confirm !== action) {
        this._confirm = action;
        clearTimeout(this._confirmTimer);
        this._confirmTimer = setTimeout(() => {
          this._confirm = null;
          this._updateControls(this._status()[0]);
        }, 4000);
      } else {
        this._confirm = null;
        clearTimeout(this._confirmTimer);
        this._press(action);
      }
      this._updateControls(this._status()[0]);
    }

    _press(name) {
      const id = this._ids[name];
      if (id) this._hass.callService("button", "press", { entity_id: id });
    }

    _moreInfo(entityId) {
      if (!entityId || this.preview) return;
      this.dispatchEvent(
        new CustomEvent("hass-more-info", { bubbles: true, composed: true, detail: { entityId } })
      );
    }
  }

  // Editor ----------------------------------------------------------------------

  class AutodartsCardEditor extends Base {
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
        // Loading a built-in card editor makes ha-form and its selectors available.
        const helpers = await window.loadCardHelpers();
        const card = await helpers.createCardElement({ type: "entities", entities: [] });
        await card.constructor.getConfigElement?.();
      }
      this._render();
    }

    _schema() {
      const t = (key) => translate(this._hass, key);
      const options = (prefix, values) =>
        values.map((value) => ({ value, label: t(`${prefix}_${value}`) }));
      return [
        { name: "device_id", selector: { device: { filter: { integration: "autodarts" } } } },
        { name: "title", selector: { text: {} } },
        {
          type: "grid",
          name: "",
          schema: [
            {
              name: "layout",
              selector: {
                select: { mode: "dropdown", options: options("layout", ["auto", "horizontal", "vertical", "board"]) },
              },
            },
            {
              name: "board_style",
              selector: { select: { mode: "dropdown", options: options("style", ["classic", "autodarts"]) } },
            },
          ],
        },
        {
          name: "highlight",
          selector: { select: { mode: "dropdown", options: options("highlight", ["visit", "last", "none"]) } },
        },
        {
          type: "grid",
          name: "",
          schema: [
            "blink",
            "show_markers",
            "show_numbers",
            "show_stats",
            "show_connection",
            "show_controls",
          ].map((name) => ({ name, selector: { boolean: {} } })),
        },
      ];
    }

    _render() {
      if (!this._hass || !this._config || !customElements.get("ha-form")) return;
      if (!this._form) {
        this._form = document.createElement("ha-form");
        this._form.computeLabel = (schema) => translate(this._hass, schema.name);
        this._form.computeHelper = (schema) =>
          schema.name === "device_id" ? translate(this._hass, "device_helper") : undefined;
        this._form.addEventListener("value-changed", (event) => {
          const config = { ...event.detail.value };
          for (const [key, value] of Object.entries(config)) {
            if (value === "" || value === undefined || DEFAULTS[key] === value) delete config[key];
          }
          this._config = { type: this._config.type, ...config };
          this.dispatchEvent(
            new CustomEvent("config-changed", { bubbles: true, composed: true, detail: { config: this._config } })
          );
        });
        this.appendChild(this._form);
      }
      this._form.hass = this._hass;
      this._form.schema = this._schema();
      this._form.data = { ...DEFAULTS, ...this._config };
    }
  }

  return [AutodartsCard, AutodartsCardEditor];
}

function register() {
  const registry = window.customElements;
  const [AutodartsCard, AutodartsCardEditor] = createElements(window.HTMLElement);
  if (!registry.get(CARD_TYPE)) registry.define(CARD_TYPE, AutodartsCard);
  if (!registry.get(EDITOR_TYPE)) registry.define(EDITOR_TYPE, AutodartsCardEditor);
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === CARD_TYPE)) {
    window.customCards.push({
      type: CARD_TYPE,
      name: "Autodarts",
      description:
        "Current visit on a live dartboard with hit beds, dart positions, training statistics and controls.",
      preview: true,
      documentationURL: "https://github.com/Dennis-Otto/HACSAutodarts#dashboard-card",
    });
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

export { bedPath, beds, boardSvg, escapeHtml, kind, label, NORM, NUMBERS, numbersSvg, parseSegment, R, sectorAt };
