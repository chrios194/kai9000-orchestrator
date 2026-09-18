const { createState, transition } = require("./state-machine");
const { createPersistence } = require("../db/persistence");
const { createRouter } = require("../llm/router");

function createOrchestrator(options = {}) {
  const persistence = options.persistence || createPersistence(options);
  const router = options.router || createRouter(options);
  const channels = new Map();

  function registerChannel(channel) {
    if (!channel || !channel.id) throw new Error("channel.id is required");
    if (channels.has(channel.id)) throw new Error(`Channel already exists: ${channel.id}`);
    channels.set(channel.id, { ...channel, createdAt: new Date().toISOString() });
    return channels.get(channel.id);
  }

  function listChannels() {
    return Array.from(channels.values()).map(channel => ({ ...channel }));
  }

  function createJob(channelId, payload = {}) {
    if (!channels.has(channelId)) throw new Error(`Unknown channel: ${channelId}`);
    const state = createState({ channelId, payload });
    persistence.saveJob(state);
    return state;
  }

  function advanceJob(job, next) {
    const updated = transition(job, next);
    persistence.saveJob(updated);
    return updated;
  }

  async function route(task, context = {}) {
    return router.complete(task, context);
  }

  return { registerChannel, listChannels, createJob, advanceJob, route, persistence, router };
}

module.exports = { createOrchestrator };
