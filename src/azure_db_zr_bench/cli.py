"""CLI entry point for azure-db-zr-bench."""

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional
import json

from .config import load_config, BenchmarkTarget
from .benchmark import BenchmarkRunner
from .report import generate_report

app = typer.Typer(
    name="azure-db-zr-bench",
    help="Azure Database Zone Redundancy Benchmark Tool",
    no_args_is_help=True,
)
console = Console()


@app.command("list")
def list_targets(
    config: Path = typer.Option(
        Path("config.yaml"),
        "--config",
        "-c",
        help="Path to configuration file",
    ),
):
    """List available benchmark targets from the config file."""
    try:
        targets = load_config(config)
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {config}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise typer.Exit(1)

    table = Table(title="Available Benchmark Targets")
    table.add_column("Name", style="cyan")
    table.add_column("Service", style="green")
    table.add_column("Mode", style="yellow")
    table.add_column("Host", style="dim")

    for name, target in targets.items():
        table.add_row(name, target.service, target.mode, target.host)

    console.print(table)


@app.command("run")
def run_benchmark(
    target: str = typer.Option(
        ...,
        "--target",
        "-t",
        help="Target name from config file",
    ),
    config: Path = typer.Option(
        Path("config.yaml"),
        "--config",
        "-c",
        help="Path to configuration file",
    ),
    concurrency: int = typer.Option(
        4,
        "--concurrency",
        "-n",
        help="Number of concurrent workers",
    ),
    duration: int = typer.Option(
        300,
        "--duration",
        "-d",
        help="Benchmark duration in seconds",
    ),
    warmup: int = typer.Option(
        30,
        "--warmup",
        "-w",
        help="Warmup duration in seconds (excluded from stats)",
    ),
    batch_size: int = typer.Option(
        1,
        "--batch-size",
        "-b",
        help="Number of rows per INSERT batch",
    ),
    output_dir: Path = typer.Option(
        Path("results"),
        "--output",
        "-o",
        help="Output directory for results",
    ),
):
    """Run a write benchmark against a specific target."""
    try:
        targets = load_config(config)
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {config}[/red]")
        raise typer.Exit(1)

    if target not in targets:
        console.print(f"[red]Target '{target}' not found in config[/red]")
        console.print(f"Available targets: {', '.join(targets.keys())}")
        raise typer.Exit(1)

    target_config = targets[target]

    console.print(f"[bold]Starting benchmark for target: {target}[/bold]")
    console.print(f"  Service: {target_config.service}")
    console.print(f"  Mode: {target_config.mode}")
    console.print(f"  Host: {target_config.host}")
    console.print(f"  Concurrency: {concurrency}")
    console.print(f"  Duration: {duration}s")
    console.print(f"  Warmup: {warmup}s")
    console.print(f"  Batch size: {batch_size}")

    runner = BenchmarkRunner(
        target_name=target,
        target_config=target_config,
        concurrency=concurrency,
        duration=duration,
        warmup=warmup,
        batch_size=batch_size,
        output_dir=output_dir,
    )

    try:
        result = runner.run()
        console.print("\n[bold green]Benchmark completed successfully![/bold green]")
        console.print(f"Results saved to: {result.output_path}")

        # Print summary
        table = Table(title="Benchmark Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Writes", f"{result.summary['total_writes']:,}")
        table.add_row("Throughput (writes/sec)", f"{result.summary['throughput_wps']:.2f}")
        table.add_row("Latency P50 (ms)", f"{result.summary['latency_p50_ms']:.2f}")
        table.add_row("Latency P95 (ms)", f"{result.summary['latency_p95_ms']:.2f}")
        table.add_row("Latency P99 (ms)", f"{result.summary['latency_p99_ms']:.2f}")
        table.add_row("Error Count", f"{result.summary['error_count']:,}")
        table.add_row("Error Rate", f"{result.summary['error_rate']:.2%}")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Benchmark failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("suite")
def run_suite(
    service: str = typer.Option(
        ...,
        "--service",
        "-s",
        help="Service type to benchmark (postgres, mysql, sqldb, all)",
    ),
    config: Path = typer.Option(
        Path("config.yaml"),
        "--config",
        "-c",
        help="Path to configuration file",
    ),
    concurrency: str = typer.Option(
        "1,4,16",
        "--concurrency",
        "-n",
        help="Comma-separated list of concurrency levels",
    ),
    duration: int = typer.Option(
        300,
        "--duration",
        "-d",
        help="Benchmark duration in seconds per run",
    ),
    warmup: int = typer.Option(
        30,
        "--warmup",
        "-w",
        help="Warmup duration in seconds",
    ),
    batch_size: int = typer.Option(
        1,
        "--batch-size",
        "-b",
        help="Number of rows per INSERT batch",
    ),
    output_dir: Path = typer.Option(
        Path("results"),
        "--output",
        "-o",
        help="Output directory for results",
    ),
):
    """Run a suite of benchmarks for a service type across all HA/ZR modes."""
    try:
        targets = load_config(config)
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {config}[/red]")
        raise typer.Exit(1)

    # Parse concurrency levels
    concurrency_levels = [int(c.strip()) for c in concurrency.split(",")]

    # Filter targets by service
    if service.lower() == "all":
        filtered_targets = targets
    else:
        service_map = {
            "postgres": "postgres",
            "postgresql": "postgres",
            "pg": "postgres",
            "mysql": "mysql",
            "sqldb": "sqldb",
            "sql": "sqldb",
            "azuresql": "sqldb",
        }
        service_name = service_map.get(service.lower())
        if not service_name:
            console.print(f"[red]Unknown service: {service}[/red]")
            raise typer.Exit(1)
        filtered_targets = {
            k: v for k, v in targets.items() if v.service == service_name
        }

    if not filtered_targets:
        console.print(f"[red]No targets found for service: {service}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Running benchmark suite for service: {service}[/bold]")
    console.print(f"Targets: {', '.join(filtered_targets.keys())}")
    console.print(f"Concurrency levels: {concurrency_levels}")

    results = []

    for target_name, target_config in filtered_targets.items():
        for conc in concurrency_levels:
            console.print(f"\n[bold cyan]Running: {target_name} @ concurrency={conc}[/bold cyan]")

            runner = BenchmarkRunner(
                target_name=target_name,
                target_config=target_config,
                concurrency=conc,
                duration=duration,
                warmup=warmup,
                batch_size=batch_size,
                output_dir=output_dir,
            )

            try:
                result = runner.run()
                results.append(result)
                console.print(
                    f"[green]✓ {target_name} @ {conc}: "
                    f"{result.summary['throughput_wps']:.2f} writes/sec, "
                    f"p95={result.summary['latency_p95_ms']:.2f}ms[/green]"
                )
            except Exception as e:
                console.print(f"[red]✗ {target_name} @ {conc}: {e}[/red]")

    if results:
        console.print("\n[bold]Generating comparison report...[/bold]")
        report_path = generate_report(results, output_dir)
        console.print(f"[green]Report saved to: {report_path}[/green]")


@app.command("report")
def generate_comparison_report(
    results_dir: Path = typer.Option(
        Path("results"),
        "--results",
        "-r",
        help="Directory containing benchmark results",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for report (defaults to results_dir)",
    ),
):
    """Generate a comparison report from existing benchmark results."""
    from .report import load_results, generate_report

    if output_dir is None:
        output_dir = results_dir

    console.print(f"[bold]Loading results from: {results_dir}[/bold]")

    try:
        results = load_results(results_dir)
        if not results:
            console.print("[red]No results found[/red]")
            raise typer.Exit(1)

        console.print(f"Found {len(results)} result files")

        report_path = generate_report(results, output_dir)
        console.print(f"[green]Report saved to: {report_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
