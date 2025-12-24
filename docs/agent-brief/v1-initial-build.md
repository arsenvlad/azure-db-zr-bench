## Reference Agent Prompt (v1)

You are a coding agent. Build a Python project called `azure-db-zr-bench` that provisions Azure database infrastructure and runs write-focused benchmarks to measure the performance impact of enabling Zone Redundancy / cross-zone HA.

High-level goal

- Measure relative write performance between:
  - PostgreSQL Flexible Server: Non-HA vs SameZone-HA vs CrossZone-HA (zone redundant HA)
  - MySQL Flexible Server: Non-HA vs SameZone-HA vs CrossZone-HA (zone redundant HA)
  - Azure SQL Database (General Purpose, and later maybe Premium, Business Critical and other tiers): Non-zone-redundant vs zone-redundant (as supported for the SKU/region)
- The purpose is relative comparison (ZR vs non-ZR and HA modes), not absolute “world-record” numbers.
- The code should run from a test VM located in the same VNet as the databases in the `centralus` region (parameterize region)

Repo structure requirements

1) One GitHub repo: `azure-db-zr-bench`
2) Include:
   - README with short instructions
   - `infra/` folder with Bicep files to deploy everything
   - `src/` for the Python package
   - `scripts/` helper scripts for setup/run
   - `results/` output folder (gitignored) for benchmark outputs and generated reports

Infrastructure requirements (Bicep)
Deploy in `centralus`. Everything should be in one resource group.

Networking

- Create one VNet with at least 2 subnets:
  - `db-subnet` for DB private endpoints or delegated subnets where applicable
  - `vm-subnet` for the test VM
- Since this is test only, configure connectivity and authentication in the simplest way possible (not production grade)
- Configure NSGs to allow the VM to reach DB ports:
  - PostgreSQL 5432, MySQL 3306, SQL 1433
Test VM
- Create a Linux VM in the same VNet (Ubuntu LTS) with:
  - A public IP for SSH access
  - User Assigned Managed identity assigned to the VM just in case it is helpful
  - Cloud-init or Customer Linux Script extension to install prerequisites:
    - Python 3.11+ (or 3.10 if needed), pip, git
    - DB client libs/tools helpful for debugging (psql/mysql/sqlcmd optional)
    - Azure CLI (optional, but helpful)
  - Optionally install `poetry` or use `venv`
Databases
Create the following resources with predictable names to identify “mode”:
- PostgreSQL Flexible Server:
  - Deploy 3 variants:
    1) Non-HA (single server)
    2) SameZone-HA (HA enabled but same zone)
    3) CrossZone-HA / Zone redundant HA
- MySQL Flexible Server:
  - Deploy 3 variants:
    1) Non-HA
    2) SameZone-HA
    3) CrossZone-HA / Zone redundant HA
  - Note: treat these as separate servers because MySQL does not allow changing HA mode after creation (assume immutable).
- Azure SQL Database (General Purpose):
  - Deploy two DBs or two logical configurations:
    - Non-ZR version
    - ZR version
  - Use one logical server (or two if required by constraints) and two databases with clear naming.

DB configuration

- Use parameters for admin usernames/passwords (secure parameters).
- Choose reasonable defaults for SKU/compute that are not small (avoid “too small to measure”), but keep cost controlled. Parameterize the sizes/SKUs.
- Ensure that test VM is able to connect to the databases

Python app requirements

Core behavior

- Provide a CLI entrypoint: `azure-db-zr-bench` (or `python -m azure_db_zr_bench`)
- The CLI should be able to:
  1) List available deployed targets from a config file (not by discovering Azure resources)
  2) Run a write benchmark against a chosen target

Config

- Store connection info in a config file (YAML or JSON), with placeholders and examples:
  - host, port, dbname, username, password
  - service type: postgres/mysql/sqldb
  - mode: no-ha/samezone-ha/crosszone-ha, non-zr/zr
- Do NOT hardcode secrets; allow env var overrides for passwords.

Benchmark design (keep it simple and write-focused)

- Focus on write operations since reads shouldn’t be materially impacted by ZR.
- Implement one primary scenario: “OLTP write-heavy”
  - Create a table like:
    - id (bigint auto-increment / identity)
    - tenant_id (int)
    - ts (timestamp)
    - payload (varchar/text ~ 256-1024 bytes)
  - Workload:
    - Batched INSERTs or single-row INSERTs (pick one; document which)
    - Optional UPDATE workload (secondary scenario), but INSERT-only is fine for v1.
- Concurrency:
  - Support configurable concurrency (e.g., 1, 4, 16, 64) and duration (e.g., 5 min)
  - Include warm-up time (e.g., 30-60 seconds) and exclude it from summary stats
Metrics to capture
- For each run:
  - throughput: writes/sec
  - latency: p50, p95, p99 for write operations
  - error count and error rate
- Output raw samples if feasible; otherwise output aggregated metrics plus a small time-series.
- Save results as JSON in `results/<timestamp>/<target>/result.json` and also a `summary.json`.

Reporting

- Generate a simple HTML report (static) and/or Markdown summary that compares:
  - Postgres: Non-HA vs SameZone-HA vs CrossZone-HA
  - MySQL: Non-HA vs SameZone-HA vs CrossZone-HA
  - SQL GP: non-ZR vs ZR
- Include deltas (% change) between baseline and ZR/HA modes.
- Keep charts minimal: throughput and p95 latency over time are enough.

Implementation notes

- Use Python with well-known libraries:
  - CLI: Typer (preferred) or Click/Argparse
  - DB drivers:
    - Postgres: psycopg (psycopg3) or psycopg2
    - MySQL: mysql-connector-python or PyMySQL
    - SQL DB: pyodbc (ODBC Driver 18) preferred; include VM prereqs for ODBC driver
  - Stats: numpy/pandas optional
  - HTML report: Plotly (offline) preferred for easy interactive charts, or generate Markdown only if simpler
- Make the benchmark loop robust:
  - Use connection pooling where appropriate (or per-worker connections)
  - Ensure transactions/commits are explicit and consistent across DB types
  - Handle transient errors cleanly and record them

Developer experience / docs
README must include:

- Prereqs: Azure subscription, Bicep/Az CLI, region assumption centralus, cost warning
- How to deploy infra:
  - `az deployment group create ...` or a script wrapping it
  - How to SSH into VM
- How to configure targets and run benchmarks:
  - Example config file
  - Example commands:
    - `azure-db-zr-bench run --target pg-crosszoneha --concurrency 16 --duration 300`
    - `azure-db-zr-bench suite --service postgres --concurrency 1,4,16 --duration 300`
- Where results go and how to open the report

Acceptance criteria

- `infra/` can deploy: VNet + VM + the required DB variants in centralus (or another region provided).
- From the VM, I can:
  - install/run the Python CLI
  - point it at each DB variant
  - run write benchmarks with configurable concurrency/duration
  - generate a comparison report showing relative throughput/latency differences across the HA/ZR modes.

Keep the code clean, readable, and minimal—v1 prioritizes correctness, repeatability, and ease of running over sophistication.
