# Azure DB Zone Redundancy Benchmark (azure-db-zr-bench)

A benchmarking tool to measure the **relative write-performance impact** of enabling Zone Redundancy (ZR) and High Availability (HA) modes in Azure managed databases.

## Purpose

This tool compares write performance between:

- **PostgreSQL Flexible Server**: Non-HA vs SameZone-HA vs CrossZone-HA (zone redundant)
- **MySQL Flexible Server**: Non-HA vs SameZone-HA vs CrossZone-HA (zone redundant)
- **Azure SQL Database**: Non-zone-redundant vs Zone-redundant (General Purpose tier)

The goal is **relative comparison**, not absolute benchmarks. Results help understand the performance trade-offs when enabling ZR/HA features.

## Prerequisites

- **Azure subscription** with permissions to create resources
- **Azure CLI** installed and logged in (`az login`)
- **SSH key pair** for VM access
- **jq** (for parsing deployment output)
- Sufficient quota for the chosen VM and database SKUs

### Cost Warning ⚠️

This deployment creates multiple database instances and a VM that will incur Azure charges. The default configuration uses:

- 1x Standard_D4s_v5 VM
- 3x PostgreSQL Flexible Servers (Standard_D4ds_v5)
- 3x MySQL Flexible Servers (Standard_D4ds_v5)
- 1x Azure SQL logical server with 2 databases (4 vCores each)

**Estimated cost**: ~$50-100/day depending on region. Delete resources when done!

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/arsenvlad/azure-db-zr-bench.git
cd azure-db-zr-bench
```

### 2. Deploy Infrastructure

```bash
# Set your variables
RESOURCE_GROUP="rg-zrbench"
LOCATION="centralus"
SSH_KEY="$(cat ~/.ssh/id_rsa.pub)"
DB_PASSWORD="YourSecureP@ssw0rd123!"  # Min 12 chars, complexity required

# Deploy (takes 20-30 minutes)
./scripts/deploy.sh \
    -g "$RESOURCE_GROUP" \
    -l "$LOCATION" \
    -p "$SSH_KEY" \
    -s "$DB_PASSWORD"
```

The script will:
- Create a resource group
- Deploy VNet, VM, and all database instances
- Generate a `config.generated.yaml` file with connection details
- Output the VM's public IP and SSH command

### 3. SSH into the VM

```bash
ssh benchadmin@<VM_PUBLIC_IP>
```

### 4. Set Up the Benchmark Tool

On the VM:

```bash
# Clone and install
cd /opt/benchmark
git clone https://github.com/arsenvlad/azure-db-zr-bench.git
cd azure-db-zr-bench
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 5. Copy Configuration

Copy the generated config file to the VM:

```bash
# From your local machine
scp config.generated.yaml benchadmin@<VM_PUBLIC_IP>:/opt/benchmark/azure-db-zr-bench/config.yaml
```

### 6. Run Benchmarks

On the VM:

```bash
# Activate environment
cd /opt/benchmark/azure-db-zr-bench
source .venv/bin/activate

# Set password
export DB_PASSWORD='YourSecureP@ssw0rd123!'

# List targets
azure-db-zr-bench list --config config.yaml

# Run a single target
azure-db-zr-bench run \
    --target pg-noha \
    --concurrency 4 \
    --duration 300

# Run a full suite for PostgreSQL
azure-db-zr-bench suite \
    --service postgres \
    --concurrency 1,4,16 \
    --duration 300

# Run all services
azure-db-zr-bench suite \
    --service all \
    --concurrency 1,4,16 \
    --duration 300
```

### 7. Generate Report

```bash
azure-db-zr-bench report --results results/
```

This creates:
- `results/report.html` - Interactive HTML report with charts
- `results/report.md` - Markdown summary
- `results/comparison.json` - Raw comparison data

### 8. Clean Up

```bash
# Delete all resources
./scripts/cleanup.sh -g rg-zrbench
```

## CLI Reference

### List Targets

```bash
azure-db-zr-bench list --config config.yaml
```

### Run Single Benchmark

```bash
azure-db-zr-bench run \
    --target <target-name> \
    --config config.yaml \
    --concurrency 4 \
    --duration 300 \
    --warmup 30 \
    --batch-size 1 \
    --output results/
```

Options:
- `--target, -t`: Target name from config file (required)
- `--config, -c`: Path to config file (default: config.yaml)
- `--concurrency, -n`: Number of concurrent workers (default: 4)
- `--duration, -d`: Benchmark duration in seconds (default: 300)
- `--warmup, -w`: Warmup duration in seconds (default: 30)
- `--batch-size, -b`: Rows per INSERT (default: 1)
- `--output, -o`: Output directory (default: results/)

### Run Benchmark Suite

```bash
azure-db-zr-bench suite \
    --service postgres \
    --config config.yaml \
    --concurrency 1,4,16 \
    --duration 300 \
    --warmup 30
```

Options:
- `--service, -s`: Service type (postgres, mysql, sqldb, all) (required)
- `--concurrency, -n`: Comma-separated concurrency levels (default: 1,4,16)

### Generate Report

```bash
azure-db-zr-bench report \
    --results results/ \
    --output results/
```

## Configuration File

The configuration file (`config.yaml`) defines database targets:

```yaml
targets:
  pg-noha:
    host: "pg-noha-xxx.privatelink.postgres.database.azure.com"
    port: 5432
    database: "benchmark"
    username: "benchadmin"
    password: "${DB_PASSWORD}"    # Environment variable
    service: "postgres"           # postgres, mysql, or sqldb
    mode: "no-ha"                 # no-ha, samezone-ha, crosszone-ha, non-zr, zr
    ssl_mode: "require"           # Optional: require, disable, etc.
```

Environment variable syntax:
- `${VAR_NAME}` - Required variable
- `${VAR_NAME:-default}` - Variable with default value

## Benchmark Design

### Workload

The benchmark runs a **write-heavy OLTP** workload:

1. Creates a table:
   ```sql
   CREATE TABLE benchmark_writes (
       id BIGINT AUTO_INCREMENT PRIMARY KEY,
       tenant_id INT NOT NULL,
       ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       payload VARCHAR(1024) NOT NULL
   )
   ```

2. Runs concurrent INSERT operations
3. Each write is committed immediately (explicit commits)
4. Measures latency per operation

### Metrics

For each run:
- **Throughput**: Writes per second
- **Latency**: P50, P95, P99 in milliseconds
- **Errors**: Count and rate

### Output

Results are saved to `results/<timestamp>/<target>/`:
- `result.json` - Full result with time series
- `summary.json` - Condensed metrics
- `latencies.json` - Raw latency samples for histogram

## Infrastructure Details

### Network Architecture

```
VNet (10.0.0.0/16)
├── snet-vm (10.0.1.0/24)      - Test VM
├── snet-db (10.0.2.0/24)      - PostgreSQL (delegated subnet)
├── snet-mysql (10.0.3.0/24)   - MySQL (delegated subnet)
└── snet-sql (10.0.4.0/24)     - Azure SQL private endpoint
```

### Database Instances

| Service | Name Pattern | HA Mode |
|---------|--------------|---------|
| PostgreSQL | pg-noha-* | Disabled |
| PostgreSQL | pg-szha-* | SameZone |
| PostgreSQL | pg-czha-* | ZoneRedundant |
| MySQL | mysql-noha-* | Disabled |
| MySQL | mysql-szha-* | SameZone |
| MySQL | mysql-czha-* | ZoneRedundant |
| Azure SQL | sqldb-nonzr | zoneRedundant=false |
| Azure SQL | sqldb-zr | zoneRedundant=true |

## Project Structure

```
azure-db-zr-bench/
├── infra/                      # Bicep infrastructure
│   ├── main.bicep
│   └── main.parameters.example.json
├── src/azure_db_zr_bench/      # Python package
│   ├── __init__.py
│   ├── cli.py                  # CLI entry point
│   ├── config.py               # Configuration handling
│   ├── providers.py            # Database providers
│   ├── benchmark.py            # Benchmark runner
│   └── report.py               # Report generation
├── scripts/                    # Helper scripts
│   ├── deploy.sh
│   ├── setup-vm.sh
│   ├── run-suite.sh
│   └── cleanup.sh
├── config.example.yaml         # Example configuration
├── pyproject.toml              # Python project config
└── README.md
```

## Troubleshooting

### Connection Issues

1. **From VM, verify connectivity**:
   ```bash
   # PostgreSQL
   psql "host=pg-noha-xxx.privatelink.postgres.database.azure.com port=5432 dbname=benchmark user=benchadmin password=xxx sslmode=require"
   
   # MySQL
   mysql -h mysql-noha-xxx.privatelink.mysql.database.azure.com -u benchadmin -p benchmark --ssl-mode=REQUIRED
   
   # Azure SQL
   sqlcmd -S sql-xxx.privatelink.database.windows.net -U benchadmin -P xxx -d sqldb-nonzr
   ```

2. **Check DNS resolution**:
   ```bash
   nslookup pg-noha-xxx.privatelink.postgres.database.azure.com
   ```

3. **Verify NSG rules** allow outbound traffic to DB ports (5432, 3306, 1433)

### ODBC Driver Issues

The VM cloud-init installs ODBC Driver 18. If issues persist:

```bash
# Verify installation
odbcinst -q -d

# Reinstall if needed
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo apt-get update
ACCEPT_EULA=Y sudo apt-get install -y msodbcsql18
```

### Python Environment

```bash
# Recreate venv
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

1. Follow the guidelines in [AGENTS.md](AGENTS.md)
2. Keep code simple and readable
3. Focus on correctness and repeatability
4. Update docs with any changes
