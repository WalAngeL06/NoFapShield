from __future__ import annotations

import socket
import threading
from unittest.mock import patch, MagicMock, call

import dns.message
import dns.rdatatype
import dns.rcode
import pytest

from shield.dns_proxy.blocklist import BlocklistManager
from shield.dns_proxy.server import DNSProxyService


def _make_query_wire(domain: str) -> bytes:
    return dns.message.make_query(domain, dns.rdatatype.A).to_wire()


def _make_blocked_blocklist(domain: str) -> BlocklistManager:
    mgr = BlocklistManager()
    mgr._domains = {domain.lower()}
    return mgr


def _make_empty_blocklist() -> BlocklistManager:
    return BlocklistManager()


class TestDNSProxyServiceInit:
    def test_default_upstream(self):
        svc = DNSProxyService(_make_empty_blocklist())
        assert svc._upstream == "8.8.8.8"

    def test_custom_upstream(self):
        svc = DNSProxyService(_make_empty_blocklist(), upstream="1.1.1.1")
        assert svc._upstream == "1.1.1.1"

    def test_last_queried_domain_initially_none(self):
        svc = DNSProxyService(_make_empty_blocklist())
        assert svc.get_last_queried_domain() is None


class TestDNSProxyServiceStop:
    def test_stop_sets_event(self):
        svc = DNSProxyService(_make_empty_blocklist())
        svc.stop()
        assert svc._stop_event.is_set()


class TestDNSProxyServiceStart:
    """Tests that use a mocked socket to verify server behavior without binding port 53."""

    def _build_mock_socket(self, recv_sequence):
        """recv_sequence: list of (data, addr) tuples or socket.timeout exceptions."""
        mock_sock = MagicMock()
        side_effects = []
        for item in recv_sequence:
            if item is socket.timeout:
                side_effects.append(socket.timeout())
            else:
                side_effects.append(item)
        mock_sock.recvfrom.side_effect = side_effects
        return mock_sock

    def _run_server_with_mock(self, svc, mock_sock_instance, stop_after_sends=1):
        """Patches socket.socket to return mock_sock_instance, runs start() in a thread."""
        sent_packets = []

        def capture_sendto(data, addr):
            sent_packets.append((data, addr))

        mock_sock_instance.sendto.side_effect = capture_sendto

        with patch("socket.socket", return_value=mock_sock_instance):
            thread = threading.Thread(target=svc.start, daemon=True)
            thread.start()
            thread.join(timeout=2.0)

        return sent_packets

    def test_blocked_domain_returns_nxdomain(self):
        domain = "pornhub.com"
        blocklist = _make_blocked_blocklist(domain)
        svc = DNSProxyService(blocklist)

        query_wire = _make_query_wire(domain)
        addr = ("127.0.0.1", 12345)

        sent_packets = []

        def recvfrom_side_effect(bufsize):
            if not sent_packets:
                return (query_wire, addr)
            svc.stop()
            raise socket.timeout()

        mock_sock = MagicMock()
        mock_sock.recvfrom.side_effect = recvfrom_side_effect
        mock_sock.sendto.side_effect = lambda d, a: sent_packets.append((d, a))

        with patch("socket.socket", return_value=mock_sock):
            svc.start()

        assert len(sent_packets) == 1
        response = dns.message.from_wire(sent_packets[0][0])
        assert response.rcode() == dns.rcode.NXDOMAIN

    def test_non_blocked_domain_forwarded_upstream(self):
        domain = "google.com"
        blocklist = _make_empty_blocklist()
        svc = DNSProxyService(blocklist, upstream="8.8.8.8")

        query = dns.message.make_query(domain, dns.rdatatype.A)
        query_wire = query.to_wire()
        addr = ("127.0.0.1", 12345)

        upstream_response = dns.message.make_response(query)
        upstream_response_wire = upstream_response.to_wire()

        sent_packets = []

        def recvfrom_side_effect(bufsize):
            if not sent_packets:
                return (query_wire, addr)
            svc.stop()
            raise socket.timeout()

        mock_sock = MagicMock()
        mock_sock.recvfrom.side_effect = recvfrom_side_effect
        mock_sock.sendto.side_effect = lambda d, a: sent_packets.append((d, a))

        with patch("socket.socket", return_value=mock_sock), \
             patch("dns.query.udp", return_value=upstream_response):
            svc.start()

        assert len(sent_packets) == 1
        assert sent_packets[0][0] == upstream_response_wire

    def test_last_queried_domain_updated(self):
        domain = "xvideos.com"
        blocklist = _make_blocked_blocklist(domain)
        svc = DNSProxyService(blocklist)

        query_wire = _make_query_wire(domain)
        addr = ("127.0.0.1", 12345)

        sent_packets = []

        def recvfrom_side_effect(bufsize):
            if not sent_packets:
                return (query_wire, addr)
            svc.stop()
            raise socket.timeout()

        mock_sock = MagicMock()
        mock_sock.recvfrom.side_effect = recvfrom_side_effect
        mock_sock.sendto.side_effect = lambda d, a: sent_packets.append((d, a))

        with patch("socket.socket", return_value=mock_sock):
            svc.start()

        assert svc.get_last_queried_domain() == domain

    def test_malformed_packet_ignored(self):
        blocklist = _make_empty_blocklist()
        svc = DNSProxyService(blocklist)

        bad_data = b"\x00\x01garbage"
        addr = ("127.0.0.1", 12345)

        call_count = [0]

        def recvfrom_side_effect(bufsize):
            call_count[0] += 1
            if call_count[0] == 1:
                return (bad_data, addr)
            svc.stop()
            raise socket.timeout()

        mock_sock = MagicMock()
        mock_sock.recvfrom.side_effect = recvfrom_side_effect
        mock_sock.sendto = MagicMock()

        with patch("socket.socket", return_value=mock_sock):
            svc.start()

        mock_sock.sendto.assert_not_called()

    def test_upstream_failure_returns_servfail(self):
        domain = "google.com"
        blocklist = _make_empty_blocklist()
        svc = DNSProxyService(blocklist, upstream="8.8.8.8")

        query_wire = _make_query_wire(domain)
        addr = ("127.0.0.1", 12345)

        sent_packets = []

        def recvfrom_side_effect(bufsize):
            if not sent_packets:
                return (query_wire, addr)
            svc.stop()
            raise socket.timeout()

        mock_sock = MagicMock()
        mock_sock.recvfrom.side_effect = recvfrom_side_effect
        mock_sock.sendto.side_effect = lambda d, a: sent_packets.append((d, a))

        with patch("socket.socket", return_value=mock_sock), \
             patch("dns.query.udp", side_effect=Exception("timeout")):
            svc.start()

        assert len(sent_packets) == 1
        response = dns.message.from_wire(sent_packets[0][0])
        assert response.rcode() == dns.rcode.SERVFAIL

    def test_socket_bound_to_localhost_53(self):
        blocklist = _make_empty_blocklist()
        svc = DNSProxyService(blocklist)

        def recvfrom_side_effect(bufsize):
            svc.stop()
            raise socket.timeout()

        mock_sock = MagicMock()
        mock_sock.recvfrom.side_effect = recvfrom_side_effect

        with patch("socket.socket", return_value=mock_sock):
            svc.start()

        mock_sock.bind.assert_called_once_with(("127.0.0.1", 53))

    def test_stop_can_be_called_before_start(self):
        svc = DNSProxyService(_make_empty_blocklist())
        svc.stop()
        assert svc._stop_event.is_set()
