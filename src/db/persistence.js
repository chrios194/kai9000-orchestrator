const { createDbClient } = require("./client");

function createPersistence(options = {}) {
  const jobs = new Map();
  const db = options.db || createDbClient(options);
  const useNeon = options.useNeon !== false && db.configured;

  function saveJob(job) {
    jobs.set(job.id, { ...job });
    if (useNeon) {
      return db.query(
        `INSERT INTO workflow_runs (run_id, channel_id, current_state, approval_status, created_at, updated_at)
         VALUES ($1,$2,$3,'PENDING',$4,$5)
         ON CONFLICT (run_id) DO UPDATE SET current_state=EXCLUDED.current_state, updated_at=EXCLUDED.updated_at`,
        [job.id, job.channelId, job.status, job.createdAt, job.updatedAt]
      ).then(() => job);
    }
    return job;
  }

  async function getJob(id) {
    if (!useNeon) return jobs.get(id) || null;
    const rows = await db.query(
      'SELECT run_id AS id, channel_id AS "channelId", current_state AS status, created_at AS "createdAt", updated_at AS "updatedAt" FROM workflow_runs WHERE run_id=$1',
      [id]
    );
    return rows[0] || null;
  }

  async function listJobs(channelId) {
    if (!useNeon) return Array.from(jobs.values()).filter(job => !channelId || job.channelId === channelId);
    const rows = channelId
      ? await db.query('SELECT run_id AS id, channel_id AS "channelId", current_state AS status, created_at AS "createdAt", updated_at AS "updatedAt" FROM workflow_runs WHERE channel_id=$1 ORDER BY created_at DESC', [channelId])
      : await db.query('SELECT run_id AS id, channel_id AS "channelId", current_state AS status, created_at AS "createdAt", updated_at AS "updatedAt" FROM workflow_runs ORDER BY created_at DESC');
    return rows;
  }

  return { saveJob, getJob, listJobs, db, useNeon };
}

module.exports = { createPersistence };
