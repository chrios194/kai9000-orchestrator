const test = require("node:test");
const assert = require("node:assert/strict");
const { createAIOS } = require("../src");
const { canTransition } = require("../src/workflow/state-machine");

test("AIOS creates isolated channel jobs", async () => {
  const aios = createAIOS();
  aios.registerChannel({ id: "cashvolt", name: "CashVolt" });
  aios.registerChannel({ id: "channel-2", name: "Channel 2" });

  const first = await aios.createJob("cashvolt", { topic: "money" });
  const second = await aios.createJob("channel-2", { topic: "science" });

  assert.equal(first.channelId, "cashvolt");
  assert.equal(second.channelId, "channel-2");
  assert.equal((await aios.persistence.listJobs("cashvolt")).length, 1);
  assert.equal((await aios.persistence.listJobs("channel-2")).length, 1);
});

test("workflow transitions are explicit", () => {
  assert.equal(canTransition("queued", "researching"), true);
  assert.equal(canTransition("queued", "published"), false);
});
