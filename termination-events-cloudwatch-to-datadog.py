from __future__ import print_function
import boto3
import json
import logging
import urllib
import urllib2
import time

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

print('Loading function')

def lambda_handler(event, context):
    logger.info(json.dumps(event))
    instance = (event['detail']['instance-id'])
    # connect to EC2
    ec2 = boto3.client('ec2')
    # Get all tags from instance
    tags = ec2.describe_tags(
        Filters=[
            {
                'Name': 'resource-id',
                'Values': [instance],
            },
        ],
    )
    tags_extracted=tags['Tags'] #tags_extracted is a list of dicts
    final_tags = []
    for tags_extracted_dict in tags_extracted:
        pair = '%s : %s' % (tags_extracted_dict.pop("Key"), tags_extracted_dict.pop("Value"))
        final_tags.append(pair)
    print(final_tags)
    
    datadog_keys = {
    'api_key':'<insert-api-key>',
    'app_key':'<insert-app-key>'
    }

    creds = urllib.urlencode(datadog_keys)
    base_dict = [
        {
        'metric': 'aws.ec2.termination.event',
        'points': [(int(time.time()), 1)],
        'type': 'gauge',
        'tags': final_tags,
        'host': instance,
    }
    ]
    metrics_dict = {
        'series': base_dict,
    }
    data = json.dumps(metrics_dict)
    url = '%s?%s' % (datadog_keys.get('api_host', 'https://app.datadoghq.com/api/v1/series'), creds)
    req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
    try:
        response = urllib2.urlopen(req)
        contents = response.read()
    except urllib2.HTTPError, error:
        contents = error.read()
    logger.info(response.getcode())
