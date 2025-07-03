import boto3
from botocore.exceptions import ClientError
import datetime
from app.utils.aws_helper import get_boto3_session

def get_log_streams(region, log_group_name, profile=None):
    """Get log streams for a specific log group"""
    session = get_boto3_session(region, profile)
    logs_client = session.client('logs')
    
    log_streams = []
    paginator = logs_client.get_paginator('describe_log_streams')
    
    # Use a smaller page size for faster initial response
    page_iterator = paginator.paginate(
        logGroupName=log_group_name,
        orderBy='LastEventTime',
        descending=True,
        PaginationConfig={
            'MaxItems': 100,
            'PageSize': 20
        }
    )
    
    for page in page_iterator:
        for log_stream in page['logStreams']:
            log_streams.append({
                'name': log_stream['logStreamName'],
                'firstEventTimestamp': log_stream.get('firstEventTimestamp'),
                'lastEventTimestamp': log_stream.get('lastEventTimestamp'),
                'lastIngestionTime': log_stream.get('lastIngestionTime'),
                'storedBytes': log_stream.get('storedBytes', 0)
            })
    
    return log_streams
