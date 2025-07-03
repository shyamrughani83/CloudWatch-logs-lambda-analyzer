"""
Lambda Client Module for CloudWatch Logs Analyzer

This module provides functionality to interact with AWS Lambda functions.
"""

import boto3
import json
import base64
import datetime
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger("lambda_client")

class LambdaClient:
    """Client for interacting with AWS Lambda functions."""
    
    def __init__(self, region_name: str = None, profile_name: str = None):
        """
        Initialize the Lambda client.
        
        Args:
            region_name (str, optional): AWS region name. Defaults to None.
            profile_name (str, optional): AWS profile name. Defaults to None.
        """
        self.region = region_name
        self.profile = profile_name
        self.lambda_client = None
        self.iam_client = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AWS clients."""
        try:
            session = boto3.Session(region_name=self.region, profile_name=self.profile)
            self.lambda_client = session.client('lambda')
            self.iam_client = session.client('iam')
            logger.info(f"Initialized Lambda client in region {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize Lambda client: {str(e)}")
            self.lambda_client = None
            self.iam_client = None
    
    def is_authenticated(self) -> bool:
        """
        Check if the client is authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        if not self.lambda_client:
            return False
        
        try:
            # Try to list functions with a small limit to check authentication
            self.lambda_client.list_functions(MaxItems=1)
            return True
        except Exception as e:
            logger.error(f"Authentication check failed: {str(e)}")
            return False
    
    def list_functions(self, max_items: int = 50) -> List[Dict[str, Any]]:
        """
        List Lambda functions.
        
        Args:
            max_items (int, optional): Maximum number of functions to return. Defaults to 50.
            
        Returns:
            List[Dict[str, Any]]: List of Lambda functions
        """
        if not self.lambda_client:
            logger.error("Lambda client not initialized")
            return []
        
        try:
            functions = []
            paginator = self.lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate(MaxItems=max_items):
                functions.extend(page.get('Functions', []))
            
            logger.info(f"Retrieved {len(functions)} Lambda functions")
            return functions
        except Exception as e:
            logger.error(f"Failed to list Lambda functions: {str(e)}")
            return []
    
    def get_function(self, function_name: str) -> Dict[str, Any]:
        """
        Get details of a Lambda function.
        
        Args:
            function_name (str): Name or ARN of the Lambda function
            
        Returns:
            Dict[str, Any]: Function details
        """
        if not self.lambda_client:
            logger.error("Lambda client not initialized")
            return {}
        
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            logger.info(f"Retrieved details for function {function_name}")
            return response
        except Exception as e:
            logger.error(f"Failed to get function {function_name}: {str(e)}")
            return {}
    
    def invoke_function(self, 
                       function_name: str, 
                       payload: Union[Dict[str, Any], str] = None, 
                       invocation_type: str = 'RequestResponse',
                       fetch_logs: bool = True) -> Dict[str, Any]:
        """
        Invoke a Lambda function and optionally fetch its logs.
        
        Args:
            function_name (str): Name or ARN of the Lambda function
            payload (Union[Dict[str, Any], str], optional): Payload to send to the function. Defaults to None.
            invocation_type (str, optional): Invocation type (RequestResponse, Event, DryRun). Defaults to 'RequestResponse'.
            fetch_logs (bool, optional): Whether to fetch logs after invocation. Defaults to True.
            
        Returns:
            Dict[str, Any]: Invocation result including logs if fetch_logs is True
        """
        if not self.lambda_client:
            logger.error("Lambda client not initialized")
            return {'error': 'Lambda client not initialized'}
        
        try:
            # Convert payload to JSON string if it's a dictionary
            if isinstance(payload, dict):
                payload_json = json.dumps(payload)
            elif isinstance(payload, str):
                # Validate that the string is valid JSON
                try:
                    json.loads(payload)
                    payload_json = payload
                except json.JSONDecodeError:
                    logger.error("Invalid JSON payload")
                    return {'error': 'Invalid JSON payload'}
            else:
                payload_json = '{}'
            
            # Record start time for log fetching
            start_time = datetime.datetime.now() - datetime.timedelta(seconds=5)  # 5 seconds buffer
            
            # Invoke the function
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                LogType='Tail' if invocation_type == 'RequestResponse' else 'None',  # Get logs in the response if synchronous
                Payload=payload_json
            )
            
            # Process the response
            result = {
                'StatusCode': response.get('StatusCode'),
                'ExecutedVersion': response.get('ExecutedVersion')
            }
            
            # If there's a payload in the response, decode it
            if 'Payload' in response:
                payload_bytes = response['Payload'].read()
                if payload_bytes:
                    try:
                        result['Response'] = json.loads(payload_bytes.decode('utf-8'))
                    except:
                        result['Response'] = payload_bytes.decode('utf-8')
            
            # Check for function error
            if response.get('FunctionError'):
                result['FunctionError'] = response.get('FunctionError')
            
            # Get logs from the response if available (for synchronous invocations)
            if 'LogResult' in response:
                try:
                    log_result = base64.b64decode(response['LogResult']).decode('utf-8')
                    result['LogResult'] = log_result
                except Exception as e:
                    logger.error(f"Failed to decode log result: {str(e)}")
            
            # Fetch additional logs from CloudWatch if requested
            if fetch_logs and invocation_type == 'RequestResponse':
                # Wait a moment for logs to be available in CloudWatch
                import time
                time.sleep(2)
                
                # End time for log fetching
                end_time = datetime.datetime.now() + datetime.timedelta(seconds=5)  # 5 seconds buffer
                
                # Get the function's log group name
                log_group_name = f"/aws/lambda/{function_name}"
                
                # Create CloudWatch Logs client
                try:
                    cloudwatch_logs = boto3.client('logs', region_name=self.region)
                    
                    # Get log streams for the function, sorted by last event time
                    log_streams = cloudwatch_logs.describe_log_streams(
                        logGroupName=log_group_name,
                        orderBy='LastEventTime',
                        descending=True,
                        limit=5
                    )
                    
                    # Fetch logs from the most recent log streams
                    all_logs = []
                    for stream in log_streams.get('logStreams', [])[:3]:  # Check the 3 most recent streams
                        stream_name = stream.get('logStreamName')
                        try:
                            logs = cloudwatch_logs.get_log_events(
                                logGroupName=log_group_name,
                                logStreamName=stream_name,
                                startTime=int(start_time.timestamp() * 1000),
                                endTime=int(end_time.timestamp() * 1000),
                                limit=100
                            )
                            
                            # Add logs to the result
                            for event in logs.get('events', []):
                                all_logs.append({
                                    'timestamp': event.get('timestamp'),
                                    'message': event.get('message')
                                })
                        except Exception as e:
                            logger.error(f"Failed to fetch logs from stream {stream_name}: {str(e)}")
                    
                    # Sort logs by timestamp
                    all_logs.sort(key=lambda x: x.get('timestamp', 0))
                    
                    # Add logs to the result
                    if all_logs:
                        result['CloudWatchLogs'] = all_logs
                except Exception as e:
                    logger.error(f"Failed to fetch CloudWatch logs: {str(e)}")
            
            logger.info(f"Invoked function {function_name} with status code {result.get('StatusCode')}")
            return result
        except Exception as e:
            logger.error(f"Failed to invoke function {function_name}: {str(e)}")
            return {'error': str(e)}
    
    def update_function_configuration(self, 
                                     function_name: str, 
                                     memory_size: int = None, 
                                     timeout: int = None,
                                     environment_variables: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Update a Lambda function's configuration.
        
        Args:
            function_name (str): Name or ARN of the Lambda function
            memory_size (int, optional): Memory size in MB. Defaults to None.
            timeout (int, optional): Timeout in seconds. Defaults to None.
            environment_variables (Dict[str, str], optional): Environment variables. Defaults to None.
            
        Returns:
            Dict[str, Any]: Updated function configuration
        """
        if not self.lambda_client:
            logger.error("Lambda client not initialized")
            return {'error': 'Lambda client not initialized'}
        
        try:
            # Build update parameters
            update_params = {'FunctionName': function_name}
            
            if memory_size is not None:
                update_params['MemorySize'] = memory_size
            
            if timeout is not None:
                update_params['Timeout'] = timeout
            
            if environment_variables is not None:
                update_params['Environment'] = {'Variables': environment_variables}
            
            # Update function configuration
            response = self.lambda_client.update_function_configuration(**update_params)
            logger.info(f"Updated configuration for function {function_name}")
            return response
        except Exception as e:
            logger.error(f"Failed to update function {function_name}: {str(e)}")
            return {'error': str(e)}
    
    def get_function_metrics(self, function_name: str) -> Dict[str, Any]:
        """
        Get CloudWatch metrics for a Lambda function.
        
        Args:
            function_name (str): Name or ARN of the Lambda function
            
        Returns:
            Dict[str, Any]: Function metrics
        """
        if not self.lambda_client:
            logger.error("Lambda client not initialized")
            return {}
        
        try:
            # Create CloudWatch client
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            
            # Get invocation metrics
            invocation_metrics = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=datetime.datetime.utcnow() - datetime.timedelta(days=1),
                EndTime=datetime.datetime.utcnow(),
                Period=3600,
                Statistics=['Sum']
            )
            
            # Get error metrics
            error_metrics = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=datetime.datetime.utcnow() - datetime.timedelta(days=1),
                EndTime=datetime.datetime.utcnow(),
                Period=3600,
                Statistics=['Sum']
            )
            
            # Get duration metrics
            duration_metrics = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=datetime.datetime.utcnow() - datetime.timedelta(days=1),
                EndTime=datetime.datetime.utcnow(),
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            metrics = {
                'invocations': invocation_metrics.get('Datapoints', []),
                'errors': error_metrics.get('Datapoints', []),
                'duration': duration_metrics.get('Datapoints', [])
            }
            
            logger.info(f"Retrieved metrics for function {function_name}")
            return metrics
        except Exception as e:
            logger.error(f"Failed to get metrics for function {function_name}: {str(e)}")
            return {}
    
    def get_function_policy(self, function_name: str) -> Dict[str, Any]:
        """
        Get the resource-based policy for a Lambda function.
        
        Args:
            function_name (str): Name or ARN of the Lambda function
            
        Returns:
            Dict[str, Any]: Function policy
        """
        if not self.lambda_client:
            logger.error("Lambda client not initialized")
            return {}
        
        try:
            response = self.lambda_client.get_policy(FunctionName=function_name)
            if 'Policy' in response:
                policy = json.loads(response['Policy'])
                logger.info(f"Retrieved policy for function {function_name}")
                return policy
            return {}
        except Exception as e:
            logger.error(f"Failed to get policy for function {function_name}: {str(e)}")
            return {}
    
    def get_function_role_policy(self, function_name: str) -> Dict[str, Any]:
        """
        Get the execution role policy for a Lambda function.
        
        Args:
            function_name (str): Name or ARN of the Lambda function
            
        Returns:
            Dict[str, Any]: Role policies
        """
        if not self.lambda_client or not self.iam_client:
            logger.error("Lambda or IAM client not initialized")
            return {}
        
        try:
            # Get function configuration to find the role
            function_config = self.lambda_client.get_function_configuration(FunctionName=function_name)
            role_arn = function_config.get('Role', '')
            
            # Extract role name from ARN
            role_name = role_arn.split('/')[-1]
            
            # Get attached policies
            attached_policies = self.iam_client.list_attached_role_policies(RoleName=role_name)
            
            # Get inline policies
            inline_policies = self.iam_client.list_role_policies(RoleName=role_name)
            
            policies = {
                'attached_policies': attached_policies.get('AttachedPolicies', []),
                'inline_policies': inline_policies.get('PolicyNames', [])
            }
            
            logger.info(f"Retrieved role policies for function {function_name}")
            return policies
        except Exception as e:
            logger.error(f"Failed to get role policies for function {function_name}: {str(e)}")
            return {}
