# Quick Start Guide

Get the Gold Mining Operations Data Platform running in 5 minutes!

## Prerequisites

- Docker Desktop installed
- 4GB RAM minimum
- 10GB disk space

## Step 1: Clone and Start (2 minutes)

```bash
# Clone repository
git clone https://github.com/soroushyasini/Data-deriven-mine-ops.git
cd Data-deriven-mine-ops

# Start all services
docker-compose up -d
```

Wait for all containers to start (check with `docker-compose ps`).

## Step 2: Initialize Database (1 minute)

```bash
# Initialize database schema and load configuration
docker-compose exec pipeline python scripts/init_db.py
```

You should see:
```
✓ Database tables created
✓ Loaded 3 facilities
✓ Loaded 3 drivers
```

## Step 3: Generate Sample Data (30 seconds)

```bash
# Create sample data files
docker-compose exec pipeline python scripts/create_sample_data.py

# Copy to incoming directory
docker-compose exec pipeline cp data/samples/*.json data/incoming/
```

## Step 4: Run Ingestion Pipeline (1 minute)

```bash
# Process all data
docker-compose exec pipeline python scripts/ingest.py
```

You should see:
```
✓ Converted 3 truck shipments
✓ Converted 3 bunker loads
✓ Converted 7 lab samples
✓ Generated X alerts
✓ Loaded data into database
```

## Step 5: Generate Reports (30 seconds)

```bash
# Generate all reports
docker-compose exec pipeline python scripts/generate_report.py all --date 1404/10/14
```

Reports are saved in `reports_output/` directory.

## Step 6: Access Dashboard

Open your browser and go to:
```
http://localhost:3000
```

Follow the Metabase setup wizard:
1. Create admin account
2. Connect to database:
   - Database type: PostgreSQL
   - Host: `postgres`
   - Port: `5432`
   - Database: `mining_ops`
   - Username: `postgres`
   - Password: `postgres`

## Verify Everything Works

```bash
# Check logs
docker-compose logs -f pipeline

# Run tests
docker-compose exec pipeline pytest tests/ -v

# View alerts
docker-compose exec pipeline cat logs/alerts.log
```

## Next Steps

1. **Add Real Data**: Place your Excel/JSON files in `data/incoming/`
2. **Configure Alerts**: Edit `.env` file with Telegram/Email credentials
3. **Explore Dashboard**: Create charts and dashboards in Metabase
4. **Schedule Jobs**: Set up cron jobs for automatic daily ingestion

## Common Commands

```bash
# Stop all services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f [service_name]

# Access database
docker-compose exec postgres psql -U postgres -d mining_ops

# Run Python shell
docker-compose exec pipeline python

# Clean everything (WARNING: deletes data)
docker-compose down -v
```

## Troubleshooting

### Database connection error
```bash
# Wait for database to be ready
docker-compose exec postgres pg_isready -U postgres
```

### Permission issues
```bash
# Fix permissions on Linux
sudo chown -R $USER:$USER data/ logs/ reports_output/
```

### Missing Python packages
```bash
# Rebuild pipeline container
docker-compose build pipeline
```

## Getting Help

- Check `README.md` for detailed documentation
- Review `CONTRIBUTING.md` for development guide
- Open an issue on GitHub
- Check logs: `docker-compose logs -f`

## Success! 🎉

You now have a fully functional data platform for gold mining operations!

Next, customize it for your specific needs by:
- Adding your actual data files
- Configuring alert channels
- Creating custom reports
- Building dashboards in Metabase
