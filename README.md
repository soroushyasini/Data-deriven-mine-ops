# Gold Mining Operations Data Platform

A comprehensive data-driven decision-making platform for gold mining supply chain operations in Iran. This system automates data ingestion, validation, analysis, and reporting for the complete mining → grinding → processing → lab analysis workflow.

## 🌟 Features

- **Automated Data Pipeline**: Convert Excel/JSON data from trucking, grinding facilities, and lab analysis
- **Persian/Farsi Support**: Full UTF-8 support with Persian text handling and Jalali calendar dates
- **Data Validation**: Real-time alerts for anomalies, quality issues, and critical thresholds
- **Complete Tracing**: Link lab results back through bunker loads to original mine shipments
- **Multi-Channel Alerts**: Telegram, Email, Dashboard, and persistent logs
- **Professional Reports**: PDF and Markdown reports for management and technical teams
- **Interactive Dashboard**: Metabase-powered analytics and visualization
- **Docker Deployment**: One-command deployment with docker-compose

## 📋 Supply Chain Flow

```
Mine (Single Source)
  ↓ [Trucking]
Grinding Facilities (3)
  • Hejazian (A) - رباط سفید
  • Shen Beton (B) - شن بتن مشهد
  • Kavian (C) - شهرک کاویان
  ↓ [Bunker Transport]
Processing Factory
  ↓ [Sampling]
Lab Analysis
  ↓ [Results]
Decision Feedback
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/soroushyasini/Data-deriven-mine-ops.git
   cd Data-deriven-mine-ops
   ```

2. **Create environment file** (optional for alerts):
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start the system**:
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**:
   ```bash
   docker-compose exec pipeline python scripts/init_db.py
   ```

5. **Access the dashboard**:
   - Open http://localhost:3000 in your browser
   - Default Metabase setup wizard will guide you

### Data Ingestion

1. **Place data files** in `data/incoming/`:
   - `trucking_data_for_llm.json` - Mine to grinding truck shipments
   - `data_for_llm_enhanced.json` - Grinding to factory bunker loads
   - `lab_data_for_llm.json` - Lab analysis results

2. **Run ingestion pipeline**:
   ```bash
   docker-compose exec pipeline python scripts/ingest.py
   ```

3. **Generate reports**:
   ```bash
   # Daily operations report
   docker-compose exec pipeline python scripts/generate_report.py daily --date 1404/10/14
   
   # Grade report for specific facility
   docker-compose exec pipeline python scripts/generate_report.py grade --facility A
   
   # All reports
   docker-compose exec pipeline python scripts/generate_report.py all
   ```

## 📁 Project Structure

```
Data-deriven-mine-ops/
├── config/                      # Configuration files (JSON)
│   ├── facilities.json         # Facility registry (A/B/C)
│   ├── drivers.json            # Driver canonical names & aliases
│   ├── trucks.json             # Truck registry
│   ├── sample_types.json       # Lab sample type definitions
│   └── validation_rules.json   # Alert thresholds
│
├── src/                        # Source code
│   ├── core/                   # Core utilities
│   │   ├── base_converter.py  # Persian text handling, date normalization
│   │   ├── validator.py       # Data validation engine
│   │   └── linker.py          # Lab → Bunker → Truck tracing
│   │
│   ├── converters/             # Data converters
│   │   ├── bunker_converter.py
│   │   ├── assay_converter.py
│   │   ├── trucking_converter.py
│   │   └── finance_converter.py
│   │
│   ├── database/               # Database layer
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── connection.py      # Database connection
│   │   └── ingestion.py       # Data loading
│   │
│   ├── reports/                # Report generators
│   │   ├── base_report.py     # Base class (PDF + Markdown)
│   │   ├── daily_ops.py       # Daily operations
│   │   └── grade_report.py    # Grade analysis
│   │
│   └── alerts/                 # Alert system
│       ├── alert_engine.py    # Core alert logic
│       ├── telegram_notifier.py
│       ├── email_notifier.py
│       └── log_notifier.py
│
├── scripts/                    # Utility scripts
│   ├── init_db.py             # Initialize database
│   ├── ingest.py              # Run ingestion pipeline
│   └── generate_report.py     # Generate reports
│
├── data/                       # Data directories
│   ├── incoming/              # Drop files here
│   ├── processed/             # Converted JSON output
│   └── samples/               # Sample data
│
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Python container
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔧 Configuration

### Facilities (config/facilities.json)

Defines the three grinding facilities with Persian and English names:

```json
{
  "A": {
    "name_fa": "حجازیان",
    "name_en": "Hejazian",
    "bunker_sheet": "رباط سفید",
    "truck_dest": "رباط سفید"
  }
}
```

### Drivers (config/drivers.json)

Canonical driver names with spelling variants:

```json
{
  "canonical_drivers": {
    "محمد احمدآبادی": {
      "aliases": ["محمد احمد آبادی", "محمد احمدآبادی"],
      "status": "active"
    }
  }
}
```

### Validation Rules (config/validation_rules.json)

Alert thresholds for different sample types and conditions:

```json
{
  "ore_input": {
    "warning_threshold_ppm": 5.0,
    "critical_threshold_ppm": 20.0
  },
  "tailings": {
    "critical_threshold_ppm": 0.2
  }
}
```

## 📊 Sample Code Format

Lab samples use a standardized code format that enables complete tracing:

```
C 1404 10 14 K2
│  │    │  │  │
│  │    │  │  └─ Sample type + number
│  │    │  │      K = Ore Input
│  │    │  │      L = Solution
│  │    │  │      T = Tailings
│  │    │  │      CR = Carbon
│  │    │  └──── Day of month
│  │    └─────── Month (Jalali)
│  └──────────── Year (Jalali, 1404)
└─────────────── Facility (A/B/C)
```

## 🚨 Alert Rules

The system monitors for:

- **Ore Input (K)**: Au > 5 ppm (warning), Au > 20 ppm (critical)
- **Tailings (T)**: Au > 0.2 ppm (critical - gold loss)
- **Return Water (RC)**: Au > 0.05 ppm (critical - circuit leak)
- **Carbon (CR)**: Au < 200 ppm (warning - exhausted)
- **Tonnage**: < 15,000 or > 32,000 kg (unusual load)
- **Data Quality**: Missing receipts, unknown drivers, invalid sample codes

## 📈 Reports

### Daily Operations Report
- Truck shipments
- Bunker loads received
- Lab samples processed
- By-facility breakdown

### Grade Report per Facility
- Au ppm statistics by sample type
- Trend analysis
- Outlier detection
- Process recommendations

### Additional Reports (Planned)
- Facility comparison
- Finance summary
- Monthly executive summary

## 🔔 Alert Channels

1. **Telegram Bot**: Real-time alerts to team chat
2. **Email**: Critical alerts and daily digest
3. **Dashboard**: Alert panel in Metabase
4. **Log File**: Persistent record in `logs/alerts.log`

### Setting Up Alerts

Edit `.env` file with your credentials:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=alerts@mining-ops.com
EMAIL_TO=manager@mining-ops.com,engineer@mining-ops.com
```

## 🗄️ Database Schema

PostgreSQL database with the following tables:

- `facilities` - Grinding facility registry
- `drivers` - Driver canonical names and aliases
- `trucks` - Truck registry
- `shipments` - Mine → Grinding truck shipments
- `bunker_loads` - Grinding → Factory bunker loads
- `lab_samples` - Lab analysis results
- `transport_costs` - Historical transport cost records
- `payments` - Driver payment tracking
- `alerts` - Alert history

## 🧪 Development

### Running Tests

```bash
pytest tests/
```

### Adding New Data Sources

1. Create converter in `src/converters/`
2. Extend database models in `src/database/models.py`
3. Update ingestion script `scripts/ingest.py`
4. Add configuration if needed

### Adding New Reports

1. Create report class in `src/reports/`
2. Inherit from `BaseReport`
3. Implement `generate_data()` and `format_markdown()`
4. Add to `scripts/generate_report.py`

## 📝 Data Quality Features

- **Persian number cleaning**: Remove commas, convert `/` to `.`
- **Date normalization**: Jalali dates to YYYY/MM/DD format
- **Driver name canonicalization**: Handle spelling variants
- **Truck number cleaning**: Remove `.0` suffix from floats
- **Cost calculation fixes**: Proper ton-based calculations
- **Null row filtering**: Automatic removal of empty rows
- **Column typo correction**: Fix known Persian typos

## 🌐 Persian/Farsi Support

All text handling uses UTF-8 encoding. The system natively supports:

- Persian column names in Excel files
- Jalali (Persian) calendar dates
- Persian driver and facility names
- Bi-directional text in reports

## 💰 Currency

The system uses Iranian Rial as the base currency:
- 1 Toman = 10 Rial
- Reports display both Rial and Toman where relevant

## 🤝 Contributing

This is a specialized platform for a specific operation. For questions or issues, please open a GitHub issue.

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built for gold mining operations in Iran, automating decision-making and replacing WhatsApp-based communication with a proper data pipeline.

## 📞 Support

For questions or support:
- Open an issue on GitHub
- Review the documentation in `/docs` (coming soon)
- Check the example data in `/data/samples`

## 🚦 Status

✅ Core data pipeline complete
✅ Database schema and ingestion
✅ Alert system with multiple channels
✅ Report generation (PDF + Markdown)
✅ Docker deployment
🚧 Advanced analytics (in progress)
🚧 Predictive modeling (planned)
🚧 Mobile app (planned)
