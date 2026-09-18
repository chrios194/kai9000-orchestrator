function createAgentTools(orchestrator) {
  if (!orchestrator) throw new Error("orchestrator is required");

  return Object.freeze({
    listChannels: () => orchestrator.listChannels(),
    createJob: (channelId, payload) => orchestrator.createJob(channelId, payload),
    getJob: async id => orchestrator.persistence.getJob(id),
    listJobs: async channelId => orchestrator.persistence.listJobs(channelId),
    transitionJob: async (id, next) => {
      const job = await orchestrator.persistence.getJob(id);
      if (!job) throw new Error(`Unknown job: ${id}`);
      return orchestrator.advanceJob(job, next);
    },
    approveJob: (id, approvedBy) => orchestrator.approveJob(id, approvedBy),
    saveResearchSource: source => orchestrator.persistence.saveResearchSource(source),
    listResearchSources: (jobId, channelId) => orchestrator.listResearchSources(jobId, channelId),
    saveOpportunityAnalysis: item => orchestrator.persistence.saveOpportunityAnalysis(item),
    listOpportunityAnalyses: (jobId, channelId) => orchestrator.listOpportunityAnalyses(jobId, channelId),
    saveReviewReport: report => orchestrator.persistence.saveReviewReport(report),
    listReviewReports: (jobId, channelId) => orchestrator.listReviewReports(jobId, channelId),
    saveContentBrief: (jobId, brief) => orchestrator.saveContentBrief(jobId, brief),
    listContentBriefs: (jobId, channelId) => orchestrator.listContentBriefs(jobId, channelId)
  });
}

module.exports = { createAgentTools };
