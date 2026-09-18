function createPersistence(options = {}) {
  const jobs = new Map();
  const external = options.db || null;

  function saveJob(job) {
    jobs.set(job.id, { ...job });
    return job;
  }

  function getJob(id) {
    return jobs.get(id) || null;
  }

  function listJobs(channelId) {
    return Array.from(jobs.values()).filter(job => !channelId || job.channelId === channelId);
  }

  return { saveJob, getJob, listJobs, external };
}

module.exports = { createPersistence };
