const { createDbClient } = require("../src/db/client");

const statements = [
  `create table if not exists aios_jobs (
    id text primary key,
    channel_id text not null,
    status text not null,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null,
    updated_at timestamptz not null
  )`
];

async function main() {
  const db = createDbClient();
  if (!db.configured) {
    console.log("Migration skipped: DATABASE_URL is not configured.");
    return;
  }
  for (const statement of statements) await db.query(statement);
  console.log("Migration complete.");
}

if (require.main === module) main().catch(error => { console.error(error); process.exitCode = 1; });

module.exports = { statements };
