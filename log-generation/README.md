# HTTP Log generator

Generates log messages ready for bulk ingest into Elasticsearch.

To make the data a bit more interesting there is a normal distribution curve in the middle 50% of the data where 5xx statuses increase to 100% of the data and then decrease back to 0%.

```
export MY_ELASTIC=my.elastic.search.server
export MY_USERNAME=
export MY_PASSWORD=

python loggen.py

cat http_server_logs_bulk.ndjson | curl -u ${MY_USERNAME}:${MY_PASSWORD} -X POST "https://MY_ELASTIC:9200/_bulk" -H "Content-Type: application/json" -H "Cache-Control: no-cache" --data-binary @- > /dev/null
```
