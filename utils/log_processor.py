"""
Log Processor Module for CloudWatch Logs Analyzer

This module provides functionality to process and analyze CloudWatch log data.
"""

import json
import re
import pandas as pd
import numpy as np
import random
from typing import List, Dict, Any, Optional, Tuple
import datetime

class LogProcessor:
    """Process and analyze CloudWatch log data."""
    
    def __init__(self):
        """Initialize the log processor."""
        # Lambda report line regex pattern
        self.report_pattern = re.compile(
            r'REPORT RequestId: ([0-9a-f-]+)\s+'
            r'Duration: ([\d.]+) ms\s+'
            r'Billed Duration: ([\d.]+) ms\s+'
            r'Memory Size: ([\d.]+) MB\s+'
            r'Max Memory Used: ([\d.]+) MB'
        )
        
        # Error pattern
        self.error_pattern = re.compile(r'ERROR|Error|error|Exception|exception|EXCEPTION|Failed|FAILED|failed')
    
    def process_log_events(self, log_events: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Process log events from CloudWatch and extract relevant information.
        
        Args:
            log_events (List[Dict[str, Any]]): List of CloudWatch log events
            
        Returns:
            pd.DataFrame: DataFrame containing processed log data
        """
        if not log_events:
            return pd.DataFrame()
        
        # Extract Lambda metrics
        lambda_metrics_df = self.extract_lambda_metrics(log_events)
        
        # Extract errors
        errors_df = self.extract_errors(log_events)
        
        # Try to parse JSON logs
        json_logs_df = self.parse_json_logs(log_events)
        
        # Create a base DataFrame with all events
        all_events = []
        for event in log_events:
            timestamp = event.get('timestamp', 0)
            event_time = datetime.datetime.fromtimestamp(timestamp / 1000)
            
            event_data = {
                'timestamp': event_time,
                'message': event.get('message', ''),
                'log_group_name': event.get('logGroupName', ''),
                'log_stream_name': event.get('logStreamName', ''),
                'event_id': event.get('eventId', ''),
                'ingestion_time': datetime.datetime.fromtimestamp(event.get('ingestionTime', 0) / 1000) if event.get('ingestionTime') else None
            }
            all_events.append(event_data)
        
        # Create the base DataFrame
        base_df = pd.DataFrame(all_events)
        
        # If we have Lambda metrics, merge them with the base DataFrame
        if not lambda_metrics_df.empty:
            # Use request_id to match with message content
            base_df['is_lambda_report'] = base_df['message'].str.contains('REPORT RequestId:', regex=False)
            
            # Extract request IDs from messages for matching
            def extract_request_id(message):
                if 'RequestId:' in message:
                    parts = message.split('RequestId:')
                    if len(parts) > 1:
                        request_id = parts[1].strip().split(' ')[0]
                        return request_id
                return None
            
            base_df['request_id'] = base_df['message'].apply(extract_request_id)
            
            # Merge Lambda metrics
            if 'request_id' in lambda_metrics_df.columns:
                metrics_columns = ['duration', 'billed_duration', 'memory_size', 'memory_used', 'memory_utilization']
                for col in metrics_columns:
                    if col in lambda_metrics_df.columns:
                        base_df = base_df.merge(
                            lambda_metrics_df[['request_id', col]], 
                            on='request_id', 
                            how='left'
                        )
        
        # Add error flag
        base_df['is_error'] = base_df['message'].apply(lambda x: bool(self.error_pattern.search(x)))
        
        return base_df
    
    def generate_demo_data(self, 
                          num_entries: int, 
                          start_time: datetime.datetime,
                          end_time: datetime.datetime,
                          error_rate: float = 0.05,
                          cold_start_rate: float = 0.1,
                          memory_size: int = 1024) -> pd.DataFrame:
        """
        Generate demo log data for demonstration purposes.
        
        Args:
            num_entries (int): Number of log entries to generate
            start_time (datetime.datetime): Start time for generated logs
            end_time (datetime.datetime): End time for generated logs
            error_rate (float, optional): Percentage of entries that should be errors (0-1). Defaults to 0.05.
            cold_start_rate (float, optional): Percentage of entries that should be cold starts (0-1). Defaults to 0.1.
            memory_size (int, optional): Memory size in MB. Defaults to 1024.
            
        Returns:
            pd.DataFrame: DataFrame containing generated log data
        """
        # Calculate time range in seconds
        time_range = (end_time - start_time).total_seconds()
        
        # Generate random timestamps within the range
        timestamps = [start_time + datetime.timedelta(seconds=random.random() * time_range) for _ in range(num_entries)]
        timestamps.sort()
        
        # Generate request IDs
        request_ids = [f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}" for _ in range(num_entries)]
        
        # Generate durations (normal distribution around 200ms with some outliers)
        durations = np.random.normal(200, 100, num_entries)
        durations = np.clip(durations, 10, 10000)  # Clip to reasonable range
        
        # Add some cold starts (longer durations)
        cold_start_indices = random.sample(range(num_entries), int(num_entries * cold_start_rate))
        for idx in cold_start_indices:
            durations[idx] += random.uniform(500, 2000)
        
        # Generate memory usage (normal distribution around 60% of memory_size)
        memory_used = np.random.normal(memory_size * 0.6, memory_size * 0.2, num_entries)
        memory_used = np.clip(memory_used, memory_size * 0.1, memory_size * 0.95)  # Clip to reasonable range
        
        # Generate log messages
        messages = []
        is_error = []
        
        for i in range(num_entries):
            if random.random() < error_rate:
                error_type = random.choice(["RuntimeError", "ValueError", "KeyError", "TypeError", "IndexError"])
                messages.append(f"ERROR: {error_type}: Something went wrong in function xyz at line 123")
                is_error.append(True)
            else:
                messages.append(f"INFO: Function executed successfully in {durations[i]:.2f}ms")
                is_error.append(False)
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'request_id': request_ids,
            'message': messages,
            'duration': durations,
            'billed_duration': durations + 1,  # Billed duration is slightly higher
            'memory_size': memory_size,
            'memory_used': memory_used,
            'memory_utilization': (memory_used / memory_size) * 100,
            'is_error': is_error,
            'log_group_name': '/aws/lambda/demo-function',
            'log_stream_name': '2023/06/23/[$LATEST]abcdef123456'
        })
        
        return df
    
    def extract_lambda_metrics(self, log_events: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Extract Lambda performance metrics from log events.
        
        Args:
            log_events (List[Dict[str, Any]]): List of CloudWatch log events
            
        Returns:
            pd.DataFrame: DataFrame containing Lambda performance metrics
        """
        metrics = []
        
        for event in log_events:
            message = event.get('message', '')
            timestamp = event.get('timestamp', 0)
            
            # Convert timestamp from milliseconds to datetime
            event_time = datetime.datetime.fromtimestamp(timestamp / 1000)
            
            # Check if this is a Lambda report line
            match = self.report_pattern.search(message)
            if match:
                request_id, duration, billed_duration, memory_size, memory_used = match.groups()
                
                metrics.append({
                    'timestamp': event_time,
                    'request_id': request_id,
                    'duration': float(duration),
                    'billed_duration': float(billed_duration),
                    'memory_size': float(memory_size),
                    'memory_used': float(memory_used),
                    'memory_utilization': (float(memory_used) / float(memory_size)) * 100
                })
        
        if metrics:
            return pd.DataFrame(metrics)
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'timestamp', 'request_id', 'duration', 'billed_duration',
                'memory_size', 'memory_used', 'memory_utilization'
            ])
    
    def extract_errors(self, log_events: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Extract error messages from log events.
        
        Args:
            log_events (List[Dict[str, Any]]): List of CloudWatch log events
            
        Returns:
            pd.DataFrame: DataFrame containing error information
        """
        errors = []
        
        for event in log_events:
            message = event.get('message', '')
            timestamp = event.get('timestamp', 0)
            
            # Convert timestamp from milliseconds to datetime
            event_time = datetime.datetime.fromtimestamp(timestamp / 1000)
            
            # Check if message contains error indicators
            if self.error_pattern.search(message):
                errors.append({
                    'timestamp': event_time,
                    'message': message.strip(),
                    'log_stream_name': event.get('logStreamName', '')
                })
        
        if errors:
            return pd.DataFrame(errors)
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['timestamp', 'message', 'log_stream_name'])
    
    def parse_json_logs(self, log_events: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Parse JSON formatted log messages into a structured DataFrame.
        
        Args:
            log_events (List[Dict[str, Any]]): List of CloudWatch log events
            
        Returns:
            pd.DataFrame: DataFrame containing parsed JSON log data
        """
        parsed_logs = []
        
        for event in log_events:
            message = event.get('message', '')
            timestamp = event.get('timestamp', 0)
            
            # Convert timestamp from milliseconds to datetime
            event_time = datetime.datetime.fromtimestamp(timestamp / 1000)
            
            try:
                # Try to parse the message as JSON
                log_data = json.loads(message)
                
                # Add timestamp and flatten the JSON structure
                if isinstance(log_data, dict):
                    log_data['timestamp'] = event_time
                    parsed_logs.append(log_data)
            except json.JSONDecodeError:
                # Skip non-JSON messages
                continue
        
        if parsed_logs:
            return pd.DataFrame(parsed_logs)
        else:
            # Return empty DataFrame
            return pd.DataFrame()
