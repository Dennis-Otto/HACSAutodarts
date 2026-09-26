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

test("training games show their target, progress and beds to aim at", async () => {
  const { drillView, drillBeds } = await import("../../custom_components/autodarts/frontend/autodarts-card.js");
  assert.equal(drillView(undefined), null);
  assert.equal(drillView({ state: "7", attributes: { drill: "golf" } }), null);
  const clock = drillView({
    state: "7",
    attributes: { drill: "around_the_clock", progress: 6, targets: 21, darts: 9, hit_rate: 66.7, finished: false },
  });
  assert.deepEqual([clock.target, clock.progress, clock.darts, clock.hitRate], ["7", 6, 9, 66.7]);
  assert.deepEqual(drillBeds(clock), ["SI7", "SO7", "T7", "D7"]);
  assert.deepEqual(drillBeds({ ...clock, target: "BULL" }), ["Bull", "25"]);
  const doubles = drillView({ state: "D16", attributes: { drill: "doubles" } });
  assert.deepEqual(drillBeds(doubles), ["D16"]);
  const done = drillView({
    state: "unknown",
    attributes: { drill: "bobs_27", finished: true, score: 77, results: [{ completed: true }] },
  });
  assert.deepEqual([done.target, done.finished, done.completed, done.score], [null, true, true, 77]);
  assert.deepEqual(drillBeds(done), []);
  const checkout = drillView({
    state: "81",
    attributes: { drill: "checkout", remaining: 81, checkout: "T15 D18", attempt_visit: 2, attempts: 4, successes: 1, rate: 25 },
  });
  assert.deepEqual([checkout.remaining, checkout.visit, checkout.rate], [81, 2, 25]);
  assert.deepEqual(drillBeds(checkout), ["T15"]);
});

test("the training view charts practice legs per day and the practice trend", () => {
  const entity = (entity_id, translation_key) => ({ entity_id, translation_key, device_id: "dev", platform: "autodarts" });
  const entities = [
    entity("sensor.board_darts", "training_darts"),
    entity("sensor.board_practice_legs", "practice_legs_played"),
    entity("sensor.board_first_nine", "practice_first_9_average"),
    entity("sensor.board_checkout_rate", "practice_checkout_rate"),
  ];
  const hass = {
    locale: { language: "en" },
    entities: Object.fromEntries(entities.map((item) => [item.entity_id, item])),
    devices: {},
    states: {},
  };
  const training = dashboardStrategy(hass).views[1];
  const [darts, legs, trend] = training.sections[1].cards;
  assert.deepEqual(darts.entities, ["sensor.board_darts"]);
  assert.deepEqual([legs.title, legs.entities, legs.stat_types], [
    "Practice legs per day",
    ["sensor.board_practice_legs"],
    ["change"],
  ]);
  assert.deepEqual(trend.entities, ["sensor.board_first_nine", "sensor.board_checkout_rate"]);
});
