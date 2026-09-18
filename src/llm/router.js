const { createLiteLLMClient } = require("./litellm-client");

function createRouter(options = {}) {
  const client = options.client || createLiteLLMClient(options);
  const model = options.model || process.env.AIOS_DEFAULT_MODEL || "auto";

  async function complete(task, context = {}) {
    const messages = [
      { role: "system", content: context.system || "You are the AIOS orchestration router. Return concise, structured work output." },
      { role: "user", content: typeof task === "string" ? task : JSON.stringify(task) }
    ];
    return client.complete(messages, { model, ...context.request });
  }

  return { complete, model };
}

module.exports = { createRouter };
