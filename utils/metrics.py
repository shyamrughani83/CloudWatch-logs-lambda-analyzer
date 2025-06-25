"""
Metrics Calculator Module for CloudWatch Logs Analyzer

This module provides functionality to calculate metrics from CloudWatch log data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import datetime

class MetricsCalculator:
    """Calculate metrics from CloudWatch log data."""
    
    @staticmethod
    def calculate_lambda_performance_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate performance metrics for Lambda functions.
        
        Args:
            df (pd.DataFrame): DataFrame containing Lambda metrics
            
        Returns:
            Dict[str, Any]: Dictionary of calculated metrics
        """
        if df.empty or 'duration' not in df.columns:
            return {
                'count': 0,
                'avg_duration': 0,
                'p95_duration': 0,
                'max_duration': 0,
                'avg_memory_utilization': 0,
                'max_memory_utilization': 0,
                'cold_starts': 0
            }
        
        metrics = {
            'count': len(df),
            'avg_duration': df['duration'].mean() if 'duration' in df.columns else 0,
            'p95_duration': df['duration'].quantile(0.95) if 'duration' in df.columns else 0,
            'max_duration': df['duration'].max() if 'duration' in df.columns else 0,
            'avg_memory_utilization': df['memory_utilization'].mean() if 'memory_utilization' in df.columns else 0,
            'max_memory_utilization': df['memory_utilization'].max() if 'memory_utilization' in df.columns else 0,
            # Estimate cold starts (duration > 2x average might indicate cold start)
            'cold_starts': len(df[df['duration'] > 2 * df['duration'].mean()]) if 'duration' in df.columns else 0
        }
        
        return metrics
    
    @staticmethod
    def calculate_memory_optimization(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate memory optimization recommendations.
        
        Args:
            df (pd.DataFrame): DataFrame containing Lambda metrics
            
        Returns:
            Dict[str, Any]: Dictionary with memory optimization recommendations
        """
        if df.empty or 'memory_size' not in df.columns or 'memory_used' not in df.columns:
            return {
                'current_memory': 0,
                'recommended_memory': 0,
                'potential_savings': 0,
                'utilization': 0
            }
        
        current_memory = df['memory_size'].iloc[0]  # Assuming consistent memory size
        max_memory_used = df['memory_used'].max()
        p95_memory_used = df['memory_used'].quantile(0.95)
        
        # Add 20% buffer to the 95th percentile memory usage
        recommended_memory = min(
            round(p95_memory_used * 1.2 / 64) * 64,  # Round to nearest 64MB (AWS Lambda increment)
            3008  # Maximum Lambda memory
        )
        
        # Ensure minimum of 128MB (AWS Lambda minimum)
        recommended_memory = max(recommended_memory, 128)
        
        # Calculate potential cost savings
        # Lambda pricing is proportional to memory, so savings are proportional to memory reduction
        if current_memory > recommended_memory:
            potential_savings = (current_memory - recommended_memory) / current_memory
        else:
            potential_savings = 0
        
        return {
            'current_memory': current_memory,
            'recommended_memory': recommended_memory,
            'potential_savings': potential_savings,
            'utilization': (max_memory_used / current_memory)
        }
    
    @staticmethod
    def calculate_error_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate error metrics from log data.
        
        Args:
            df (pd.DataFrame): DataFrame containing error information
            
        Returns:
            Dict[str, Any]: Dictionary with error metrics
        """
        if df.empty:
            return {
                'error_count': 0,
                'unique_errors': 0
            }
        
        # Filter for error messages if is_error column exists
        if 'is_error' in df.columns:
            error_df = df[df['is_error'] == True]
        else:
            # Assume all rows are errors if no is_error column
            error_df = df
        
        # Count total errors
        error_count = len(error_df)
        
        # Count unique error messages (simplified by just counting unique messages)
        unique_errors = error_df['message'].nunique() if 'message' in error_df.columns else 0
        
        return {
            'error_count': error_count,
            'unique_errors': unique_errors
        }
    
    @staticmethod
    def calculate_time_series_metrics(df: pd.DataFrame, 
                                     time_column: str = 'timestamp',
                                     value_column: str = 'duration',
                                     freq: str = '1min') -> pd.DataFrame:
        """
        Calculate time series metrics by resampling data.
        
        Args:
            df (pd.DataFrame): DataFrame containing time series data
            time_column (str): Column name for timestamp
            value_column (str): Column name for value to aggregate
            freq (str): Frequency for resampling (e.g., '1min', '5min', '1h')
            
        Returns:
            pd.DataFrame: Resampled time series data
        """
        if df.empty or time_column not in df.columns or value_column not in df.columns:
            return pd.DataFrame(columns=['timestamp', 'mean', 'count', 'max'])
        
        # Ensure timestamp column is datetime type
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
            df[time_column] = pd.to_datetime(df[time_column])
        
        # Set timestamp as index for resampling
        df.set_index(time_column, inplace=True)
        
        # Resample and calculate metrics
        resampled = df[value_column].resample(freq).agg(['mean', 'count', 'max'])
        
        # Reset index to make timestamp a column again
        resampled.reset_index(inplace=True)
        
        return resampled
    
    @staticmethod
    def calculate_basic_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate basic metrics from log data.
        
        Args:
            df (pd.DataFrame): DataFrame containing log data
            
        Returns:
            Dict[str, Any]: Dictionary with basic metrics
        """
        if df.empty:
            return {
                'total_logs': 0,
                'time_range': {
                    'start': None,
                    'end': None,
                    'duration_hours': 0
                },
                'log_groups': [],
                'error_rate': 0
            }
        
        # Calculate time range
        if 'timestamp' in df.columns:
            start_time = df['timestamp'].min()
            end_time = df['timestamp'].max()
            duration_seconds = (end_time - start_time).total_seconds()
            duration_hours = duration_seconds / 3600
        else:
            start_time = None
            end_time = None
            duration_hours = 0
        
        # Count log groups
        log_groups = df['log_group_name'].unique().tolist() if 'log_group_name' in df.columns else []
        
        # Calculate error rate
        if 'is_error' in df.columns:
            error_count = df['is_error'].sum()
            error_rate = error_count / len(df) if len(df) > 0 else 0
        else:
            error_rate = 0
        
        return {
            'total_logs': len(df),
            'time_range': {
                'start': start_time,
                'end': end_time,
                'duration_hours': duration_hours
            },
            'log_groups': log_groups,
            'error_rate': error_rate
        }
    
    @staticmethod
    def analyze_errors(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze errors in log data.
        
        Args:
            df (pd.DataFrame): DataFrame containing log data
            
        Returns:
            Dict[str, Any]: Dictionary with error analysis
        """
        if df.empty:
            return {
                'error_count': 0,
                'error_rate': 0,
                'top_errors': [],
                'error_trend': []
            }
        
        # Filter for error messages if is_error column exists
        if 'is_error' in df.columns:
            error_df = df[df['is_error'] == True]
        else:
            # Assume no errors if no is_error column
            return {
                'error_count': 0,
                'error_rate': 0,
                'top_errors': [],
                'error_trend': []
            }
        
        # Count total errors
        error_count = len(error_df)
        error_rate = error_count / len(df) if len(df) > 0 else 0
        
        # Get top errors
        if 'message' in error_df.columns:
            top_errors = error_df['message'].value_counts().head(5).reset_index()
            top_errors.columns = ['message', 'count']
            top_errors = top_errors.to_dict('records')
        else:
            top_errors = []
        
        # Calculate error trend over time
        if 'timestamp' in error_df.columns and len(error_df) > 0:
            # Group by hour and count errors
            error_df = error_df.copy()
            error_df['hour'] = error_df['timestamp'].dt.floor('H')
            error_trend = error_df.groupby('hour').size().reset_index()
            error_trend.columns = ['timestamp', 'count']
            error_trend = error_trend.to_dict('records')
        else:
            error_trend = []
        
        return {
            'error_count': error_count,
            'error_rate': error_rate,
            'top_errors': top_errors,
            'error_trend': error_trend
        }
    
    @staticmethod
    def analyze_memory_usage(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze memory usage in log data.
        
        Args:
            df (pd.DataFrame): DataFrame containing log data
            
        Returns:
            Dict[str, Any]: Dictionary with memory usage analysis
        """
        if df.empty or 'memory_size' not in df.columns or 'memory_used' not in df.columns:
            return {
                'memory_size': 0,
                'avg_memory_used': 0,
                'max_memory_used': 0,
                'p95_memory_used': 0,
                'utilization': 0,
                'recommendation': {
                    'recommended_memory': 0,
                    'potential_savings': 0
                }
            }
        
        # Calculate memory metrics
        memory_size = df['memory_size'].iloc[0]  # Assuming consistent memory size
        avg_memory_used = df['memory_used'].mean()
        max_memory_used = df['memory_used'].max()
        p95_memory_used = df['memory_used'].quantile(0.95)
        utilization = avg_memory_used / memory_size if memory_size > 0 else 0
        
        # Calculate recommended memory
        recommended_memory = min(
            round(p95_memory_used * 1.2 / 64) * 64,  # Round to nearest 64MB (AWS Lambda increment)
            3008  # Maximum Lambda memory
        )
        
        # Ensure minimum of 128MB (AWS Lambda minimum)
        recommended_memory = max(recommended_memory, 128)
        
        # Calculate potential cost savings
        if memory_size > recommended_memory:
            potential_savings = (memory_size - recommended_memory) / memory_size
        else:
            potential_savings = 0
        
        return {
            'memory_size': memory_size,
            'avg_memory_used': avg_memory_used,
            'max_memory_used': max_memory_used,
            'p95_memory_used': p95_memory_used,
            'utilization': utilization,
            'recommendation': {
                'recommended_memory': recommended_memory,
                'potential_savings': potential_savings
            }
        }
    
    @staticmethod
    def analyze_cold_starts(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze cold starts in log data.
        
        Args:
            df (pd.DataFrame): DataFrame containing log data
            
        Returns:
            Dict[str, Any]: Dictionary with cold start analysis
        """
        if df.empty or 'duration' not in df.columns:
            return {
                'cold_start_count': 0,
                'cold_start_rate': 0,
                'avg_cold_start_duration': 0,
                'avg_warm_start_duration': 0
            }
        
        # Identify cold starts (duration > 2x average might indicate cold start)
        avg_duration = df['duration'].mean()
        cold_start_threshold = 2 * avg_duration
        
        cold_starts = df[df['duration'] > cold_start_threshold]
        warm_starts = df[df['duration'] <= cold_start_threshold]
        
        cold_start_count = len(cold_starts)
        cold_start_rate = cold_start_count / len(df) if len(df) > 0 else 0
        
        avg_cold_start_duration = cold_starts['duration'].mean() if len(cold_starts) > 0 else 0
        avg_warm_start_duration = warm_starts['duration'].mean() if len(warm_starts) > 0 else 0
        
        return {
            'cold_start_count': cold_start_count,
            'cold_start_rate': cold_start_rate,
            'avg_cold_start_duration': avg_cold_start_duration,
            'avg_warm_start_duration': avg_warm_start_duration
        }
    
    @staticmethod
    def get_invocation_patterns(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get invocation patterns from log data.
        
        Args:
            df (pd.DataFrame): DataFrame containing log data
            
        Returns:
            Dict[str, Any]: Dictionary with invocation patterns
        """
        if df.empty or 'timestamp' not in df.columns:
            return {
                'hourly_pattern': [],
                'daily_pattern': [],
                'peak_hour': None,
                'peak_day': None
            }
        
        # Calculate hourly pattern
        df = df.copy()
        df['hour'] = df['timestamp'].dt.hour
        hourly_pattern = df.groupby('hour').size().reset_index()
        hourly_pattern.columns = ['hour', 'count']
        
        # Calculate daily pattern
        df['day'] = df['timestamp'].dt.day_name()
        daily_pattern = df.groupby('day').size().reset_index()
        daily_pattern.columns = ['day', 'count']
        
        # Find peak hour and day
        peak_hour = hourly_pattern.loc[hourly_pattern['count'].idxmax()]['hour'] if len(hourly_pattern) > 0 else None
        peak_day = daily_pattern.loc[daily_pattern['count'].idxmax()]['day'] if len(daily_pattern) > 0 else None
        
        return {
            'hourly_pattern': hourly_pattern.to_dict('records'),
            'daily_pattern': daily_pattern.to_dict('records'),
            'peak_hour': peak_hour,
            'peak_day': peak_day
        }
