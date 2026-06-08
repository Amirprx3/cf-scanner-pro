from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IPResult:
    ip: str
    index: int = 0

    # Ping
    ping_ok: bool = False
    ping_ms: Optional[float] = None

    # TCP connect
    tcp80_ok: bool = False
    tcp443_ok: bool = False

    # HTTP check
    http_ok: bool = False
    http_ms: Optional[float] = None
    http_status: Optional[int] = None

    # TLS handshake
    tls_ok: bool = False
    tls_ms: Optional[float] = None
    tls_jitter: Optional[float] = None    # ms std-dev across retries
    cf_ray: bool = False                  # cf-ray header present
    cf_server: bool = False               # server: cloudflare
    tls_version: Optional[str] = None

    # Download speed
    speed_mbps: Optional[float] = None

    # Derived
    score: int = 0                        # 0-100 quality score
    alive: bool = False

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "score": self.score,
            "alive": self.alive,
            "ping_ok": self.ping_ok,
            "ping_ms": self.ping_ms,
            "http_ok": self.http_ok,
            "http_ms": self.http_ms,
            "http_status": self.http_status,
            "tls_ok": self.tls_ok,
            "tls_ms": self.tls_ms,
            "tls_jitter": self.tls_jitter,
            "tls_version": self.tls_version,
            "cf_ray": self.cf_ray,
            "cf_server": self.cf_server,
            "speed_mbps": self.speed_mbps,
        }
