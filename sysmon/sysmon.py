from __future__ import annotations

import json
import os
import platform
import socket
import time
from datetime import datetime
from datetime import timedelta

import psutil


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (float)):
            return round(obj, 3)
        return super().default(obj)


def get_cpu_data():
    # Basic CPU info
    cpu_data = {
        'physical_cores': psutil.cpu_count(logical=False),
        'logical_cores': psutil.cpu_count(logical=True),
        'cores': {},
        'load_average': {},
    }

    # CPU load averages
    load1, load5, load15 = os.getloadavg()
    cpu_data['load_average'] = {
        '1min': round(load1, 3),
        '5min': round(load5, 3),
        '15min': round(load15, 3),
    }

    # First call to get baseline for measuring CPU usage
    psutil.cpu_percent(percpu=True)
    psutil.cpu_times_percent(percpu=True)

    # Short sleep to measure actual CPU usage
    time.sleep(0.5)

    # Get the actual CPU measurements
    cpu_percentages = psutil.cpu_percent(percpu=True)
    cpu_times = psutil.cpu_times_percent(percpu=True)

    # CPU frequency info if available
    try:
        cpu_freqs = psutil.cpu_freq(percpu=True)
    except Exception:
        cpu_freqs = [None] * len(cpu_percentages)

    # Collect per-core data
    for i in range(cpu_data['logical_cores']):
        freq = cpu_freqs[i] if cpu_freqs and i < len(cpu_freqs) else None
        times = cpu_times[i] if i < len(cpu_times) else None
        percent = cpu_percentages[i] if i < len(cpu_percentages) else None

        core_data = {
            'frequency_mhz': None,
            'total_percent': round(percent, 3) if percent is not None else None,
            'usage_percent': {},
        }

        # Add frequency data if available
        if freq:
            core_data['frequency_mhz'] = {
                'current': round(freq.current, 3),
                'min': round(freq.min, 3),
                'max': round(freq.max, 3),
            }

        # Add detailed CPU time percentages
        if times:
            core_data['usage_percent'] = {
                'user': round(times.user, 3),
                'nice': round(times.nice, 3),
                'system': round(times.system, 3),
                'idle': round(times.idle, 3),
                'iowait': round(getattr(times, 'iowait', 0), 3),
                'irq': round(getattr(times, 'irq', 0), 3),
                'softirq': round(getattr(times, 'softirq', 0), 3),
                'steal': round(getattr(times, 'steal', 0), 3),
                'guest': round(getattr(times, 'guest', 0), 3),
                'guest_nice': round(getattr(times, 'guest_nice', 0), 3),
            }

        cpu_data['cores'][f'cpu{i}'] = core_data

    return cpu_data


def get_ip_addresses():
    ip_addresses = {
        'hostname': socket.gethostname(),
        'interfaces': {},
    }

    net_if_addrs = psutil.net_if_addrs()
    for interface, addrs in net_if_addrs.items():
        ip_addresses['interfaces'][interface] = []
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ip_addresses['interfaces'][interface].append(
                    {
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast,
                    },
                )

    return ip_addresses


def get_logged_in_users():
    users = []
    for user in psutil.users():
        users.append(
            {
                'name': user.name,
                'terminal': user.terminal,
                'host': user.host,
                'started': int(user.started),
            },
        )
    return users


def get_system_metrics():
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'system': {
            'hostname': platform.node(),
            'kernel': {
                'version': platform.release(),
                'full_version': platform.uname().version,
            },
            'network': get_ip_addresses(),
            'uptime': {
                'seconds': int(psutil.boot_time()),
                'readable': str(
                    timedelta(seconds=int(time.time() - psutil.boot_time())),
                ),
            },
            'users': {
                'logged_in_count': len(psutil.users()),
                'sessions': get_logged_in_users(),
            },
        },
        'cpu': get_cpu_data(),
        'memory': {},
        'filesystems': {},
        'disk_io': {},
        'network_io': {},
    }

    # Memory metrics
    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()
    metrics['memory'] = {
        'virtual': {
            'total_bytes': vm.total,
            'available_bytes': vm.available,
            'used_bytes': vm.used,
            'free_bytes': vm.free,
            'percent_used': round(vm.percent, 3),
            'cached_bytes': vm.cached,
            'buffers_bytes': vm.buffers,
        },
        'swap': {
            'total_bytes': sm.total,
            'used_bytes': sm.used,
            'free_bytes': sm.free,
            'percent_used': round(sm.percent, 3),
            'sin_bytes': sm.sin,
            'sout_bytes': sm.sout,
        },
    }

    # Filesystem metrics - exclude virtual filesystems
    virtual_filesystems = {
        'devtmpfs',
        'tmpfs',
        'devfs',
        'ramfs',
        'proc',
        'sysfs',
        'debugfs',
        'cgroup2fs',
    }
    for partition in psutil.disk_partitions(all=False):
        if partition.fstype not in virtual_filesystems:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                metrics['filesystems'][partition.mountpoint] = {
                    'device': partition.device,
                    'fstype': partition.fstype,
                    'opts': partition.opts,
                    'total_bytes': usage.total,
                    'used_bytes': usage.used,
                    'free_bytes': usage.free,
                    'percent_used': round(usage.percent, 3),
                }
            except (PermissionError, OSError):
                continue

    # Disk I/O metrics - exclude loop devices
    disk_io = psutil.disk_io_counters(perdisk=True)
    for disk_name, counters in disk_io.items():
        if not disk_name.startswith('loop'):
            metrics['disk_io'][disk_name] = {
                'read_bytes': counters.read_bytes,
                'write_bytes': counters.write_bytes,
                'read_count': counters.read_count,
                'write_count': counters.write_count,
                'read_time_ms': counters.read_time,
                'write_time_ms': counters.write_time,
                'busy_time_ms': getattr(counters, 'busy_time', None),
            }

    # Network I/O metrics
    net_io = psutil.net_io_counters(pernic=True)
    for nic_name, counters in net_io.items():
        metrics['network_io'][nic_name] = {
            'bytes_sent': counters.bytes_sent,
            'bytes_recv': counters.bytes_recv,
            'packets_sent': counters.packets_sent,
            'packets_recv': counters.packets_recv,
            'errin': counters.errin,
            'errout': counters.errout,
            'dropin': counters.dropin,
            'dropout': counters.dropout,
        }

    return metrics


if __name__ == '__main__':
    import sys

    if not platform.system() == 'Linux':
        print(
            json.dumps(
                {'error': 'This script is intended for Linux systems only'},
            ),
        )
        sys.exit(1)

    metrics = get_system_metrics()
    print(json.dumps(metrics, separators=(',', ':'), cls=CustomJSONEncoder))
