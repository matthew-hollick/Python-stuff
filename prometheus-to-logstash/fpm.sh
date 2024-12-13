VERSION=0.0.1

fpm \
  --architecture all \
  --depends prometheus-snmp-exporter \
  --depends python3 \
  --depends python3-pip \
  --depends logstash \
  --depends wait-for-it \
  --force \
  --maintainer "Matthew Hollick <matthew@hedgehoganalytics.uk>" \
  --name prometheus-to-logstash \
  --package prometheus-to-logstash \
  --input-type dir \
  --output-type deb \
  --version ${VERSION} \
  --after-install after-install.sh \
  --before-install before-install.sh \
  --deb-systemd prometheus-to-logstash.service \
  --deb-systemd-enable \
  --deb-systemd-restart-after-upgrade \
  --deb-default prometheus-to-logstash.default \
  --description "Pull data from a prometheus exporter and forward it to logstash" \
  prometheus-to-logstash.py=/usr/local/bin/prometheus-to-logstash.py
 
