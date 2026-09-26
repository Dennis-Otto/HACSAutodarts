// Registration with Home Assistant: elements, card picker entries and the dashboard strategy.
import assert from "node:assert/strict";
import { test } from "node:test";

import { Window } from "happy-dom";

// The browser comes first; the module then waits for Home Assistant's app element.
import { READY, makeHass, settle, window as page } from "./dom.mjs";
import {
  createElements,
  dashboardStrategy,
  frontendReady,
  register,
} from "../../custom_components/autodarts/frontend/autodarts-card.js";

const DOCS = "https://github.com/Dennis-Otto/ha-autodarts#dashboard-cards";
const CARDS = [
  ["autodarts-card", "Autodarts"],
  ["autodarts-training-card", "Autodarts training"],
  ["autodarts-status-card", "Autodarts board status"],
  ["autodarts-scoreboard-card", "Autodarts scoreboard"],
  ["autodarts-players-card", "Autodarts players"],
  ["autodarts-doubles-card", "Autodarts doubles"],
];
const ELEMENTS = [
  "ll-strategy-dashboard-autodarts",
  "autodarts-card",
  "autodarts-card-editor",
  "autodarts-training-card",
  "autodarts-training-card-editor",
  "autodarts-status-card",
  "autodarts-status-card-editor",
  "autodarts-scoreboard-card",
  "autodarts-scoreboard-card-editor",
  "autodarts-players-card",
  "autodarts-players-card-editor",
  "autodarts-doubles-card",
  "autodarts-doubles-card-editor",
];
const STRATEGY = {
  type: "autodarts",
  strategyType: "dashboard",
  name: "Autodarts",
  description: "Live board, training analytics and board status for every Autodarts board.",
  documentationURL: DOCS,
};

test("the cards wait for Home Assistant's app element before they register", async () => {
  await new Promise((resolve) => setTimeout(resolve, 120));
  assert.equal(customElements.get("autodarts-card"), undefined);
  assert.equal(page.customCards, undefined);

  customElements.define("home-assistant", class extends HTMLElement {});
  await customElements.whenDefined("autodarts-card");
  for (const type of ELEMENTS) assert.equal(typeof customElements.get(type), "function", type);
  assert.deepEqual(
    page.customCards.map(({ type, name, preview, documentationURL }) => [type, name, preview, documentationURL]),
    CARDS.map(([type, name]) => [type, name, true, DOCS])
  );
  for (const card of page.customCards) assert.ok(card.description.length > 40, card.type);
  assert.deepEqual(page.customStrategies, [STRATEGY]);
});

test("registering again adds no duplicate cards, strategies or elements", () => {
  const cards = [...page.customCards];
  const live = customElements.get("autodarts-card");
  register();
  assert.deepEqual(page.customCards, cards);
  assert.deepEqual(page.customStrategies, [STRATEGY]);
  assert.equal(customElements.get("autodarts-card"), live);
});

test("elements and entries the page already knows are kept", (t) => {
  const other = new Window({ url: "http://localhost:8123/" });
  const own = class extends other.HTMLElement {};
  other.customElements.define("autodarts-card", own);
  other.customCards = [{ type: "autodarts-card", name: "Mine" }];
  other.customStrategies = [{ type: "autodarts", name: "Mine" }];
  globalThis.window = other;
  t.after(async () => {
    globalThis.window = page;
    await other.happyDOM.close();
  });
  register();
  assert.equal(other.customElements.get("autodarts-card"), own);
  assert.equal(typeof other.customElements.get("autodarts-training-card"), "function");
  assert.deepEqual(
    other.customCards.map((card) => [card.type, card.name]),
    [["autodarts-card", "Mine"], ...CARDS.slice(1)]
  );
  assert.deepEqual(other.customStrategies, [{ type: "autodarts", name: "Mine" }]);
});

test("other hosts get the cards after thirty seconds", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  globalThis.window = { customElements: { get: () => undefined } };
  t.after(() => (globalThis.window = page));
  let ready = false;
  const waiting = frontendReady().then(() => (ready = true));
  for (let waited = 0; waited < 29950; waited += 50) {
    t.mock.timers.tick(50);
    await settle();
  }
  assert.equal(ready, false);
  t.mock.timers.tick(50);
  await waiting;
  assert.equal(ready, true);
});

test("the element factory builds every card, editor and the strategy on the given base class", () => {
  class Base {}
  const elements = createElements(Base);
  assert.deepEqual(Object.keys(elements), ELEMENTS);
  for (const element of Object.values(elements)) assert.ok(element.prototype instanceof Base);
});

test("the strategy element generates the dashboard of every board", async () => {
  const Strategy = customElements.get("ll-strategy-dashboard-autodarts");
  const hass = makeHass({ states: READY });
  const dashboard = await Strategy.generate({ title: "Darts" }, hass);
  assert.deepEqual(dashboard, dashboardStrategy(hass, { title: "Darts" }));
  assert.equal(dashboard.title, "Darts");
  assert.deepEqual(
    dashboard.views.map((view) => view.path),
    ["live", "scoreboard", "training", "board"]
  );
});

test("every card asks for a board in its own style when there is none", () => {
  const styles = CARDS.map(([type]) => {
    const card = document.createElement(type);
    card.setConfig({});
    card.hass = makeHass({ language: "de" });
    assert.equal(
      card.shadowRoot.querySelector("ha-card .message").textContent,
      "Kein Autodarts-Board gefunden. Wähle ein Gerät in den Karteneinstellungen.",
      type
    );
    return card.shadowRoot.querySelector("style").textContent;
  });
  assert.equal(new Set(styles).size, CARDS.length);
});

test("a card without its own style shows its message with the base style", () => {
  const Live = customElements.get("autodarts-card");
  class BareCard extends Object.getPrototypeOf(Live) {}
  customElements.define("bare-autodarts-card", BareCard);
  const bare = document.createElement("bare-autodarts-card");
  bare.setConfig({});
  bare.hass = makeHass();
  const live = document.createElement("autodarts-card");
  live.setConfig({});
  live.hass = makeHass();
  const base = bare.shadowRoot.querySelector("style").textContent;
  const full = live.shadowRoot.querySelector("style").textContent;
  assert.equal(
    bare.shadowRoot.querySelector(".message").textContent,
    "No Autodarts board found. Select a device in the card settings."
  );
  assert.ok(full.startsWith(base) && full.length > base.length);
  assert.deepEqual(bare.getGridOptions(), { columns: 12, min_columns: 6 });
});
