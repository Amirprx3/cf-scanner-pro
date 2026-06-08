"""
cli.py – interactive wizard for running without flags.
"""

import os
from .display import Display
from .config import ScanConfig
from .scanner import Scanner


def run_interactive():
    display = Display()
    display.print_banner()

    display.console.print("[bold cyan]Interactive mode[/bold cyan] – answer a few questions.\n")

    # ── Source ───────────────────────────────────────────────
    source = input("  IP file path (or CIDR like 104.16.0.0/20) [hosts.txt]: ").strip()
    if not source:
        source = "hosts.txt"

    is_cidr = "/" in source and not os.path.exists(source)

    # ── Threads ──────────────────────────────────────────────
    t_input = input("  Threads [100]: ").strip()
    threads = int(t_input) if t_input.isdigit() else 100

    # ── Timeout ──────────────────────────────────────────────
    to_input = input("  Timeout per check in seconds [3]: ").strip()
    try:
        timeout = float(to_input) if to_input else 3.0
    except ValueError:
        timeout = 3.0

    # ── TLS only ─────────────────────────────────────────────
    tls_only_input = input("  Skip ping, TCP checks? TLS-only mode? [y/N]: ").strip().lower()
    tls_only = tls_only_input in ("y", "yes")

    # ── Speed test ───────────────────────────────────────────
    speed_input = input("  Run download speed test? [Y/n]: ").strip().lower()
    do_speed = speed_input not in ("n", "no")

    # ── Output ───────────────────────────────────────────────
    out_input = input("  Output file base name [results]: ").strip()
    output_base = out_input if out_input else "results"

    # ── Top N ────────────────────────────────────────────────
    top_input = input("  Show only top N results? (leave blank = all): ").strip()
    top_n = int(top_input) if top_input.isdigit() else None

    display.console.print()

    config = ScanConfig(
        threads=threads,
        timeout=timeout,
        tls_only=tls_only,
        do_speed=do_speed,
        output_base=output_base,
        top_n=top_n,
    )

    scanner = Scanner(config, display)

    if is_cidr:
        scanner.scan_cidr(source)
    else:
        if not os.path.exists(source):
            display.error(f"File not found: {source}")
            return
        scanner.scan_file(source)
