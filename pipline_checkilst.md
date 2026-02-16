
#### Standard Data Entry Protocol

**Step 1: Prepare your files**
When new month data arrives, use the same Python scripts to convert Excel → JSON. The 3 files should be named exactly:
```
data_for_llm_enhanced.json      ← bunker loads
lab_data_for_llm.json           ← lab samples
trucking_data_for_llm.json      ← truck shipments
```

**Step 2: Place files**
```bash
# Copy to incoming folder (this overwrites the old files — that's OK!)
cp new_data_for_llm_enhanced.json data/incoming/data_for_llm_enhanced.json
cp new_lab_data_for_llm.json data/incoming/lab_data_for_llm.json
cp new_trucking_data_for_llm.json data/incoming/trucking_data_for_llm.json
```

**Step 3: Re-initialize and ingest**
```bash
# Reset database (drops old data, recreates tables)
docker exec -it mining_ops_pipeline python scripts/init_db.py

# Re-import everything
docker exec -it mining_ops_pipeline python scripts/ingest.py
```

#### ⚠️ Important: How to Handle Overlapping Data

**Current approach (simple, reliable):** Each time you update, the JSON files should contain **ALL data from the beginning** — not just the new month. So when month 11 arrives:

```
Month 10 file: rows 1-109 (what we have now)
Month 11 file: rows 1-145 (month 10 rows + new month 11 rows)
```

The pipeline does **DROP + RECREATE + REIMPORT** — so duplicates are impossible because we start fresh every time. This is the safest approach during this phase.

#### Data Entry Checklist

```
☐ 1. Export all 3 Excel files (bunker, lab, trucking) with ALL months included
☐ 2. Run Python conversion scripts to create JSON files
☐ 3. Copy JSON files to data/incoming/
☐ 4. Run: docker exec -it mining_ops_pipeline python scripts/init_db.py
☐ 5. Run: docker exec -it mining_ops_pipeline python scripts/ingest.py
☐ 6. Verify counts in terminal output
☐ 7. Refresh Metabase dashboards
☐ 8. Check Telegram for any critical alerts
```

