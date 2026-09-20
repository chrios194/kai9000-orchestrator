const test = require("node:test");
const assert = require("node:assert/strict");
const { createOrchestrator } = require("../src/workflow/orchestrator");

function mockPersistence() {
  const jobs = new Map();
  return {
    channels: new Map(),
    jobs,
    events: [],
    approvals: [],
    async saveChannel(c) { this.channels.set(c.id, { ...c }); return { ...c }; },
    async saveJob(j) { jobs.set(j.id, { ...j }); return { ...j }; },
    async getJob(id) { return jobs.get(id) ? { ...jobs.get(id) } : null; },
    async saveWorkflowEvent(e) { this.events.push(e); return e; },
    async saveApproval(a) {
      this.approvals.push(a);
      const job = jobs.get(a.job.id);
      jobs.set(a.job.id, { ...job, approvalStatus: a.status });
      return a;
    },
    async saveResearchSource(x) { return x; },
    async saveOpportunityAnalysis(x) { return x; },
    async saveReviewReport(x) { return x; },
    async saveContentBrief(x) { return x; },
    async listResearchSources() { return []; },
    async listOpportunityAnalyses() { return []; },
    async listReviewReports() { return []; },
    async listContentBriefs() { return []; }
  };
}

function mockRouter() {
  return { async complete(task, context) { return { task, channelId: context.channelId }; } };
}

test("workflow remains channel-scoped and requires approval before publishing", async () => {
  const persistence = mockPersistence();
  const orchestrator = createOrchestrator({ persistence, router: mockRouter() });
  await orchestrator.registerChannel({ id: "a", name: "A" });
  await orchestrator.registerChannel({ id: "b", name: "B" });

  const jobA = await orchestrator.createJob("a", { topic: "x" });
  assert.throws(() => orchestrator.advanceJob(jobA, "researching"), /Promise/);

  const researching = await orchestrator.advanceJob(jobA, "researching");
  const planning = await orchestrator.advanceJob(researching, "planning");
  const generating = await orchestrator.advanceJob(planning, "generating");
  const reviewing = await orchestrator.advanceJob(generating, "reviewing");

  await assert.rejects(() => orchestrator.advanceJob(reviewing, "approved"), /Promise/);
  await assert.rejects(() => orchestrator.advanceJob(reviewing, "publishing"), /Human approval is required/);

  await orchestrator.approveJob(reviewing.id, "human");
  const approved = await persistence.getJob(reviewing.id);
  assert.equal(approved.approvalStatus, "APPROVED");

  const publishedPath = await orchestrator.advanceJob(approved, "approved");
  const publishing = await orchestrator.advanceJob(publishedPath, "publishing");
  assert.equal(publishing.status, "publishing");

  await assert.rejects(
    () => orchestrator.research(jobA.id, { sourceId: "s1", channelId: "b" }),
    /Job\/channel mismatch/
  );
});

test("router requires matching channel execution context", async () => {
  const persistence = mockPersistence();
  const orchestrator = createOrchestrator({ persistence, router: mockRouter() });
  await orchestrator.registerChannel({ id: "a", name: "A" });
  const job = await orchestrator.createJob("a", {});
  const result = await orchestrator.route("hello", { jobId: job.id, channelId: "a" });
  assert.equal(result.channelId, "a");
  await assert.rejects(
    () => orchestrator.route("hello", { jobId: job.id, channelId: "b" }),
    /Execution context\/channel mismatch/
  );
});
