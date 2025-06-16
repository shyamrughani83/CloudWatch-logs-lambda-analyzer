"""
Tests for the CloudWatchLogsClient module.
"""

import pytest
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from unittest.mock import MagicMock, patch

from utils.aws_client import CloudWatchLogsClient, get_aws_profiles


def test_initialize_client():
    """Test initializing the CloudWatch Logs client."""
    with patch('boto3.Session') as mock_session:
        # Mock the session and client
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        # Create the client
        client = CloudWatchLogsClient(region_name='us-east-1')
        
        # Check that the session was created with the correct parameters
        mock_session.assert_called_once_with(profile_name=None, region_name='us-east-1')
        
        # Check that the logs client was created
        mock_session.return_value.client.assert_called_once_with('logs')
        
        # Check that the client attributes were set correctly
        assert client.region_name == 'us-east-1'
        assert client.profile_name is None
        assert client.logs_client == mock_client


def test_initialize_client_with_profile():
    """Test initializing the CloudWatch Logs client with a profile."""
    with patch('boto3.Session') as mock_session:
        # Mock the session and client
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        # Create the client with a profile
        client = CloudWatchLogsClient(region_name='us-east-1', profile_name='test-profile')
        
        # Check that the session was created with the correct parameters
        mock_session.assert_called_once_with(profile_name='test-profile', region_name='us-east-1')
        
        # Check that the logs client was created
        mock_session.return_value.client.assert_called_once_with('logs')
        
        # Check that the client attributes were set correctly
        assert client.region_name == 'us-east-1'
        assert client.profile_name == 'test-profile'
        assert client.logs_client == mock_client


def test_initialize_client_error():
    """Test handling errors when initializing the client."""
    with patch('boto3.Session') as mock_session:
        # Mock the session to raise an error
        mock_session.side_effect = NoCredentialsError()
        
        # Create the client (should handle the error)
        with patch('streamlit.error') as mock_error:
            client = CloudWatchLogsClient(region_name='us-east-1')
            
            # Check that the error was logged
            mock_error.assert_called_once()
            
            # Check that the client was initialized but logs_client is None
            assert client.region_name == 'us-east-1'
            assert client.logs_client is None


def test_is_authenticated(mock_aws_client):
    """Test checking if the client is authenticated."""
    # Mock the describe_log_groups method to return successfully
    mock_aws_client.logs_client.describe_log_groups.return_value = {'logGroups': []}
    
    # Check authentication
    assert mock_aws_client.is_authenticated() == True
    
    # Mock the describe_log_groups method to raise an error
    mock_aws_client.logs_client.describe_log_groups.side_effect = ClientError(
        {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}},
        'DescribeLogGroups'
    )
    
    # Check authentication again
    assert mock_aws_client.is_authenticated() == False


def test_get_log_groups(mock_aws_client):
    """Test getting log groups."""
    # Mock the paginator
    paginator = MagicMock()
    mock_aws_client.logs_client.get_paginator.return_value = paginator
    
    # Mock the paginate method to return log groups
    paginator.paginate.return_value = [
        {
            'logGroups': [
                {'logGroupName': '/aws/lambda/test-function-1'},
                {'logGroupName': '/aws/lambda/test-function-2'}
            ]
        }
    ]
    
    # Get log groups
    with patch('streamlit.spinner'):
        log_groups = mock_aws_client.get_log_groups()
    
    # Check that we got the expected log groups
    assert len(log_groups) == 2
    assert log_groups[0]['logGroupName'] == '/aws/lambda/test-function-1'
    assert log_groups[1]['logGroupName'] == '/aws/lambda/test-function-2'
    
    # Check that the paginator was called with the correct parameters
    mock_aws_client.logs_client.get_paginator.assert_called_once_with('describe_log_groups')
    paginator.paginate.assert_called_once_with(limit=50)


def test_get_log_groups_with_prefix(mock_aws_client):
    """Test getting log groups with a prefix."""
    # Mock the paginator
    paginator = MagicMock()
    mock_aws_client.logs_client.get_paginator.return_value = paginator
    
    # Mock the paginate method to return log groups
    paginator.paginate.return_value = [
        {
            'logGroups': [
                {'logGroupName': '/aws/lambda/test-function-1'}
            ]
        }
    ]
    
    # Get log groups with a prefix
    with patch('streamlit.spinner'):
        log_groups = mock_aws_client.get_log_groups(prefix='test')
    
    # Check that we got the expected log groups
    assert len(log_groups) == 1
    assert log_groups[0]['logGroupName'] == '/aws/lambda/test-function-1'
    
    # Check that the paginator was called with the correct parameters
    mock_aws_client.logs_client.get_paginator.assert_called_once_with('describe_log_groups')
    paginator.paginate.assert_called_once_with(limit=50, logGroupNamePrefix='test')


def test_get_log_groups_error(mock_aws_client):
    """Test handling errors when getting log groups."""
    # Mock the paginator to raise an error
    mock_aws_client.logs_client.get_paginator.side_effect = ClientError(
        {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}},
        'DescribeLogGroups'
    )
    
    # Get log groups (should handle the error)
    with patch('streamlit.error') as mock_error:
        with patch('streamlit.spinner'):
            log_groups = mock_aws_client.get_log_groups()
        
        # Check that the error was logged
        mock_error.assert_called_once()
        
        # Check that we got an empty list
        assert log_groups == []


def test_get_log_events(mock_aws_client):
    """Test getting log events."""
    # Mock the paginator
    paginator = MagicMock()
    mock_aws_client.logs_client.get_paginator.return_value = paginator
    
    # Mock the paginate method to return log events
    paginator.paginate.return_value = [
        {
            'events': [
                {
                    'timestamp': 1623456789000,
                    'message': 'Test message 1',
                    'logStreamName': 'test-stream',
                    'eventId': '12345678901234567890123456789012'
                },
                {
                    'timestamp': 1623456790000,
                    'message': 'Test message 2',
                    'logStreamName': 'test-stream',
                    'eventId': '12345678901234567890123456789013'
                }
            ]
        }
    ]
    
    # Get log events
    with patch('streamlit.progress'):
        with patch('streamlit.empty'):
            log_events, total = mock_aws_client.get_log_events(
                log_group_name='/aws/lambda/test-function',
                start_time=1623456789000,
                end_time=1623456790000
            )
    
    # Check that we got the expected log events
    assert len(log_events) == 2
    assert log_events[0]['message'] == 'Test message 1'
    assert log_events[1]['message'] == 'Test message 2'
    assert total == 2
    
    # Check that the paginator was called with the correct parameters
    mock_aws_client.logs_client.get_paginator.assert_called_once_with('filter_log_events')
    paginator.paginate.assert_called_once_with(
        logGroupName='/aws/lambda/test-function',
        startTime=1623456789000,
        endTime=1623456790000,
        interleaved=True
    )


def test_get_log_events_with_filter(mock_aws_client):
    """Test getting log events with a filter pattern."""
    # Mock the paginator
    paginator = MagicMock()
    mock_aws_client.logs_client.get_paginator.return_value = paginator
    
    # Mock the paginate method to return log events
    paginator.paginate.return_value = [
        {
            'events': [
                {
                    'timestamp': 1623456789000,
                    'message': 'ERROR: Test error message',
                    'logStreamName': 'test-stream',
                    'eventId': '12345678901234567890123456789012'
                }
            ]
        }
    ]
    
    # Get log events with a filter pattern
    with patch('streamlit.progress'):
        with patch('streamlit.empty'):
            log_events, total = mock_aws_client.get_log_events(
                log_group_name='/aws/lambda/test-function',
                start_time=1623456789000,
                end_time=1623456790000,
                filter_pattern='ERROR'
            )
    
    # Check that we got the expected log events
    assert len(log_events) == 1
    assert log_events[0]['message'] == 'ERROR: Test error message'
    assert total == 1
    
    # Check that the paginator was called with the correct parameters
    mock_aws_client.logs_client.get_paginator.assert_called_once_with('filter_log_events')
    paginator.paginate.assert_called_once_with(
        logGroupName='/aws/lambda/test-function',
        startTime=1623456789000,
        endTime=1623456790000,
        filterPattern='ERROR',
        interleaved=True
    )


def test_get_log_events_error(mock_aws_client):
    """Test handling errors when getting log events."""
    # Mock the paginator to raise an error
    mock_aws_client.logs_client.get_paginator.side_effect = ClientError(
        {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}},
        'FilterLogEvents'
    )
    
    # Get log events (should handle the error)
    with patch('streamlit.error') as mock_error:
        with patch('streamlit.progress'):
            with patch('streamlit.empty'):
                log_events, total = mock_aws_client.get_log_events(
                    log_group_name='/aws/lambda/test-function'
                )
        
        # Check that the error was logged
        mock_error.assert_called_once()
        
        # Check that we got empty results
        assert log_events == []
        assert total == 0


def test_get_available_regions(mock_aws_client):
    """Test getting available AWS regions."""
    # Mock the EC2 client
    with patch('boto3.client') as mock_client:
        # Mock the describe_regions method
        mock_ec2 = MagicMock()
        mock_client.return_value = mock_ec2
        mock_ec2.describe_regions.return_value = {
            'Regions': [
                {'RegionName': 'us-east-1'},
                {'RegionName': 'us-east-2'},
                {'RegionName': 'us-west-1'}
            ]
        }
        
        # Get available regions
        regions = mock_aws_client.get_available_regions()
        
        # Check that we got the expected regions
        assert len(regions) == 3
        assert 'us-east-1' in regions
        assert 'us-east-2' in regions
        assert 'us-west-1' in regions
        
        # Check that the EC2 client was created
        mock_client.assert_called_once_with('ec2')
        
        # Check that describe_regions was called
        mock_ec2.describe_regions.assert_called_once()


def test_get_available_regions_error(mock_aws_client):
    """Test handling errors when getting available regions."""
    # Mock the EC2 client to raise an error
    with patch('boto3.client') as mock_client:
        mock_client.side_effect = NoCredentialsError()
        
        # Get available regions (should handle the error)
        regions = mock_aws_client.get_available_regions()
        
        # Check that we got the fallback regions
        assert len(regions) > 0
        assert 'us-east-1' in regions


def test_get_aws_profiles():
    """Test getting AWS profiles."""
    # Mock the boto3 Session
    with patch('boto3.Session') as mock_session:
        # Mock the available_profiles property
        mock_session.return_value.available_profiles = ['default', 'test-profile']
        
        # Get AWS profiles
        profiles = get_aws_profiles()
        
        # Check that we got the expected profiles
        assert len(profiles) == 2
        assert 'default' in profiles
        assert 'test-profile' in profiles
        
        # Check that the Session was created
        mock_session.assert_called_once()


def test_get_aws_profiles_error():
    """Test handling errors when getting AWS profiles."""
    # Mock the boto3 Session to raise an error
    with patch('boto3.Session') as mock_session:
        mock_session.side_effect = Exception('Test error')
        
        # Get AWS profiles (should handle the error)
        profiles = get_aws_profiles()
        
        # Check that we got an empty list
        assert profiles == []
