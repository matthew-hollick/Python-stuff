from faker import Faker
import random
from datetime import datetime, timedelta
import math
import json

# Initialize Faker
fake = Faker()

# Constants
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
STATUS_2XX = [200, 201, 204]
STATUS_5XX = [500, 502, 503, 504]

# Function to calculate the percentage of 2xx statuses at a given time
def get_2xx_percentage(current_time, start_transition, end_transition, sigma):
    midpoint = (start_transition + end_transition) / 2
    if current_time < start_transition or current_time > end_transition:
        return 1.0  # 100% 2xx outside the transition range
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
def generate_logs(start_time, end_time, log_rate):
    logs = []
    total_seconds = int((end_time - start_time).total_seconds())
    start_transition = total_seconds * 0.25  # 25% of the dataset
    end_transition = total_seconds * 0.75    # 75% of the dataset
    sigma = (end_transition - start_transition) / 6  # Standard deviation for normal distribution

    for i in range(0, total_seconds, log_rate):
        current_time = start_time + timedelta(seconds=i)
        elapsed_time = i

        # Calculate the percentage of 2xx statuses
        percent_2xx = get_2xx_percentage(elapsed_time, start_transition, end_transition, sigma)

        # Determine the status code based on the percentage
        if random.random() < percent_2xx:
            status = random.choice(STATUS_2XX)
        else:
            status = random.choice(STATUS_5XX)

        # Generate the log entry as a JSON object
        log_entry = generate_log_entry(current_time.strftime("%Y-%m-%dT%H:%M:%S%z"), status)
        logs.append(log_entry)

    return logs

# Main function
def main():
    # Define start time, end time, and log rate
    start_time = datetime(2023, 10, 27, 0, 0, 0)  # Example: October 27, 2023, 00:00:00
    end_time = datetime(2023, 10, 28, 0, 0, 0)    # Example: October 28, 2023, 00:00:00
    log_rate = 1  # Logs per second

    # Generate logs
    logs = generate_logs(start_time, end_time, log_rate)

    # Write logs to a JSON file
    with open("http_server_logs.json", "w") as f:
        json.dump(logs, f, indent=2)

    print(f"Logs generated successfully! Total logs: {len(logs)}")

# Run the script
if __name__ == "__main__":
    main()