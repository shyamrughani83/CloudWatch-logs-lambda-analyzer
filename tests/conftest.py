"""
Test fixtures and configuration for CloudWatch Logs Analyzer tests.
"""

import pytest
import pandas as pd
import datetime
import json
import os
from typing import Dict, Any, List

# Add the parent directory to the path so we can import the application modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.aws_client import CloudWatchLogsClient
from utils.log_processor import LogProcessor
from utils.metrics import MetricsCalculator


@pytest.fixture
def sample_log_events() -> List[Dict[str, Any]]:
    """
    Fixture providing sample CloudWatch log events.
    
    Returns:
        List of sample log events
    """
    return [
        {
            'timestamp': 1623456789000,
            'message': 'START RequestId: 1234abcd-56ef-78gh-90ij-1234klmnopqr Version: $LATEST',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789012'
        },
        {
            'timestamp': 1623456789100,
            'message': '2023-06-15T12:34:56.789Z\t1234abcd-56ef-78gh-90ij-1234klmnopqr\tINFO\tFunction execution started',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789013'
        },
        {
            'timestamp': 1623456789200,
            'message': '2023-06-15T12:34:56.890Z\t1234abcd-56ef-78gh-90ij-1234klmnopqr\tINFO\tProcessing request data',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789014'
        },
        {
            'timestamp': 1623456789300,
            'message': 'END RequestId: 1234abcd-56ef-78gh-90ij-1234klmnopqr',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789015'
        },
        {
            'timestamp': 1623456789400,
            'message': 'REPORT RequestId: 1234abcd-56ef-78gh-90ij-1234klmnopqr\tDuration: 123.45 ms\tBilled Duration: 124 ms\tMemory Size: 128 MB\tMax Memory Used: 75 MB',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789016'
        },
        {
            'timestamp': 1623456790000,
            'message': 'START RequestId: 2345bcde-67fg-89hi-01jk-2345lmnopqrs Version: $LATEST',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789017'
        },
        {
            'timestamp': 1623456790100,
            'message': '2023-06-15T12:35:56.789Z\t2345bcde-67fg-89hi-01jk-2345lmnopqrs\tERROR\tTypeError: Cannot read property \'id\' of undefined',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789018'
        },
        {
            'timestamp': 1623456790200,
            'message': 'END RequestId: 2345bcde-67fg-89hi-01jk-2345lmnopqrs',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789019'
        },
        {
            'timestamp': 1623456790300,
            'message': 'REPORT RequestId: 2345bcde-67fg-89hi-01jk-2345lmnopqrs\tDuration: 156.78 ms\tBilled Duration: 157 ms\tMemory Size: 128 MB\tMax Memory Used: 82 MB',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789020'
        },
        {
            'timestamp': 1623456791000,
            'message': 'START RequestId: 3456cdef-78gh-90ij-12kl-3456mnopqrst Version: $LATEST',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789021'
        },
        {
            'timestamp': 1623456791100,
            'message': '2023-06-15T12:36:56.789Z\t3456cdef-78gh-90ij-12kl-3456mnopqrst\tINFO\tFunction execution started',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789022'
        },
        {
            'timestamp': 1623456791200,
            'message': 'END RequestId: 3456cdef-78gh-90ij-12kl-3456mnopqrst',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789023'
        },
        {
            'timestamp': 1623456791300,
            'message': 'REPORT RequestId: 3456cdef-78gh-90ij-12kl-3456mnopqrst\tDuration: 89.01 ms\tBilled Duration: 90 ms\tMemory Size: 128 MB\tMax Memory Used: 68 MB\tInit Duration: 123.45 ms',
            'logStreamName': '2023/06/15/[$LATEST]abcdef123456',
            'eventId': '12345678901234567890123456789024'
        }
    ]


@pytest.fixture
def processed_log_data(sample_log_events) -> pd.DataFrame:
    """
    Fixture providing processed log data.
    
    Args:
        sample_log_events: Sample log events fixture
        
    Returns:
        DataFrame with processed log data
    """
    log_processor = LogProcessor()
    return log_processor.process_log_events(sample_log_events)


@pytest.fixture
def demo_log_data() -> pd.DataFrame:
    """
    Fixture providing demo log data.
    
    Returns:
        DataFrame with demo log data
    """
    log_processor = LogProcessor()
    start_time = datetime.datetime.now() - datetime.timedelta(hours=24)
    end_time = datetime.datetime.now()
    return log_processor.generate_demo_data(
        num_entries=100,
        start_time=start_time,
        end_time=end_time
    )


@pytest.fixture
def mock_aws_client(mocker):
    """
    Fixture providing a mocked AWS client.
    
    Args:
        mocker: pytest-mock fixture
        
    Returns:
        Mocked CloudWatchLogsClient
    """
    # Mock the boto3 session and client
    mock_session = mocker.patch('boto3.Session')
    mock_client = mocker.MagicMock()
    mock_session.return_value.client.return_value = mock_client
    
    # Create the client with the mocked session
    client = CloudWatchLogsClient(region_name='us-east-1')
    
    # Mock the get_log_groups method
    mock_client.get_paginator.return_value.paginate.return_value = [
        {
            'logGroups': [
                {'logGroupName': '/aws/lambda/test-function-1'},
                {'logGroupName': '/aws/lambda/test-function-2'}
            ]
        }
    ]
    
    return client
