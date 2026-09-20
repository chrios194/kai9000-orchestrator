const { createDbClient } = require("./client");

function createPersistence(options = {}) {
  const jobs = new Map();
  const briefs = new Map();
  const researchSources = new Map();
  const opportunityAnalyses = new Map();
  const reviewReports = new Map();
  const db = options.db || createDbClient(options);
  const useNeon = options.useNeon !== false && db.configured;

  function saveChannel(channel) {
    if (!channel || !channel.id) throw new Error("channel.id is required");
    if (useNeon) {
      return db.query(
        `INSERT INTO channels (channel_id, name, repo)
         VALUES ($1,$2,$3)
         ON CONFLICT (channel_id) DO UPDATE SET name=EXCLUDED.name, repo=EXCLUDED.repo`,
        [channel.id, channel.name || channel.id, channel.repo || `channel://${channel.id}`]
      ).then(() => ({ ...channel }));
    }
    return { ...channel };
  }

  async function saveJob(job) {
    if (!job || !job.id || !job.channelId || !job.status) throw new Error("job.id, job.channelId and job.status are required");
    if (useNeon) {
      await db.query(
        `INSERT INTO workflow_runs (run_id, channel_id, current_state, approval_status, created_at, updated_at)
         VALUES ($1,$2,$3,'PENDING',$4,$5)
         ON CONFLICT (run_id) DO UPDATE SET current_state=EXCLUDED.current_state, updated_at=EXCLUDED.updated_at`,
        [job.id, job.channelId, job.status, job.approvalStatus || "PENDING", job.createdAt, job.updatedAt]
      );
    }
    jobs.set(job.id, { ...job });
    return { ...job };
  }

  async function saveWorkflowEvent({ eventId, job, previousState = null, nextState, eventType, metadata = {} }) {
    if (!eventId || !job?.id || !job?.channelId || !nextState || !eventType) {
      throw new Error("eventId, job, nextState and eventType are required");
    }
    if (useNeon) {
      await db.query(
        `INSERT INTO workflow_events
         (event_id, run_id, channel_id, previous_state, next_state, event_type, metadata)
         VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb)`,
        [eventId, job.id, job.channelId, previousState, nextState, eventType, JSON.stringify(metadata)]
      );
    }
    return { eventId, jobId: job.id, channelId: job.channelId };
  }

  async function saveApproval({ approvalId, job, status, approvedBy }) {
    if (!approvalId || !job?.id || !job?.channelId || !status || !approvedBy) {
      throw new Error("approvalId, job, status and approvedBy are required");
    }
    if (useNeon) {
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
    }
    return { approvalId, jobId: job.id, channelId: job.channelId, status, approvedBy };
  }

  async function saveResearchSource(source) {
    if (!source || !source.sourceId || !source.jobId || !source.channelId) throw new Error("sourceId, jobId and channelId are required");
    if (useNeon) {
      await db.query(
        `INSERT INTO research_sources
         (source_id, run_id, channel_id, source_uri, title, source_type, provenance)
         VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb)
         ON CONFLICT (source_id) DO UPDATE SET source_uri=EXCLUDED.source_uri, title=EXCLUDED.title, source_type=EXCLUDED.source_type, provenance=EXCLUDED.provenance
         WHERE research_sources.run_id=EXCLUDED.run_id AND research_sources.channel_id=EXCLUDED.channel_id`,
        [source.sourceId, source.jobId, source.channelId, source.sourceUri || null, source.title || null, source.sourceType || null, JSON.stringify(source.provenance || {})]
      );
    }
    researchSources.set(source.sourceId, { ...source });
    return { ...source };
  }

  async function listResearchSources(jobId, channelId) {
    if (useNeon) {
      const rows = channelId
        ? await db.query("SELECT source_id AS \"sourceId\", run_id AS \"jobId\", channel_id AS \"channelId\", source_uri AS \"sourceUri\", title, source_type AS \"sourceType\", provenance, created_at AS \"createdAt\" FROM research_sources WHERE run_id=$1 AND channel_id=$2 ORDER BY created_at DESC", [jobId, channelId])
        : await db.query("SELECT source_id AS \"sourceId\", run_id AS \"jobId\", channel_id AS \"channelId\", source_uri AS \"sourceUri\", title, source_type AS \"sourceType\", provenance, created_at AS \"createdAt\" FROM research_sources WHERE run_id=$1 ORDER BY created_at DESC", [jobId]);
      return rows;
    }
    return Array.from(researchSources.values()).filter(item => item.jobId === jobId && (!channelId || item.channelId === channelId));
  }

  async function saveOpportunityAnalysis(item) {
    if (!item || !item.analysisId || !item.jobId || !item.channelId || item.analysis == null) throw new Error("analysisId, jobId, channelId and analysis are required");
    if (useNeon) {
      await db.query(
        `INSERT INTO opportunity_analysis
         (analysis_id, run_id, channel_id, analysis, provider, model)
         VALUES ($1,$2,$3,$4::jsonb,$5,$6)
         ON CONFLICT (analysis_id) DO UPDATE SET
           analysis=EXCLUDED.analysis,
           provider=EXCLUDED.provider,
           model=EXCLUDED.model
         WHERE opportunity_analysis.run_id=EXCLUDED.run_id AND opportunity_analysis.channel_id=EXCLUDED.channel_id`,
        [item.analysisId, item.jobId, item.channelId, JSON.stringify(item.analysis), item.provider || null, item.model || null]
      );
    }
    opportunityAnalyses.set(item.analysisId, { ...item });
    return { ...item };
  }

  async function listOpportunityAnalyses(jobId, channelId) {
    if (useNeon) {
      const rows = channelId
        ? await db.query("SELECT analysis_id AS \"analysisId\", run_id AS \"jobId\", channel_id AS \"channelId\", analysis, provider, model, created_at AS \"createdAt\" FROM opportunity_analysis WHERE run_id=$1 AND channel_id=$2 ORDER BY created_at DESC", [jobId, channelId])
        : await db.query("SELECT analysis_id AS \"analysisId\", run_id AS \"jobId\", channel_id AS \"channelId\", analysis, provider, model, created_at AS \"createdAt\" FROM opportunity_analysis WHERE run_id=$1 ORDER BY created_at DESC", [jobId]);
      return rows;
    }
    return Array.from(opportunityAnalyses.values()).filter(item => item.jobId === jobId && (!channelId || item.channelId === channelId));
  }

  async function saveReviewReport(report) {
    if (!report || !report.reviewId || !report.jobId || !report.channelId || !report.reviewer || !report.reviewType || report.findings == null) throw new Error("reviewId, jobId, channelId, reviewer, reviewType and findings are required");
    if (useNeon) {
      await db.query(
        `INSERT INTO review_reports
         (review_id, run_id, channel_id, reviewer, provider, model, review_type, findings)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8::jsonb)
         ON CONFLICT (review_id) DO UPDATE SET
           reviewer=EXCLUDED.reviewer,
           provider=EXCLUDED.provider,
           model=EXCLUDED.model,
           review_type=EXCLUDED.review_type,
           findings=EXCLUDED.findings
         WHERE review_reports.run_id=EXCLUDED.run_id AND review_reports.channel_id=EXCLUDED.channel_id`,
        [report.reviewId, report.jobId, report.channelId, report.reviewer, report.provider || null, report.model || null, report.reviewType, JSON.stringify(report.findings)]
      );
    }
    reviewReports.set(report.reviewId, { ...report });
    return { ...report };
  }

  async function listReviewReports(jobId, channelId) {
    if (useNeon) {
      const rows = channelId
        ? await db.query("SELECT review_id AS \"reviewId\", run_id AS \"jobId\", channel_id AS \"channelId\", reviewer, provider, model, review_type AS \"reviewType\", findings, created_at AS \"createdAt\" FROM review_reports WHERE run_id=$1 AND channel_id=$2 ORDER BY created_at DESC", [jobId, channelId])
        : await db.query("SELECT review_id AS \"reviewId\", run_id AS \"jobId\", channel_id AS \"channelId\", reviewer, provider, model, review_type AS \"reviewType\", findings, created_at AS \"createdAt\" FROM review_reports WHERE run_id=$1 ORDER BY created_at DESC", [jobId]);
      return rows;
    }
    return Array.from(reviewReports.values()).filter(item => item.jobId === jobId && (!channelId || item.channelId === channelId));
  }

  async function saveContentBrief(brief) {
    if (!brief || !brief.briefId || !brief.jobId || !brief.channelId || brief.brief == null) throw new Error("briefId, jobId, channelId and brief are required");
    if (useNeon) {
      await db.query(
        `INSERT INTO content_briefs (brief_id, run_id, channel_id, brief)
         VALUES ($1,$2,$3,$4::jsonb)
         ON CONFLICT (brief_id) DO UPDATE SET brief=EXCLUDED.brief
         WHERE content_briefs.run_id=EXCLUDED.run_id AND content_briefs.channel_id=EXCLUDED.channel_id`,
        [brief.briefId, brief.jobId, brief.channelId, JSON.stringify(brief.brief)]
      );
    }
    briefs.set(brief.briefId, { ...brief });
    return { ...brief };
  }

  async function listContentBriefs(jobId, channelId) {
    if (useNeon) {
      const rows = channelId
        ? await db.query("SELECT brief_id AS \"briefId\", run_id AS \"jobId\", channel_id AS \"channelId\", brief, created_at AS \"createdAt\" FROM content_briefs WHERE run_id=$1 AND channel_id=$2 ORDER BY created_at DESC", [jobId, channelId])
        : await db.query("SELECT brief_id AS \"briefId\", run_id AS \"jobId\", channel_id AS \"channelId\", brief, created_at AS \"createdAt\" FROM content_briefs WHERE run_id=$1 ORDER BY created_at DESC", [jobId]);
      return rows;
    }
    return Array.from(briefs.values()).filter(item => item.jobId === jobId && (!channelId || item.channelId === channelId));
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
      : await db.query('SELECT run_id AS id, channel_id AS "channelId", approval_status AS "approvalStatus", current_state AS status, created_at AS "createdAt", updated_at AS "updatedAt" FROM workflow_runs ORDER BY created_at DESC', []);
    return rows;
  }

  return {
    saveChannel, saveJob, saveWorkflowEvent, saveApproval,
    saveResearchSource, listResearchSources,
    saveOpportunityAnalysis, listOpportunityAnalyses,
    saveReviewReport, listReviewReports,
    saveContentBrief, listContentBriefs,
    getJob, listJobs, db, useNeon
  };
}

module.exports = { createPersistence };
