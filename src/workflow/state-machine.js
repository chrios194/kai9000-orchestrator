const STATES = Object.freeze([
  "queued",
  "researching",
  "planning",
  "generating",
  "reviewing",
  "approved",
  "publishing",
  "published",
  "failed"
]);

const TRANSITIONS = Object.freeze({
  queued: ["researching", "failed"],
  researching: ["planning", "failed"],
  planning: ["generating", "failed"],
  generating: ["reviewing", "failed"],
  reviewing: ["approved", "generating", "failed"],
  approved: ["publishing", "failed"],
  publishing: ["published", "failed"],
  published: [],
  failed: ["queued"]
});

function canTransition(from, to) {
  return STATES.includes(from) && STATES.includes(to) && TRANSITIONS[from].includes(to);
}

function transition(state, next) {
  if (!state || typeof state !== "object") throw new Error("Workflow state is required");
  if (!state.channelId) throw new Error("Workflow state channelId is required");
  const current = state.status;
  if (!STATES.includes(current)) throw new Error(`Unknown workflow state: ${current}`);
  if (!canTransition(current, next)) {
    throw new Error(`Invalid workflow transition: ${current} -> ${next}`);
  }
  return { ...state, status: next, updatedAt: new Date().toISOString() };
}

function createState(input = {}) {
  if (!input.channelId) throw new Error("channelId is required");
  if (input.payload != null && (typeof input.payload !== "object" || Array.isArray(input.payload))) {
    throw new Error("payload must be an object");
  }
  const now = new Date().toISOString();
  return {
    id: input.id || `job_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    channelId: input.channelId,
    status: "queued",
    payload: input.payload || {},
    createdAt: now,
    updatedAt: now
  };
}

module.exports = { STATES, TRANSITIONS, canTransition, transition, createState };
