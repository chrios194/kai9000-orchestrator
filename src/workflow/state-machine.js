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
  const current = state && state.status ? state.status : "queued";
  if (!canTransition(current, next)) {
    throw new Error(`Invalid workflow transition: ${current} -> ${next}`);
  }
  return { ...state, status: next, updatedAt: new Date().toISOString() };
}

function createState(input = {}) {
  return {
    id: input.id || `job_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    channelId: input.channelId || null,
    status: "queued",
    payload: input.payload || {},
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
}

module.exports = { STATES, TRANSITIONS, canTransition, transition, createState };
