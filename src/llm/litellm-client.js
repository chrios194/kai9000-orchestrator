function createLiteLLMClient(options = {}) {
  const baseUrl = (options.baseUrl || process.env.LITELLM_BASE_URL || "http://localhost:4000").replace(/\/$/, "");
  const apiKey = options.apiKey || process.env.LITELLM_API_KEY || "";
  const timeoutMs = Number(options.timeoutMs || process.env.LITELLM_TIMEOUT_MS || 60000);

  async function complete(messages, request = {}) {
    if (!Array.isArray(messages) || messages.length === 0) throw new Error("messages are required");
    if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) throw new Error("LLM timeout must be a positive number");

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    const body = {
      model: request.model || "auto",
      messages
    };
    if (request.temperature !== undefined) body.temperature = request.temperature;
    if (request.maxTokens !== undefined) body.max_tokens = request.maxTokens;

    try {
      const response = await fetch(`${baseUrl}/v1/chat/completions`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          ...(apiKey ? { authorization: `Bearer ${apiKey}` } : {})
        },
        body: JSON.stringify(body),
        signal: controller.signal
      });

      const text = await response.text();
      let payload = null;
      if (text) {
        try {
          payload = JSON.parse(text);
        } catch {
          payload = { raw: text };
        }
      }

      if (!response.ok) {
        const detail = payload?.error?.message || payload?.message || payload?.raw || "unknown error";
        throw new Error(`LLM request failed: ${response.status} ${detail}`);
      }

      return payload || {};
    } catch (error) {
      if (error?.name === "AbortError") {
        throw new Error(`LLM request timed out after ${timeoutMs}ms`);
      }
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }

  return { complete };
}

module.exports = { createLiteLLMClient };
