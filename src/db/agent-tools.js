function createAgentTools(orchestrator) {
  if (!orchestrator) throw new Error("orchestrator is required");

  return Object.freeze({
    listChannels: () => orchestrator.listChannels(),
    createJob: (channelId, payload) => orchestrator.createJob(channelId, payload),
    getJob: id => orchestrator.persistence.getJob(id),
    listJobs: channelId => orchestrator.persistence.listJobs(channelId),
    transitionJob: (id, next) => {
      const job = orchestrator.persistence.getJob(id);
      if (!job) throw new Error(`Unknown job: ${id}`);
      return orchestrator.advanceJob(job, next);
    }
  });
}

module.exports = { createAgentTools };
