#!/usr/bin/env python3

import sys
import argparse
import signal
import time
import json
import logging
import requests
from prometheus_client.parser import text_string_to_metric_families
from typing import Dict, Any, Optional, NoReturn
from datetime import datetime
import socket
import platform

session = requests.Session()

def setup_logging(log_level: str = "INFO") -> None:
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

class PrometheusCollector:
    def __init__(self, url: str, targets: list[str], timeout: int = 10):
        self.base_url = url
        self.targets = targets
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
    
    def parse_target(self, target: str) -> Dict[str, str]:
        """Parse target string into components."""
        parts = target.split('&')
        result = {
            'host': parts[0],  # The IP/hostname is always the first part
            'auth': '',
            'module': ''
        }
        
        for part in parts[1:]:
            if '=' in part:
                key, value = part.split('=', 1)
                result[key] = value
        
        return result
    
    def collect(self) -> list:
        all_metrics = []
        for target in self.targets:
            try:
                target_info = self.parse_target(target)
                url = f"{self.base_url}/snmp?target={target_info['host']}&auth={target_info['auth']}&module={target_info['module']}"
                self.logger.debug(f"Collecting metrics from {url}")
                response = session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                metrics = []
                for family in text_string_to_metric_families(response.text):
                    for sample in family.samples:
                        metric = {
                            "name": sample.name,
                            "labels": sample.labels,
                            "value": sample.value,
                            "timestamp": int(time.time() * 1000),  # Milliseconds
                            "target": target_info['host'],
                            "tags": {
                                "auth": target_info['auth'],
                                "module": target_info['module'].split(',') if target_info['module'] else []
                            }
                        }
                        metrics.append(metric)
                all_metrics.extend(metrics)
                self.logger.debug(f"Collected {len(metrics)} metrics from {target_info['host']}")
                
            except Exception as e:
                self.logger.error(f"Failed to collect metrics from {target}: {str(e)}")
                continue
                
        return all_metrics

class PrometheusToLogstash:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.hostname = socket.gethostname()
        self.prometheus_collector = PrometheusCollector(
            url=config["prometheus_url"],
            targets=config["targets"],
            timeout=config["timeout"]
        )
        self.metrics_collected = 0
        self.metrics_sent = 0
        self.errors = 0

    def send_to_logstash(self, data: Dict[str, Any]) -> None:
        try:
            if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                current_time = int(time.time() * 1000)  # Milliseconds for consistency
                timestamp_in_data = data.get('@timestamp')
                self.logger.debug(f"Current Unix time: {current_time}")
                self.logger.debug(f"Timestamp in data: {timestamp_in_data}")
                self.logger.debug(f"Sending metric to Logstash: {json.dumps(data, indent=2)}")
                
            payload = json.dumps(data).encode('utf-8')
            headers = {
                'Content-Type': 'application/json',
                'Content-Length': str(len(payload))
            }
            
            req = session.post(
                self.config["logstash_url"],
                data=payload,
                headers=headers,
                timeout=self.config["timeout"]
            )
            
            if req.status_code == 200:
                self.metrics_sent += 1
                return True
            else:
                self.logger.warning(
                    f"Unexpected status code from Logstash: {req.status_code}"
                )
                self.errors += 1
                return False
                    
        except Exception as e:
            self.logger.error(f"Failed to send data to Logstash: {str(e)}")
            self.errors += 1
            return False

    def collect_and_send_prometheus_metrics(self) -> None:
        try:
            metrics = self.prometheus_collector.collect()
            for metric in metrics:
                self.metrics_collected += 1
                data = {
                    "@timestamp": datetime.utcfromtimestamp(metric["timestamp"] / 1000).isoformat() + "Z",
                    "agent": {
                        "hostname": self.hostname,
                        "name": platform.node(),
                        "type": "prometheus-to-logstash",
                        "version": "1.0.0"
                    },
                    "event": {
                        "module": "prometheus",
                        "dataset": "prometheus.metrics"
                    },
                    "prometheus": {
                        "metric": {
                            "name": metric["name"],
                            "labels": metric["labels"],
                            "value": metric["value"],
                            "timestamp": metric["timestamp"],
                            "target": metric["target"]
                        },
                        "tags": metric["tags"]
                    }
                }
                self.send_to_logstash(data)
                
        except Exception as e:
            self.logger.error(f"Error collecting Prometheus metrics: {str(e)}")
            self.errors += 1

    def run(self) -> None:
        self.logger.info("Starting Prometheus to Logstash forwarder")
        
        while True:
            self.collect_and_send_prometheus_metrics()
            time.sleep(self.config["interval"])

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Forward Prometheus metrics to Logstash"
    )
    parser.add_argument(
        "--prometheus-url",
        required=True,
        help="URL of the Prometheus metrics endpoint (e.g., http://localhost:9116)"
    )
    parser.add_argument(
        "--targets",
        required=True,
        nargs="+",
        help="Target devices to monitor (space separated)"
    )
    parser.add_argument(
        "--logstash-url",
        required=True,
        help="URL of the Logstash HTTP input plugin"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Prometheus scraping interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP request timeout in seconds (default: 10)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level"
    )
    
    return parser

def validate_args(args: argparse.Namespace) -> None:
    if args.interval < 1:
        raise ValueError("interval must be greater than 0")
    if args.timeout < 1:
        raise ValueError("timeout must be greater than 0")

def signal_handler(signum: int, frame: Any) -> NoReturn:
    logging.info("Received signal to terminate")
    sys.exit(0)

def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        validate_args(args)
    except ValueError as e:
        parser.error(str(e))
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    setup_logging(args.log_level)
    
    config = {
        "prometheus_url": args.prometheus_url,
        "logstash_url": args.logstash_url,
        "targets": args.targets,
        "interval": args.interval,
        "timeout": args.timeout
    }
    
    forwarder = PrometheusToLogstash(config)
    forwarder.run()

if __name__ == "__main__":
    main()

