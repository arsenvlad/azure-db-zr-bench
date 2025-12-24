"""Report generation for azure-db-zr-bench."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from jinja2 import Template

from .benchmark import BenchmarkResult


def load_results(results_dir: Path) -> List[BenchmarkResult]:
    """Load benchmark results from a directory.

    Scans for result.json files in subdirectories.
    """
    results = []

    for result_file in results_dir.rglob("result.json"):
        try:
            with open(result_file, "r") as f:
                data = json.load(f)

            # Load latencies if available
            latencies_file = result_file.parent / "latencies.json"
            raw_latencies = []
            if latencies_file.exists():
                with open(latencies_file, "r") as f:
                    lat_data = json.load(f)
                    raw_latencies = lat_data.get("latencies_ms", [])

            result = BenchmarkResult(
                target_name=data["target_name"],
                service=data["service"],
                mode=data["mode"],
                concurrency=data["concurrency"],
                duration=data["duration"],
                warmup=data["warmup"],
                batch_size=data["batch_size"],
                start_time=data["start_time"],
                end_time=data["end_time"],
                summary=data["summary"],
                time_series=data.get("time_series", []),
                raw_latencies=raw_latencies,
                errors=data.get("errors", []),
                output_path=result_file.parent,
            )
            results.append(result)

        except Exception as e:
            print(f"Warning: Failed to load {result_file}: {e}")

    return results


def generate_report(results: List[BenchmarkResult], output_dir: Path) -> Path:
    """Generate an HTML comparison report from benchmark results."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group results by service and concurrency
    grouped = group_results(results)

    # Calculate deltas
    comparisons = calculate_comparisons(grouped)

    # Generate HTML report
    html_content = render_html_report(grouped, comparisons)
    html_path = output_dir / "report.html"
    with open(html_path, "w") as f:
        f.write(html_content)

    # Generate Markdown summary
    md_content = render_markdown_report(grouped, comparisons)
    md_path = output_dir / "report.md"
    with open(md_path, "w") as f:
        f.write(md_content)

    # Save comparison data as JSON
    comparison_path = output_dir / "comparison.json"
    with open(comparison_path, "w") as f:
        json.dump(comparisons, f, indent=2)

    return html_path


def group_results(
    results: List[BenchmarkResult],
) -> Dict[str, Dict[int, Dict[str, BenchmarkResult]]]:
    """Group results by service, concurrency, and mode."""
    grouped = {}

    for result in results:
        service = result.service
        concurrency = result.concurrency
        mode = result.mode

        if service not in grouped:
            grouped[service] = {}
        if concurrency not in grouped[service]:
            grouped[service][concurrency] = {}

        # Use the most recent result for each combination
        existing = grouped[service][concurrency].get(mode)
        if existing is None or result.start_time > existing.start_time:
            grouped[service][concurrency][mode] = result

    return grouped


def calculate_comparisons(
    grouped: Dict[str, Dict[int, Dict[str, BenchmarkResult]]],
) -> Dict[str, Any]:
    """Calculate comparison metrics between baseline and HA/ZR modes."""
    comparisons = {}

    # Define baselines for each service
    baselines = {
        "postgres": "no-ha",
        "mysql": "no-ha",
        "sqldb": "non-zr",
    }

    for service, concurrency_data in grouped.items():
        baseline_mode = baselines.get(service)
        if not baseline_mode:
            continue

        comparisons[service] = {}

        for concurrency, mode_data in concurrency_data.items():
            baseline = mode_data.get(baseline_mode)
            if not baseline:
                continue

            comparisons[service][concurrency] = {}

            for mode, result in mode_data.items():
                if mode == baseline_mode:
                    continue

                # Calculate deltas
                throughput_delta = (
                    (result.summary["throughput_wps"] - baseline.summary["throughput_wps"])
                    / baseline.summary["throughput_wps"]
                    * 100
                    if baseline.summary["throughput_wps"] > 0
                    else 0
                )

                latency_p95_delta = (
                    (result.summary["latency_p95_ms"] - baseline.summary["latency_p95_ms"])
                    / baseline.summary["latency_p95_ms"]
                    * 100
                    if baseline.summary["latency_p95_ms"] > 0
                    else 0
                )

                comparisons[service][concurrency][mode] = {
                    "baseline_mode": baseline_mode,
                    "baseline_throughput_wps": baseline.summary["throughput_wps"],
                    "baseline_latency_p95_ms": baseline.summary["latency_p95_ms"],
                    "target_throughput_wps": result.summary["throughput_wps"],
                    "target_latency_p95_ms": result.summary["latency_p95_ms"],
                    "throughput_delta_pct": throughput_delta,
                    "latency_p95_delta_pct": latency_p95_delta,
                }

    return comparisons


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Azure DB Zone Redundancy Benchmark Report</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        :root {
            --bg-color: #f5f5f5;
            --card-bg: #ffffff;
            --text-color: #333333;
            --border-color: #e0e0e0;
            --primary-color: #0078d4;
            --success-color: #107c10;
            --warning-color: #ffb900;
            --danger-color: #d13438;
        }
        
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1, h2, h3 {
            color: var(--text-color);
        }
        
        h1 {
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 10px;
        }
        
        .card {
            background: var(--card-bg);
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric {
            text-align: center;
            padding: 15px;
            background: var(--bg-color);
            border-radius: 6px;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .metric-label {
            font-size: 0.9em;
            color: #666;
        }
        
        .delta-positive {
            color: var(--success-color);
        }
        
        .delta-negative {
            color: var(--danger-color);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        th {
            background: var(--bg-color);
            font-weight: 600;
        }
        
        tr:hover {
            background: var(--bg-color);
        }
        
        .chart-container {
            margin: 20px 0;
            min-height: 400px;
        }
        
        .service-section {
            margin-bottom: 40px;
        }
        
        .service-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .service-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .service-badge.postgres {
            background: #336791;
            color: white;
        }
        
        .service-badge.mysql {
            background: #00758f;
            color: white;
        }
        
        .service-badge.sqldb {
            background: #0078d4;
            color: white;
        }
        
        .timestamp {
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Azure DB Zone Redundancy Benchmark Report</h1>
        <p class="timestamp">Generated: {{ generated_at }}</p>
        
        {% for service, service_data in grouped.items() %}
        <div class="service-section">
            <div class="service-header">
                <h2>{{ service_names[service] }}</h2>
                <span class="service-badge {{ service }}">{{ service }}</span>
            </div>
            
            {% for concurrency, mode_data in service_data.items() %}
            <div class="card">
                <h3>Concurrency: {{ concurrency }}</h3>
                
                <table>
                    <thead>
                        <tr>
                            <th>Mode</th>
                            <th>Throughput (writes/sec)</th>
                            <th>P50 Latency (ms)</th>
                            <th>P95 Latency (ms)</th>
                            <th>P99 Latency (ms)</th>
                            <th>Error Rate</th>
                            <th>Throughput Δ</th>
                            <th>P95 Latency Δ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for mode, result in mode_data.items() %}
                        <tr>
                            <td><strong>{{ mode }}</strong></td>
                            <td>{{ "%.2f"|format(result.summary.throughput_wps) }}</td>
                            <td>{{ "%.2f"|format(result.summary.latency_p50_ms) }}</td>
                            <td>{{ "%.2f"|format(result.summary.latency_p95_ms) }}</td>
                            <td>{{ "%.2f"|format(result.summary.latency_p99_ms) }}</td>
                            <td>{{ "%.2f%%"|format(result.summary.error_rate * 100) }}</td>
                            <td>
                                {% if comparisons[service][concurrency][mode] is defined %}
                                    {% set delta = comparisons[service][concurrency][mode].throughput_delta_pct %}
                                    <span class="{{ 'delta-positive' if delta >= 0 else 'delta-negative' }}">
                                        {{ "%+.1f%%"|format(delta) }}
                                    </span>
                                {% else %}
                                    <em>baseline</em>
                                {% endif %}
                            </td>
                            <td>
                                {% if comparisons[service][concurrency][mode] is defined %}
                                    {% set delta = comparisons[service][concurrency][mode].latency_p95_delta_pct %}
                                    <span class="{{ 'delta-negative' if delta >= 0 else 'delta-positive' }}">
                                        {{ "%+.1f%%"|format(delta) }}
                                    </span>
                                {% else %}
                                    <em>baseline</em>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                
                <div class="chart-container" id="chart-{{ service }}-{{ concurrency }}-throughput"></div>
                <div class="chart-container" id="chart-{{ service }}-{{ concurrency }}-latency"></div>
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </div>
    
    <script>
        // Chart data
        const chartData = {{ chart_data | safe }};
        
        // Render charts
        for (const [chartId, data] of Object.entries(chartData)) {
            if (document.getElementById(chartId)) {
                Plotly.newPlot(chartId, data.traces, data.layout, {responsive: true});
            }
        }
    </script>
</body>
</html>
"""


def render_html_report(
    grouped: Dict[str, Dict[int, Dict[str, BenchmarkResult]]],
    comparisons: Dict[str, Any],
) -> str:
    """Render the HTML report using Jinja2."""
    # Prepare chart data
    chart_data = {}

    for service, concurrency_data in grouped.items():
        for concurrency, mode_data in concurrency_data.items():
            # Throughput chart
            throughput_traces = []
            for mode, result in mode_data.items():
                if result.time_series:
                    throughput_traces.append({
                        "x": [ts["elapsed_sec"] for ts in result.time_series],
                        "y": [ts["throughput_wps"] for ts in result.time_series],
                        "name": mode,
                        "type": "scatter",
                        "mode": "lines",
                    })

            chart_data[f"chart-{service}-{concurrency}-throughput"] = {
                "traces": throughput_traces,
                "layout": {
                    "title": f"Throughput Over Time ({service}, concurrency={concurrency})",
                    "xaxis": {"title": "Elapsed Time (seconds)"},
                    "yaxis": {"title": "Writes/second"},
                    "height": 350,
                },
            }

            # Latency chart
            latency_traces = []
            for mode, result in mode_data.items():
                if result.time_series:
                    latency_traces.append({
                        "x": [ts["elapsed_sec"] for ts in result.time_series],
                        "y": [ts["avg_latency_ms"] for ts in result.time_series],
                        "name": mode,
                        "type": "scatter",
                        "mode": "lines",
                    })

            chart_data[f"chart-{service}-{concurrency}-latency"] = {
                "traces": latency_traces,
                "layout": {
                    "title": f"Average Latency Over Time ({service}, concurrency={concurrency})",
                    "xaxis": {"title": "Elapsed Time (seconds)"},
                    "yaxis": {"title": "Latency (ms)"},
                    "height": 350,
                },
            }

    # Service display names
    service_names = {
        "postgres": "PostgreSQL Flexible Server",
        "mysql": "MySQL Flexible Server",
        "sqldb": "Azure SQL Database (General Purpose)",
    }

    template = Template(HTML_TEMPLATE)
    return template.render(
        grouped=grouped,
        comparisons=comparisons,
        chart_data=json.dumps(chart_data),
        service_names=service_names,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


MARKDOWN_TEMPLATE = """# Azure DB Zone Redundancy Benchmark Report

Generated: {{ generated_at }}

## Summary

This report compares write performance across different HA/ZR modes for Azure managed databases.

{% for service, service_data in grouped.items() %}
## {{ service_names[service] }}

{% for concurrency, mode_data in service_data.items() %}
### Concurrency: {{ concurrency }}

| Mode | Throughput (w/s) | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Throughput Δ | P95 Δ |
| ---- | ---------------- | -------- | -------- | -------- | ------ | ------------ | ----- |
{% for mode, result in mode_data.items() -%}
| {{ mode }} | {{ "%.2f"|format(result.summary.throughput_wps) }} | {{ "%.2f"|format(result.summary.latency_p50_ms) }} | {{ "%.2f"|format(result.summary.latency_p95_ms) }} | {{ "%.2f"|format(result.summary.latency_p99_ms) }} | {{ result.summary.error_count }} | {% if comparisons[service][concurrency][mode] is defined %}{{ "%+.1f%%"|format(comparisons[service][concurrency][mode].throughput_delta_pct) }}{% else %}baseline{% endif %} | {% if comparisons[service][concurrency][mode] is defined %}{{ "%+.1f%%"|format(comparisons[service][concurrency][mode].latency_p95_delta_pct) }}{% else %}baseline{% endif %} |
{% endfor %}
{% endfor %}
{% endfor %}

## Key Findings
{% for service, service_comparisons in comparisons.items() %}

### {{ service_names[service] }}
{% for concurrency, mode_comparisons in service_comparisons.items() %}

**Concurrency {{ concurrency }}:**
{% for mode, comp in mode_comparisons.items() -%}
- **{{ mode }}** vs baseline: Throughput {{ "%+.1f%%"|format(comp.throughput_delta_pct) }}, P95 latency {{ "%+.1f%%"|format(comp.latency_p95_delta_pct) }}
{% endfor -%}
{% endfor -%}
{% endfor %}
---

*Note: Negative throughput delta indicates slower performance. Positive latency delta indicates higher latency.*
"""


def render_markdown_report(
    grouped: Dict[str, Dict[int, Dict[str, BenchmarkResult]]],
    comparisons: Dict[str, Any],
) -> str:
    """Render a Markdown summary report."""
    service_names = {
        "postgres": "PostgreSQL Flexible Server",
        "mysql": "MySQL Flexible Server",
        "sqldb": "Azure SQL Database (General Purpose)",
    }

    template = Template(MARKDOWN_TEMPLATE)
    return template.render(
        grouped=grouped,
        comparisons=comparisons,
        service_names=service_names,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
