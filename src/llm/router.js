const { createLiteLLMClient } = require("./litellm-client");
const { createModelRegistry } = require("./model-registry");

function createRouter(options = {}) {
  const client = options.client || createLiteLLMClient(options);
  const registry = createModelRegistry(options.models || {});
  const defaultRole = options.defaultRole || "writer";

  if (!registry[defaultRole]) throw new Error(`Unknown default LLM role: ${defaultRole}`);

  async function complete(task, context = {}) {
    if (!context || !context.channelId) throw new Error("channelId is required");
    const role = context.role || defaultRole;
    const model = context.model || context.request?.model || registry[role] || registry.fallback;
    if (!model) throw new Error(`No model configured for role: ${role}`);
    const request = context.request && typeof context.request === "object" ? context.request : {};
    const messages = [
      {
        role: "system",
        content: context.system || "You are the AIOS orchestration router. Return concise, structured work output."
      },
      {
        role: "user",
        content: typeof task === "string" ? task : JSON.stringify(task)
      }
    ];
    return client.complete(messages, { ...request, model });
  }

  return { complete, model: registry[defaultRole], registry };
}

module.exports = { createRouter };
