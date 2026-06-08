"""
display.py – all terminal UI via `rich`.

Provides:
  - Banner
  - Live scanning dashboard (progress + live table)
  - Final summary table
  - Error/info helpers
"""

from __future__ import annotations
import threading
from typing import List, Optional, TYPE_CHECKING

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TextColumn,
    MofNCompleteColumn,
)
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box

if TYPE_CHECKING:
    from .result import IPResult

console = Console()

BANNER = r"""
  ___  _____   ____
 / __||  ___| / ___|   ___   __ _  _ __   _ __    ___  _ __
| |   | |_    \___ \  / __| / _` || '_ \ | '_ \  / _ \| '__|
| |___|  _|    ___) || (__ | (_| || | | || | | ||  __/| |
 \____||_|    |____/  \___| \__,_||_| |_||_| |_| \___||_|

          ╔═ Pro v1.0 ═╗  Advanced Cloudflare IP Scanner
"""

GRADE_COLORS = {
    "S": "bold bright_green",
    "A": "bold green",
    "B": "bold yellow",
    "C": "yellow",
    "D": "dim yellow",
    "F": "dim red",
}

STATUS_OK = "[green]✔[/green]"
STATUS_FAIL = "[red]✘[/red]"
STATUS_NA = "[dim]–[/dim]"


def _bool_cell(val: bool) -> str:
    return STATUS_OK if val else STATUS_FAIL


def _ms_cell(val: Optional[float], warn=300, bad=600) -> str:
    if val is None:
        return STATUS_NA
    if val < warn:
        color = "bright_green"
    elif val < bad:
        color = "yellow"
    else:
        color = "red"
    return f"[{color}]{val:.0f}ms[/{color}]"


def _speed_cell(val: Optional[float]) -> str:
    if val is None:
        return STATUS_NA
    if val >= 10:
        color = "bright_green"
    elif val >= 3:
        color = "yellow"
    else:
        color = "red"
    return f"[{color}]{val:.1f}M[/{color}]"


def _score_bar(score: int) -> str:
    filled = round(score / 10)
    bar = "█" * filled + "░" * (10 - filled)
    if score >= 70:
        color = "bright_green"
    elif score >= 40:
        color = "yellow"
    else:
        color = "red"
    return f"[{color}]{bar}[/{color}] [bold]{score}[/bold]"


class Display:
    def __init__(self):
        self.console = Console()
        self._lock = threading.Lock()

    def print_banner(self):
        self.console.print(
            Panel(
                Align.center(Text(BANNER, style="bold cyan")),
                border_style="cyan",
                padding=(0, 2),
            )
        )

    def error(self, msg: str):
        self.console.print(f"[bold red]✘ Error:[/bold red] {msg}")

    def info(self, msg: str):
        self.console.print(f"[cyan]ℹ[/cyan] {msg}")

    def success(self, msg: str):
        self.console.print(f"[bold green]✔[/bold green] {msg}")

    def make_progress(self) -> Progress:
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
        )

    def build_result_table(
        self,
        results: List["IPResult"],
        top_n: Optional[int] = None,
        title: str = "Scan Results",
    ) -> Table:
        from .scorer import grade

        sorted_results = sorted(
            [r for r in results if r.alive],
            key=lambda r: r.score,
            reverse=True,
        )
        if top_n:
            sorted_results = sorted_results[:top_n]

        table = Table(
            title=title,
            box=box.ROUNDED,
            border_style="cyan",
            show_header=True,
            header_style="bold cyan",
            row_styles=["", "dim"],
            min_width=90,
        )

        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("IP Address", style="bold white", width=16)
        table.add_column("Grade", justify="center", width=7)
        table.add_column("Score", width=20)
        table.add_column("Ping", justify="center", width=9)
        table.add_column("HTTP", justify="center", width=9)
        table.add_column("TLS", justify="center", width=9)
        table.add_column("Jitter", justify="center", width=9)
        table.add_column("TLS Ver", justify="center", width=8)
        table.add_column("CF✓", justify="center", width=5)
        table.add_column("Speed", justify="center", width=9)

        for i, r in enumerate(sorted_results, 1):
            g = grade(r.score)
            cf_ok = STATUS_OK if (r.cf_ray or r.cf_server) else STATUS_FAIL
            tls_ver = r.tls_version or "–"

            table.add_row(
                str(i),
                r.ip,
                f"[{GRADE_COLORS.get(g, 'white')}]{g}[/]",
                _score_bar(r.score),
                _ms_cell(r.ping_ms, 100, 300),
                _ms_cell(r.http_ms, 300, 600),
                _ms_cell(r.tls_ms, 150, 400),
                _ms_cell(r.tls_jitter, 20, 50) if r.tls_jitter else STATUS_NA,
                f"[dim]{tls_ver}[/dim]",
                cf_ok,
                _speed_cell(r.speed_mbps),
            )

        return table

    def print_summary(
        self,
        results: List["IPResult"],
        elapsed: float,
        output_base: Optional[str],
        top_n: Optional[int],
    ):
        alive = [r for r in results if r.alive]
        total = len(results)

        self.console.print()
        self.console.print(self.build_result_table(alive, top_n=top_n, title="✦ Clean IP Results ✦"))

        # Stats panel
        best = alive[0] if alive else None
        stats_text = (
            f"[cyan]Total scanned:[/cyan] [bold]{total:,}[/bold]   "
            f"[green]Alive:[/green] [bold]{len(alive)}[/bold]   "
            f"[red]Dead:[/red] [bold]{total - len(alive)}[/bold]   "
            f"[yellow]Elapsed:[/yellow] [bold]{elapsed:.1f}s[/bold]"
        )
        if best:
            stats_text += (
                f"\n[cyan]Best IP:[/cyan] [bold bright_green]{best.ip}[/bold bright_green]"
                f"  TLS={best.tls_ms or '–'}ms  Score={best.score}"
            )

        self.console.print(
            Panel(stats_text, title="Summary", border_style="blue", padding=(0, 2))
        )

        if output_base:
            self.success(f"Results saved → [bold]{output_base}.csv[/bold] & [bold]{output_base}.json[/bold]")
