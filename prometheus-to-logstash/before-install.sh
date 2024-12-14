#!/usr/bin/env bash
set -e

# Create monitoring user if it doesn't exist
echo "Checking for monitoring user..."
if ! getent passwd monitoring > /dev/null; then
    echo "Creating monitoring user..."
    useradd -r -s /bin/false monitoring
else
    echo "User monitoring already exists, skipping creation"
fi

echo "Adding Elastic repository..."
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch -o /etc/apt/trusted.gpg.d/elastic.asc
chmod 644 /etc/apt/trusted.gpg.d/elastic.asc
echo "deb [signed-by=/etc/apt/trusted.gpg.d/elastic.asc] https://artifacts.elastic.co/packages/8.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-8.x.list
