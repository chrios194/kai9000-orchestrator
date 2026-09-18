function createLiteLLMClient(options = {}) {
  const baseUrl = (options.baseUrl || process.env.LITELLM_BASE_URL || "http://localhost:4000").replace(/\/$/, "");
  const apiKey = options.apiKey || process.env.LITELLM_API_KEY || "";

  async function complete(messages, request = {}) {
    const response = await fetch(`${baseUrl}/v1/chat/completions`, {
      method: "POST",
      headers: { "content-type": "application/json", ...(apiKey ? { authorization: `Bearer ${apiKey}` } : {}) },
      body: JSON.stringify({
        model: request.model || "auto",
        messages,
        temperature: request.temperature,
        max_tokens: request.maxTokens
      })
    });
    if (!response.ok) throw new Error(`LLM request failed: ${response.status}`);
    return response.json();
  }

  return { complete };
}

module.exports = { createLiteLLMClient };
