#!/usr/bin/env python3

import sys
import argparse
import signal
import time
import json
import logging
import psutil
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
    def __init__(self, url: str, target: str, timeout: int = 10):
        self.base_url = url
        self.target = target
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
    
    def collect(self) -> list:
        try:
            url = f"{self.base_url}/snmp?target={self.target}"
            response = session.get(url, timeout=self.timeout)
            response.raise_for_status()
            metrics = []
            for family in text_string_to_metric_families(response.text):
                for sample in family.samples:
                    metric = {
                        "name": sample.name,
                        "labels": sample.labels,
                        "value": sample.value,
                        "timestamp": int(time.time() * 1000)  # Milliseconds
                    }
                    metrics.append(metric)
            return metrics
        except Exception as e:
            self.logger.error(f"Failed to collect Prometheus metrics: {str(e)}")
            return []

class SystemMetricsCollector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def collect(self) -> list:
        try:
            metrics = []
            cpu_times = psutil.cpu_times()
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            
            metrics.extend([
                {
                    "name": "system_cpu_user",
                    "value": cpu_times.user,
                    "timestamp": int(time.time() * 1000)  # Milliseconds
                },
                {
                    "name": "system_cpu_system",
                    "value": cpu_times.system,
                    "timestamp": int(time.time() * 1000)  # Milliseconds
                }
            ])
            
            for i, percent in enumerate(cpu_percent):
                metrics.append({
                    "name": "system_cpu_percent",
                    "labels": {"cpu": str(i)},
                    "value": percent,
                    "timestamp": int(time.time() * 1000)  # Milliseconds
                })
            
            memory = psutil.virtual_memory()
            metrics.extend([
                {
                    "name": "system_memory_total",
                    "value": memory.total,
                    "timestamp": int(time.time() * 1000)  # Milliseconds
                },
                {
                    "name": "system_memory_available",
                    "value": memory.available,
                    "timestamp": int(time.time() * 1000)  # Milliseconds
                },
                {
                    "name": "system_memory_percent",
                    "value": memory.percent,
                    "timestamp": int(time.time() * 1000)  # Milliseconds
                }
            ])
            
            disk = psutil.disk_usage('/')
            metrics.extend([
                {
                    "name": "system_disk_total",
                    "value": disk.total,
                    "timestamp": int(time.time() * 1000)  # Milliseconds
                },
                {
                    "name": "system_disk_used",
                    "value": disk.used,
                    "timestamp": int(time.time() * 1000)  # Milliseconds
                },
                {
                    "name": "system_disk_percent",
                    "value": disk.percent,
                    "timestamp": int(time.time() * 1000)  # Milliseconds
                }
            ])
            
            return metrics
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {str(e)}")
            return []

class PrometheusToLogstash:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.prometheus_collector = PrometheusCollector(
            url=config["prometheus_url"],
            target=config["target"],
            timeout=config["timeout"]
        )
        self.system_collector = (
            SystemMetricsCollector() if config["enable_system_metrics"] else None
        )
        self.last_system_collection = 0
        self.metrics_collected = 0
        self.metrics_sent = 0
        self.errors = 0
        self.hostname = socket.gethostname()

    def send_to_logstash(self, data: Dict[str, Any]) -> bool:
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
            self.metrics_collected += len(metrics)
            
            for metric in metrics:
                formatted_metric = {
                    "@timestamp": datetime.fromtimestamp(metric["timestamp"] / 1000).isoformat(),
                    "agent": {
                        "hostname": self.hostname,
                        "name": "prometheus-to-logstash",
                        "type": "prometheus-forwarder",
                        "version": "1.0.0"
                    },
                    "observer": {
                        "hostname": self.hostname
                    },
                    "device": {
                        "ip": self.config["target"]
                    },
                    "metric_name": metric["name"],
                    "metric_value": metric["value"],
                    "labels": metric.get("labels", {}),
                    "type": "prometheus"
                }
                self.send_to_logstash(formatted_metric)
                
        except Exception as e:
            self.logger.error(f"Error processing Prometheus metrics: {str(e)}")

    def collect_and_send_system_metrics(self) -> None:
        if not self.system_collector:
            return
            
        try:
            current_time = time.time()
            if (current_time - self.last_system_collection) >= self.config["system_metrics_interval"]:
                metrics = self.system_collector.collect()
                self.metrics_collected += len(metrics)
                
                for metric in metrics:
                    formatted_metric = {
                        "@timestamp": datetime.fromtimestamp(metric["timestamp"] / 1000).isoformat(),
                        "agent": {
                            "hostname": self.hostname,
                            "name": "prometheus-to-logstash",
                            "type": "prometheus-forwarder",
                            "version": "1.0.0",
                            "host": {
                                "hostname": self.hostname,
                                "name": self.hostname,
                                "architecture": platform.machine(),
                                "os": {
                                    "platform": platform.system(),
                                    "version": platform.release(),
                                    "family": "linux" if platform.system().lower() == "linux" else platform.system().lower()
                                }
                            }
                        },
                        "metric_name": metric["name"],
                        "metric_value": metric["value"],
                        "labels": metric.get("labels", {}),
                        "type": "system"
                    }
                    self.send_to_logstash(formatted_metric)
                    
                self.last_system_collection = current_time
                
        except Exception as e:
            self.logger.error(f"Error processing system metrics: {str(e)}")

    def run(self) -> None:
        self.logger.info("Starting Prometheus to Logstash forwarder")
        while True:
            try:
                self.collect_and_send_prometheus_metrics()
                self.collect_and_send_system_metrics()
                time.sleep(self.config["interval"])
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(1)

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
        "--target",
        required=True,
        help="Target device to monitor (will be appended as ?target=<target> to the URL)"
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
        "--enable-system-metrics",
        action="store_true",
        help="Enable collection of system metrics"
    )
    parser.add_argument(
        "--system-metrics-interval",
        type=int,
        default=300,
        help="System metrics collection interval in seconds (default: 300)"
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
    if args.system_metrics_interval < 1:
        raise ValueError("system_metrics_interval must be greater than 0")

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
        "target": args.target,
        "interval": args.interval,
        "timeout": args.timeout,
        "enable_system_metrics": args.enable_system_metrics,
        "system_metrics_interval": args.system_metrics_interval
    }
    
    forwarder = PrometheusToLogstash(config)
    forwarder.run()

if __name__ == "__main__":
    main()

