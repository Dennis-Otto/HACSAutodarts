// The card editors in a browser DOM: loading Home Assistant's form, schemas, labels and changes.
import assert from "node:assert/strict";
import { test } from "node:test";

import { DEVICE, READY, loadCards, makeHass, settle, update, window, withLanguage } from "./dom.mjs";

await loadCards();

// Home Assistant's form element, reduced to the properties an editor sets.
class FakeForm extends HTMLElement {}
const hass = makeHass({ states: READY });
const editor = (type, config = { type: "custom:autodarts-card" }, withHass = hass) => {
  const element = document.createElement(type);
  element.setConfig(config);
  if (withHass) element.hass = withHass;
  document.body.append(element);
  return element;
};
const formOf = (element) => element.querySelector("ha-form");
// Field names of a schema, with grids as nested lists.
const names = (schema) => schema.map((field) => (field.schema ? names(field.schema) : field.name));
const labels = (field) => field.selector.select.options.map((option) => option.label);
const DEVICE_FIELD = { name: "device_id", selector: { device: { filter: { integration: "autodarts" } } } };
const TITLE_FIELD = { name: "title", selector: { text: {} } };

test("an editor waits for Home Assistant's form, however it gets loaded", async () => {
  // Without card helpers the editor just waits for the form.
  delete window.loadCardHelpers;
  const waiting = editor("autodarts-card-editor");
  window.loadCardHelpers = async () => {
    throw new Error("helpers unavailable");
  };
  const failing = editor("autodarts-status-card-editor");
  window.loadCardHelpers = async () => ({ createCardElement: async () => ({}) });
  const plain = editor("autodarts-players-card-editor");
  await settle();
  for (const element of [waiting, failing, plain]) assert.equal(formOf(element), null);

  // The entities card editor defines the form, as it does in Home Assistant.
  const created = [];
  class EntitiesCard {
    static getConfigElement() {
      customElements.define("ha-form", FakeForm);
    }
  }
  window.loadCardHelpers = async () => ({
    createCardElement: async (config) => {
      created.push(config);
      return new EntitiesCard();
    },
  });
  const loading = editor("autodarts-doubles-card-editor");
  await settle();
  await settle();
  assert.deepEqual(created, [{ type: "entities", entities: [] }]);
  for (const element of [waiting, failing, plain, loading]) {
    assert.ok(formOf(element) instanceof FakeForm);
    assert.equal(element.querySelectorAll("ha-form").length, 1);
  }
  delete window.loadCardHelpers;
});

test("the live card editor offers layout, board style, highlight and every switch", async () => {
  const element = editor("autodarts-card-editor", { type: "custom:autodarts-card", device_id: DEVICE, blink: false });
  await settle();
  const form = formOf(element);
  assert.deepEqual(form.schema, [
    DEVICE_FIELD,
    TITLE_FIELD,
    {
      type: "grid",
      name: "",
      schema: [
        {
          name: "layout",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: "auto", label: "Automatic" },
                { value: "horizontal", label: "Board on the right" },
                { value: "vertical", label: "Board below" },
                { value: "board", label: "Board only" },
              ],
            },
          },
        },
        {
          name: "board_style",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: "classic", label: "Classic" },
                { value: "autodarts", label: "Autodarts" },
              ],
            },
          },
        },
      ],
    },
    {
      name: "highlight",
      selector: {
        select: {
          mode: "dropdown",
          options: [
            { value: "visit", label: "All darts of the visit" },
            { value: "last", label: "Last dart only" },
            { value: "none", label: "Off" },
          ],
        },
      },
    },
    {
      type: "grid",
      name: "",
      schema: [
        "blink",
        "show_markers",
        "show_numbers",
        "show_stats",
        "show_recent",
        "show_practice",
        "show_connection",
        "show_controls",
      ].map((name) => ({ name, selector: { boolean: {} } })),
    },
  ]);
  assert.equal(form.hass, hass);
  assert.deepEqual(form.data, {
    layout: "auto",
    board_style: "classic",
    highlight: "visit",
    blink: false,
    show_markers: true,
    show_numbers: true,
    show_stats: true,
    show_connection: true,
    show_controls: true,
    show_recent: true,
    show_practice: true,
    type: "custom:autodarts-card",
    device_id: DEVICE,
  });
});

test("fields are labelled in the language of Home Assistant, with help for the board and player", () => {
  const form = formOf(editor("autodarts-doubles-card-editor", { type: "custom:autodarts-doubles-card" }));
  assert.equal(form.computeLabel({ name: "board_style" }), "Board style");
  assert.equal(form.computeLabel({ name: "" }), "");
  assert.equal(
    form.computeHelper({ name: "device_id" }),
    "Optional. Without a selection, the card uses the first Autodarts board."
  );
  assert.equal(
    form.computeHelper({ name: "player" }),
    "Optional. A player name shows that player's doubles; empty shows everybody's."
  );
  assert.equal(form.computeHelper({ name: "title" }), undefined);
});

test("every editor builds the form of its own card", () => {
  const forms = Object.fromEntries(
    ["training", "status", "scoreboard", "players", "doubles"].map((card) => [
      card,
      formOf(editor(`autodarts-${card}-card-editor`, { type: `custom:autodarts-${card}-card` })),
    ])
  );
  assert.deepEqual(names(forms.training.schema), [
    "device_id",
    "title",
    ["mode", "board_style"],
    "history_size",
    ["show_heatmap", "show_stats", "show_top", "show_history", "show_sessions", "show_reset"],
  ]);
  const [mode, style] = forms.training.schema[2].schema;
  assert.deepEqual(labels(mode), ["Beds", "Numbers"]);
  assert.deepEqual(labels(style), ["Muted", "Classic", "Autodarts"]);
  assert.deepEqual(forms.training.schema[3].selector, { number: { min: 5, max: 60, step: 1, mode: "slider" } });
  assert.equal(forms.training.data.history_size, 20);

  assert.deepEqual(names(forms.status.schema), [
    "device_id",
    "title",
    ["show_connection", "show_system", "show_cameras", "show_controls"],
  ]);
  assert.deepEqual(names(forms.scoreboard.schema), [
    "device_id",
    "title",
    ["full_height", "show_visit", "show_status"],
    ["caller", "call_scores", "call_checkouts", "call_results", "call_sounds"],
  ]);
  assert.equal(forms.scoreboard.data.caller, false);
  assert.deepEqual(names(forms.players.schema), ["device_id", "title", ["show_head_to_head", "show_matches"]]);
  assert.deepEqual(forms.doubles.schema, [DEVICE_FIELD, TITLE_FIELD, { name: "player", selector: { text: {} } }]);
  assert.deepEqual(forms.doubles.data, { type: "custom:autodarts-doubles-card" });
});

test("a changed form reports the configuration without defaults and empty fields", () => {
  const element = editor("autodarts-card-editor", { type: "custom:autodarts-card", title: "Old" });
  const events = [];
  document.addEventListener("config-changed", (event) => events.push(event), { once: true });
  formOf(element).dispatchEvent(
    new CustomEvent("value-changed", {
      detail: {
        value: {
          type: "custom:autodarts-card",
          device_id: "",
          title: "Pub",
          layout: "auto",
          highlight: undefined,
          blink: false,
          show_stats: true,
        },
      },
    })
  );
  assert.equal(events.length, 1);
  assert.deepEqual([events[0].bubbles, events[0].composed], [true, true]);
  assert.deepEqual(events[0].detail.config, { type: "custom:autodarts-card", title: "Pub", blink: false });
});

test("the form keeps its schema until the language changes, and follows the configuration", () => {
  const element = editor("autodarts-card-editor");
  const form = formOf(element);
  const schema = form.schema;
  const next = update(hass, { "sensor.local_status": "Takeout in progress" });
  element.hass = next;
  assert.equal(form.schema, schema);
  assert.equal(form.hass, next);

  element.hass = withLanguage(next, "de");
  assert.notEqual(form.schema, schema);
  assert.deepEqual(labels(form.schema[2].schema[0]), ["Automatisch", "Scheibe rechts", "Scheibe unten", "Nur Scheibe"]);
  assert.equal(form.computeLabel({ name: "layout" }), "Anordnung");

  element.setConfig({ type: "custom:autodarts-card", layout: "vertical" });
  assert.equal(form.data.layout, "vertical");
  assert.equal(formOf(element), form);
});

test("an editor without Home Assistant renders nothing yet", async () => {
  const element = editor("autodarts-status-card-editor", { type: "custom:autodarts-status-card" }, null);
  await settle();
  assert.equal(formOf(element), null);
  element.hass = hass;
  assert.ok(formOf(element) instanceof FakeForm);
});

test("an editor without fields of its own shows an empty form with its configuration", () => {
  class BareEditor extends Object.getPrototypeOf(customElements.get("autodarts-card-editor")) {}
  customElements.define("bare-autodarts-card-editor", BareEditor);
  const form = formOf(editor("bare-autodarts-card-editor", { type: "custom:bare-card", title: "Bare" }));
  assert.deepEqual(form.schema, []);
  assert.deepEqual(form.data, { type: "custom:bare-card", title: "Bare" });
});
