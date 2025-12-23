# ADR-001: Initial Architecture Decisions

**Date**: 2024-12-23  
**Status**: Accepted

## Context

We need to build a benchmarking tool to measure the relative write-performance impact of enabling Zone Redundancy (ZR) and High Availability (HA) modes in Azure managed databases.

## Decisions

### 1. Benchmark Approach: Single-Row INSERTs with Explicit Commits

**Decision**: Use single-row INSERTs (batch_size=1 default) with explicit commits per operation.

**Rationale**:
- Single-row inserts more accurately measure synchronous replication overhead
- Each commit must wait for the standby replica in ZR/HA modes
- This makes ZR/HA impact more visible compared to batched operations where commit overhead is amortized
- Batch size is configurable for alternative testing scenarios

### 2. Database Provider Architecture

**Decision**: Use an abstract base class `DatabaseProvider` with concrete implementations for each database type.

**Rationale**:
- Clean separation of database-specific connection/query logic
- Consistent interface for the benchmark runner
- Easy to add new database types in the future

### 3. Networking: Delegated Subnets for PostgreSQL/MySQL, Private Endpoint for SQL

**Decision**: Use VNet integration with delegated subnets for PostgreSQL and MySQL Flexible Servers, and Private Endpoint for Azure SQL.

**Rationale**:
- PostgreSQL and MySQL Flexible Servers support (and prefer) delegated subnet deployment
- Azure SQL requires Private Endpoint for VNet connectivity
- All databases accessible only from within the VNet

### 4. Configuration: YAML with Environment Variable Support

**Decision**: Use YAML configuration files with `${VAR}` syntax for environment variable substitution.

**Rationale**:
- YAML is human-readable and well-supported
- Environment variables keep secrets out of config files
- Pattern `${VAR:-default}` allows optional variables with defaults

### 5. Metrics: Time-Series and Percentile Aggregation

**Decision**: Capture both time-series data (per-second throughput/latency) and overall percentile statistics.

**Rationale**:
- Time-series shows performance stability over time
- Percentiles (P50/P95/P99) are standard for latency reporting
- Both are useful for different analysis needs

### 6. Report Format: HTML with Plotly for Charts

**Decision**: Generate static HTML reports using Plotly.js for interactive charts.

**Rationale**:
- Self-contained HTML files (Plotly loaded from CDN)
- Interactive charts for exploring data
- No server required to view reports
- Markdown summary also generated for quick reference

### 7. Concurrency Model: Thread Pool with Per-Thread Connections

**Decision**: Use Python's `ThreadPoolExecutor` with one database connection per worker thread.

**Rationale**:
- Simple and effective for I/O-bound database operations
- Avoids connection pool contention issues
- Each thread has its own connection lifecycle
- GIL impact is minimal for network I/O

### 8. Warmup Phase: Separate from Measured Results

**Decision**: Include a configurable warmup period (default 30s) that is excluded from metrics.

**Rationale**:
- Allows connection establishment, JIT compilation, and caching to stabilize
- Results represent steady-state performance
- Warmup duration is clearly documented in output

## Consequences

### Positive
- Clear separation of concerns in code structure
- Repeatable benchmarks with explicit configuration
- Results include all metadata for reproducibility
- Interactive reports for data exploration

### Negative
- Thread-based concurrency limits scalability beyond ~64 workers (sufficient for this use case)
- Single-row inserts may not represent all real-world workloads
- Static HTML reports require internet for Plotly CDN (could embed if needed)

## Alternatives Considered

1. **AsyncIO instead of threads**: Would add complexity without significant benefit for this use case
2. **SQLAlchemy ORM**: Overkill for simple benchmark operations, adds overhead
3. **PDF reports**: More complex to generate, less interactive
4. **Connection pooling library**: Unnecessary complexity for dedicated worker connections
