const { createState, transition } = require("./state-machine");
const { createPersistence } = require("../db/persistence");
const { createRouter } = require("../llm/router");
const { assertExecutionContext } = require("./execution-context");

function createOrchestrator(options = {}) {
  const persistence = options.persistence || createPersistence(options);
  const router = options.router || createRouter(options);
  const channels = new Map();

  async function registerChannel(channel) {
    if (!channel || !channel.id) throw new Error("channel.id is required");
    if (channels.has(channel.id)) throw new Error(`Channel already exists: ${channel.id}`);
    const stored = { ...channel, createdAt: new Date().toISOString() };
    await persistence.saveChannel(stored);
    channels.set(channel.id, stored);
    return { ...stored };
  }

  function listChannels() {
    return Array.from(channels.values()).map(channel => ({ ...channel }));
  }

  function assertJobChannel(job, channelId) {
    if (!job || !channelId || job.channelId !== channelId) throw new Error("Job/channel mismatch");
  }

  async function createJob(channelId, payload = {}) {
    if (!channels.has(channelId)) throw new Error(`Unknown channel: ${channelId}`);
    const state = createState({ channelId, payload });
    await persistence.saveJob(state);
    await persistence.saveWorkflowEvent({
      eventId: `${state.id}:queued`,
      job: state,
      nextState: state.status,
      eventType: "job.created",
      metadata: { payloadKeys: Object.keys(payload) }
    });
    return state;
  }

  async function advanceJob(job, next) {
    if (!job || !job.id) throw new Error("job.id is required");
    const stored = await persistence.getJob(job.id);
    if (!stored) throw new Error(`Unknown job: ${job.id}`);
    assertJobChannel(stored, job.channelId);
    if (stored.status !== job.status) throw new Error("Stale job state");
    if (next === "publishing" && stored.approvalStatus !== "APPROVED") {\n      throw new Error("Human approval is required before publishing");\n    }\n    const updated = transition(stored, next);
    await persistence.saveJob(updated);
    await persistence.saveWorkflowEvent({
      eventId: `${updated.id}:${updated.updatedAt}`,
      job: updated,
      previousState: job.status,
      nextState: updated.status,
      eventType: "job.transitioned"
    });
    return updated;
  }

  async function approveJob(jobId, approvedBy) {
    if (!approvedBy) throw new Error("approvedBy is required");
    const job = await persistence.getJob(jobId);
    if (!job) throw new Error(`Unknown job: ${jobId}`);
    if (job.status !== "reviewing") throw new Error("Only reviewing jobs can be approved");
    await persistence.saveApproval({
      approvalId: `${job.id}:approval:${Date.now()}`,
      job,
      status: "APPROVED",
      approvedBy
    });
    return advanceJob(job, "approved");
  }

  async function route(task, context = {}) {
    if (context.jobId) {
      const job = await persistence.getJob(context.jobId);
      if (!job) throw new Error(`Unknown job: ${context.jobId}`);
      assertExecutionContext(context, job.channelId);
    } else {
      assertExecutionContext(context);
    }
    return router.complete(task, context);
  }

  async function research(jobId, source) {
    if (!source || !source.channelId) throw new Error("source.channelId is required");
    const job = await persistence.getJob(jobId);
    assertJobChannel(job, source.channelId);
    return persistence.saveResearchSource({ ...source, jobId });
  }

  async function analyzeOpportunity(jobId, item) {
    if (!item || !item.channelId) throw new Error("item.channelId is required");
    const job = await persistence.getJob(jobId);
    assertJobChannel(job, item.channelId);
    return persistence.saveOpportunityAnalysis({ ...item, jobId });
  }

  async function review(jobId, report) {
    if (!report || !report.channelId) throw new Error("report.channelId is required");
    const job = await persistence.getJob(jobId);
    assertJobChannel(job, report.channelId);
    return persistence.saveReviewReport({ ...report, jobId });
  }

  async function saveContentBrief(jobId, brief) {
    if (!brief || !brief.channelId) throw new Error("brief.channelId is required");
    const job = await persistence.getJob(jobId);
    assertJobChannel(job, brief.channelId);
    return persistence.saveContentBrief({ ...brief, jobId });
  }

  async function listResearchSources(jobId, channelId) {
    const job = await persistence.getJob(jobId);
    if (!job) throw new Error(`Unknown job: ${jobId}`);
    assertJobChannel(job, channelId || job.channelId);
    return persistence.listResearchSources(jobId, job.channelId);
  }

  async function listOpportunityAnalyses(jobId, channelId) {
    const job = await persistence.getJob(jobId);
    if (!job) throw new Error(`Unknown job: ${jobId}`);
    assertJobChannel(job, channelId || job.channelId);
    return persistence.listOpportunityAnalyses(jobId, job.channelId);
  }

  async function listReviewReports(jobId, channelId) {
    const job = await persistence.getJob(jobId);
    if (!job) throw new Error(`Unknown job: ${jobId}`);
    assertJobChannel(job, channelId || job.channelId);
    return persistence.listReviewReports(jobId, job.channelId);
  }

  async function listContentBriefs(jobId, channelId) {
    const job = await persistence.getJob(jobId);
    if (!job) throw new Error(`Unknown job: ${jobId}`);
    assertJobChannel(job, channelId || job.channelId);
    return persistence.listContentBriefs(jobId, job.channelId);
  }

  return {
    registerChannel, listChannels, createJob, advanceJob, approveJob, route,
    research, analyzeOpportunity, review, saveContentBrief,
    listResearchSources, listOpportunityAnalyses, listReviewReports, listContentBriefs,
    persistence, router
  };
}

module.exports = { createOrchestrator };
