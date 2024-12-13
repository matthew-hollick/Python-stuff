#!/usr/bin/env bash
set -e

# Create monitoring user if it doesn't exist
echo "Creating monitoring user..."
if ! id "monitoring" &>/dev/null; then
    useradd -r -s /bin/false monitoring
fi

# Add Elasticsearch repository for Logstash
echo "Adding Elastic repository..."
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-8.x.list
