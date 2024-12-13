#!/usr/bin/env python3
from __future__ import annotations

import argparse
import socket
import ssl
import sys
from datetime import datetime
from typing import List
from typing import NamedTuple

import OpenSSL.SSL

# Nagios return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


class CertInfo(NamedTuple):
    host: str
    port: int
    expiry_date: datetime
    days_remaining: int
    error: str = ''


def get_certificate_expiry(host: str, port: int) -> CertInfo:
    """Connect to host:port and get certificate expiration information."""
    try:
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Connect and get certificate
        with socket.create_connection(
            (host, port),
            timeout=10,
        ) as sock, context.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert(binary_form=True)
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_ASN1, cert,
            )

            # Get expiration date
            expiry = datetime.strptime(
                x509.get_notAfter().decode('ascii'),
                '%Y%m%d%H%M%SZ',
            )
            days_remaining = (expiry - datetime.now()).days

            return CertInfo(host, port, expiry, days_remaining)

    except Exception as e:
        return CertInfo(host, port, datetime.min, -1, str(e))


def main():
    parser = argparse.ArgumentParser(
        description='Nagios plugin to check SSL certificate expiration',
    )
    parser.add_argument(
        '-H',
        '--hosts',
        required=True,
        help='Comma-separated list of host:port',
    )
    parser.add_argument(
        '-d',
        '--days',
        type=int,
        required=True,
        help='Minimum days until expiration',
    )
    args = parser.parse_args()

    # Parse hosts and ports
    try:
        host_ports = [tuple(hp.split(':')) for hp in args.hosts.split(',')]
        host_ports = [(host, int(port)) for host, port in host_ports]
    except Exception as e:
        print(f"UNKNOWN - Error parsing host:port list: {e}")
        sys.exit(UNKNOWN)

    # Check all certificates
    results: list[CertInfo] = []
    for host, port in host_ports:
        cert_info = get_certificate_expiry(host, port)
        results.append(cert_info)

    # Sort results by days remaining (errors at the end)
    results.sort(
        key=lambda x: float(
            'inf',
        ) if x.days_remaining < 0 else x.days_remaining,
    )

    # Generate output
    output_lines = []
    status = OK

    for result in results:
        if result.error:
            status = CRITICAL
            output_lines.append(
                f"{result.host}:{result.port} - ERROR: {result.error}",
            )
        elif result.days_remaining < args.days:
            status = CRITICAL
            output_lines.append(
                f"{result.host}:{result.port} - CRITICAL: {result.days_remaining} days remaining "
                f"(expires {result.expiry_date.strftime('%Y-%m-%d')})",
            )
        else:
            output_lines.append(
                f"{result.host}:{result.port} - OK: {result.days_remaining} days remaining "
                f"(expires {result.expiry_date.strftime('%Y-%m-%d')})",
            )

    # Print final status and output
    status_text = 'OK' if status == OK else 'CRITICAL'
    print(f"SSL_CERT {status_text} - Certificate expiration check")
    for line in output_lines:
        print(line)

    sys.exit(status)


if __name__ == '__main__':
    main()
