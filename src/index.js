const { createOrchestrator } = require("./workflow/orchestrator");
const { createIntegrations } = require("./integrations");

function createAIOS(options = {}) {
  const orchestrator = createOrchestrator(options);
  const integrations = createIntegrations(orchestrator, options.integrations || {});
  return Object.assign(orchestrator, { integrations });
}

module.exports = { createAIOS, createOrchestrator };

if (require.main === module) {
  const orchestrator = createAIOS();
  console.log(JSON.stringify({ name: "aios-core", status: "ready", channels: orchestrator.listChannels() }));
}
