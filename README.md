# Fincube Performance Testing and Visualization: k6 + InfluxDB + Grafana

This guide walks you through installing [k6](https://k6.io/), running performance tests, sending results to [InfluxDB](https://www.influxdata.com/), and visualizing your metrics in [Grafana](https://grafana.com/).

---

## 1. Install k6

**On Linux/macOS:**

```sh
sudo gpg -k

sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69

echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list

sudo apt-get update

sudo apt-get install k6
```

---

## 2. Install InfluxDB

Setup InfluxDB via Docker:

```sh
docker run -d \
  -p 8086:8086 \
  -e INFLUXDB_DB=k6 \
  --name influxdb \
  influxdb:1.8
```

- **Port 8086** is InfluxDB’s default API port.
- **INFLUXDB_DB=k6** creates a database named `k6`.

---

## 3. Install Grafana

Setup Grafana via Docker:

```sh
docker run -d -p 5000:3000 --name=grafana grafana/grafana
```

- Grafana will be available at [http://localhost:5000](http://localhost:5000).

---

## 5. Run k6 and Output to InfluxDB

Run your test using any of the scripts from the repository and send results to InfluxDB:

```sh
k6 run --out influxdb=http://localhost:8086/k6 <script_file>
```

---

## 6. Set Up Grafana Data Source

1. Open Grafana at [http://localhost:5000](http://localhost:5000).
2. Log in (`admin` / `admin` by default).
3. Go to **Settings** → **Data Sources** → **Add data source**.
4. Select **InfluxDB**.
5. Set:
   - **URL:** `http://host.docker.internal:8086`
   - **Database:** `k6`
   - **User/Password:** leave blank

Click **Save & Test**.

---

## 7. Import k6 Grafana Dashboard

1. In Grafana, go to **Dashboards → Import**.
2. Paste the JSON object from the `primary-dashboard.json` file of the repository
3. Click **Load**.
4. Select your InfluxDB data source and import.

---

## 8. Visualize and Analyze

- Run more k6 tests; Grafana will auto-update.
- You can customize panels, add new queries, or create your own dashboards.

---

## 9. Onchain Sync Success Rate Analysis

### Overview

This repository includes comprehensive Python-based analysis tools to evaluate the success rates of onchain synchronization for the audit trail service.

### Success Criteria

- **Confirmation Source Success**: `confirmation_source != "pending_source"`
- **Transaction Confirmation Trace Success**: `transaction_confirmation_trace IS NOT NULL`

### Running the Analysis

```sh
python3 analysis/compare_success_rates.py --input transactions.csv --outdir reports
```

### Generated Reports

The analysis generates:

- **4 High-Quality Visualizations** (PNG, 300 DPI)
  - Success Rate Comparison
  - Sync Duration Analysis
  - Transaction Trace Analysis
  - Advanced Performance Metrics
- **4 CSV Reports** with detailed metrics
- **1 JSON Report** with complete results
- **Comprehensive Analysis Report** (Markdown)

### Key Metrics Tracked

- Overall success rates (confirmation source vs transaction trace)
- Sync duration statistics and distributions
- Service-level trace analysis
- Time-based performance patterns
- Source-specific success rates

### Documentation

- 📊 [Full Analysis Report](reports/ANALYSIS_REPORT.md)
- 📈 [Visualization Guide](reports/VISUALIZATION_GUIDE.md)

---

## Useful Links

- [k6 Documentation](https://k6.io/docs/)
- [InfluxDB Documentation](https://docs.influxdata.com/influxdb/v1.8/)
- [Grafana Documentation](https://grafana.com/docs/)
- [k6 Official Grafana Dashboard](https://grafana.com/grafana/dashboards/2587-k6-load-testing-results/)
