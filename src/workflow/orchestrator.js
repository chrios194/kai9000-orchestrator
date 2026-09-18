const { createState, transition } = require("./state-machine");
const { createPersistence } = require("../db/persistence");
const { createRouter } = require("../llm/router");

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
    const updated = transition(job, next);
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
    return router.complete(task, context);
  }

  async function research(jobId, source) {
    const job = await persistence.getJob(jobId);
    assertJobChannel(job, source.channelId);
    return persistence.saveResearchSource({ ...source, jobId });
  }

  async function analyzeOpportunity(jobId, item) {
    const job = await persistence.getJob(jobId);
    assertJobChannel(job, item.channelId);
    return persistence.saveOpportunityAnalysis({ ...item, jobId });
  }

  async function review(jobId, report) {
    const job = await persistence.getJob(jobId);
    assertJobChannel(job, report.channelId);
    return persistence.saveReviewReport({ ...report, jobId });
  }

  return { registerChannel, listChannels, createJob, advanceJob, approveJob, route, research, analyzeOpportunity, review, persistence, router };
}

module.exports = { createOrchestrator };
