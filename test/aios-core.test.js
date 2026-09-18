const test = require("node:test");
const assert = require("node:assert/strict");
const { createAIOS } = require("../src");

test("AIOS persists structured workflow records with channel isolation", async () => {
  const aios = createAIOS();
  await aios.registerChannel({ id: "cashvolt", name: "CashVolt" });
  await aios.registerChannel({ id: "channel-2", name: "Channel 2" });

  const first = await aios.createJob("cashvolt", { topic: "money" });
  const second = await aios.createJob("channel-2", { topic: "science" });

  assert.equal((await aios.persistence.listJobs("cashvolt")).length, 1);
  assert.equal((await aios.persistence.listJobs("channel-2")).length, 1);

  await aios.research(first.id, { channelId: "cashvolt", sourceId: "s1", title: "Money source" });
  await aios.analyzeOpportunity(first.id, { channelId: "cashvolt", analysisId: "a1", analysis: { score: 1 } });
  await aios.review(first.id, { channelId: "cashvolt", reviewId: "r1", reviewer: "system", reviewType: "quality", findings: { pass: true } });
  await aios.saveContentBrief(first.id, { channelId: "cashvolt", briefId: "b1", brief: { hook: "test" } });

  assert.equal((await aios.listResearchSources(first.id)).length, 1);
  assert.equal((await aios.listOpportunityAnalyses(first.id)).length, 1);
  assert.equal((await aios.listReviewReports(first.id)).length, 1);
  assert.equal((await aios.listContentBriefs(first.id)).length, 1);
  assert.equal((await aios.listResearchSources(second.id)).length, 0);

  await assert.rejects(
    () => aios.saveContentBrief(first.id, { channelId: "channel-2", briefId: "cross", brief: {} }),
    /Job\/channel mismatch/
  );
});
