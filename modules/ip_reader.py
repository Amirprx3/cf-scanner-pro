"""
IP reader: reads a .txt file or a single CIDR string and
returns a flat list of IP strings.

Supported line formats in .txt file:
  104.16.0.0/20     → expand all IPs in CIDR
  104.16.0.0/24     → same
  104.16.0.1        → single IP
  # comment         → ignored
"""

import ipaddress
from typing import List


def _expand_cidr(cidr: str) -> List[str]:
    try:
        network = ipaddress.ip_network(cidr.strip(), strict=False)
        # For large ranges skip host-only expansion to save memory;
        # return network address strings for very large /8-/16 etc.
        if network.num_addresses > 65536:
            # Yield all /24 sub-networks hosts
            ips = []
            for subnet in network.subnets(new_prefix=24):
                for ip in list(subnet.hosts())[:254]:
                    ips.append(str(ip))
            return ips
        return [str(ip) for ip in network.hosts()]
    except ValueError:
        return []


def read_file(path: str) -> List[str]:
    ips: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "/" in line:
                    ips.extend(_expand_cidr(line))
                else:
                    try:
                        ipaddress.ip_address(line)
                        ips.append(line)
                    except ValueError:
                        continue
    except FileNotFoundError:
        pass
    return ips


def read_cidr(cidr: str) -> List[str]:
    return _expand_cidr(cidr)
