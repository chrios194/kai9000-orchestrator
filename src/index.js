const { createOrchestrator } = require("./workflow/orchestrator");

function createAIOS(options = {}) {
  return createOrchestrator(options);
}

module.exports = { createAIOS, createOrchestrator };

if (require.main === module) {
  const orchestrator = createAIOS();
  console.log(JSON.stringify({ name: "aios-core", status: "ready", channels: orchestrator.listChannels() }));
}
