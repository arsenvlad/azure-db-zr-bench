# Azure DB Zone Redundancy Benchmark Report

Generated: 2025-12-23 23:42:41

## Summary

This report compares write performance across different HA/ZR modes for Azure managed databases.

## PostgreSQL Flexible Server

### Concurrency: 1

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
|------|-----------------|----------|----------|----------|--------|--------------|-------|
| no-ha | 579.37 | 1.53 | 2.65 | 4.81 | 0 | baseline | baseline |
| samezone-ha | 281.00 | 3.23 | 5.29 | 8.39 | 0 | -51.5% | +99.8% |
| crosszone-ha | 273.31 | 3.32 | 5.85 | 7.63 | 0 | -52.8% | +121.2% |

### Concurrency: 4

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
|------|-----------------|----------|----------|----------|--------|--------------|-------|
| no-ha | 1673.96 | 2.06 | 3.89 | 7.32 | 0 | baseline | baseline |
| samezone-ha | 894.93 | 4.00 | 7.33 | 11.94 | 0 | -46.5% | +88.5% |
| crosszone-ha | 838.14 | 4.28 | 8.01 | 10.71 | 0 | -49.9% | +105.8% |

### Concurrency: 16

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
|------|-----------------|----------|----------|----------|--------|--------------|-------|
| no-ha | 2820.59 | 5.31 | 8.34 | 11.99 | 0 | baseline | baseline |
| samezone-ha | 2241.91 | 6.44 | 11.31 | 16.62 | 0 | -20.5% | +35.7% |
| crosszone-ha | 2199.35 | 6.67 | 11.32 | 14.55 | 0 | -22.0% | +35.7% |

## MySQL Flexible Server

### Concurrency: 1

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
|------|-----------------|----------|----------|----------|--------|--------------|-------|
| no-ha | 146.90 | 6.82 | 7.41 | 8.84 | 0 | baseline | baseline |
| samezone-ha | 135.96 | 7.04 | 9.23 | 10.73 | 0 | -7.4% | +24.7% |
| crosszone-ha | 146.53 | 6.44 | 8.27 | 10.03 | 0 | -0.3% | +11.6% |

### Concurrency: 4

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
|------|-----------------|----------|----------|----------|--------|--------------|-------|
| no-ha | 431.89 | 9.45 | 10.74 | 12.13 | 0 | baseline | baseline |
| samezone-ha | 306.13 | 12.75 | 15.72 | 18.02 | 0 | -29.1% | +46.4% |
| crosszone-ha | 361.77 | 11.23 | 13.57 | 15.49 | 0 | -16.2% | +26.4% |

### Concurrency: 16

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
|------|-----------------|----------|----------|----------|--------|--------------|-------|
| no-ha | 1659.38 | 9.78 | 11.22 | 12.83 | 0 | baseline | baseline |
| samezone-ha | 1176.00 | 13.29 | 16.35 | 19.07 | 0 | -29.1% | +45.7% |
| crosszone-ha | 1337.67 | 11.88 | 14.68 | 17.49 | 0 | -19.4% | +30.8% |

## Azure SQL Database (General Purpose)

### Concurrency: 1
| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
|------|-----------------|----------|----------|----------|--------|--------------|-------|
| non-zr | 146.29 | 5.73 | 6.81 | 7.90 | 0 | baseline | baseline |
| zr | 152.94 | 5.65 | 6.80 | 8.55 | 0 | +4.5% | -0.1% |

### Concurrency: 4

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
|------|-----------------|----------|----------|----------|--------|--------------|-------|
| non-zr | 530.67 | 5.79 | 7.12 | 10.48 | 0 | baseline | baseline |
| zr | 557.49 | 5.98 | 7.69 | 10.89 | 0 | +5.1% | +8.0% |

### Concurrency: 16

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
|------|-----------------|----------|----------|----------|--------|--------------|-------|
| non-zr | 1808.71 | 5.48 | 8.11 | 17.19 | 0 | baseline | baseline |
| zr | 2302.21 | 5.69 | 7.45 | 11.33 | 0 | +27.3% | -8.1% |

## Key Findings

### PostgreSQL Flexible Server

**Concurrency 1:**

- **samezone-ha** vs baseline: Throughput -51.5%, P95 latency +99.8%
- **crosszone-ha** vs baseline: Throughput -52.8%, P95 latency +121.2%


**Concurrency 4:**

- **samezone-ha** vs baseline: Throughput -46.5%, P95 latency +88.5%
- **crosszone-ha** vs baseline: Throughput -49.9%, P95 latency +105.8%

**Concurrency 16:**

- **samezone-ha** vs baseline: Throughput -20.5%, P95 latency +35.7%
- **crosszone-ha** vs baseline: Throughput -22.0%, P95 latency +35.7%

### MySQL Flexible Server

**Concurrency 1:**

- **samezone-ha** vs baseline: Throughput -7.4%, P95 latency +24.7%
- **crosszone-ha** vs baseline: Throughput -0.3%, P95 latency +11.6%

**Concurrency 4:**

- **samezone-ha** vs baseline: Throughput -29.1%, P95 latency +46.4%
- **crosszone-ha** vs baseline: Throughput -16.2%, P95 latency +26.4%

**Concurrency 16:**

- **samezone-ha** vs baseline: Throughput -29.1%, P95 latency +45.7%
- **crosszone-ha** vs baseline: Throughput -19.4%, P95 latency +30.8%

### Azure SQL Database (General Purpose)

**Concurrency 1:**

- **zr** vs baseline: Throughput +4.5%, P95 latency -0.1%

**Concurrency 4:**

- **zr** vs baseline: Throughput +5.1%, P95 latency +8.0%

**Concurrency 16:**

- **zr** vs baseline: Throughput +27.3%, P95 latency -8.1%

---
*Note: Negative throughput delta indicates slower performance. Positive latency delta indicates higher latency.*