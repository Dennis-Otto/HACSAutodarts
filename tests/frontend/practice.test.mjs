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
    {
      game: 501,
      remaining: 121,
      route: ["T20", "25", "D18"],
      bust: false,
      won: false,
      darts: 9,
      average: 126.67,
      player: 1,
      name: null,
      winner: null,
      legsToWin: 1,
      setsToWin: 1,
      scores: [],
    }
  );
  const bust = practiceView({ state: "32", attributes: { checkout: "<b> D16", bust: true, darts: "x" } });
  assert.deepEqual([bust.route, bust.bust, bust.darts, bust.average, bust.game], [["D16"], true, 0, null, null]);
  assert.deepEqual(practiceView({ state: "0", attributes: { won: true, checkout: null } }).route, []);
});

test("a match brings every player's score", () => {
  const view = practiceView({
    state: "281",
    attributes: {
      game: 301,
      player: 2,
      name: "",
      winner: null,
      legs_to_win: 3,
      sets_to_win: 1,
      scores: [
        { player: 1, name: "Dennis", remaining: 121, legs: 1, sets: 0, average: 90 },
        { player: 2, name: null, remaining: 281, legs: "x", sets: 0, average: null },
        { player: "3", remaining: 1 },
        null,
      ],
    },
  });
  assert.equal(view.player, 2);
  assert.equal(view.name, null);
  assert.equal(view.legsToWin, 3);
  assert.deepEqual(view.scores, [
    { player: 1, name: "Dennis", remaining: 121, legs: 1, sets: 0, average: 90 },
    { player: 2, name: null, remaining: 281, legs: 0, sets: 0, average: null },
  ]);
});

test("the live view offers the practice controls and player names", () => {
  const entity = (entity_id, translation_key) => ({ entity_id, translation_key, device_id: "dev", platform: "autodarts" });
  const entities = [
    entity("select.board_practice_game", "practice_game"),
    entity("number.board_players", "practice_players"),
    entity("number.board_legs", "practice_legs"),
    entity("number.board_sets", "practice_sets"),
    entity("button.board_new_leg", "practice_new_leg"),
    entity("button.board_new_match", "practice_new_match"),
    entity("switch.board_double_out", "practice_double_out"),
    entity("text.board_player_1", "practice_player"),
    entity("text.board_player_2", "practice_player"),
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
      entities: [
        "select.board_practice_game",
        "number.board_players",
        "number.board_legs",
        "number.board_sets",
        "switch.board_double_out",
        "button.board_new_leg",
        "button.board_new_match",
      ],
    },
    { type: "entities", title: "Spielernamen", entities: ["text.board_player_1", "text.board_player_2"] },
  ]);
});
