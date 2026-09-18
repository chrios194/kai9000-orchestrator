const { createDbClient } = require("./client");

function createPersistence(options = {}) {
  const jobs = new Map();
  const db = options.db || createDbClient(options);
  const useNeon = options.useNeon !== false && db.configured;

  function saveChannel(channel) {
    if (useNeon) {
      return db.query(
        `INSERT INTO channels (channel_id, name, repo)
         VALUES ($1,$2,$3)
         ON CONFLICT (channel_id) DO UPDATE SET name=EXCLUDED.name, repo=EXCLUDED.repo`,
        [channel.id, channel.name || channel.id, channel.repo || `channel://${channel.id}`]
      ).then(() => channel);
    }
    return channel;
  }

  async function saveJob(job) {
    jobs.set(job.id, { ...job });
    if (useNeon) {
      await db.query(
        `INSERT INTO workflow_runs (run_id, channel_id, current_state, approval_status, created_at, updated_at)
         VALUES ($1,$2,$3,'PENDING',$4,$5)
         ON CONFLICT (run_id) DO UPDATE SET current_state=EXCLUDED.current_state, updated_at=EXCLUDED.updated_at`,
        [job.id, job.channelId, job.status, job.createdAt, job.updatedAt]
      );
    }
    return job;
  }

  async function saveWorkflowEvent({ eventId, job, previousState = null, nextState, eventType, metadata = {} }) {
    if (!useNeon) return { eventId, jobId: job.id, channelId: job.channelId };
    await db.query(
      `INSERT INTO workflow_events
       (event_id, run_id, channel_id, previous_state, next_state, event_type, metadata)
       VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb)`,
      [eventId, job.id, job.channelId, previousState, nextState, eventType, JSON.stringify(metadata)]
    );
    return { eventId, jobId: job.id, channelId: job.channelId };
  }

  async function saveApproval({ approvalId, job, status, approvedBy }) {
    if (!useNeon) return { approvalId, jobId: job.id, channelId: job.channelId, status, approvedBy };
    await db.query(
      `INSERT INTO approval_events (approval_id, run_id, channel_id, status, approved_by)
       VALUES ($1,$2,$3,$4,$5)`,
      [approvalId, job.id, job.channelId, status, approvedBy]
    );
    await db.query(
      `UPDATE workflow_runs SET approval_status=$1, updated_at=now()
       WHERE run_id=$2 AND channel_id=$3`,
      [status, job.id, job.channelId]
    );
    return { approvalId, jobId: job.id, channelId: job.channelId, status, approvedBy };
  }

  async function saveResearchSource(source) {
    if (!source || !source.sourceId || !source.jobId || !source.channelId) throw new Error("sourceId, jobId and channelId are required");
    if (!useNeon) return { ...source };
    await db.query(
      `INSERT INTO research_sources
       (source_id, run_id, channel_id, source_uri, title, source_type, provenance)
       VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb)
       ON CONFLICT (source_id) DO UPDATE SET source_uri=EXCLUDED.source_uri, title=EXCLUDED.title, source_type=EXCLUDED.source_type, provenance=EXCLUDED.provenance`,
      [source.sourceId, source.jobId, source.channelId, source.sourceUri || null, source.title || null, source.sourceType || null, JSON.stringify(source.provenance || {})]
    );
    return { ...source };
  }

  async function saveOpportunityAnalysis(item) {
    if (!item || !item.analysisId || !item.jobId || !item.channelId || item.analysis == null) throw new Error("analysisId, jobId, channelId and analysis are required");
    if (!useNeon) return { ...item };
    await db.query(
      `INSERT INTO opportunity_analysis
       (analysis_id, run_id, channel_id, analysis, provider, model)
       VALUES ($1,$2,$3,$4::jsonb,$5,$6)`,
      [item.analysisId, item.jobId, item.channelId, JSON.stringify(item.analysis), item.provider || null, item.model || null]
    );
    return { ...item };
  }

  async function saveReviewReport(report) {
    if (!report || !report.reviewId || !report.jobId || !report.channelId || !report.reviewer || !report.reviewType || report.findings == null) throw new Error("reviewId, jobId, channelId, reviewer, reviewType and findings are required");
    if (!useNeon) return { ...report };
    await db.query(
      `INSERT INTO review_reports
       (review_id, run_id, channel_id, reviewer, provider, model, review_type, findings)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8::jsonb)`,
      [report.reviewId, report.jobId, report.channelId, report.reviewer, report.provider || null, report.model || null, report.reviewType, JSON.stringify(report.findings)]
    );
    return { ...report };
  }

  async function getJob(id) {
    if (!useNeon) return jobs.get(id) || null;
    const rows = await db.query(
      'SELECT run_id AS id, channel_id AS "channelId", current_state AS status, approval_status AS "approvalStatus", created_at AS "createdAt", updated_at AS "updatedAt" FROM workflow_runs WHERE run_id=$1',
      [id]
    );
    return rows[0] || null;
  }

  async function listJobs(channelId) {
    if (!useNeon) return Array.from(jobs.values()).filter(job => !channelId || job.channelId === channelId);
    const rows = channelId
      ? await db.query('SELECT run_id AS id, channel_id AS "channelId", current_state AS status, approval_status AS "approvalStatus", created_at AS "createdAt", updated_at AS "updatedAt" FROM workflow_runs WHERE channel_id=$1 ORDER BY created_at DESC', [channelId])
      : await db.query('SELECT run_id AS id, channel_id AS "channelId", approval_status AS "approvalStatus", current_state AS status, created_at AS "createdAt", updated_at AS "updatedAt" FROM workflow_runs ORDER BY created_at DESC');
    return rows;
  }

  return { saveChannel, saveJob, saveWorkflowEvent, saveApproval, saveResearchSource, saveOpportunityAnalysis, saveReviewReport, getJob, listJobs, db, useNeon };
}

module.exports = { createPersistence };
