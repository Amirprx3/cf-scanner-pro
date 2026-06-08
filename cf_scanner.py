#!/usr/bin/env python3
"""
CF Scanner Pro - Advanced Cloudflare Clean IP Scanner
Author: Built for Amirhossein Bahrami
"""

import argparse
import sys
import os

from modules.cli import run_interactive
from modules.scanner import Scanner
from modules.config import ScanConfig
from modules.display import Display


def parse_args():
    parser = argparse.ArgumentParser(
        prog="cf-scanner",
        description="Advanced Cloudflare Clean IP Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cf_scanner.py                          # Interactive mode
  python cf_scanner.py -f hosts.txt -t 100     # Scan with 100 threads
  python cf_scanner.py -f hosts.txt --tls-only  # TLS check only
  python cf_scanner.py -f hosts.txt -o results  # Save to results.csv & results.json
  python cf_scanner.py -r 104.16.0.0/12        # Scan a CIDR range directly
        """,
    )

    parser.add_argument(
        "-f", "--file",
        help="Path to IP ranges file (.txt)",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-r", "--range",
        help="CIDR range to scan (e.g. 104.16.0.0/20)",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-t", "--threads",
        help="Number of concurrent threads (default: 100)",
        type=int,
        default=100,
    )
    parser.add_argument(
        "-T", "--timeout",
        help="Timeout per check in seconds (default: 3)",
        type=float,
        default=3.0,
    )
    parser.add_argument(
        "--top",
        help="Show only top N results by latency (default: all)",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--tls-only",
        help="Skip ping; do TLS + HTTP checks only",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--no-speed",
        help="Skip download speed test (faster scan)",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file base name (no extension). Creates .csv and .json",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--min-score",
        help="Only save IPs with quality score >= N (1-100, default: 1)",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--sni",
        help="SNI hostname for TLS checks (default: speed.cloudflare.com)",
        type=str,
        default="speed.cloudflare.com",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # No args → interactive mode
    if len(sys.argv) == 1:
        run_interactive()
        return

    config = ScanConfig(
        threads=args.threads,
        timeout=args.timeout,
        tls_only=args.tls_only,
        do_speed=not args.no_speed,
        output_base=args.output,
        min_score=args.min_score,
        sni=args.sni,
        top_n=args.top,
    )

    display = Display()
    display.print_banner()

    scanner = Scanner(config, display)

    if args.range:
        scanner.scan_cidr(args.range)
    elif args.file:
        if not os.path.exists(args.file):
            display.error(f"File not found: {args.file}")
            sys.exit(1)
        scanner.scan_file(args.file)
    else:
        display.error("Provide --file or --range. Use -h for help.")
        sys.exit(1)


if __name__ == "__main__":
    main()


# made by Amirprx3