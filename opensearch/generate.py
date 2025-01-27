from __future__ import annotations

import random
import string
from datetime import datetime
from datetime import timedelta

import urllib3
from opensearchpy import OpenSearch
from opensearchpy import RequestsHttpConnection

# Certs are broken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def connect_to_opensearch():
    host = 'localhost'
    port = 9200
    auth = ('admin', '123Pass....')

    return OpenSearch(
        hosts=[{'host': host, 'port': port}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        connection_class=RequestsHttpConnection,
    )


def generate_random_index_name(project):
    team = ''.join(random.choices(string.ascii_lowercase, k=3))
    environment = random.choice(['dev', 'test', 'prod'])
    name = ''.join(random.choices(string.ascii_lowercase, k=5))
    date = datetime.now() - timedelta(days=random.randint(0, 365))
    year = date.strftime('%Y')
    week = date.strftime('%W')
    # I am so lazy.
    instance = str(random.randint(1, 999999)).zfill(6)

    return f'.ds-e.{team}.{environment}.{project}-{environment}.{name}.{year}.{week}-{instance}'


def create_and_populate_indices(client, num_indices, project):
    for _ in range(num_indices):
        # I should create a list of common team names realy..
        index_name = generate_random_index_name(project)
        client.indices.create(index=index_name)

        num_docs = random.randint(100, 10000)

        # Straight outa Stackexchange.
        for _ in range(num_docs):
            doc = {
                'timestamp': datetime.now().isoformat(),
                'message': ''.join(random.choices(string.ascii_lowercase + ' ', k=50)),
                'value': random.randint(1, 1000),
            }
            client.index(index=index_name, body=doc)

        print(
            f'Created and populated index: {index_name} with {num_docs} documents',
        )


def main():
    try:
        client = connect_to_opensearch()
        num_indices = int(input('Number of indices to create: '))
        project = input("Project name (default is 'ipass'): ") or 'ipass'
        create_and_populate_indices(client, num_indices, project)
        print('Done, done.')
    except Exception as e:
        print(f'Bugger: {e}')


if __name__ == '__main__':
    main()
