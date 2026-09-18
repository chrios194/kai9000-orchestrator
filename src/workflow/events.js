function createWorkflowEvents(orchestrator) {
  if (!orchestrator) throw new Error("orchestrator is required");

  async function record(jobId, eventType, metadata = {}) {
    const job = await orchestrator.persistence.getJob(jobId);
    if (!job) throw new Error(`Unknown job: ${jobId}`);
    if (!eventType) throw new Error("eventType is required");

    return orchestrator.persistence.saveWorkflowEvent({
      eventId: `${job.id}:event:${Date.now()}:${Math.random().toString(36).slice(2, 8)}`,
      job,
      previousState: job.status,
      nextState: job.status,
      eventType,
      metadata
    });
  }

  return Object.freeze({ record });
}

module.exports = { createWorkflowEvents };
