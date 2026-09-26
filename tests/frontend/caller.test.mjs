// The caller of the scoreboard: what it says, and when.
import assert from "node:assert/strict";
import { test } from "node:test";

import { callerCalls, callerState, callerText } from "../../custom_components/autodarts/frontend/autodarts-card.js";

const dart = (number, multiplier) => ({ number, multiplier });
const visit = (...darts) => ({ state: "0", attributes: { throws: darts } });
const x01 = (overrides = {}) => ({
  mode: "x01",
  practice: {
    player: 1,
    name: "Alex",
    remaining: 501,
    route: [],
    bust: false,
    won: false,
    winner: null,
    scores: [
      { player: 1, name: "Alex" },
      { player: 2, name: "Sam" },
    ],
    ...overrides,
  },
});
const all = { call_scores: true, call_checkouts: true, call_results: true, call_sounds: true };
const calls = (before, after, options = all) => callerCalls(before, after, options).map((call) => call.kind);

test("the caller waits for a first state and repeats nothing", () => {
  const state = callerState(visit(), x01());
  assert.deepEqual(callerCalls(null, state, all), []);
  assert.deepEqual(callerCalls(state, state, all), []);
});

test("the third dart calls the visit, a 180 with a fanfare", () => {
  const two = callerState(visit(dart(20, 3), dart(20, 3)), x01());
  const three = callerState(visit(dart(20, 3), dart(20, 3), dart(20, 1)), x01());
  assert.deepEqual(callerCalls(two, three, all), [{ kind: "score", score: 140 }]);
  const maximum = callerState(visit(dart(20, 3), dart(20, 3), dart(20, 3)), x01());
  assert.deepEqual(calls(two, maximum), ["score", "fanfare"]);
  assert.deepEqual(calls(two, maximum, { ...all, call_sounds: false }), ["score"]);
  assert.deepEqual(calls(two, maximum, { ...all, call_scores: false }), []);
});

test("busts, legs and the match are called once", () => {
  const before = callerState(visit(dart(20, 1)), x01());
  assert.deepEqual(calls(before, callerState(visit(dart(20, 1), dart(20, 3)), x01({ bust: true }))), ["bust"]);
  assert.deepEqual(calls(before, callerState(visit(dart(20, 2)), x01({ won: true }))), ["leg"]);
  const match = callerCalls(before, callerState(visit(dart(20, 2)), x01({ won: true, winner: 1 })), all);
  assert.deepEqual(match, [{ kind: "match", name: "Alex" }]);
  assert.deepEqual(calls(before, callerState(visit(dart(20, 1), dart(20, 3)), x01({ bust: true })), { ...all, call_results: false }), []);
});

test("the next player hears what they require", () => {
  const pulled = callerState(visit(dart(20, 3)), x01({ remaining: 141 }));
  const sam = callerState(visit(), x01({ player: 2, name: "Sam", remaining: 81, route: ["T15", "D18"] }));
  assert.deepEqual(callerCalls(pulled, sam, all), [
    { kind: "require", name: "Sam", player: 2, players: 2, remaining: 81 },
  ]);
  const far = callerState(visit(), x01({ player: 2, remaining: 301, route: [] }));
  assert.deepEqual(callerCalls(pulled, far, all), []);
  assert.deepEqual(calls(pulled, sam, { ...all, call_checkouts: false }), []);
  const cricket = { mode: "cricket", cricket: { player: 2, won: false, winner: null, scores: [] } };
  assert.deepEqual(callerCalls(pulled, callerState(visit(), cricket), all), []);
});

test("calls read like a caller in the card's language", () => {
  const t = (key) =>
    ({
      say_require: "{name}, you require {remaining}",
      say_require_alone: "You require {remaining}",
      say_bust: "No score",
      say_leg: "Game shot, and the leg!",
      say_match: "Game shot, and the match, {name}!",
      score_player: "Player",
    })[key] ?? key;
  assert.equal(callerText({ kind: "score", score: 180 }, t), "180");
  assert.equal(callerText({ kind: "require", name: "Sam", player: 2, players: 2, remaining: 81 }, t), "Sam, you require 81");
  assert.equal(callerText({ kind: "require", name: null, player: 1, players: 2, remaining: 40 }, t), "Player 1, you require 40");
  assert.equal(callerText({ kind: "require", name: "Alex", player: 1, players: 1, remaining: 40 }, t), "You require 40");
  assert.equal(callerText({ kind: "bust" }, t), "No score");
  assert.equal(callerText({ kind: "leg" }, t), "Game shot, and the leg!");
  assert.equal(callerText({ kind: "match", name: "Alex" }, t), "Game shot, and the match, Alex!");
  assert.equal(callerText({ kind: "match", name: null }, t), "Game shot, and the match!");
  assert.equal(callerText({ kind: "fanfare" }, t), "");
});
