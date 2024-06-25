from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
import re
from collections import defaultdict
import urllib3
from datetime import datetime

# Broken certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def connect_to_opensearch():
    host = "localhost"
    port = 9200
    auth = ("admin", "123Pass....")

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


def upload_detailed_stats(client, stats, project):
    actions = []
    timestamp = datetime.utcnow().isoformat()

    for index_name, index_stats in stats.items():
        parsed = parse_index_name(index_name, project)
        if parsed:
            team, environment, name, year, week, instance = parsed
            action = {
                "_index": "detailed_index_stats",
                "_source": {
                    "timestamp": timestamp,
                    "environment": environment,
                    "team": team,
                    "name": name,
                    "year": year,
                    "week": week,
                    "instance": instance,
                    "total_size": index_stats["total"]["store"]["size_in_bytes"],
                    "size_of_primaries": index_stats["primaries"]["store"][
                        "size_in_bytes"
                    ],
                    "total_documents": index_stats["total"]["docs"]["count"],
                    "deleted_documents": index_stats["total"]["docs"]["deleted"],
                    "primaries": index_stats["primaries"]["docs"]["count"],
                    "replicas": index_stats["total"]["docs"]["count"]
                    - index_stats["primaries"]["docs"]["count"],
                },
            }
            actions.append(action)

    helpers.bulk(client, actions)
    print(f"Uploaded {len(actions)} detailed stats to OpenSearch.")


def upload_aggregated_stats(client, stats, project):
    aggregated = defaultdict(int)
    for index_name, index_stats in stats.items():
        parsed = parse_index_name(index_name, project)
        if parsed:
            team = parsed[0]
            aggregated[team] += index_stats["total"]["store"]["size_in_bytes"]

    actions = []
    timestamp = datetime.utcnow().isoformat()

    for team, total_size in aggregated.items():
        action = {
            "_index": "aggregated_index_stats",
            "_source": {"timestamp": timestamp, "team": team, "total_size": total_size},
        }
        actions.append(action)

    helpers.bulk(client, actions)
    print(f"Uploaded {len(actions)} aggregated stats to OpenSearch.")


def main():
    try:
        client = connect_to_opensearch()
        project = input("Project name (default is 'ipass'): ") or "ipass"
        stats = get_index_stats(client)

        upload_detailed_stats(client, stats, project)
        upload_aggregated_stats(client, stats, project)

        print("Stats have been successfully uploaded to OpenSearch.")

    except Exception as e:
        print(f"Bugger: {e}")


if __name__ == "__main__":
    main()
