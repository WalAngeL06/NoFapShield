from __future__ import annotations

import socket
import threading

import dns.message
import dns.query
import dns.rcode
import dns.rdatatype

from shield.dns_proxy.blocklist import BlocklistManager

_BUFFER_SIZE = 512
_LISTEN_ADDR = "127.0.0.1"
_LISTEN_PORT = 53


class DNSProxyService:
    def __init__(self, blocklist: BlocklistManager, upstream: str = "8.8.8.8") -> None:
        self._blocklist = blocklist
        self._upstream = upstream
        self._stop_event = threading.Event()
        self._last_queried_domain: str | None = None

    def start(self) -> None:
        """Binds UDP socket to 127.0.0.1:53.
        Forwards non-blocked queries to upstream DNS.
        Blocked domains: returns NXDOMAIN response.
        Runs in current thread until stop() is called.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((_LISTEN_ADDR, _LISTEN_PORT))
        sock.settimeout(1.0)
        try:
            while True:
                try:
                    data, addr = sock.recvfrom(_BUFFER_SIZE)
                except socket.timeout:
                    if self._stop_event.is_set():
                        break
                    continue

                try:
                    request = dns.message.from_wire(data)
                except Exception:
                    continue

                domain = self._extract_domain(request)
                if domain:
                    self._last_queried_domain = domain

                if domain and self._blocklist.is_blocked(domain):
                    response = dns.message.make_response(request)
                    response.set_rcode(dns.rcode.NXDOMAIN)
                    sock.sendto(response.to_wire(), addr)
                else:
                    try:
                        upstream_resp = dns.query.udp(request, self._upstream, timeout=5)
                        sock.sendto(upstream_resp.to_wire(), addr)
                    except Exception:
                        response = dns.message.make_response(request)
                        response.set_rcode(dns.rcode.SERVFAIL)
                        sock.sendto(response.to_wire(), addr)
        finally:
            sock.close()

    def stop(self) -> None:
        """Signals the server loop to exit."""
        self._stop_event.set()

    def get_last_queried_domain(self) -> str | None:
        """Returns the most recently queried domain (for orchestrator DNS TTL)."""
        return self._last_queried_domain

    @staticmethod
    def _extract_domain(request: dns.message.Message) -> str | None:
        if request.question:
            return str(request.question[0].name).rstrip(".")
        return None
