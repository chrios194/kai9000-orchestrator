function createProviderRegistry(integrations = {}) {
  const names = ["research", "generation", "media", "publishing", "analytics", "knowledge"];
  const providers = {};

  for (const name of names) {
    const configured = integrations[name];
    if (configured && typeof configured.execute !== "function") {
      throw new Error(`Integration provider must expose execute(): ${name}`);
    }
    providers[name] = configured || null;
  }

  async function execute(name, input = {}, context = {}) {
    if (!providers[name]) throw new Error(`Integration provider not configured: ${name}`);
    if (!context.channelId) throw new Error("channelId is required");
    return providers[name].execute(input, context);
  }

  return Object.freeze({ providers: Object.freeze({ ...providers }), execute });
}

module.exports = { createProviderRegistry };
