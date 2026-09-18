function createExecutionContext(channelId, values = {}) {
  if (!channelId) throw new Error("channelId is required");
  return Object.freeze({
    ...values,
    channelId
  });
}

function assertExecutionContext(context, expectedChannelId) {
  if (!context || !context.channelId) throw new Error("channelId is required");
  if (expectedChannelId && context.channelId !== expectedChannelId) {
    throw new Error("Execution context/channel mismatch");
  }
  return context;
}

module.exports = { createExecutionContext, assertExecutionContext };
