"""
scorer.py – compute a 0-100 quality score for each IPResult.

Weights:
  TLS ok + latency ........... 40 pts
  Cloudflare headers ......... 20 pts
  HTTP ok .................... 10 pts
  Ping ok .................... 10 pts
  Speed ...................... 10 pts
  Low jitter ................. 10 pts
"""

from .result import IPResult


def compute_score(r: IPResult) -> int:
    score = 0

    # TLS (40 pts max)
    if r.tls_ok:
        score += 20
        if r.tls_ms is not None:
            if r.tls_ms < 100:
                score += 20
            elif r.tls_ms < 200:
                score += 15
            elif r.tls_ms < 400:
                score += 10
            elif r.tls_ms < 700:
                score += 5

    # CF headers (20 pts)
    if r.cf_ray:
        score += 12
    if r.cf_server:
        score += 8

    # HTTP (10 pts)
    if r.http_ok:
        score += 5
        if r.http_ms is not None and r.http_ms < 300:
            score += 5

    # Ping (10 pts)
    if r.ping_ok:
        score += 5
        if r.ping_ms is not None and r.ping_ms < 150:
            score += 5

    # Speed (10 pts)
    if r.speed_mbps is not None:
        if r.speed_mbps >= 10:
            score += 10
        elif r.speed_mbps >= 5:
            score += 7
        elif r.speed_mbps >= 1:
            score += 4

    # Jitter (10 pts) – lower is better
    if r.tls_jitter is not None:
        if r.tls_jitter < 10:
            score += 10
        elif r.tls_jitter < 30:
            score += 6
        elif r.tls_jitter < 60:
            score += 3

    return min(score, 100)


def grade(score: int) -> str:
    if score >= 85:
        return "S"
    if score >= 70:
        return "A"
    if score >= 55:
        return "B"
    if score >= 40:
        return "C"
    if score >= 20:
        return "D"
    return "F"
