function requireChannelContext(context = {}) {
  if (!context.channelId) throw new Error("channelId is required");
  return context;
}

function createIntegrationAdapters(orchestrator, options = {}) {
  if (!orchestrator) throw new Error("orchestrator is required");

  const adapter = (name) => {
    const configured = options[name];
    if (configured && typeof configured !== "object" && typeof configured !== "function") {
      throw new Error(`Integration config must be an object or function: ${name}`);
    }
    return Object.freeze({
      name,
      configured: Boolean(configured),
      config: configured && typeof configured === "object" ? { ...configured } : {},
      async execute(input = {}, context = {}) {
        requireChannelContext(context);
        if (configured && typeof configured.execute === "function") {
          return configured.execute(input, Object.freeze({ ...context, channelId: context.channelId }));
        }
        if (typeof configured === "function") {
          return configured(input, Object.freeze({ ...context, channelId: context.channelId }));
        }
        return {
          integration: name,
          status: "unconfigured",
          channelId: context.channelId,
          input,
          configured: false
        };
      }
    });
  };

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
