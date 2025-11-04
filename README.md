# Tuya Voltage Monitor

Automatically collect voltage data from Tuya smart plug energy monitors every 5 minutes and store it in a PostgreSQL database for analysis.

## Features

- 📊 Collects voltage data from Tuya smart plug energy monitors
- ⏰ Configurable collection interval (default: 5 minutes)
- 💾 Stores data in PostgreSQL for long-term analysis
- ☁️ Runs continuously on Railway (no local computer needed)
- 🔍 Indexed database for fast queries
- 📈 **Web Dashboard** with interactive graphs and filters:
  - View data by hour, day, or month
  - Filter by voltage thresholds (min/max)
  - Compare multiple devices on the same graph
  - Real-time statistics and auto-refresh

## Setup

### 1. Get Tuya API Credentials

1. Go to [Tuya IoT Platform](https://iot.tuya.com)
2. Sign in and create a Cloud Project:
   - Click "Cloud" → "Development"
   - Create a new project (choose "Smart Home" industry)
3. Note your credentials:
   - **Access ID/Client ID**
   - **Access Secret/Client Secret**
4. Link your devices:
   - Go to "Devices" → "Link Tuya App Account"
   - Link your Tuya Smart app account
   - Your devices will appear in the device list
5. Copy your **Device IDs** from the device list

### 2. Deploy to Railway

1. Push this repository to GitHub
2. Go to [Railway](https://railway.app)
3. Create a new project → "Deploy from GitHub repo"
4. Select your `tuya-voltage-monitor` repository
5. Add PostgreSQL database:
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically set the `DATABASE_URL` variable
6. Configure environment variables in Railway:
   - `TUYA_CLIENT_ID` - Your Tuya Access ID
   - `TUYA_CLIENT_SECRET` - Your Tuya Access Secret
   - `TUYA_REGION` - Your region (`us`, `eu`, or `cn`)
   - `DEVICE_IDS` - Comma-separated device IDs (e.g., `device1,device2`)
   - `COLLECTION_INTERVAL` - Optional, seconds between collections (default: 300)

### 3. Access the Dashboard

Once deployed, Railway will provide two URLs:
- **Worker Service**: Data collector (runs in background)
- **Web Service**: Dashboard at `https://your-app.up.railway.app`

Open the web URL to access the interactive dashboard with:
- Real-time voltage graphs
- Time scale filters (hour/day/month)
- Voltage threshold filters
- Device statistics

### 4. Verify Collector is Running

Check the Railway logs for the worker service to see:
```
✓ Tuya collector initialized for 2 device(s)
✓ Connected to database
✓ Database schema initialized
[2025-11-02 10:00:00] Collection #1
✓ device1: 120.5V
✓ device2: 119.8V
✓ Stored 2 reading(s)
```

## Database Schema

All timestamps are stored in **Brazilian time (GMT-3)** as naive timestamps (no timezone offset).

When you query the database, you'll see the actual Brazilian time directly, without needing to calculate timezone conversions.

```sql
CREATE TABLE voltage_readings (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,      -- Brazilian time (GMT-3)
    voltage REAL NOT NULL,
    created_at TIMESTAMP NOT NULL      -- Brazilian time (GMT-3)
);
```

## Web Dashboard

The dashboard provides an intuitive interface to visualize your voltage data:

### Features
- **Interactive Line Chart**: Visualize voltage trends over time
- **Time Scale Options**:
  - Real-time (raw data points)
  - Hourly aggregation
  - Daily aggregation
  - Monthly aggregation
- **Time Range Filters**: Last 6h, 12h, 24h, 48h, week, or month
- **Voltage Filters**: Set min/max voltage thresholds to highlight specific ranges
- **Device Filtering**: View all devices or focus on a specific one
- **Auto-refresh**: Dashboard updates every 5 minutes
- **Statistics Cards**: See average, min, max voltage and total readings per device

### API Endpoints

The dashboard uses REST API endpoints that you can also use directly:

- `GET /api/devices` - List all monitored devices
- `GET /api/stats` - Get statistics for all devices
- `GET /api/data?scale=hour&hours=24` - Get voltage data with filters

Example API query with filters:
```bash
curl "https://your-app.up.railway.app/api/data?scale=hour&hours=48&min_voltage=210&max_voltage=230"
```

## Querying Your Data Directly

You can also connect to your Railway PostgreSQL database to analyze the data:

```sql
-- Get latest readings
SELECT * FROM voltage_readings
ORDER BY timestamp DESC
LIMIT 100;

-- Average voltage by device over last 24 hours
SELECT
    device_id,
    AVG(voltage) as avg_voltage,
    MIN(voltage) as min_voltage,
    MAX(voltage) as max_voltage,
    COUNT(*) as reading_count
FROM voltage_readings
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY device_id;

-- Voltage over time
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    device_id,
    AVG(voltage) as avg_voltage
FROM voltage_readings
GROUP BY hour, device_id
ORDER BY hour DESC;
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env

# Run locally
python main.py
```

## Troubleshooting

### "No voltage data found"
- Check that your devices are energy monitoring plugs (not just switches)
- Verify device IDs are correct in Railway settings
- Some Tuya devices use different data point codes - check logs for available data

### "Connection test failed"
- Verify your Tuya API credentials
- Make sure you've linked your Tuya app account to the cloud project
- Check that TUYA_REGION matches your account region

### "Database connection failed"
- Ensure PostgreSQL database is added in Railway
- DATABASE_URL should be automatically set by Railway

## Cost Estimate

**Railway free tier**: $5/month credit
- Worker service: ~$2-3/month
- PostgreSQL: ~$1-2/month
- **Total**: Should fit within free tier for this light workload

## License

MIT
