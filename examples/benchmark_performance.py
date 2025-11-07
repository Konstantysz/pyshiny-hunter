"""Performance benchmarking suite for PyShiny Hunter.

This script measures and visualizes performance metrics across different configurations:

Benchmarks:
1. OCR Performance: CPU vs GPU speed comparison (isolated OCR pipeline)
2. Full CV Pipeline: CV detection + OCR on real frames (no emulator)
3. End-to-End: Complete pipeline with DeSmuME emulator
4. Multi-Worker Scaling: 1 vs 2 vs 4 vs 8 vs 12 vs 16 workers
5. Memory Usage: Per-worker memory consumption
6. Startup Time: With background OCR loading

Output:
- JSON results file (benchmark_results.json)
- Markdown table (benchmark_results.md)
- Performance charts (PNG files)

Usage:
    python examples/benchmark_performance.py --rom path/to/rom.nds --state path/to/state.dst
    python examples/benchmark_performance.py --rom path/to/rom.nds --state path/to/state.dst --quick
    python examples/benchmark_performance.py --rom path/to/rom.nds --state path/to/state.dst --output results/
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import psutil

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyshiny_hunter import config
from pyshiny_hunter.enhanced_ocr import EnhancedOCR
from pyshiny_hunter.module_logger import logger


def load_pokemon_database() -> dict[str, int]:
    """Load Pokemon database from CSV files.

    Returns:
        Dictionary mapping Pokemon names to Pokedex numbers.
    """
    pokemon_database: dict[str, int] = {}
    for gen_file in config.POKEMON_CSV_FILES:
        try:
            with open(f"{config.POKEMON_DATABASE_PATH}{gen_file}", encoding="utf-8") as file:
                next(file)  # Skip header line
                entries = (
                    (
                        line.split(",")[1].strip(),
                        int(line.split(",")[0].strip()),
                    )
                    for line in file
                    if line.strip()
                    and "," in line
                    and not line.startswith("number")
                    and len(line.split(",")) > 1
                )
                pokemon_database.update(entries)
        except FileNotFoundError:
            logger.warning(f"File {gen_file} not found. Skipping.")

    return pokemon_database


def _worker_process_frames(rom_path: str, state_path: str, duration_sec: int) -> int:
    """Worker function that processes frames through the emulator + hunter pipeline.

    This function is called by each worker process in the multiprocessing pool.

    Args:
        rom_path: Path to ROM file
        state_path: Path to save state file
        duration_sec: Duration to run the worker (seconds)

    Returns:
        Number of frames processed
    """
    from desmume.emulator import DeSmuME

    from pyshiny_hunter.black2_hunter import Black2Hunter

    # Initialize emulator and hunter
    emu = DeSmuME()
    emu.open(rom_path)
    emu.savestate.load_file(state_path)
    hunter = Black2Hunter()

    # Process frames for the specified duration
    start_time = time.perf_counter()
    frames_processed = 0

    while (time.perf_counter() - start_time) < duration_sec:
        # Emulate one frame
        emu.cycle()

        # Capture screenshot and split
        screen = np.array(emu.screenshot().convert("RGBA"))[:, :, ::-1].copy()
        top_screen = screen[: int(screen.shape[0] / 2), :, 1:]
        bottom_screen = screen[int(screen.shape[0] / 2) :, :, 1:]

        # Process through CV + OCR pipeline
        hunter.send("searching_pokemon", top_screen, bottom_screen)

        frames_processed += 1

    return frames_processed


@dataclass
class BenchmarkResult:
    """Single benchmark measurement result."""

    name: str
    value: float
    unit: str
    metadata: dict[str, Any]
    timestamp: str


@dataclass
class BenchmarkSuite:
    """Complete benchmark suite results."""

    system_info: dict[str, Any]
    ocr_benchmarks: list[BenchmarkResult]
    pipeline_benchmarks: list[BenchmarkResult]  # Full CV + OCR pipeline
    worker_benchmarks: list[BenchmarkResult]
    memory_benchmarks: list[BenchmarkResult]
    startup_benchmarks: list[BenchmarkResult]
    timestamp: str


class PerformanceBenchmark:
    """Performance benchmarking system for PyShiny Hunter."""

    def __init__(self, rom_path: str, state_path: str, output_dir: str = "benchmark_output"):
        """Initialize benchmark suite.

        Args:
            rom_path: Path to Pokemon ROM file
            state_path: Path to save state file
            output_dir: Directory for output files
        """
        self.rom_path = rom_path
        self.state_path = state_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results = BenchmarkSuite(
            system_info=self._collect_system_info(),
            ocr_benchmarks=[],
            pipeline_benchmarks=[],
            worker_benchmarks=[],
            memory_benchmarks=[],
            startup_benchmarks=[],
            timestamp=datetime.now().isoformat(),
        )

        logger.info(f"Benchmark suite initialized. Output directory: {self.output_dir}")

    def _collect_system_info(self) -> dict[str, Any]:
        """Collect system information for benchmark context."""
        info = {
            "cpu_count": psutil.cpu_count(logical=False),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else "N/A",
            "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
        }

        # Check GPU availability
        try:
            import torch

            info["gpu_available"] = torch.cuda.is_available()
            if torch.cuda.is_available():
                info["gpu_name"] = torch.cuda.get_device_name(0)
                info["gpu_memory_gb"] = round(
                    torch.cuda.get_device_properties(0).total_memory / (1024**3), 2
                )
        except ImportError:
            info["gpu_available"] = False
            info["gpu_name"] = "N/A"
            info["gpu_memory_gb"] = 0

        return info

    def benchmark_ocr_performance(self, num_samples: int = 100) -> None:
        """Benchmark OCR performance on CPU vs GPU.

        Args:
            num_samples: Number of OCR operations to perform
        """
        logger.info("=" * 70)
        logger.info("BENCHMARK 1: OCR Performance (CPU vs GPU)")
        logger.info("=" * 70)

        # Load Pokemon database
        pokemon_db = load_pokemon_database()

        # Generate synthetic test images (simulating Pokemon name regions)
        test_images = self._generate_test_ocr_images(num_samples)

        # Test GPU performance (if available)
        if self.results.system_info["gpu_available"]:
            logger.info(f"\n[GPU Test] Running {num_samples} OCR operations...")
            ocr_gpu = EnhancedOCR(pokemon_database=pokemon_db)
            # Force GPU mode by waiting for reader to load
            _ = ocr_gpu.reader

            start_time = time.perf_counter()
            for img in test_images:
                ocr_gpu.recognize(img)
            gpu_duration = time.perf_counter() - start_time

            gpu_ops_per_sec = num_samples / gpu_duration
            logger.info(f"GPU: {gpu_duration:.2f}s total | {gpu_ops_per_sec:.1f} ops/sec")

            self.results.ocr_benchmarks.append(
                BenchmarkResult(
                    name="OCR GPU Speed",
                    value=round(gpu_ops_per_sec, 2),
                    unit="ops/sec",
                    metadata={
                        "total_time_sec": round(gpu_duration, 2),
                        "num_samples": num_samples,
                        "gpu_name": self.results.system_info.get("gpu_name", "Unknown"),
                    },
                    timestamp=datetime.now().isoformat(),
                )
            )

        # Test CPU performance
        logger.info(f"\n[CPU Test] Running {num_samples} OCR operations...")
        # Force CPU mode by temporarily disabling GPU
        import torch

        original_cuda = torch.cuda.is_available
        torch.cuda.is_available = lambda: False  # type: ignore

        ocr_cpu = EnhancedOCR(pokemon_database=pokemon_db)
        _ = ocr_cpu.reader

        start_time = time.perf_counter()
        for img in test_images:
            ocr_cpu.recognize(img)
        cpu_duration = time.perf_counter() - start_time

        torch.cuda.is_available = original_cuda  # type: ignore

        cpu_ops_per_sec = num_samples / cpu_duration
        logger.info(f"CPU: {cpu_duration:.2f}s total | {cpu_ops_per_sec:.1f} ops/sec")

        self.results.ocr_benchmarks.append(
            BenchmarkResult(
                name="OCR CPU Speed",
                value=round(cpu_ops_per_sec, 2),
                unit="ops/sec",
                metadata={
                    "total_time_sec": round(cpu_duration, 2),
                    "num_samples": num_samples,
                },
                timestamp=datetime.now().isoformat(),
            )
        )

        # Calculate speedup
        if self.results.system_info["gpu_available"]:
            speedup = gpu_ops_per_sec / cpu_ops_per_sec
            logger.info(f"\nGPU Speedup: {speedup:.2f}x faster than CPU")
            self.results.ocr_benchmarks.append(
                BenchmarkResult(
                    name="GPU Speedup",
                    value=round(speedup, 2),
                    unit="x",
                    metadata={},
                    timestamp=datetime.now().isoformat(),
                )
            )

        logger.info("✓ OCR benchmark complete\n")

    def benchmark_startup_time(self, num_runs: int = 5) -> None:
        """Benchmark application startup time with background OCR loading.

        Args:
            num_runs: Number of startup measurements to average
        """
        logger.info("=" * 70)
        logger.info("BENCHMARK 2: Startup Time (Background OCR Loading)")
        logger.info("=" * 70)

        pokemon_db = load_pokemon_database()

        startup_times = []

        for i in range(num_runs):
            logger.info(f"\n[Run {i + 1}/{num_runs}] Measuring startup time...")

            start_time = time.perf_counter()

            # Simulate startup: Initialize OCR and wait for background load
            ocr = EnhancedOCR(pokemon_database=pokemon_db)
            _ = ocr.reader  # Wait for background thread to finish loading

            startup_duration = time.perf_counter() - start_time
            startup_times.append(startup_duration)

            logger.info(f"Startup time: {startup_duration:.2f}s")

        avg_startup = np.mean(startup_times)
        std_startup = np.std(startup_times)

        logger.info(f"\nAverage startup time: {avg_startup:.2f}s ± {std_startup:.2f}s")

        self.results.startup_benchmarks.append(
            BenchmarkResult(
                name="Average Startup Time",
                value=round(avg_startup, 2),
                unit="seconds",
                metadata={
                    "std_dev": round(std_startup, 2),
                    "num_runs": num_runs,
                    "min": round(min(startup_times), 2),
                    "max": round(max(startup_times), 2),
                },
                timestamp=datetime.now().isoformat(),
            )
        )

        logger.info("✓ Startup benchmark complete\n")

    def benchmark_worker_scaling(self, duration_per_config: int = 30) -> None:
        """Benchmark REAL multi-worker scaling with actual process spawning.

        Args:
            duration_per_config: Duration to run each configuration (seconds)

        Note:
            This spawns actual worker processes running DeSmuME + Black2Hunter.
            Measures real performance including GPU contention and CPU bottlenecks.
        """
        logger.info("=" * 70)
        logger.info("BENCHMARK 3: Multi-Worker Scaling (REAL MEASUREMENTS)")
        logger.info("=" * 70)
        logger.info(
            f"\nRunning ACTUAL multi-worker benchmarks ({duration_per_config}s per configuration)"
            "\nThis measures real-world performance with GPU contention and CPU bottlenecks."
        )

        # Import required modules
        try:
            from desmume.emulator import DeSmuME  # noqa: F401

            from pyshiny_hunter.black2_hunter import Black2Hunter  # noqa: F401
        except ImportError as e:
            logger.warning(
                f"\nSkipping multi-worker benchmark: {e}"
                "\nEnsure DeSmuME and Black2Hunter are available."
            )
            return

        worker_counts = [1, 2, 4, 8, 12]
        encounter_cycle_frames = 450  # Average frames per encounter (from documentation)
        base_encounters_per_min = None  # Will be set after first worker measurement

        for num_workers in worker_counts:
            logger.info(f"\n[{num_workers} Worker(s)] - Running for {duration_per_config}s...")

            # Measure performance
            start_time = time.perf_counter()

            # Spawn worker processes
            with multiprocessing.Pool(processes=num_workers) as pool:
                # Each worker runs the emulator + hunter pipeline for the specified duration
                results = pool.starmap(
                    _worker_process_frames,
                    [
                        (self.rom_path, self.state_path, duration_per_config)
                        for _ in range(num_workers)
                    ],
                )

            duration = time.perf_counter() - start_time

            # Calculate total frames processed
            total_frames = sum(results)
            total_fps = total_frames / duration

            # Calculate encounters/min (frames per minute / frames per encounter)
            encounters_per_min = (total_frames / duration) * 60 / encounter_cycle_frames

            # Measure memory usage
            memory_mb = self._measure_memory_usage(num_workers)

            logger.info(f"  Frames processed: {total_frames}")
            logger.info(f"  Total FPS: {total_fps:.1f}")
            logger.info(f"  Encounters/min: {encounters_per_min:.1f}")
            logger.info(f"  Memory usage: {memory_mb:.0f} MB")

            # Calculate scaling efficiency (vs single worker)
            if base_encounters_per_min is None:
                base_encounters_per_min = encounters_per_min
                efficiency = 100.0
            else:
                efficiency = (encounters_per_min / num_workers) / base_encounters_per_min * 100

            logger.info(f"  Scaling efficiency: {efficiency:.1f}%")

            self.results.worker_benchmarks.append(
                BenchmarkResult(
                    name=f"{num_workers} Worker(s) - Encounters/min",
                    value=round(encounters_per_min, 1),
                    unit="encounters/min",
                    metadata={
                        "num_workers": num_workers,
                        "total_frames": total_frames,
                        "total_fps": round(total_fps, 1),
                        "duration_sec": round(duration, 1),
                        "efficiency_pct": round(efficiency, 1),
                        "type": "measured",
                    },
                    timestamp=datetime.now().isoformat(),
                )
            )

            self.results.memory_benchmarks.append(
                BenchmarkResult(
                    name=f"{num_workers} Worker(s) - Memory",
                    value=round(memory_mb, 0),
                    unit="MB",
                    metadata={
                        "num_workers": num_workers,
                        "type": "measured",
                    },
                    timestamp=datetime.now().isoformat(),
                )
            )

        logger.info("\n✓ Worker scaling benchmark complete\n")

    def _measure_memory_usage(self, num_workers: int) -> float:
        """Measure current process memory usage.

        Args:
            num_workers: Number of workers (for context, not used directly)

        Returns:
            Memory usage in MB
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        return float(memory_info.rss) / (1024 * 1024)  # Convert bytes to MB

    def benchmark_full_pipeline(self, num_frames: int = 300) -> None:
        """Benchmark end-to-end performance with DeSmuME emulator.

        Args:
            num_frames: Number of frames to process through the emulator (default: 300 = ~5 seconds)

        Note:
            This measures real-world performance including emulator overhead:
            - DeSmuME emulation
            - Screenshot capture
            - CV detection pipeline
            - OCR name recognition
        """
        logger.info("=" * 70)
        logger.info("BENCHMARK 4: End-to-End Performance (DeSmuME Emulator)")
        logger.info("=" * 70)

        # Import required modules
        try:
            from desmume.emulator import DeSmuME

            from pyshiny_hunter.black2_hunter import Black2Hunter
        except ImportError as e:
            logger.warning(
                f"\nSkipping end-to-end benchmark: {e}"
                "\nEnsure DeSmuME and Black2Hunter are available."
            )
            return

        # Initialize DeSmuME emulator
        logger.info("\nInitializing DeSmuME emulator...")
        logger.info(f"  ROM: {self.rom_path}")
        logger.info(f"  State: {self.state_path}")

        try:
            emu = DeSmuME()
            emu.open(self.rom_path)

            # Load save state
            emu.savestate.load_file(self.state_path)

            logger.info("✓ Emulator initialized and save state loaded")
        except Exception as e:
            logger.warning(f"Failed to initialize emulator: {e}")
            return

        # Initialize Black2Hunter
        logger.info("\nInitializing Black2Hunter with full pipeline...")
        hunter = Black2Hunter()

        # Warm-up: Process a few frames to ensure OCR is loaded
        logger.info("Warming up (5 frames)...")
        for _ in range(5):
            emu.cycle()
            # Get screenshot and split into top/bottom screens
            screen = np.array(emu.screenshot().convert("RGBA"))[:, :, ::-1].copy()
            top_screen = screen[: int(screen.shape[0] / 2), :, 1:]
            bottom_screen = screen[int(screen.shape[0] / 2) :, :, 1:]
            # Send frame to hunter state machine
            hunter.send("searching_pokemon", top_screen, bottom_screen)

        # Benchmark: Process frames through complete pipeline
        logger.info(f"\nBenchmarking {num_frames} frames through end-to-end pipeline...")
        logger.info("  (Emulator → Screenshot → CV Detection → OCR)")

        start_time = time.perf_counter()
        frames_processed = 0

        for _ in range(num_frames):
            # Emulate one frame
            emu.cycle()

            # Capture screenshot and split (this is overhead #1)
            screen = np.array(emu.screenshot().convert("RGBA"))[:, :, ::-1].copy()
            top_screen = screen[: int(screen.shape[0] / 2), :, 1:]
            bottom_screen = screen[int(screen.shape[0] / 2) :, :, 1:]

            # Process through CV + OCR pipeline (this is overhead #2)
            hunter.send("searching_pokemon", top_screen, bottom_screen)

            frames_processed += 1

        duration = time.perf_counter() - start_time
        fps = frames_processed / duration
        frame_time_ms = (duration / frames_processed) * 1000

        logger.info("\nEnd-to-End Performance:")
        logger.info(f"  Total time: {duration:.2f}s")
        logger.info(f"  Frames processed: {frames_processed}")
        logger.info(f"  FPS: {fps:.1f}")
        logger.info(f"  Frame time: {frame_time_ms:.1f}ms per frame")

        self.results.pipeline_benchmarks.append(
            BenchmarkResult(
                name="End-to-End FPS (with DeSmuME)",
                value=round(fps, 1),
                unit="fps",
                metadata={
                    "num_frames": frames_processed,
                    "total_time_sec": round(duration, 2),
                    "frame_time_ms": round(frame_time_ms, 1),
                    "type": "end_to_end_emulator",
                },
                timestamp=datetime.now().isoformat(),
            )
        )

        # Calculate total overhead breakdown
        if self.results.ocr_benchmarks:
            gpu_ocr_speed = next(
                (r.value for r in self.results.ocr_benchmarks if r.name == "OCR GPU Speed"),
                None,
            )
            if gpu_ocr_speed:
                # Isolated OCR time
                ocr_time_ms = 1000 / gpu_ocr_speed

                # End-to-end time
                total_time_ms = frame_time_ms

                # Calculate overhead
                overhead_ms = total_time_ms - ocr_time_ms
                overhead_pct = (overhead_ms / total_time_ms) * 100

                logger.info("\nOverhead Breakdown:")
                logger.info(
                    f"  Isolated OCR time: {ocr_time_ms:.1f}ms ({(ocr_time_ms / total_time_ms) * 100:.1f}%)"
                )
                logger.info(f"  Emulator + CV overhead: {overhead_ms:.1f}ms ({overhead_pct:.1f}%)")
                logger.info(f"  Total frame time: {total_time_ms:.1f}ms")
                logger.info(f"\n  → Emulator + CV detection adds {overhead_ms:.1f}ms per frame")
                logger.info(f"  → Maximum achievable FPS: {1000 / total_time_ms:.1f} fps")

                self.results.pipeline_benchmarks.append(
                    BenchmarkResult(
                        name="Emulator + CV Overhead",
                        value=round(overhead_pct, 1),
                        unit="%",
                        metadata={
                            "overhead_ms": round(overhead_ms, 1),
                            "ocr_time_ms": round(ocr_time_ms, 1),
                            "total_frame_time_ms": round(total_time_ms, 1),
                            "max_fps": round(1000 / total_time_ms, 1),
                        },
                        timestamp=datetime.now().isoformat(),
                    )
                )

        logger.info("\n✓ End-to-end benchmark complete\n")

    def _generate_test_ocr_images(self, num_images: int) -> list[np.ndarray]:
        """Generate synthetic test images for OCR benchmarking.

        Args:
            num_images: Number of test images to generate

        Returns:
            List of BGR images (numpy arrays)
        """
        import cv2 as cv

        # Create realistic Pokemon name region images
        # Dimensions based on config.py OCR region settings
        width = config.OCR_NAME_REGION_X_END - config.OCR_NAME_REGION_X_START
        height = config.OCR_NAME_REGION_Y_END - config.OCR_NAME_REGION_Y_START

        test_images = []

        pokemon_names = ["WATCHOG", "PATRAT", "PIKACHU", "CHARIZARD", "BULBASAUR"]

        for i in range(num_images):
            # Create white background
            img = np.ones((height, width, 3), dtype=np.uint8) * 255

            # Add text (simulating Pokemon name)
            name = pokemon_names[i % len(pokemon_names)]
            font = cv.FONT_HERSHEY_SIMPLEX
            font_scale = 0.4
            thickness = 1

            # Center text
            text_size = cv.getTextSize(name, font, font_scale, thickness)[0]
            text_x = (width - text_size[0]) // 2
            text_y = (height + text_size[1]) // 2

            cv.putText(img, name, (text_x, text_y), font, font_scale, (0, 0, 0), thickness)

            # Keep as BGR for OCR (EnhancedOCR expects BGR input)
            test_images.append(img)

        return test_images

    def generate_visualizations(self) -> None:
        """Generate performance visualization charts."""
        logger.info("=" * 70)
        logger.info("GENERATING VISUALIZATIONS")
        logger.info("=" * 70)

        # 1. OCR Performance Chart
        if self.results.ocr_benchmarks:
            self._plot_ocr_performance()

        # 2. Worker Scaling Chart
        if self.results.worker_benchmarks:
            self._plot_worker_scaling()

        # 3. Memory Usage Chart
        if self.results.memory_benchmarks:
            self._plot_memory_usage()

        # 4. Pipeline Comparison Chart (if emulator benchmark was run)
        if self.results.pipeline_benchmarks:
            self._plot_pipeline_comparison()

        logger.info("✓ Visualizations generated\n")

    def _plot_ocr_performance(self) -> None:
        """Generate OCR performance comparison chart."""
        ocr_results = {r.name: r.value for r in self.results.ocr_benchmarks}

        if "OCR GPU Speed" not in ocr_results or "OCR CPU Speed" not in ocr_results:
            logger.warning("Insufficient OCR data for chart")
            return

        # Check if we have emulator data
        end_to_end_fps = next(
            (
                r.value
                for r in self.results.pipeline_benchmarks
                if r.name == "End-to-End FPS (with DeSmuME)"
            ),
            None,
        )

        fig, ax = plt.subplots(figsize=(12, 6))

        if end_to_end_fps:
            configs = ["CPU\n(isolated)", "GPU\n(isolated)", "GPU + Emulator\n(end-to-end)"]
            speeds = [ocr_results["OCR CPU Speed"], ocr_results["OCR GPU Speed"], end_to_end_fps]
            colors = ["#3498db", "#2ecc71", "#e67e22"]
        else:
            configs = ["CPU", "GPU"]
            speeds = [ocr_results["OCR CPU Speed"], ocr_results["OCR GPU Speed"]]
            colors = ["#3498db", "#2ecc71"]

        bars = ax.bar(configs, speeds, color=colors, alpha=0.8, edgecolor="black")

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.1f}",
                ha="center",
                va="bottom",
                fontsize=12,
                fontweight="bold",
            )

        ax.set_ylabel("Operations/Frames per Second", fontsize=12, fontweight="bold")

        if end_to_end_fps:
            ax.set_title(
                "Performance Comparison: Isolated OCR vs End-to-End Pipeline",
                fontsize=14,
                fontweight="bold",
            )
        else:
            ax.set_title("OCR Performance: CPU vs GPU", fontsize=14, fontweight="bold")

        ax.set_ylim(0, max(speeds) * 1.2)
        ax.grid(axis="y", alpha=0.3)

        # Add speedup annotation
        if "GPU Speedup" in ocr_results:
            speedup = ocr_results["GPU Speedup"]
            annotation_text = f"GPU Speedup: {speedup:.2f}x"

            if end_to_end_fps:
                # Calculate overhead
                overhead_pct = (
                    (ocr_results["OCR GPU Speed"] - end_to_end_fps) / ocr_results["OCR GPU Speed"]
                ) * 100
                annotation_text += f"\nEmulator overhead: {overhead_pct:.1f}%"

            ax.text(
                0.5,
                0.95,
                annotation_text,
                transform=ax.transAxes,
                ha="center",
                va="top",
                fontsize=11,
                bbox={"boxstyle": "round", "facecolor": "yellow", "alpha": 0.7},
            )

        plt.tight_layout()
        output_path = self.output_dir / "ocr_performance.png"
        plt.savefig(output_path, dpi=150)
        logger.info(f"Saved chart: {output_path}")
        plt.close()

    def _plot_worker_scaling(self) -> None:
        """Generate worker scaling performance chart."""
        workers = []
        measured_encounters = []
        efficiencies = []

        for result in self.results.worker_benchmarks:
            if "Encounters/min" in result.name:
                workers.append(result.metadata["num_workers"])
                measured_encounters.append(result.value)
                efficiencies.append(result.metadata.get("efficiency_pct", 100.0))

        if not workers:
            logger.warning("No worker scaling data for chart")
            return

        # Calculate ideal linear scaling for reference
        if measured_encounters:
            base_rate = measured_encounters[0]  # Single worker baseline
            ideal_scaling = [base_rate * w for w in workers]
        else:
            ideal_scaling = []

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Chart 1: Measured Performance vs Ideal Linear Scaling
        # Plot ideal linear scaling (dotted reference line)
        if ideal_scaling:
            ax1.plot(
                workers,
                ideal_scaling,
                marker="",
                linewidth=2,
                linestyle=":",
                color="#95a5a6",
                alpha=0.5,
                label="Ideal Linear Scaling",
            )

        # Plot measured performance
        ax1.plot(
            workers,
            measured_encounters,
            marker="o",
            linewidth=3,
            markersize=12,
            color="#e74c3c",
            label="Measured Performance",
        )

        # Add value labels
        for w, e in zip(workers, measured_encounters):
            ax1.text(w, e, f"{e:.1f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

        ax1.set_xlabel("Number of Workers", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Encounters per Minute", fontsize=12, fontweight="bold")
        ax1.set_title("Multi-Worker Scaling: Measured Performance", fontsize=14, fontweight="bold")
        ax1.set_xticks(workers)

        # Set y-axis limits based on data (add 15% margin for labels)
        if ideal_scaling:
            max_value = max(max(measured_encounters), max(ideal_scaling))
        else:
            max_value = max(measured_encounters)
        ax1.set_ylim(0, max_value * 1.15)

        ax1.grid(alpha=0.3)
        ax1.legend(fontsize=11, loc="upper left")

        # Chart 2: Scaling Efficiency
        colors = [
            "#2ecc71" if e >= 90 else "#f39c12" if e >= 70 else "#e74c3c" for e in efficiencies
        ]

        bars = ax2.bar(
            [str(w) for w in workers], efficiencies, color=colors, alpha=0.8, edgecolor="black"
        )

        # Add value labels
        for bar, eff in zip(bars, efficiencies):
            height = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{eff:.1f}%",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
            )

        ax2.axhline(
            y=100, color="#95a5a6", linestyle="--", alpha=0.5, label="100% Efficiency (Ideal)"
        )
        ax2.set_xlabel("Number of Workers", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Scaling Efficiency (%)", fontsize=12, fontweight="bold")
        ax2.set_title("Scaling Efficiency by Worker Count", fontsize=14, fontweight="bold")
        ax2.set_ylim(0, 110)
        ax2.grid(axis="y", alpha=0.3)
        ax2.legend(fontsize=10)

        plt.tight_layout()
        output_path = self.output_dir / "worker_scaling.png"
        plt.savefig(output_path, dpi=150)
        logger.info(f"Saved chart: {output_path}")
        plt.close()

    def _plot_memory_usage(self) -> None:
        """Generate memory usage chart."""
        workers = []
        memory_mb = []

        for result in self.results.memory_benchmarks:
            workers.append(result.metadata["num_workers"])
            memory_mb.append(result.value)

        if not workers:
            logger.warning("No memory usage data for chart")
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        bars = ax.bar(
            [str(w) for w in workers], memory_mb, color="#9b59b6", alpha=0.8, edgecolor="black"
        )

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.0f} MB",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        ax.set_xlabel("Number of Workers", fontsize=12, fontweight="bold")
        ax.set_ylabel("Memory Usage (MB)", fontsize=12, fontweight="bold")
        ax.set_title("Memory Usage by Worker Count", fontsize=14, fontweight="bold")
        ax.set_ylim(0, max(memory_mb) * 1.2)
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        output_path = self.output_dir / "memory_usage.png"
        plt.savefig(output_path, dpi=150)
        logger.info(f"Saved chart: {output_path}")
        plt.close()

    def _plot_pipeline_comparison(self) -> None:
        """Generate pipeline overhead comparison chart."""
        # Extract metrics
        ocr_gpu_speed = next(
            (r.value for r in self.results.ocr_benchmarks if r.name == "OCR GPU Speed"), None
        )
        end_to_end_fps = next(
            (
                r.value
                for r in self.results.pipeline_benchmarks
                if r.name == "End-to-End FPS (with DeSmuME)"
            ),
            None,
        )

        if not ocr_gpu_speed or not end_to_end_fps:
            logger.warning("Insufficient pipeline data for comparison chart")
            return

        # Convert to frame times (ms)
        ocr_time_ms = 1000 / ocr_gpu_speed
        end_to_end_time_ms = 1000 / end_to_end_fps
        emulator_cv_overhead_ms = end_to_end_time_ms - ocr_time_ms

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Chart 1: Stacked bar showing overhead breakdown
        categories = ["Isolated\nOCR", "End-to-End\n(+ Emulator + CV)"]
        ocr_times = [ocr_time_ms, ocr_time_ms]
        overhead_times = [0, emulator_cv_overhead_ms]

        ax1.bar(
            categories, ocr_times, color="#3498db", alpha=0.8, edgecolor="black", label="OCR Time"
        )
        ax1.bar(
            categories,
            overhead_times,
            bottom=ocr_times,
            color="#e74c3c",
            alpha=0.8,
            edgecolor="black",
            label="Emulator + CV Overhead",
        )

        # Add value labels
        for i, (_cat, ocr, overhead) in enumerate(zip(categories, ocr_times, overhead_times)):
            total = ocr + overhead
            ax1.text(
                i,
                total / 2,
                f"{ocr:.1f} ms",
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                color="white",
            )
            if overhead > 0:
                ax1.text(
                    i,
                    ocr + overhead / 2,
                    f"+{overhead:.1f} ms",
                    ha="center",
                    va="center",
                    fontsize=11,
                    fontweight="bold",
                    color="white",
                )
            # Total at top
            ax1.text(
                i,
                total + 1,
                f"{total:.1f} ms",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        ax1.set_ylabel("Frame Time (ms)", fontsize=12, fontweight="bold")
        ax1.set_title("Pipeline Overhead Breakdown", fontsize=14, fontweight="bold")
        ax1.legend(fontsize=10, loc="upper left")
        ax1.set_ylim(0, max(ocr_times[0], ocr_times[1] + overhead_times[1]) * 1.15)
        ax1.grid(axis="y", alpha=0.3)

        # Chart 2: FPS comparison
        fps_categories = ["Isolated OCR\n(theoretical max)", "End-to-End\n(with emulator)"]
        fps_values = [ocr_gpu_speed, end_to_end_fps]
        colors = ["#2ecc71", "#e67e22"]

        bars = ax2.bar(fps_categories, fps_values, color=colors, alpha=0.8, edgecolor="black")

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.1f} fps",
                ha="center",
                va="bottom",
                fontsize=12,
                fontweight="bold",
            )

        ax2.set_ylabel("Frames per Second", fontsize=12, fontweight="bold")
        ax2.set_title("FPS Comparison: OCR vs End-to-End", fontsize=14, fontweight="bold")
        ax2.set_ylim(0, max(fps_values) * 1.2)
        ax2.grid(axis="y", alpha=0.3)

        # Add overhead percentage annotation
        overhead_pct = (emulator_cv_overhead_ms / end_to_end_time_ms) * 100
        fig.text(
            0.5,
            0.02,
            f"Emulator + CV overhead: {overhead_pct:.1f}% ({emulator_cv_overhead_ms:.1f} ms per frame)",
            ha="center",
            fontsize=11,
            bbox={"boxstyle": "round", "facecolor": "yellow", "alpha": 0.7},
        )

        plt.tight_layout(rect=[0, 0.05, 1, 1])
        output_path = self.output_dir / "pipeline_comparison.png"
        plt.savefig(output_path, dpi=150)
        logger.info(f"Saved chart: {output_path}")
        plt.close()

    def export_results(self) -> None:
        """Export benchmark results to JSON and Markdown."""
        logger.info("=" * 70)
        logger.info("EXPORTING RESULTS")
        logger.info("=" * 70)

        # Export to JSON
        json_path = self.output_dir / "benchmark_results.json"
        with open(json_path, "w") as f:
            json.dump(asdict(self.results), f, indent=2)
        logger.info(f"Saved JSON: {json_path}")

        # Export to Markdown
        md_path = self.output_dir / "benchmark_results.md"
        self._generate_markdown_report(md_path)
        logger.info(f"Saved Markdown: {md_path}")

        logger.info("✓ Results exported\n")

    def _generate_markdown_report(self, output_path: Path) -> None:
        """Generate markdown report with tables and results.

        Args:
            output_path: Path to save markdown file
        """
        with open(output_path, "w") as f:
            f.write("# PyShiny Hunter - Performance Benchmark Results\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # System Information
            f.write("## System Information\n\n")
            f.write("| Component | Specification |\n")
            f.write("|-----------|---------------|\n")
            for key, value in self.results.system_info.items():
                formatted_key = key.replace("_", " ").title()
                f.write(f"| {formatted_key} | {value} |\n")
            f.write("\n")

            # OCR Benchmarks
            if self.results.ocr_benchmarks:
                f.write("## OCR Performance\n\n")
                f.write("| Metric | Value | Unit |\n")
                f.write("|--------|-------|------|\n")
                for result in self.results.ocr_benchmarks:
                    f.write(f"| {result.name} | {result.value} | {result.unit} |\n")
                f.write("\n")

            # Worker Scaling
            if self.results.worker_benchmarks:
                f.write("## Multi-Worker Scaling (Real Measurements)\n\n")
                f.write("| Workers | Encounters/min | Scaling Efficiency | Total FPS |\n")
                f.write("|---------|----------------|--------------------|-----------|\n")

                for result in self.results.worker_benchmarks:
                    num_workers = result.metadata["num_workers"]
                    rate = result.value
                    efficiency = result.metadata.get("efficiency_pct", 100.0)
                    total_fps = result.metadata.get("total_fps", "N/A")

                    f.write(f"| {num_workers} | {rate:.1f} | {efficiency:.1f}% | {total_fps} |\n")
                f.write("\n")

            # Memory Usage
            if self.results.memory_benchmarks:
                f.write("## Memory Usage\n\n")
                f.write("| Workers | Memory (MB) |\n")
                f.write("|---------|-------------|\n")
                for result in self.results.memory_benchmarks:
                    f.write(f"| {result.metadata['num_workers']} | {result.value:.0f} |\n")
                f.write("\n")

            # Startup Time
            if self.results.startup_benchmarks:
                f.write("## Startup Performance\n\n")
                f.write("| Metric | Value | Unit |\n")
                f.write("|--------|-------|------|\n")
                for result in self.results.startup_benchmarks:
                    f.write(f"| {result.name} | {result.value} | {result.unit} |\n")
                    if result.metadata:
                        f.write(
                            f"| Min/Max | {result.metadata.get('min', 'N/A')} / {result.metadata.get('max', 'N/A')} | {result.unit} |\n"
                        )
                f.write("\n")

            # End-to-End Pipeline Performance
            if self.results.pipeline_benchmarks:
                f.write("## End-to-End Pipeline Performance\n\n")
                f.write("| Metric | Value | Unit |\n")
                f.write("|--------|-------|------|\n")
                for result in self.results.pipeline_benchmarks:
                    f.write(f"| {result.name} | {result.value} | {result.unit} |\n")
                f.write("\n")

            # Charts
            f.write("## Performance Charts\n\n")
            if (self.output_dir / "ocr_performance.png").exists():
                f.write("### OCR Performance: CPU vs GPU\n\n")
                f.write("![OCR Performance](ocr_performance.png)\n\n")

            if (self.output_dir / "worker_scaling.png").exists():
                f.write("### Multi-Worker Scaling\n\n")
                f.write("![Worker Scaling](worker_scaling.png)\n\n")

            if (self.output_dir / "memory_usage.png").exists():
                f.write("### Memory Usage\n\n")
                f.write("![Memory Usage](memory_usage.png)\n\n")

            if (self.output_dir / "pipeline_comparison.png").exists():
                f.write("### Pipeline Overhead Comparison\n\n")
                f.write("![Pipeline Comparison](pipeline_comparison.png)\n\n")

    def run_full_suite(self, quick_mode: bool = False, with_emulator: bool = False) -> None:
        """Run complete benchmark suite.

        Args:
            quick_mode: If True, run reduced iterations for faster results
            with_emulator: If True, include end-to-end emulator benchmark (slower)
        """
        logger.info("\n" + "=" * 70)
        logger.info("PYSHINY HUNTER - PERFORMANCE BENCHMARK SUITE")
        logger.info("=" * 70)
        logger.info(f"Mode: {'QUICK' if quick_mode else 'FULL'}")
        logger.info(f"Emulator benchmark: {'ENABLED' if with_emulator else 'DISABLED'}")
        logger.info(f"Output: {self.output_dir}")
        logger.info("=" * 70 + "\n")

        # Adjust parameters for quick mode
        ocr_samples = 20 if quick_mode else 100
        startup_runs = 3 if quick_mode else 5
        emulator_frames = 150 if quick_mode else 300

        try:
            # Run benchmarks
            self.benchmark_ocr_performance(num_samples=ocr_samples)
            self.benchmark_startup_time(num_runs=startup_runs)
            self.benchmark_worker_scaling()

            # Optional: End-to-end emulator benchmark
            if with_emulator:
                self.benchmark_full_pipeline(num_frames=emulator_frames)

            # Generate outputs
            self.generate_visualizations()
            self.export_results()

            logger.info("=" * 70)
            logger.info("BENCHMARK SUITE COMPLETE!")
            logger.info("=" * 70)
            logger.info(f"\nResults saved to: {self.output_dir}")
            logger.info("  - benchmark_results.json")
            logger.info("  - benchmark_results.md")
            logger.info("  - ocr_performance.png")
            logger.info("  - worker_scaling.png")
            logger.info("  - memory_usage.png")

        except Exception as e:
            logger.error(f"Benchmark suite failed: {e}", exc_info=True)
            raise


def main() -> None:
    """Main entry point for benchmark script."""
    parser = argparse.ArgumentParser(
        description="PyShiny Hunter Performance Benchmark Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full benchmark suite
  python examples/benchmark_performance.py --rom roms/black2.nds --state savestate.dst

  # Quick mode (reduced iterations)
  python examples/benchmark_performance.py --rom roms/black2.nds --state savestate.dst --quick

  # Custom output directory
  python examples/benchmark_performance.py --rom roms/black2.nds --state savestate.dst --output results/
        """,
    )

    parser.add_argument("--rom", type=str, required=True, help="Path to Pokemon ROM file")
    parser.add_argument("--state", type=str, required=True, help="Path to save state file")
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_output",
        help="Output directory for results (default: benchmark_output)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode with reduced iterations for faster results",
    )
    parser.add_argument(
        "--with-emulator",
        action="store_true",
        help="Include end-to-end emulator benchmark (measures real-world FPS with DeSmuME overhead)",
    )

    args = parser.parse_args()

    # Validate paths
    if not os.path.exists(args.rom):
        logger.error(f"ROM file not found: {args.rom}")
        sys.exit(1)

    if not os.path.exists(args.state):
        logger.error(f"Save state file not found: {args.state}")
        sys.exit(1)

    # Run benchmark suite
    benchmark = PerformanceBenchmark(
        rom_path=args.rom, state_path=args.state, output_dir=args.output
    )
    benchmark.run_full_suite(quick_mode=args.quick, with_emulator=args.with_emulator)


if __name__ == "__main__":
    # Required for multiprocessing on Windows
    multiprocessing.freeze_support()
    main()
