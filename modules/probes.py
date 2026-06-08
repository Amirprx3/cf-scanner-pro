"""
probes.py – all low-level measurement primitives.

Each function returns (success: bool, latency_ms: float | None, extras: dict)
"""

import socket
import ssl
import time
import statistics
import urllib.request
import urllib.error
from typing import Optional, Tuple, Dict, Any

from .config import ScanConfig


# ─────────────────────────────────────────────────────────────
# TCP Connect
# ─────────────────────────────────────────────────────────────

def tcp_connect(ip: str, port: int, timeout: float) -> Tuple[bool, Optional[float]]:
    t0 = time.perf_counter()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        ms = (time.perf_counter() - t0) * 1000
        sock.close()
        return result == 0, round(ms, 2) if result == 0 else None
    except Exception:
        return False, None


# ─────────────────────────────────────────────────────────────
# ICMP Ping (platform-aware)
# ─────────────────────────────────────────────────────────────

def icmp_ping(ip: str, timeout: float) -> Tuple[bool, Optional[float]]:
    """
    Use raw socket ICMP on Linux (needs root or cap_net_raw),
    fallback to TCP port 80 connect.
    """
    try:
        import subprocess, platform
        param = "-n" if platform.system().lower() == "windows" else "-c"
        timeout_flag = "-w" if platform.system().lower() == "windows" else "-W"
        timeout_int = max(1, int(timeout))

        t0 = time.perf_counter()
        r = subprocess.run(
            ["ping", param, "1", timeout_flag, str(timeout_int), ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1,
        )
        ms = (time.perf_counter() - t0) * 1000
        ok = r.returncode == 0
        return ok, round(ms, 2) if ok else None
    except Exception:
        # Fallback: TCP connect to port 80
        return tcp_connect(ip, 80, timeout)


# ─────────────────────────────────────────────────────────────
# HTTP check
# ─────────────────────────────────────────────────────────────

def http_check(ip: str, timeout: float) -> Tuple[bool, Optional[float], Optional[int]]:
    url = f"http://{ip}/"
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (cf-scanner-pro/2.0)",
                "Host": "speed.cloudflare.com",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ms = (time.perf_counter() - t0) * 1000
            return True, round(ms, 2), resp.status
    except urllib.error.HTTPError as e:
        ms = (time.perf_counter() - t0) * 1000
        # Any HTTP response (even 4xx/5xx) means the server is alive
        return True, round(ms, 2), e.code
    except Exception:
        return False, None, None


# ─────────────────────────────────────────────────────────────
# TLS Handshake
# ─────────────────────────────────────────────────────────────

def tls_handshake(
    ip: str,
    sni: str,
    timeout: float,
    retries: int = 2,
) -> Tuple[bool, Optional[float], Optional[float], Dict[str, Any]]:
    """
    Returns (ok, avg_ms, jitter_ms, extras)
    extras: {cf_ray, cf_server, tls_version, http_status}
    """
    latencies = []
    extras: Dict[str, Any] = {
        "cf_ray": False,
        "cf_server": False,
        "tls_version": None,
        "http_status": None,
    }

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for _ in range(retries):
        t0 = time.perf_counter()
        try:
            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_sock.settimeout(timeout)
            raw_sock.connect((ip, 443))

            tls_sock = ctx.wrap_socket(raw_sock, server_hostname=sni)
            tls_ms = (time.perf_counter() - t0) * 1000
            latencies.append(tls_ms)

            # Grab TLS version
            if extras["tls_version"] is None:
                extras["tls_version"] = tls_sock.version()

            # Send minimal HTTP/1.1 GET to read response headers
            request = (
                f"GET /cdn-cgi/trace HTTP/1.1\r\n"
                f"Host: {sni}\r\n"
                f"Connection: close\r\n\r\n"
            )
            tls_sock.sendall(request.encode())

            response = b""
            while True:
                chunk = tls_sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                # Stop after headers
                if b"\r\n\r\n" in response:
                    break

            tls_sock.close()

            resp_str = response.decode("utf-8", errors="ignore").lower()
            if "cf-ray" in resp_str:
                extras["cf_ray"] = True
            if "server: cloudflare" in resp_str:
                extras["cf_server"] = True

            # Extract HTTP status
            if extras["http_status"] is None:
                try:
                    status_line = resp_str.split("\r\n")[0]
                    extras["http_status"] = int(status_line.split()[1])
                except Exception:
                    pass

        except Exception:
            continue

    if not latencies:
        return False, None, None, extras

    avg = round(statistics.mean(latencies), 2)
    jitter = round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0.0
    return True, avg, jitter, extras


# ─────────────────────────────────────────────────────────────
# Download Speed Test
# ─────────────────────────────────────────────────────────────

def speed_test(ip: str, sni: str, timeout: float) -> Optional[float]:
    """
    Download ~100KB from Cloudflare speed test endpoint via the given IP.
    Returns speed in Mbps or None.
    """
    # Use __down endpoint on Cloudflare's speed test CDN
    url = f"https://{ip}/__down?bytes=102400"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.settimeout(timeout)
        raw_sock.connect((ip, 443))
        tls_sock = ctx.wrap_socket(raw_sock, server_hostname=sni)

        request = (
            f"GET /__down?bytes=102400 HTTP/1.1\r\n"
            f"Host: {sni}\r\n"
            f"Connection: close\r\n\r\n"
        )
        tls_sock.sendall(request.encode())

        t0 = time.perf_counter()
        received = 0
        header_done = False
        buf = b""

        while True:
            chunk = tls_sock.recv(8192)
            if not chunk:
                break
            if not header_done:
                buf += chunk
                if b"\r\n\r\n" in buf:
                    header_done = True
                    body_start = buf.index(b"\r\n\r\n") + 4
                    received += len(buf) - body_start
            else:
                received += len(chunk)

        elapsed = time.perf_counter() - t0
        tls_sock.close()

        if elapsed > 0 and received > 0:
            mbps = round((received * 8) / (elapsed * 1_000_000), 2)
            return mbps
        return None
    except Exception:
        return None
