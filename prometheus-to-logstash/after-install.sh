#!/usr/bin/env bash
set -e

sed -i 's|^ARGS=""$|ARGS="--config.file=/etc/prometheus/*yml"|' /etc/default/prometheus-snmp-exporter

#pip3 install                  \
#    backoff==2.2.1            \
#    certifi==2024.8.30        \
#    charset-normalizer==3.4.0 \
#    idna==3.10                \
#    prometheus_client==0.21.1 \
#    psutil==6.1.0             \
#    requests==2.32.3          \
#    tenacity==9.0.0           \
#    urllib3==2.2.3

# Verify installations
#echo "Verifying installations..."
#echo "Python version: $(python3 --version)"
#echo "Pip version: $(pip3 --version)"
#echo "Logstash version: $(logstash --version)"
#echo "Wait-for-it version: $(wait-for-it --version)"
#echo "SNMP exporter installed at: $(which prometheus-snmp-exporter)"

# Verify Python packages
#echo "Verifying Python packages..."
#pip3 freeze | grep -E "backoff|certifi|charset-normalizer|idna|prometheus_client|psutil|requests|tenacity|urllib3"

# Verify user creation
#echo "Verifying monitoring user..."
#id monitoring

#echo "Installation complete!"
