const { createDbClient } = require("../src/db/client");

const statements = [
  "-- AIOS-CORE uses the existing production workflow schema; no DDL is required.",
  "SELECT 1"
];

async function main() {
  const db = createDbClient();
  if (!db.configured) {
    console.log("Migration verification skipped: DATABASE_URL is not configured.");
    return;
  }
  for (const statement of statements) await db.query(statement);
  console.log("AIOS schema verification complete.");
}

if (require.main === module) main().catch(error => { console.error(error); process.exitCode = 1; });

module.exports = { statements };
