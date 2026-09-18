const { createWorkflowEvents } = require("../workflow/events");
const { createIntegrationAdapters } = require("./adapters");
const { createProviderRegistry } = require("./provider-registry");

function createIntegrations(orchestrator, options = {}) {
  if (!orchestrator) throw new Error("orchestrator is required");
  const adapters = createIntegrationAdapters(orchestrator, options);
  const providers = createProviderRegistry(options.providers || {});
  return Object.freeze({
    events: createWorkflowEvents(orchestrator),
    llm: orchestrator.router,
    persistence: orchestrator.persistence,
    research: adapters.research,
    generation: adapters.generation,
    media: adapters.media,
    publishing: adapters.publishing,
    analytics: adapters.analytics,
    knowledge: adapters.knowledge,
    providers,
    options: { ...options }
  });
}

module.exports = { createIntegrations };
