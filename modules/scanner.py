"""
scanner.py – orchestrates the scan using ThreadPoolExecutor.
Shows a live Rich progress bar while scanning.
"""

from __future__ import annotations
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, TYPE_CHECKING

from .config import ScanConfig
from .result import IPResult
from .worker import scan_ip
from .ip_reader import read_file, read_cidr
from .exporter import export

if TYPE_CHECKING:
    from .display import Display


class Scanner:
    def __init__(self, config: ScanConfig, display: "Display"):
        self.config = config
        self.display = display
        self.results: List[IPResult] = []

    def _run(self, ip_list: List[str]):
        total = len(ip_list)
        if total == 0:
            self.display.error("No IPs to scan.")
            return

        self.display.info(
            f"[bold]{total:,}[/bold] targets  |  "
            f"[bold]{self.config.threads}[/bold] threads  |  "
            f"timeout=[bold]{self.config.timeout}s[/bold]  |  "
            f"SNI=[bold]{self.config.sni}[/bold]"
        )

        results: List[IPResult] = []
        start = time.time()

        progress = self.display.make_progress()
        task = progress.add_task("Scanning…", total=total)

        with progress:
            with ThreadPoolExecutor(max_workers=self.config.threads) as pool:
                futures = {
                    pool.submit(scan_ip, ip, idx, self.config): (idx, ip)
                    for idx, ip in enumerate(ip_list, 1)
                }

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception:
                        idx, ip = futures[future]
                        results.append(IPResult(ip=ip, index=idx))
                    progress.advance(task)

        elapsed = time.time() - start
        self.results = results

        # Sort and print
        self.display.print_summary(
            results, elapsed,
            self.config.output_base,
            self.config.top_n,
        )

        # Export
        if self.config.output_base:
            csv_p, json_p, txt_p = export(
                results, self.config.output_base, self.config.min_score
            )

    def scan_file(self, path: str):
        ips = read_file(path)
        self._run(ips)

    def scan_cidr(self, cidr: str):
        ips = read_cidr(cidr)
        self._run(ips)
