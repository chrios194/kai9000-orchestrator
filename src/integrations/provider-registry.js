const PROVIDER_NAMES = Object.freeze([
  "research",
  "generation",
  "media",
  "publishing",
  "analytics",
  "knowledge"
]);

function createProviderRegistry(integrations = {}) {
  const providers = {};

  for (const name of PROVIDER_NAMES) {
    const configured = integrations[name];
    if (configured && typeof configured.execute !== "function") {
      throw new Error(`Integration provider must expose execute(): ${name}`);
    }
    providers[name] = configured || null;
  }

  async function execute(name, input = {}, context = {}) {
    if (!PROVIDER_NAMES.includes(name)) throw new Error(`Unknown integration provider: ${name}`);
    if (!providers[name]) throw new Error(`Integration provider not configured: ${name}`);
    if (!context || !context.channelId) throw new Error("channelId is required");
    return providers[name].execute(input, Object.freeze({ ...context, channelId: context.channelId }));
  }

  return Object.freeze({
    names: PROVIDER_NAMES,
    providers: Object.freeze({ ...providers }),
    execute
  });
}

module.exports = { PROVIDER_NAMES, createProviderRegistry };
