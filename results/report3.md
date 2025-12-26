# Azure DB Zone Redundancy Benchmark Report (batch size: 10)

Generated: 2025-12-26 02:16:43

## Summary

This report compares write performance across different HA/ZR modes for Azure managed databases.


## PostgreSQL Flexible Server


### Concurrency: 1

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 4000.06 | 2.36 | 3.08 | 4.35 | 0 | baseline | baseline |
| samezone-ha | 2661.14 | 3.53 | 4.65 | 6.74 | 0 | -33.5% | +51.1% |
| crosszone-ha | 2346.22 | 3.96 | 5.74 | 7.87 | 0 | -41.3% | +86.4% |


### Concurrency: 4

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 6749.56 | 5.77 | 8.47 | 10.68 | 0 | baseline | baseline |
| samezone-ha | 5727.10 | 6.46 | 10.50 | 14.98 | 0 | -15.1% | +23.9% |
| crosszone-ha | 5763.19 | 6.41 | 10.32 | 14.80 | 0 | -14.6% | +21.8% |


### Concurrency: 16

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 6410.11 | 24.15 | 33.31 | 40.62 | 0 | baseline | baseline |
| samezone-ha | 5643.28 | 27.54 | 36.88 | 47.13 | 0 | -12.0% | +10.7% |
| crosszone-ha | 5749.40 | 26.92 | 36.01 | 46.05 | 0 | -10.3% | +8.1% |



## MySQL Flexible Server


### Concurrency: 1

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 1421.69 | 6.95 | 7.66 | 9.03 | 0 | baseline | baseline |
| samezone-ha | 1364.94 | 7.06 | 8.66 | 10.10 | 0 | -4.0% | +13.1% |
| crosszone-ha | 1162.26 | 7.99 | 10.74 | 12.79 | 0 | -18.2% | +40.3% |


### Concurrency: 4

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 3806.65 | 10.57 | 11.74 | 14.86 | 0 | baseline | baseline |
| samezone-ha | 3562.00 | 11.24 | 13.46 | 17.36 | 0 | -6.4% | +14.7% |
| crosszone-ha | 3058.93 | 13.00 | 15.67 | 19.56 | 0 | -19.6% | +33.4% |


### Concurrency: 16

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 8037.28 | 20.54 | 24.54 | 40.21 | 0 | baseline | baseline |
| samezone-ha | 8257.04 | 20.13 | 24.73 | 38.31 | 0 | +2.7% | +0.8% |
| crosszone-ha | 7684.53 | 20.59 | 27.79 | 44.53 | 0 | -4.4% | +13.2% |



## Azure SQL Database (General Purpose)


### Concurrency: 1

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| non-zr | 381.12 | 25.21 | 29.96 | 32.11 | 0 | baseline | baseline |
| zr | 380.86 | 24.85 | 29.77 | 33.99 | 0 | -0.1% | -0.6% |


### Concurrency: 4

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| non-zr | 1415.16 | 26.62 | 31.93 | 41.45 | 0 | baseline | baseline |
| zr | 1430.87 | 26.33 | 31.59 | 41.28 | 0 | +1.1% | -1.1% |


### Concurrency: 16

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| non-zr | 5294.99 | 25.75 | 33.40 | 52.44 | 0 | baseline | baseline |
| zr | 5360.85 | 27.55 | 34.89 | 59.15 | 0 | +1.2% | +4.4% |




## Key Findings


### PostgreSQL Flexible Server


**Concurrency 1:**
- **samezone-ha** vs baseline: Throughput -33.5%, P95 latency +51.1%
- **crosszone-ha** vs baseline: Throughput -41.3%, P95 latency +86.4%


**Concurrency 4:**
- **samezone-ha** vs baseline: Throughput -15.1%, P95 latency +23.9%
- **crosszone-ha** vs baseline: Throughput -14.6%, P95 latency +21.8%


**Concurrency 16:**
- **samezone-ha** vs baseline: Throughput -12.0%, P95 latency +10.7%
- **crosszone-ha** vs baseline: Throughput -10.3%, P95 latency +8.1%


### MySQL Flexible Server


**Concurrency 1:**
- **samezone-ha** vs baseline: Throughput -4.0%, P95 latency +13.1%
- **crosszone-ha** vs baseline: Throughput -18.2%, P95 latency +40.3%


**Concurrency 4:**
- **samezone-ha** vs baseline: Throughput -6.4%, P95 latency +14.7%
- **crosszone-ha** vs baseline: Throughput -19.6%, P95 latency +33.4%


**Concurrency 16:**
- **samezone-ha** vs baseline: Throughput +2.7%, P95 latency +0.8%
- **crosszone-ha** vs baseline: Throughput -4.4%, P95 latency +13.2%


### Azure SQL Database (General Purpose)


**Concurrency 1:**
- **zr** vs baseline: Throughput -0.1%, P95 latency -0.6%


**Concurrency 4:**
- **zr** vs baseline: Throughput +1.1%, P95 latency -1.1%


**Concurrency 16:**
- **zr** vs baseline: Throughput +1.2%, P95 latency +4.4%

---

*Note: Negative throughput delta indicates slower performance. Positive latency delta indicates higher latency.*