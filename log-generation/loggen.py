from faker import Faker
import random
from datetime import datetime, timedelta
import math
import json

# disclaimer - I stole the maths and I cant remember where from.
# disclaimer 2 - maths is hard

# TODO
# - write directly to Elasticsearch.
# - make varibles defined in main() commandline options
# - intervals lower than 1 second should work.

# Initialize Faker
fake = Faker()

# Constants
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE"]
STATUS_2XX = [200, 201, 204]
STATUS_5XX = [500, 502, 503, 504]

# Function to calculate the percentage of 5xx statuses at a given time
def get_5xx_percentage(current_time, start_transition, end_transition, sigma):
    midpoint = (start_transition + end_transition) / 2
    if current_time < start_transition or current_time > end_transition:
        return 0  # 0% 5xx outside the transition range
    return math.exp(-((current_time - midpoint) ** 2) / (2 * sigma ** 2))

# Function to generate a single log entry as a JSON object
def generate_log_entry(timestamp, status):
    log_entry = {
        "ip": fake.ipv4(),
        "user": fake.user_name(),
        "timestamp": timestamp,
        "method": random.choice(HTTP_METHODS),
        "path": fake.uri_path(),
        "protocol": "HTTP/1.1",
        "status": status,
        "size": random.randint(100, 5000)
    }
    return log_entry

# Function to generate logs
def generate_logs(start_time, end_time, interval):
    logs = []
    total_seconds = int((end_time - start_time).total_seconds())
    start_transition = total_seconds * 0.25
    end_transition = total_seconds * 0.75
    sigma = (end_transition - start_transition) / 6

    for i in range(0, total_seconds, interval):
        current_time = start_time + timedelta(seconds=i)
        elapsed_time = i

        # Calculate the percentage of 5xx statuses
        percent_5xx = get_5xx_percentage(elapsed_time, start_transition, end_transition, sigma)

        # Determine the status code based on the percentage
        if random.random() > percent_5xx:
            status = random.choice(STATUS_2XX)
        else:
            status = random.choice(STATUS_5XX)

        log_entry = generate_log_entry(current_time.strftime("%Y-%m-%dT%H:%M:%S%z"), status)
        logs.append(log_entry)

    return logs

# Function to format logs for Elasticsearch Bulk API
def format_for_bulk_api(logs, index_name):
    bulk_data = []
    for log in logs:
        action = {
            "index": {
                "_index": index_name,
                "_id": None  # I think that I dont need this but it is in the example.
            }
        }
        bulk_data.append(json.dumps(action))
        bulk_data.append(json.dumps(log))
    return bulk_data

# Main function
def main():
    # Define start time, end time, and message interval
    start_time = datetime(2025, 1, 1, 0, 0, 0)
    end_time = datetime(2025, 1, 2, 0, 0, 0)
    interval = 1  # seconds between records

    logs = generate_logs(start_time, end_time, interval)

    index_name = "http_server_logs"
    bulk_data = format_for_bulk_api(logs, index_name)

    with open("http_server_logs_bulk.ndjson", "w") as f:
        for line in bulk_data:
            f.write(line + "\n")

    print(f"Log records generated successfully! Total records: {len(logs)}")

# Run the script
if __name__ == "__main__":
    main()
