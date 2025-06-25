"""
AWS Client Module for CloudWatch Logs Analyzer

This module provides functionality to interact with AWS CloudWatch Logs.
"""

import boto3
import os
import configparser
from typing import List, Dict, Any, Optional, Union, Tuple
import datetime
import time
import botocore.exceptions
from utils.logger import get_logger

def get_aws_profiles() -> List[str]:
    """
    Get available AWS profiles from credentials file.
    
    Returns:
        List[str]: List of available AWS profile names
    """
    profiles = ['default']
    
    try:
        config = configparser.ConfigParser()
        config.read(os.path.expanduser('~/.aws/credentials'))
        profiles = ['default'] + [section for section in config.sections() if section != 'default']
    except Exception:
        pass
        
    return profiles

class CloudWatchLogsClient:
    """Client for interacting with AWS CloudWatch Logs."""
    
    def __init__(self, region_name: str = None, profile_name: str = None):
        """
        Initialize CloudWatch Logs client.
        
        Args:
            region_name (str, optional): AWS region. Defaults to None.
            profile_name (str, optional): AWS profile name. Defaults to None.
        """
        self.region = region_name or os.environ.get('AWS_REGION', 'us-east-1')
        self.profile = profile_name
        self.logger = get_logger("aws_client")
        
        session = boto3.Session(profile_name=profile_name, region_name=self.region)
        self.logs_client = session.client('logs')
        self._authenticated = None  # Will be set on first authentication check
    
    def is_authenticated(self) -> bool:
        """
        Check if the AWS client is authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        if self._authenticated is not None:
            return self._authenticated
            
        try:
            # Try a simple API call to check authentication
            self.logs_client.describe_log_groups(limit=1)
            self._authenticated = True
            return True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] in ['AccessDeniedException', 'UnauthorizedOperation', 'AuthFailure']:
                self._authenticated = False
                return False
            # For other errors, assume authentication is working but there's another issue
            self._authenticated = True
            return True
        except Exception:
            self._authenticated = False
            return False
    
    def get_available_regions(self) -> List[str]:
        """
        Get list of available AWS regions.
        
        Returns:
            List[str]: List of available AWS region names
        """
        # Common AWS regions
        regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'ca-central-1',
            'eu-north-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
            'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3',
            'ap-southeast-1', 'ap-southeast-2',
            'ap-south-1',
            'sa-east-1'
        ]
        
        try:
            # Try to get regions from EC2 client
            ec2_client = boto3.client('ec2', region_name='us-east-1')
            response = ec2_client.describe_regions()
            regions = [region['RegionName'] for region in response['Regions']]
        except Exception:
            # Fall back to hardcoded list
            pass
            
        return sorted(regions)
    
    def get_log_groups(self, prefix: str = None) -> List[Dict[str, Any]]:
        """
        Get list of log groups, optionally filtered by prefix.
        
        Args:
            prefix (str, optional): Log group prefix filter. Defaults to None.
            
        Returns:
            List[Dict[str, Any]]: List of log group information
        """
        params = {}
        if prefix:
            params['logGroupNamePrefix'] = prefix
            
        log_groups = []
        paginator = self.logs_client.get_paginator('describe_log_groups')
        
        for page in paginator.paginate(**params):
            log_groups.extend(page.get('logGroups', []))
            
        return log_groups
    
    def get_log_streams(self, log_group_name: str, prefix: str = None) -> List[Dict[str, Any]]:
        """
        Get list of log streams for a log group.
        
        Args:
            log_group_name (str): Name of the log group
            prefix (str, optional): Stream name prefix filter. Defaults to None.
            
        Returns:
            List[Dict[str, Any]]: List of log stream information
        """
        params = {'logGroupName': log_group_name, 'descending': True, 'orderBy': 'LastEventTime'}
        if prefix:
            params['logStreamNamePrefix'] = prefix
            
        log_streams = []
        paginator = self.logs_client.get_paginator('describe_log_streams')
        
        for page in paginator.paginate(**params):
            log_streams.extend(page.get('logStreams', []))
            
        return log_streams
    
    def get_log_events(self, 
                      log_group_name: str, 
                      log_stream_name: str = None,
                      start_time: Optional[Union[datetime.datetime, int]] = None,
                      end_time: Optional[Union[datetime.datetime, int]] = None,
                      filter_pattern: str = None,
                      limit: int = 10000) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get log events from CloudWatch Logs.
        
        Args:
            log_group_name (str): Name of the log group
            log_stream_name (str, optional): Name of the log stream. Defaults to None.
            start_time (Union[datetime.datetime, int], optional): Start time for logs. Can be datetime or int. Defaults to None.
            end_time (Union[datetime.datetime, int], optional): End time for logs. Can be datetime or int. Defaults to None.
            filter_pattern (str, optional): Filter pattern for logs. Defaults to None.
            limit (int, optional): Maximum number of log events to return. Defaults to 10000.
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: Tuple containing list of log events and count of processed events
        """
        if log_stream_name:
            # Get events from a specific log stream
            params = {
                'logGroupName': log_group_name,
                'logStreamName': log_stream_name,
                'limit': min(limit, 10000)  # AWS limit is 10000
            }
            
            if start_time is not None:
                if isinstance(start_time, datetime.datetime):
                    params['startTime'] = int(start_time.timestamp() * 1000)
                elif isinstance(start_time, int):
                    params['startTime'] = start_time
                    
            if end_time is not None:
                if isinstance(end_time, datetime.datetime):
                    params['endTime'] = int(end_time.timestamp() * 1000)
                elif isinstance(end_time, int):
                    params['endTime'] = end_time
                
            events = []
            processed_count = 0
            response = self.logs_client.get_log_events(**params)
            events.extend(response.get('events', []))
            processed_count += len(response.get('events', []))
            
            while response.get('nextForwardToken') and len(events) < limit:
                next_token = response['nextForwardToken']
                response = self.logs_client.get_log_events(
                    **params, 
                    nextToken=next_token
                )
                
                new_events = response.get('events', [])
                if not new_events:
                    break
                    
                events.extend(new_events)
                processed_count += len(new_events)
                
                if len(events) >= limit:
                    break
                    
            return events[:limit], processed_count
        else:
            # Use filter_log_events to search across all streams
            params = {
                'logGroupName': log_group_name,
                'limit': min(limit, 10000)
            }
            
            if start_time is not None:
                if isinstance(start_time, datetime.datetime):
                    params['startTime'] = int(start_time.timestamp() * 1000)
                elif isinstance(start_time, int):
                    params['startTime'] = start_time
                    
            if end_time is not None:
                if isinstance(end_time, datetime.datetime):
                    params['endTime'] = int(end_time.timestamp() * 1000)
                elif isinstance(end_time, int):
                    params['endTime'] = end_time
                
            if filter_pattern:
                params['filterPattern'] = filter_pattern
                
            events = []
            processed_count = 0
            paginator = self.logs_client.get_paginator('filter_log_events')
            
            for page in paginator.paginate(**params):
                page_events = page.get('events', [])
                events.extend(page_events)
                processed_count += len(page_events)
                
                if len(events) >= limit:
                    break
                    
            return events[:limit], processed_count
    def describe_log_group(self, log_group_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific log group.
        
        Args:
            log_group_name: Name of the log group
            
        Returns:
            Dict[str, Any]: Log group details
        """
        try:
            response = self.logs_client.describe_log_groups(
                logGroupNamePrefix=log_group_name,
                limit=1
            )
            
            log_groups = response.get('logGroups', [])
            for log_group in log_groups:
                if log_group.get('logGroupName') == log_group_name:
                    return log_group
            
            return {}
        except Exception as e:
            self.logger.error(f"Error describing log group {log_group_name}: {str(e)}")
            return {}
    
    def put_retention_policy(self, log_group_name: str, retention_in_days: int) -> bool:
        """
        Set the retention policy for a log group.
        
        Args:
            log_group_name: Name of the log group
            retention_in_days: Number of days to retain logs
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logs_client.put_retention_policy(
                logGroupName=log_group_name,
                retentionInDays=retention_in_days
            )
            return True
        except Exception as e:
            self.logger.error(f"Error setting retention policy for {log_group_name}: {str(e)}")
            return False
    
    def delete_retention_policy(self, log_group_name: str) -> bool:
        """
        Delete the retention policy for a log group.
        
        Args:
            log_group_name: Name of the log group
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logs_client.delete_retention_policy(
                logGroupName=log_group_name
            )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting retention policy for {log_group_name}: {str(e)}")
            return False
    
    def get_log_group_metrics(self, log_group_name: str, start_time: datetime.datetime, 
                             end_time: datetime.datetime, period: int = 3600) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get metrics for a log group.
        
        Args:
            log_group_name: Name of the log group
            start_time: Start time for metrics
            end_time: End time for metrics
            period: Period in seconds (default: 3600 = 1 hour)
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Metrics data
        """
        try:
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            
            # Get incoming log events
            incoming_logs_response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Logs',
                MetricName='IncomingLogEvents',
                Dimensions=[
                    {
                        'Name': 'LogGroupName',
                        'Value': log_group_name
                    },
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=['Sum']
            )
            
            # Get incoming bytes
            incoming_bytes_response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Logs',
                MetricName='IncomingBytes',
                Dimensions=[
                    {
                        'Name': 'LogGroupName',
                        'Value': log_group_name
                    },
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=['Sum']
            )
            
            return {
                'IncomingLogEvents': incoming_logs_response.get('Datapoints', []),
                'IncomingBytes': incoming_bytes_response.get('Datapoints', [])
            }
        except Exception as e:
            self.logger.error(f"Error getting metrics for {log_group_name}: {str(e)}")
            return {
                'IncomingLogEvents': [],
                'IncomingBytes': []
            }
