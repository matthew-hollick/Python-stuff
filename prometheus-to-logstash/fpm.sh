VERSION=0.0.1

fpm \
  --architecture all \
  --depends prometheus-snmp-exporter \
  --depends python3 \
  --depends python3-pip \
  --depends logstash \
  --depends wait-for-it \
  --depends snmp-mibs-downloader \
  --depends python3-requests \
  --depends python3-backoff \
  --depends python3-certifi \
  --depends python3-charset-normalizer \
  --depends python3-idna \
  --depends python3-psutil \
  --depends python3-tenacity \
  --depends python3-urllib3 \
  --depends python3-prometheus-client \
  --force \
  --maintainer "Matthew Hollick <matthew@hedgehoganalytics.uk>" \
  --name prometheus-to-logstash \
  --input-type dir \
  --output-type deb \
  --version ${VERSION} \
  --before-install before-install.sh \
  --after-install after-install.sh \
  --deb-systemd prometheus-to-logstash.service \
  --deb-systemd-enable \
  --deb-systemd-restart-after-upgrade \
  --deb-default prometheus-to-logstash.default \
  --description "Pull data from a prometheus exporter and forward it to logstash" \
  prometheus-to-logstash.py=/usr/local/bin/prometheus-to-logstash.py logstash-file-output.conf=/etc/logstash/conf.d/logstash-file-output.conf logstash-http-input.conf=/etc/logstash/conf.d/logstash-http-input.conf snmp-local.yml=/etc/prometheus/snmp-local.yml
