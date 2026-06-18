# Application Status Dashboard

Real-time monitoring dashboard for external service status pages.

## Features

- Monitors 7 critical services (Athena, AWS, Cloudflare, GitHub, Google Workspace, Okta, Zscaler)
- Health checks every 60 seconds
- Outage detection after 3 consecutive failures
- Slack notifications to configurable channels
- Daily heartbeat at 8:00 AM EST
- Self-monitoring with alerts
- Real-time web dashboard

## Quick Start

### Prerequisites

- Python 3.11+
- Slack Bot Token with permissions: chat:write, channels:read

### Installation

```bash
# Clone repository
git clone https://github.com/agil01/application-status-dashboard.git
cd application-status-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Slack token and settings

# Initialize database
python -m src.scripts.init_db

# Run application
python -m src.main
```

### Access Dashboard

Open browser to: http://localhost:8000

## Project Structure

```
application-status-dashboard/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── scheduler.py
│   ├── monitors/
│   ├── notifications/
│   ├── api/
│   └── static/
├── tests/
├── data/
├── logs/
└── docs/
```

## Configuration

See `.env.example` for all configuration options.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_monitors.py -v
```

## License

MIT
