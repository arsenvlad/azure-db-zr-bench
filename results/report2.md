# Azure DB Zone Redundancy Benchmark Report

Generated: 2025-12-25 02:13:06

## Summary

This report compares write performance across different HA/ZR modes for Azure managed databases.


## PostgreSQL Flexible Server


### Concurrency: 1

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 568.90 | 1.54 | 3.17 | 5.25 | 0 | baseline | baseline |
| samezone-ha | 321.58 | 2.93 | 4.14 | 6.03 | 0 | -43.5% | +30.3% |
| crosszone-ha | 277.01 | 3.25 | 5.59 | 8.36 | 0 | -51.3% | +76.2% |


### Concurrency: 4

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 1485.54 | 2.25 | 5.33 | 7.92 | 0 | baseline | baseline |
| samezone-ha | 923.41 | 4.04 | 6.33 | 9.32 | 0 | -37.8% | +18.7% |
| crosszone-ha | 845.81 | 4.28 | 7.62 | 12.22 | 0 | -43.1% | +42.8% |


### Concurrency: 16

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 2491.48 | 5.72 | 10.69 | 18.77 | 0 | baseline | baseline |
| samezone-ha | 2446.26 | 6.06 | 9.59 | 12.93 | 0 | -1.8% | -10.3% |
| crosszone-ha | 2164.65 | 6.73 | 11.62 | 16.42 | 0 | -13.1% | +8.7% |


### Concurrency: 32

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 3143.88 | 9.68 | 15.18 | 18.93 | 0 | baseline | baseline |
| samezone-ha | 3084.18 | 9.85 | 14.39 | 18.06 | 0 | -1.9% | -5.2% |
| crosszone-ha | 2905.98 | 10.27 | 16.12 | 21.83 | 0 | -7.6% | +6.2% |



## MySQL Flexible Server


### Concurrency: 1

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 144.99 | 7.03 | 7.56 | 8.63 | 0 | baseline | baseline |
| samezone-ha | 140.66 | 7.25 | 7.89 | 9.28 | 0 | -3.0% | +4.4% |
| crosszone-ha | 149.59 | 6.48 | 8.02 | 9.59 | 0 | +3.2% | +6.2% |


### Concurrency: 4

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 411.48 | 9.97 | 10.76 | 12.29 | 0 | baseline | baseline |
| samezone-ha | 395.85 | 10.38 | 12.16 | 13.74 | 0 | -3.8% | +13.0% |
| crosszone-ha | 344.48 | 11.54 | 13.85 | 16.26 | 0 | -16.3% | +28.7% |


### Concurrency: 16

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 1556.40 | 10.40 | 11.61 | 13.22 | 0 | baseline | baseline |
| samezone-ha | 1474.54 | 10.93 | 12.96 | 14.96 | 0 | -5.3% | +11.7% |
| crosszone-ha | 1310.53 | 12.02 | 14.57 | 17.14 | 0 | -15.8% | +25.5% |


### Concurrency: 32

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| no-ha | 2843.98 | 11.10 | 13.19 | 16.13 | 0 | baseline | baseline |
| samezone-ha | 2673.75 | 11.72 | 14.44 | 17.97 | 0 | -6.0% | +9.5% |
| crosszone-ha | 2448.19 | 12.67 | 15.91 | 20.01 | 0 | -13.9% | +20.6% |



## Azure SQL Database (General Purpose)


### Concurrency: 1

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| non-zr | 155.88 | 5.50 | 6.53 | 7.25 | 0 | baseline | baseline |
| zr | 130.63 | 6.23 | 8.59 | 18.25 | 0 | -16.2% | +31.5% |


### Concurrency: 4

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| non-zr | 585.84 | 5.54 | 6.81 | 8.47 | 0 | baseline | baseline |
| zr | 528.79 | 6.07 | 7.76 | 17.51 | 0 | -9.7% | +13.9% |


### Concurrency: 16

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| non-zr | 2032.76 | 5.34 | 6.86 | 9.68 | 0 | baseline | baseline |
| zr | 2208.52 | 5.72 | 8.53 | 14.87 | 0 | +8.6% | +24.3% |


### Concurrency: 32

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
| non-zr | 3728.25 | 5.80 | 8.00 | 16.41 | 0 | baseline | baseline |
| zr | 4013.79 | 6.16 | 8.91 | 17.70 | 0 | +7.7% | +11.4% |




## Key Findings


### PostgreSQL Flexible Server


**Concurrency 1:**
- **samezone-ha** vs baseline: Throughput -43.5%, P95 latency +30.3%
- **crosszone-ha** vs baseline: Throughput -51.3%, P95 latency +76.2%


**Concurrency 4:**
- **samezone-ha** vs baseline: Throughput -37.8%, P95 latency +18.7%
- **crosszone-ha** vs baseline: Throughput -43.1%, P95 latency +42.8%


**Concurrency 16:**
- **samezone-ha** vs baseline: Throughput -1.8%, P95 latency -10.3%
- **crosszone-ha** vs baseline: Throughput -13.1%, P95 latency +8.7%


**Concurrency 32:**
- **samezone-ha** vs baseline: Throughput -1.9%, P95 latency -5.2%
- **crosszone-ha** vs baseline: Throughput -7.6%, P95 latency +6.2%


### MySQL Flexible Server


**Concurrency 1:**
- **samezone-ha** vs baseline: Throughput -3.0%, P95 latency +4.4%
- **crosszone-ha** vs baseline: Throughput +3.2%, P95 latency +6.2%


**Concurrency 4:**
- **samezone-ha** vs baseline: Throughput -3.8%, P95 latency +13.0%
- **crosszone-ha** vs baseline: Throughput -16.3%, P95 latency +28.7%


**Concurrency 16:**
- **samezone-ha** vs baseline: Throughput -5.3%, P95 latency +11.7%
- **crosszone-ha** vs baseline: Throughput -15.8%, P95 latency +25.5%


**Concurrency 32:**
- **samezone-ha** vs baseline: Throughput -6.0%, P95 latency +9.5%
- **crosszone-ha** vs baseline: Throughput -13.9%, P95 latency +20.6%


### Azure SQL Database (General Purpose)


**Concurrency 1:**
- **zr** vs baseline: Throughput -16.2%, P95 latency +31.5%


**Concurrency 4:**
- **zr** vs baseline: Throughput -9.7%, P95 latency +13.9%


**Concurrency 16:**
- **zr** vs baseline: Throughput +8.6%, P95 latency +24.3%


**Concurrency 32:**
- **zr** vs baseline: Throughput +7.7%, P95 latency +11.4%

---

*Note: Negative throughput delta indicates slower performance. Positive latency delta indicates higher latency.*