# Results Directory

This directory contains benchmark results.

Results are organized by timestamp and target:

```text
results/
└── 20241223_143022/
    ├── pg-noha/
    │   ├── result.json
    │   ├── summary.json
    │   └── latencies.json
    ├── pg-samezoneha/
    │   └── ...
    └── report.html
```

This directory is gitignored (except this README). Do not commit benchmark results to the repository.
