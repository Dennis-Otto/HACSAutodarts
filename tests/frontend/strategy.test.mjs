// The dashboard strategy builds live, scoreboard, training and board views for every board.
import assert from "node:assert/strict";
import { test } from "node:test";

import { dashboardStrategy } from "../../custom_components/autodarts/frontend/autodarts-card.js";

const entity = (entity_id, translation_key, device_id) => ({
  entity_id,
  translation_key,
  device_id,
  platform: "autodarts",
});

function board(device, prefix) {
  return [
    entity(`sensor.${prefix}_darts`, "training_darts", device),
    entity(`sensor.${prefix}_average`, "training_average", device),
    entity(`switch.${prefix}_calibrate_on_start`, "auto_calibrate_on_start", device),
    entity(`select.${prefix}_standby`, "standby_minutes", device),
    entity(`update.${prefix}_software`, "board_software", device),
  ];
}

const hass = (entities, devices = {}) => ({
  locale: { language: "en" },
  entities: Object.fromEntries(entities.map((item) => [item.entity_id, item])),
  devices,
  states: {},
});

test("one board gets a live, a scoreboard, a training and a board view", () => {
  const config = dashboardStrategy(hass(board("dev1", "b")));
  assert.equal(config.title, "Autodarts");
  assert.deepEqual(
    config.views.map((view) => view.path),
    ["live", "scoreboard", "training", "board"]
  );
  const [live, scoreboard, training, maintenance] = config.views;
  assert.deepEqual(live.sections[0].cards[0], {
    type: "custom:autodarts-card",
    device_id: "dev1",
    grid_options: { columns: "full" },
  });
  assert.equal(scoreboard.panel, true);
  assert.deepEqual(scoreboard.cards, [
    { type: "custom:autodarts-scoreboard-card", device_id: "dev1", full_height: true },
  ]);
  const trends = training.sections[1].cards;
  assert.deepEqual(
    trends.map((card) => [card.type, card.entities]),
    [
      ["statistics-graph", ["sensor.b_darts"]],
      ["history-graph", ["sensor.b_average"]],
    ]
  );
  assert.equal(trends[0].stat_types[0], "change");
  const settings = maintenance.sections[1].cards;
  assert.deepEqual(settings[1].entities, ["switch.b_calibrate_on_start", "select.b_standby"]);
  assert.equal(settings[2].entity, "update.b_software");
});

test("several boards get their own named views", () => {
  const config = dashboardStrategy(
    hass([...board("dev1", "a"), ...board("dev2", "b")], {
      dev1: { name: "Autodarts Board", name_by_user: "Club board" },
      dev2: { name: "Garage" },
    })
  );
  assert.deepEqual(
    config.views.map((view) => view.path),
    ["live-1", "scoreboard-1", "training-1", "board-1", "live-2", "scoreboard-2", "training-2", "board-2"]
  );
  assert.equal(config.views[0].title, "Live · Club board");
  assert.equal(config.views[5].title, "Scoreboard · Garage");
  assert.equal(config.views[6].sections[0].cards[0].device_id, "dev2");
});

test("a chosen board and title are respected, and missing entities are left out", () => {
  const config = dashboardStrategy(hass([entity("sensor.x_darts", "training_darts", "dev1")]), {
    device_id: "dev1",
    title: "Darts",
  });
  assert.equal(config.title, "Darts");
  assert.equal(config.views[2].sections[1].cards.length, 1);
  // Without settings or update entities, the board view shows only the status card.
  assert.equal(config.views[3].sections.length, 1);
});

test("without boards the dashboard explains what to do", () => {
  const config = dashboardStrategy({ locale: { language: "de" }, entities: {} });
  assert.match(config.views[0].cards[0].content, /Kein Autodarts-Board/);
});

test("the training view offers the daily goal, the streak and personal bests", () => {
  const config = dashboardStrategy(
    hass([
      ...board("dev1", "b"),
      entity("number.b_goal", "training_daily_goal", "dev1"),
      entity("sensor.b_today", "darts_today", "dev1"),
      entity("sensor.b_streak", "training_streak", "dev1"),
      entity("sensor.b_best", "personal_best", "dev1"),
    ])
  );
  const training = config.views.find((view) => view.path === "training");
  assert.deepEqual(training.sections[1].cards[0], {
    type: "entities",
    title: "Goals and personal bests",
    entities: ["number.b_goal", "sensor.b_today", "sensor.b_streak", "sensor.b_best"],
  });
});
