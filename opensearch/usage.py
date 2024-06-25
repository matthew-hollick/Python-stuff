from opensearchpy import OpenSearch, RequestsHttpConnection
import csv
import re
from collections import defaultdict
import urllib3

# Disable warnings about invalid certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def connect_to_opensearch():
    host = "localhost"  # Replace with your OpenSearch host if different
    port = 9200  # Replace with your OpenSearch port if different
    auth = ("admin", "123Pass....")  # Replace with your credentials

    return OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        connection_class=RequestsHttpConnection,
    )


def parse_index_name(index_name, project):
    pattern = rf"\.ds-e\.([^.]+)\.([^.]+)\.{project}-[^.]+\.([^.]+)\.(\d{{4}})\.(\d{{2}})-(\d+)"
    match = re.match(pattern, index_name)
    if match:
        return match.groups()
    return None


def get_index_stats(client):
    stats = client.indices.stats(index="*", metric="_all")
    return stats["indices"]


def write_detailed_csv(stats, filename, project):
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "ENVIRONMENT",
                "TEAM",
                "NAME",
                "YEAR",
                "WEEK",
                "INSTANCE",
                "Total Size",
                "Size of Primaries",
                "Total Documents",
                "Deleted Documents",
                "Primaries",
                "Replicas",
            ]
        )

        for index_name, index_stats in stats.items():
            parsed = parse_index_name(index_name, project)
            if parsed:
                team, environment, name, year, week, instance = parsed
                writer.writerow(
                    [
                        environment,
                        team,
                        name,
                        year,
                        week,
                        instance,
                        index_stats["total"]["store"]["size_in_bytes"],
                        index_stats["primaries"]["store"]["size_in_bytes"],
                        index_stats["total"]["docs"]["count"],
                        index_stats["total"]["docs"]["deleted"],
                        index_stats["primaries"]["docs"]["count"],
                        index_stats["total"]["docs"]["count"]
                        - index_stats["primaries"]["docs"]["count"],
                    ]
                )


def write_aggregated_csv(stats, filename, project):
    aggregated = defaultdict(int)
    for index_name, index_stats in stats.items():
        parsed = parse_index_name(index_name, project)
        if parsed:
            team = parsed[0]
            aggregated[team] += index_stats["total"]["store"]["size_in_bytes"]

    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["TEAM", "Total Size"])
        for team, total_size in aggregated.items():
            writer.writerow([team, total_size])


def main():
    try:
        client = connect_to_opensearch()
        project = input("Project name (default is 'ipass'): ") or "ipass"
        stats = get_index_stats(client)

        write_detailed_csv(stats, "detailed_index_stats.csv", project)
        print("Detailed CSV file has been created successfully.")

        write_aggregated_csv(stats, "aggregated_index_stats.csv", project)
        print("Aggregated CSV file has been created successfully.")

    except Exception as e:
        print(f"Bugger: {e}")


if __name__ == "__main__":
    main()
