"""Hardware spike harness for Stage 1.

Standalone script executed in .venv-spike to measure memory and swap usage.
"""

import asyncio
import os
from pathlib import Path
import sys
import time
from typing import List, Tuple

import psutil


def check_environment() -> None:
    """Ensure script is running in .venv-spike and not .venv."""
    env_dir = Path(sys.prefix).name.lower()
    if env_dir == ".venv":
        print(
            "ERROR: Hardware spike harness cannot be run in the application environment (.venv).\n"
            "This harness must only be executed inside the isolated '.venv-spike' environment.",
            file=sys.stderr,
        )
        sys.exit(1)


def get_package_sizes() -> List[Tuple[str, str]]:
    """Inspect installed sizes of torch, faiss, sentence-transformers in site-packages."""
    sizes = []
    target_names = ["torch", "faiss", "sentence_transformers"]
    site_packages_dirs = [p for p in sys.path if "site-packages" in p]

    for target in target_names:
        total_size = 0
        found = False
        for sp in site_packages_dirs:
            sp_path = Path(sp)
            for item in sp_path.glob(f"{target}*"):
                found = True
                if item.is_file():
                    total_size += item.stat().st_size
                elif item.is_dir():
                    for f in item.rglob("*"):
                        if f.is_file():
                            total_size += f.stat().st_size
        if found:
            size_mb = total_size / (1024 * 1024)
            sizes.append((target, f"{size_mb:.1f} MB"))
        else:
            sizes.append((target, "Not found / not installed"))
    return sizes


def get_total_rss() -> int:
    """Return total RSS bytes for current process and all child processes."""
    proc = psutil.Process()
    rss = proc.memory_info().rss
    try:
        for child in proc.children(recursive=True):
            try:
                rss += child.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return rss


def get_swap_used_bytes() -> int:
    """Return used swap/pagefile in bytes with kernel32 fallback if PDH counters are disabled."""
    try:
        return psutil.swap_memory().used
    except Exception:
        pass

    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ('dwLength', ctypes.c_ulong),
                ('dwMemoryLoad', ctypes.c_ulong),
                ('ullTotalPhys', ctypes.c_ulonglong),
                ('ullAvailPhys', ctypes.c_ulonglong),
                ('ullTotalPageFile', ctypes.c_ulonglong),
                ('ullAvailPageFile', ctypes.c_ulonglong),
                ('ullTotalVirtual', ctypes.c_ulonglong),
                ('ullAvailVirtual', ctypes.c_ulonglong),
                ('ullAvailExtendedVirtual', ctypes.c_ulonglong)
            ]
        ms = MEMORYSTATUSEX()
        ms.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
            return int(ms.ullTotalPageFile - ms.ullAvailPageFile)
    except Exception:
        pass
    return 0


async def run_spike(duration_seconds: int = 300) -> None:
    check_environment()

    print("=" * 60)
    print("ZOE INTELLIGENCE ENGINE — HARDWARE SPIKE HARNESS (STAGE 1)")
    print("=" * 60)

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(
            f"ERROR: Missing dependency ({e}).\n"
            "Please ensure you are in .venv-spike and have installed:\n"
            "  pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
            "  pip install faiss-cpu sentence-transformers psutil\n",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\n[1/4] Inspecting package install sizes in spike environment...")
    for pkg, size_str in get_package_sizes():
        print(f"  - {pkg}: {size_str}")

    print("\n[2/4] Loading embedding model 'sentence-transformers/all-MiniLM-L6-v2'...")
    model_load_start = time.time()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"  Loaded model in {time.time() - model_load_start:.2f}s")

    print("\n[3/4] Embedding 100 chunks of representative text...")
    sample_texts = [
        f"Community discussion message sample #{i}: Discussing Zoe architecture, "
        f"operational SQLite storage, pragmas, and privacy redaction for telegram group."
        for i in range(100)
    ]
    t0 = time.time()
    embeddings = model.encode(sample_texts, show_progress_bar=False)
    t_embed = time.time() - t0
    throughput = len(sample_texts) / t_embed if t_embed > 0 else 0
    print(f"  Embedded {len(sample_texts)} chunks in {t_embed:.2f}s ({throughput:.1f} chunks/sec)")

    print(f"\n[4/4] Starting 5-minute sampling loop ({duration_seconds}s, 1s interval)...")
    print("  Simulating background polling loop and sampling memory...")

    rss_samples: List[int] = []
    initial_swap = get_swap_used_bytes()

    start_loop = time.time()
    iteration = 0
    while time.time() - start_loop < duration_seconds:
        iteration += 1
        current_rss = get_total_rss()
        rss_samples.append(current_rss)

        if iteration % 30 == 0 or iteration == 1:
            elapsed = int(time.time() - start_loop)
            print(f"  [{elapsed:3d}s / {duration_seconds}s] Current RSS: {current_rss / (1024**2):.1f} MB")

        await asyncio.sleep(1.0)

    final_swap = get_swap_used_bytes()
    swap_delta = final_swap - initial_swap

    # Compute statistics
    peak_rss = max(rss_samples) if rss_samples else 0
    sorted_rss = sorted(rss_samples)
    p95_idx = int(0.95 * len(sorted_rss))
    p95_rss = sorted_rss[min(p95_idx, len(sorted_rss) - 1)] if sorted_rss else 0

    p95_rss_gb = p95_rss / (1024 ** 3)
    swap_delta_mb = swap_delta / (1024 ** 2)

    p95_pass = p95_rss_gb <= 6.5
    swap_pass = swap_delta_mb <= 64.0
    overall_pass = p95_pass and swap_pass

    print("\n" + "=" * 60)
    print("SPIKE MEASUREMENT RESULTS")
    print("=" * 60)
    print(f"Peak RSS:               {peak_rss / (1024**3):.2f} GB ({peak_rss / (1024**2):.1f} MB)")
    print(f"p95 RSS:                {p95_rss_gb:.2f} GB (Threshold: <= 6.5 GB) -> {'PASS' if p95_pass else 'FAIL'}")
    print(f"Initial Swap Used:      {initial_swap / (1024**2):.1f} MB")
    print(f"Final Swap Used:        {final_swap / (1024**2):.1f} MB")
    print(f"Swap Delta:             {swap_delta_mb:.1f} MB (Threshold: <= 64 MB) -> {'PASS' if swap_pass else 'FAIL'}")
    print(f"Embedding Throughput:   {throughput:.1f} chunks/sec")
    print("-" * 60)
    print(f"OVERALL VERDICT:        {'OVERALL PASS' if overall_pass else 'OVERALL FAIL'}")
    print("=" * 60)
    print("\nPlease copy these measured values into 'docs/HARDWARE_SPIKE.md'.")


def main() -> None:
    duration = 300
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            pass
    asyncio.run(run_spike(duration_seconds=duration))


run = main


if __name__ == "__main__":
    main()

