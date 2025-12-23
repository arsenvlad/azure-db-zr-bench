"""Benchmark runner for azure-db-zr-bench."""

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

from .config import BenchmarkTarget
from .providers import get_provider, WriteResult


@dataclass
class BenchmarkResult:
    """Result of a complete benchmark run."""

    target_name: str
    service: str
    mode: str
    concurrency: int
    duration: int
    warmup: int
    batch_size: int
    start_time: str
    end_time: str
    summary: Dict
    time_series: List[Dict]
    raw_latencies: List[float]
    errors: List[str]
    output_path: Optional[Path] = None


@dataclass
class WorkerState:
    """State for a benchmark worker."""

    results: List[WriteResult] = field(default_factory=list)
    error_count: int = 0
    write_count: int = 0


class BenchmarkRunner:
    """Runs write benchmarks against database targets."""

    def __init__(
        self,
        target_name: str,
        target_config: BenchmarkTarget,
        concurrency: int = 4,
        duration: int = 300,
        warmup: int = 30,
        batch_size: int = 1,
        output_dir: Path = Path("results"),
    ):
        self.target_name = target_name
        self.target_config = target_config
        self.concurrency = concurrency
        self.duration = duration
        self.warmup = warmup
        self.batch_size = batch_size
        self.output_dir = output_dir

        self._stop_event = threading.Event()
        self._warmup_complete = threading.Event()

    def run(self) -> BenchmarkResult:
        """Execute the benchmark and return results."""
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.output_dir / timestamp / self.target_name
        run_dir.mkdir(parents=True, exist_ok=True)

        print(f"Connecting to {self.target_config.host}...")

        # Setup: create table using a single connection
        setup_provider = get_provider(self.target_config)
        setup_provider.connect()
        setup_provider.create_benchmark_table()
        setup_provider.truncate_benchmark_table()
        setup_provider.disconnect()

        print("Benchmark table ready")

        # Run benchmark with multiple workers
        start_time = datetime.now()
        worker_states = [WorkerState() for _ in range(self.concurrency)]
        time_series_data = []
        time_series_lock = threading.Lock()

        def worker(worker_id: int, state: WorkerState):
            """Worker function that runs in a thread."""
            provider = get_provider(self.target_config)
            provider.connect()

            try:
                interval_writes = 0
                interval_start = time.time()
                interval_latencies = []

                while not self._stop_event.is_set():
                    result = provider.write_batch(self.batch_size)
                    
                    # Only record results after warmup
                    if self._warmup_complete.is_set():
                        state.results.append(result)
                        if result.success:
                            state.write_count += result.rows_written
                            interval_writes += result.rows_written
                            interval_latencies.append(result.latency_ms)
                        else:
                            state.error_count += 1

                    # Record time series data every second (after warmup)
                    elapsed = time.time() - interval_start
                    if elapsed >= 1.0 and self._warmup_complete.is_set():
                        with time_series_lock:
                            time_series_data.append({
                                "timestamp": time.time(),
                                "worker_id": worker_id,
                                "writes": interval_writes,
                                "avg_latency_ms": (
                                    np.mean(interval_latencies) if interval_latencies else 0
                                ),
                            })
                        interval_writes = 0
                        interval_latencies = []
                        interval_start = time.time()

            finally:
                provider.disconnect()

        # Start workers
        print(f"Starting {self.concurrency} workers...")
        executor = ThreadPoolExecutor(max_workers=self.concurrency)
        futures = [
            executor.submit(worker, i, worker_states[i]) for i in range(self.concurrency)
        ]

        # Warmup phase
        print(f"Warming up for {self.warmup} seconds...")
        time.sleep(self.warmup)
        self._warmup_complete.set()
        warmup_end_time = datetime.now()

        # Main benchmark phase
        print(f"Running benchmark for {self.duration} seconds...")
        time.sleep(self.duration)

        # Stop workers
        print("Stopping workers...")
        self._stop_event.set()
        executor.shutdown(wait=True)

        end_time = datetime.now()

        # Aggregate results
        all_results = []
        total_writes = 0
        total_errors = 0
        errors = []

        for state in worker_states:
            all_results.extend(state.results)
            total_writes += state.write_count
            total_errors += state.error_count
            for r in state.results:
                if not r.success and r.error:
                    errors.append(r.error)

        # Calculate latency percentiles
        successful_latencies = [r.latency_ms for r in all_results if r.success]

        if successful_latencies:
            latency_p50 = np.percentile(successful_latencies, 50)
            latency_p95 = np.percentile(successful_latencies, 95)
            latency_p99 = np.percentile(successful_latencies, 99)
            latency_mean = np.mean(successful_latencies)
            latency_min = np.min(successful_latencies)
            latency_max = np.max(successful_latencies)
        else:
            latency_p50 = latency_p95 = latency_p99 = latency_mean = 0
            latency_min = latency_max = 0

        # Calculate throughput
        actual_duration = (end_time - warmup_end_time).total_seconds()
        throughput = total_writes / actual_duration if actual_duration > 0 else 0

        # Error rate
        total_operations = len(all_results)
        error_rate = total_errors / total_operations if total_operations > 0 else 0

        # Build summary
        summary = {
            "total_writes": total_writes,
            "total_operations": total_operations,
            "actual_duration_sec": actual_duration,
            "throughput_wps": throughput,
            "latency_p50_ms": latency_p50,
            "latency_p95_ms": latency_p95,
            "latency_p99_ms": latency_p99,
            "latency_mean_ms": latency_mean,
            "latency_min_ms": latency_min,
            "latency_max_ms": latency_max,
            "error_count": total_errors,
            "error_rate": error_rate,
        }

        # Aggregate time series by second
        aggregated_ts = aggregate_time_series(time_series_data)

        # Create result object
        result = BenchmarkResult(
            target_name=self.target_name,
            service=self.target_config.service,
            mode=self.target_config.mode,
            concurrency=self.concurrency,
            duration=self.duration,
            warmup=self.warmup,
            batch_size=self.batch_size,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            summary=summary,
            time_series=aggregated_ts,
            raw_latencies=successful_latencies[-10000:],  # Keep last 10k for histogram
            errors=errors[:100],  # Keep first 100 errors
            output_path=run_dir,
        )

        # Save results
        self._save_results(result, run_dir)

        return result

    def _save_results(self, result: BenchmarkResult, run_dir: Path) -> None:
        """Save benchmark results to files."""
        # Full result JSON
        result_dict = {
            "target_name": result.target_name,
            "service": result.service,
            "mode": result.mode,
            "concurrency": result.concurrency,
            "duration": result.duration,
            "warmup": result.warmup,
            "batch_size": result.batch_size,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "summary": result.summary,
            "time_series": result.time_series,
            "errors": result.errors,
        }

        with open(run_dir / "result.json", "w") as f:
            json.dump(result_dict, f, indent=2)

        # Summary JSON (smaller, for quick comparison)
        summary_dict = {
            "target_name": result.target_name,
            "service": result.service,
            "mode": result.mode,
            "concurrency": result.concurrency,
            **result.summary,
        }

        with open(run_dir / "summary.json", "w") as f:
            json.dump(summary_dict, f, indent=2)

        # Latency histogram data
        with open(run_dir / "latencies.json", "w") as f:
            json.dump({"latencies_ms": result.raw_latencies}, f)

        print(f"Results saved to {run_dir}")


def aggregate_time_series(data: List[Dict]) -> List[Dict]:
    """Aggregate time series data by second across all workers."""
    if not data:
        return []

    # Group by second
    by_second = {}
    for entry in data:
        second = int(entry["timestamp"])
        if second not in by_second:
            by_second[second] = {"writes": 0, "latencies": []}
        by_second[second]["writes"] += entry["writes"]
        if entry["avg_latency_ms"] > 0:
            by_second[second]["latencies"].append(entry["avg_latency_ms"])

    # Build aggregated list
    result = []
    min_second = min(by_second.keys())
    for second in sorted(by_second.keys()):
        entry = by_second[second]
        result.append({
            "elapsed_sec": second - min_second,
            "throughput_wps": entry["writes"],
            "avg_latency_ms": (
                np.mean(entry["latencies"]) if entry["latencies"] else 0
            ),
        })

    return result
