#!/usr/bin/env python

__doc__ = """
This script executes Marathon tasks for the logging stack is meant for use with DC/OS deployments only.
"""
import requests, os, json, time


def run():
    # attempt to delete an old instance..if it doesn't exists it will error but we don't care so we ignore it
    requests.delete('http://marathon.mesos:8080/v2/apps/scale-logstash')

    es_urls = os.getenv('SCALE_ELASTICSEARCH_URL')
    # if ELASTICSEARCH_URL is not set, assume we are running within DCOS and attempt to query Elastic scheduler
    if not es_urls or not len(es_urls.strip()):
        response = requests.get('http://elasticsearch.marathon.mesos:31105/v1/tasks')
        endpoints = ['http://%s' % x['http_address'] for x in json.loads(response.text)]
        es_urls = ','.join(endpoints)

    # get the Logstash container API endpoints
    logstash_image = os.getenv('LOGSTASH_DOCKER_IMAGE', 'geoint/logstash-elastic-ha')
    marathon = {
      'id': 'scale-logstash',
      'cpus': 0.5,
      'mem': 1024,
      'disk': 256,
      'instances': 1,
      'container': {
        'docker': {
          'image': logstash_image,
          'network': 'BRIDGE',
          'portMappings': [{
            'containerPort': 8000,
            'hostPort': 9229,
            'protocol': 'udp'
          },
          {
            'containerPort': 80,
            'hostPort': 0,
            'protocol': 'tcp'
          }
          ],
          'forcePullImage': True
        },
        'type': 'DOCKER',
        'volumes': []
      },
      'env': {
        'ELASTICSEARCH_URLS': es_urls
      },
      'labels': {},
      'healthChecks': [
        {
          "protocol": "HTTP",
          "path": "/",
          "gracePeriodSeconds": 5,
          "intervalSeconds": 10,
          "portIndex": 1,
          "timeoutSeconds": 2,
          "maxConsecutiveFailures": 3
        },
      ],
      'uris': []
    }

    # Capture any passed-in environment variables that are relevant to Logstash container.
    CONFIG_URI = os.getenv('CONFIG_URI')
    SLEEP_TIME = os.getenv('LOGSTASH_WATCHDOG_SLEEP_TIME')
    TEMPLATE_URI = os.getenv('LOGSTASH_TEMPLATE_URI')

    if SLEEP_TIME:
        marathon['env']['SLEEP_TIME'] = SLEEP_TIME

    if TEMPLATE_URI:
        marathon['env']['TEMPLATE_URI'] = TEMPLATE_URI

    if CONFIG_URI:
        marathon['uris'].append(CONFIG_URI)

    r = requests.post('http://marathon.mesos:8080/v2/apps/', json=marathon)
    if r.status_code >= 400:
        print(r.text)
    while int(json.loads(requests.get('http://marathon.mesos:8080/v2/apps/scale-logstash').text)['app']['tasksRunning']) == 0:
        time.sleep(5)
    # We don't need to inspect the port from Marathon since we know it based on HOST port defs
    print('udp://scale-logstash.marathon.mesos:9229')
    print(es_urls)

if __name__ == '__main__':
    # ensure this doesn't try and run if imported
    run()
