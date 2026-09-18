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

  const event = await aios.integrations.events.record(first.id, "research.completed", { sourceCount: 1 });
  assert.equal(event.channelId, "cashvolt");
  assert.equal((await aios.listResearchSources(second.id)).length, 0);

  await assert.rejects(
    () => aios.saveContentBrief(first.id, { channelId: "channel-2", briefId: "cross", brief: {} }),
    /Job\/channel mismatch/
  );
});


test("LLM routing selects role model and rejects missing or cross-channel context", async () => {
  const calls = [];
  const client = {
    async complete(messages, request) {
      calls.push({ messages, request });
      return { ok: true, model: request.model };
    }
  };
  const aios = createAIOS({
    client,
    models: { researcher: "research-model", writer: "writer-model", fallback: "fallback-model" }
  });
  await aios.registerChannel({ id: "cashvolt", name: "CashVolt" });
  await aios.registerChannel({ id: "channel-2", name: "Channel 2" });
  const job = await aios.createJob("cashvolt", { topic: "money" });

  const result = await aios.route("research task", { channelId: "cashvolt", jobId: job.id, role: "researcher" });
  assert.equal(result.model, "research-model");
  assert.equal(calls[0].request.model, "research-model");

  await assert.rejects(
    () => aios.route("bad", { channelId: "channel-2", jobId: job.id, role: "writer" }),
    /Execution context\/channel mismatch/
  );
  await assert.rejects(
    () => aios.route("bad", { role: "writer" }),
    /channelId is required/
  );
});

test("integration adapters preserve channel context", async () => {
  const aios = createAIOS();
  const result = await aios.integrations.research.execute(
    { query: "trends" },
    { channelId: "cashvolt" }
  );
  assert.equal(result.channelId, "cashvolt");
  assert.equal(result.status, "ready");
});

test("provider registry executes configured provider with channel scope", async () => {
  const calls = [];
  const aios = createAIOS({
    integrations: {
      providers: {
        research: {
          async execute(input, context) {
            calls.push({ input, context });
            return { ok: true, channelId: context.channelId };
          }
        }
      }
    }
  });
  const result = await aios.integrations.providers.execute(
    "research",
    { query: "viral topics" },
    { channelId: "cashvolt" }
  );
  assert.deepEqual(result, { ok: true, channelId: "cashvolt" });
  assert.equal(calls[0].context.channelId, "cashvolt");
  await assert.rejects(
    () => aios.integrations.providers.execute("research", {}, {}),
    /channelId is required/
  );
  await assert.rejects(
    () => aios.integrations.providers.execute("media", {}, { channelId: "cashvolt" }),
    /not configured/
  );
});


test("workflow state validation prevents malformed jobs and illegal transitions", async () => {
  const { createState, transition } = require("../src/workflow/state-machine");
  assert.throws(() => createState(), /channelId is required/);
  assert.throws(() => createState({ channelId: "cashvolt", payload: [] }), /payload must be an object/);
  const job = createState({ channelId: "cashvolt", payload: { topic: "money" } });
  assert.equal(job.status, "queued");
  const researching = transition(job, "researching");
  assert.equal(researching.status, "researching");
  assert.throws(() => transition(researching, "published"), /Invalid workflow transition/);
  assert.throws(() => transition({ status: "queued" }, "researching"), /channelId is required/);
});

test("provider registry rejects unknown provider names", async () => {
  const aios = createAIOS();
  await assert.rejects(
    () => aios.integrations.providers.execute("unknown", {}, { channelId: "cashvolt" }),
    /Unknown integration provider/
  );
});
