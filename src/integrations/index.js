const { createWorkflowEvents } = require("../workflow/events");
function createIntegrations(orchestrator, options = {}) {
  if (!orchestrator) throw new Error("orchestrator is required");
  return Object.freeze({
    events: createWorkflowEvents(orchestrator),
    llm: orchestrator.router,
    persistence: orchestrator.persistence,
    options: { ...options }
  });
}
module.exports = { createIntegrations };
