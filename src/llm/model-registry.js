const DEFAULT_MODELS = Object.freeze({
  planner: process.env.AIOS_PLANNER_MODEL || process.env.AIOS_DEFAULT_MODEL || "auto",
  researcher: process.env.AIOS_RESEARCH_MODEL || process.env.AIOS_DEFAULT_MODEL || "auto",
  writer: process.env.AIOS_WRITER_MODEL || process.env.AIOS_DEFAULT_MODEL || "auto",
  reviewer: process.env.AIOS_REVIEWER_MODEL || process.env.AIOS_DEFAULT_MODEL || "auto",
  fallback: process.env.AIOS_FALLBACK_MODEL || "auto"
});

function createModelRegistry(overrides = {}) {
  const models = { ...DEFAULT_MODELS, ...overrides };
  return Object.freeze({ ...models });
}

module.exports = { createModelRegistry, DEFAULT_MODELS };
