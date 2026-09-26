// The practice game in the live card and the dashboard strategy.
import assert from "node:assert/strict";
import { test } from "node:test";

import { dashboardStrategy, practiceView } from "../../custom_components/autodarts/frontend/autodarts-card.js";

test("the practice view reads the remaining score sensor", () => {
  assert.equal(practiceView(undefined), null);
  assert.equal(practiceView({ state: "unknown", attributes: {} }), null);
  assert.equal(practiceView({ state: "12.5", attributes: {} }), null);
  assert.deepEqual(
    practiceView({
      state: "121",
      attributes: { game: 501, checkout: "T20 25 D18", bust: false, won: false, darts: 9, average: 126.67 },
    }),
    { game: 501, remaining: 121, route: ["T20", "25", "D18"], bust: false, won: false, darts: 9, average: 126.67 }
  );
  const bust = practiceView({ state: "32", attributes: { checkout: "<b> D16", bust: true, darts: "x" } });
  assert.deepEqual([bust.route, bust.bust, bust.darts, bust.average, bust.game], [["D16"], true, 0, null, null]);
  assert.deepEqual(practiceView({ state: "0", attributes: { won: true, checkout: null } }).route, []);
});

test("the live view offers the practice controls", () => {
  const entity = (entity_id, translation_key) => ({ entity_id, translation_key, device_id: "dev", platform: "autodarts" });
  const entities = [
    entity("select.board_practice_game", "practice_game"),
    entity("button.board_new_leg", "practice_new_leg"),
    entity("switch.board_double_out", "practice_double_out"),
  ];
  const hass = {
    locale: { language: "de" },
    entities: Object.fromEntries(entities.map((item) => [item.entity_id, item])),
    devices: {},
    states: {},
  };
  const [live] = dashboardStrategy(hass).views;
  assert.deepEqual(live.sections[1].cards, [
    { type: "heading", heading: "Übungsspiel" },
    {
      type: "entities",
      entities: ["select.board_practice_game", "button.board_new_leg", "switch.board_double_out"],
    },
  ]);
});
