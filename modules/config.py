from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScanConfig:
    threads: int = 100
    timeout: float = 3.0
    tls_only: bool = False
    do_speed: bool = True
    output_base: Optional[str] = "results"
    min_score: int = 1
    sni: str = "speed.cloudflare.com"
    top_n: Optional[int] = None

    # Internal derived
    http_port: int = 80
    https_port: int = 443
    tls_retries: int = 2
    ping_count: int = 3
