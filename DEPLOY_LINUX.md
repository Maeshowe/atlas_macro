# ATLAS MACRO - Linux Server Deployment

## Quick Start

```bash
# Clone repository
cd /home/safrtam
git clone https://github.com/Maeshowe/atlas_macro.git
cd atlas_macro

# Run deployment script
chmod +x scripts/deploy_linux.sh
./scripts/deploy_linux.sh

# Configure API keys
nano .env
```

## Systemd Setup

### 1. Install systemd files

```bash
# Daily macro diagnostic
sudo cp scripts/atlas-daily.service /etc/systemd/system/
sudo cp scripts/atlas-daily.timer /etc/systemd/system/

# Dashboard web service (port 8505)
sudo cp scripts/atlas-dashboard.service /etc/systemd/system/

sudo systemctl daemon-reload
```

### 2. Enable and start services

```bash
# Enable daily diagnostic timer
sudo systemctl enable atlas-daily.timer
sudo systemctl start atlas-daily.timer

# Enable and start dashboard
sudo systemctl enable atlas-dashboard
sudo systemctl start atlas-dashboard
```

### 3. Verify

```bash
# Check timer status
sudo systemctl status atlas-daily.timer
sudo systemctl list-timers --all | grep atlas

# Check dashboard status
sudo systemctl status atlas-dashboard

# Check logs
journalctl -u atlas-daily.service -f
journalctl -u atlas-dashboard.service -f
```

## Nginx Configuration (Multi-site)

Add to `/etc/nginx/sites-available/atlas.ssh.services`:

```nginx
server {
    listen 80;
    server_name atlas.ssh.services;

    location / {
        proxy_pass http://127.0.0.1:8505;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/atlas.ssh.services /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# SSL with certbot
sudo certbot --nginx -d atlas.ssh.services
```

## Port Allocation

| Service | Port | Domain |
|---------|------|--------|
| moneyflows | 8501 | https://moneyflows.ssh.services |
| obsidian | 8502 | https://obsidian.ssh.services |
| aurora | 8503 | https://aurora.ssh.services |
| **atlas** | **8505** | **https://atlas.ssh.services** |

## Schedule

Daily macro diagnostic runs **Mon-Fri at 21:30 UTC** (22:30 CET), after US market close.
Runs 30 minutes after OBSIDIAN to avoid API contention.

## Manual Commands

```bash
cd /home/safrtam/atlas_macro
source .venv/bin/activate

# Run daily diagnostic manually
PYTHONPATH=src python scripts/run_daily.py

# Run for specific date
PYTHONPATH=src python scripts/run_daily.py --date 2026-02-05

# JSON output (for downstream integration)
PYTHONPATH=src python scripts/run_daily.py --json

# Run with verbose logging
PYTHONPATH=src python scripts/run_daily.py -v

# Run dashboard manually (for testing)
PYTHONPATH=src streamlit run src/atlas_macro/dashboard/app.py --server.port 8505
```

## Troubleshooting

```bash
# Check logs
tail -f /home/safrtam/atlas_macro/logs/daily.log

# Force run diagnostic now
sudo systemctl start atlas-daily.service

# Restart dashboard
sudo systemctl restart atlas-dashboard

# Check last result
cat /home/safrtam/atlas_macro/data/output/atlas_$(date +%Y-%m-%d).json

# Run tests
cd /home/safrtam/atlas_macro
source .venv/bin/activate
PYTHONPATH=src python -m pytest tests/ -v
```

## Git Pull Updates

```bash
cd /home/safrtam/atlas_macro
git pull origin master
sudo systemctl restart atlas-dashboard
```
