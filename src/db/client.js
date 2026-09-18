function createDbClient(options = {}) {
  const connectionString = options.connectionString || process.env.DATABASE_URL || null;
  return {
    connectionString,
    configured: Boolean(connectionString),
    async query(text, params = []) {
      if (!connectionString) throw new Error("DATABASE_URL is not configured");
      const { neon } = require("@neondatabase/serverless");
      const sql = neon(connectionString);
      return sql.query(text, params);
    }
  };
}

module.exports = { createDbClient };
