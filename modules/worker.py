"""
worker.py – single-IP scanning logic.
Called by Scanner in a thread pool.
"""

from .config import ScanConfig
from .result import IPResult
from .probes import icmp_ping, tcp_connect, http_check, tls_handshake, speed_test
from .scorer import compute_score


def scan_ip(ip: str, index: int, config: ScanConfig) -> IPResult:
    r = IPResult(ip=ip, index=index)

    # ── 1. Ping ──────────────────────────────────────────────
    if not config.tls_only:
        r.ping_ok, r.ping_ms = icmp_ping(ip, config.timeout)
        r.tcp80_ok, _ = tcp_connect(ip, 80, config.timeout)
        r.tcp443_ok, _ = tcp_connect(ip, 443, config.timeout)

        # Alive if any check passed
        r.alive = r.ping_ok or r.tcp80_ok or r.tcp443_ok
    else:
        # In tls-only mode, check port 443 first
        r.tcp443_ok, _ = tcp_connect(ip, 443, config.timeout)
        r.alive = r.tcp443_ok

    if not r.alive and not config.tls_only:
        r.score = 0
        return r

    # ── 2. HTTP ──────────────────────────────────────────────
    if r.tcp80_ok or config.tls_only:
        r.http_ok, r.http_ms, r.http_status = http_check(ip, config.timeout)

    # ── 3. TLS handshake ─────────────────────────────────────
    if r.tcp443_ok or config.tls_only:
        ok, avg_ms, jitter, extras = tls_handshake(
            ip, config.sni, config.timeout, config.tls_retries
        )
        r.tls_ok = ok
        r.tls_ms = avg_ms
        r.tls_jitter = jitter
        r.cf_ray = extras.get("cf_ray", False)
        r.cf_server = extras.get("cf_server", False)
        r.tls_version = extras.get("tls_version")

        # Mark alive if TLS succeeded (in tls-only mode)
        if config.tls_only and r.tls_ok:
            r.alive = True

    # ── 4. Speed test ────────────────────────────────────────
    if config.do_speed and r.tls_ok:
        r.speed_mbps = speed_test(ip, config.sni, config.timeout)

    # ── 5. Score ─────────────────────────────────────────────
    r.score = compute_score(r)
    return r
