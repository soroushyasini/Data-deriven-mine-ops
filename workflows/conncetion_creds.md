## Step 1: Set Up Metabase First Time

When you opened `http://localhost:3000`, Metabase should show a **setup wizard**. Go through it:
1. Choose your language
2. Create your admin account (pick any email/password you like)
3. **When it asks "Add your data"** — you can skip for now, we'll add it manually

## Step 2: Connect `mining_ops` Database to Metabase

Once you're logged into Metabase:

1. Click the **⚙️ gear icon** (top right) → **Admin settings**
2. Go to **Databases** → click **Add database**
3. Fill in:

| Field | Value |
|---|---|
| Database type | **PostgreSQL** |
| Display name | `Mining Operations` |
| Host | `postgres` (the Docker service name, NOT localhost) |
| Port | `5432` |
| Database name | `mining_ops` |
| Username | `postgres` |
| Password | `postgres` |

4. Click **Save**

Metabase will connect and scan the tables.


