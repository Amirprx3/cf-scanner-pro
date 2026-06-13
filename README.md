# CF Scanner Pro ✦

> Advanced Cloudflare Clean IP Scanner — Python 3.9+

A professional, multi-threaded CLI tool for finding clean Cloudflare IPs with rich terminal UI,
quality scoring, TLS analysis, and export to CSV/JSON.

---

## Features vs cf-scanner

| Feature | cf-scanner | CF Scanner Pro |
|---|---|---|
| ICMP ping | ✔ | ✔ |
| TCP 80/443 | ✔ | ✔ |
| HTTP latency | ✔ | ✔ |
| **TLS handshake latency** | ✘ | ✔ |
| **TLS jitter (stability)** | ✘ | ✔ |
| **TLS version detection** | ✘ | ✔ |
| **CF-Ray header check** | ✘ | ✔ |
| **Download speed test** | ✘ | ✔ |
| **Quality score (0-100)** | ✘ | ✔ |
| **Grade (S/A/B/C/D/F)** | ✘ | ✔ |
| **Rich live progress bar** | ✘ | ✔ |
| **Export CSV + JSON + TXT** | TXT only | ✔ |
| **CLI flags (argparse)** | ✘ | ✔ |
| **CIDR direct scan** | ✘ | ✔ |
| **--top N filter** | ✘ | ✔ |
| Concurrent threads | threading | ThreadPoolExecutor |

---

## Install

```bash
git clone https://github.com/Amirprx3/cf-scanner-pro
cd cf-scanner-pro
pip install -r requirements.txt
```

---

## Usage

### Interactive mode (no flags)

```bash
python cf_scanner.py
```

### CLI flags

```bash
# Scan hosts.txt with 150 threads, save to my_results.csv/.json/.txt
python cf_scanner.py -f hosts.txt -t 150 -o my_results

# Scan a specific CIDR range
python cf_scanner.py -r 104.16.0.0/20 -t 100

# TLS-only mode (faster, skips ping/TCP)
python cf_scanner.py -f hosts.txt --tls-only

# Show only top 20 results, skip speed test
python cf_scanner.py -f hosts.txt --top 20 --no-speed

# Custom SNI hostname
python cf_scanner.py -f hosts.txt --sni yoursite.com
```

### All flags

```
-f / --file        Input .txt file with CIDRs or IPs
-r / --range       CIDR range to scan directly
-t / --threads     Thread count (default: 100)
-T / --timeout     Per-check timeout in seconds (default: 3)
--top N            Show top N results by score
--tls-only         Skip ping/HTTP, do TLS checks only
--no-speed         Skip download speed test
-o / --output      Output base name (creates .csv .json .txt)
--min-score        Min quality score to include in output (1-100)
--sni              SNI hostname for TLS (default: speed.cloudflare.com)
```

---

## Scoring

Each IP gets a **0–100 quality score** based on:

| Metric | Max Points |
|---|---|
| TLS ok + low latency | 40 |
| Cloudflare headers (cf-ray, server) | 20 |
| HTTP ok + low latency | 10 |
| Ping ok + low latency | 10 |
| Download speed | 10 |
| Low TLS jitter | 10 |

Grades: **S** (≥85) · **A** (≥70) · **B** (≥55) · **C** (≥40) · **D** (≥20) · **F** (<20)

---

## Output files

After scanning, three files are created:

- `results.csv` — full data, all alive IPs, sorted by score
- `results.json` — same in JSON
- `results.txt` — IP-only list, ready for v2ray/xray/sing-box configs

---

## Project structure

```
cf-scanner-pro/
├── cf_scanner.py        # Entry point
├── hosts.txt            # All Cloudflare IP ranges
├── requirements.txt
└── modules/
    ├── config.py        # ScanConfig dataclass
    ├── result.py        # IPResult dataclass
    ├── ip_reader.py     # CIDR/file expansion
    ├── probes.py        # ping, TCP, HTTP, TLS, speed
    ├── worker.py        # Single-IP scan logic
    ├── scorer.py        # 0-100 quality scoring
    ├── scanner.py       # ThreadPoolExecutor orchestrator
    ├── display.py       # Rich terminal UI
    ├── exporter.py      # CSV/JSON/TXT export
    └── cli.py           # Interactive wizard
```

---

## Requirements

- Python 3.9+
- `rich` (terminal UI)
- No other external dependencies (stdlib only for all network code)
