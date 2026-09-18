function requireChannelContext(context = {}) {
  if (!context.channelId) throw new Error("channelId is required");
  return context;
}

function createIntegrationAdapters(orchestrator, options = {}) {
  if (!orchestrator) throw new Error("orchestrator is required");

  const adapter = (name) => Object.freeze({
    name,
    configured: Boolean(options[name]),
    config: options[name] ? { ...options[name] } : {},
    async execute(input = {}, context = {}) {
      requireChannelContext(context);
      return {
        integration: name,
        status: "ready",
        channelId: context.channelId,
        input,
        configured: Boolean(options[name])
      };
    }
  });

  return Object.freeze({
    research: adapter("research"),
    generation: adapter("generation"),
    media: adapter("media"),
    publishing: adapter("publishing"),
    analytics: adapter("analytics"),
    knowledge: adapter("knowledge")
  });
}

module.exports = { createIntegrationAdapters };
