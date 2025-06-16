"""
Tests for the LogProcessor module.
"""

import pytest
import pandas as pd
import datetime
from typing import Dict, Any, List

from utils.log_processor import LogProcessor


def test_process_log_events_empty():
    """Test processing empty log events."""
    processor = LogProcessor()
    result = processor.process_log_events([])
    
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_process_log_events(sample_log_events):
    """Test processing sample log events."""
    processor = LogProcessor()
    result = processor.process_log_events(sample_log_events)
    
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    
    # Check that we have the expected columns
    expected_columns = [
        'timestamp', 'datetime', 'message', 'log_stream', 'event_id',
        'request_id', 'duration_ms', 'billed_duration_ms', 'memory_size_mb',
        'memory_used_mb', 'cold_start', 'error', 'error_message', 'version'
    ]
    
    for col in expected_columns:
        assert col in result.columns
    
    # Check that we have the expected number of rows with request IDs
    assert len(result[result['request_id'].notna()]) > 0
    
    # Check that durations were extracted correctly
    duration_rows = result.dropna(subset=['duration_ms'])
    assert len(duration_rows) == 3  # We have 3 REPORT lines in the sample data
    
    # Check specific values from the first REPORT line
    first_report = result[result['duration_ms'] == 123.45].iloc[0]
    assert first_report['request_id'] == '1234abcd-56ef-78gh-90ij-1234klmnopqr'
    assert first_report['billed_duration_ms'] == 124
    assert first_report['memory_size_mb'] == 128
    assert first_report['memory_used_mb'] == 75


def test_extract_request_metadata():
    """Test extracting request metadata from log messages."""
    processor = LogProcessor()
    
    # Test case for REPORT line
    log_entry = {
        'message': 'REPORT RequestId: 1234abcd-56ef-78gh-90ij-1234klmnopqr\tDuration: 123.45 ms\tBilled Duration: 124 ms\tMemory Size: 128 MB\tMax Memory Used: 75 MB',
        'request_id': None,
        'duration_ms': None,
        'billed_duration_ms': None,
        'memory_size_mb': None,
        'memory_used_mb': None,
        'cold_start': False,
        'error': False,
        'error_message': None
    }
    
    request_contexts = {}
    processor._extract_request_metadata(log_entry, request_contexts)
    
    assert log_entry['request_id'] == '1234abcd-56ef-78gh-90ij-1234klmnopqr'
    assert log_entry['duration_ms'] == 123.45
    assert log_entry['billed_duration_ms'] == 124
    assert log_entry['memory_size_mb'] == 128
    assert log_entry['memory_used_mb'] == 75
    
    # Test case for START line
    log_entry = {
        'message': 'START RequestId: 1234abcd-56ef-78gh-90ij-1234klmnopqr Version: $LATEST',
        'request_id': None,
        'duration_ms': None,
        'billed_duration_ms': None,
        'memory_size_mb': None,
        'memory_used_mb': None,
        'cold_start': False,
        'error': False,
        'error_message': None
    }
    
    request_contexts = {}
    processor._extract_request_metadata(log_entry, request_contexts)
    
    assert log_entry['request_id'] == '1234abcd-56ef-78gh-90ij-1234klmnopqr'
    assert log_entry['version'] == '$LATEST'
    assert '1234abcd-56ef-78gh-90ij-1234klmnopqr' in request_contexts
    assert request_contexts['1234abcd-56ef-78gh-90ij-1234klmnopqr']['cold_start'] == True
    
    # Test case for ERROR line
    log_entry = {
        'message': '2023-06-15T12:35:56.789Z\t1234abcd-56ef-78gh-90ij-1234klmnopqr\tERROR\tTypeError: Cannot read property \'id\' of undefined',
        'request_id': None,
        'duration_ms': None,
        'billed_duration_ms': None,
        'memory_size_mb': None,
        'memory_used_mb': None,
        'cold_start': False,
        'error': False,
        'error_message': None
    }
    
    request_contexts = {'1234abcd-56ef-78gh-90ij-1234klmnopqr': {'cold_start': True}}
    processor._extract_request_metadata(log_entry, request_contexts)
    
    assert log_entry['error'] == True
    assert log_entry['error_message'] is not None


def test_identify_cold_starts():
    """Test identifying cold starts in log data."""
    processor = LogProcessor()
    
    # Create a test DataFrame with cold start information
    data = {
        'request_id': ['req1', 'req1', 'req2', 'req2', 'req3'],
        'cold_start': [True, False, False, False, False]
    }
    df = pd.DataFrame(data)
    
    # Apply the cold start identification
    processor._identify_cold_starts(df)
    
    # Check that all entries for req1 are marked as cold starts
    assert df[df['request_id'] == 'req1']['cold_start'].all()
    
    # Check that req2 and req3 are not marked as cold starts
    assert not df[df['request_id'] == 'req2']['cold_start'].any()
    assert not df[df['request_id'] == 'req3']['cold_start'].any()


def test_generate_demo_data():
    """Test generating demo data."""
    processor = LogProcessor()
    
    # Generate demo data
    start_time = datetime.datetime.now() - datetime.timedelta(hours=24)
    end_time = datetime.datetime.now()
    result = processor.generate_demo_data(
        num_entries=100,
        start_time=start_time,
        end_time=end_time
    )
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 100
    
    # Check that we have the expected columns
    expected_columns = [
        'timestamp', 'datetime', 'request_id', 'log_stream',
        'duration_ms', 'billed_duration_ms', 'memory_size_mb',
        'memory_used_mb', 'cold_start', 'error', 'error_message', 'version'
    ]
    
    for col in expected_columns:
        assert col in result.columns
    
    # Check that timestamps are within the specified range
    min_timestamp = result['datetime'].min()
    max_timestamp = result['datetime'].max()
    
    assert min_timestamp >= start_time
    assert max_timestamp <= end_time
    
    # Check that we have some cold starts and errors
    assert result['cold_start'].sum() > 0
    assert result['error'].sum() > 0


def test_extract_json_from_logs():
    """Test extracting JSON from log messages."""
    processor = LogProcessor()
    
    # Create a test DataFrame with JSON in messages
    data = {
        'message': [
            'Log message with JSON: {"id": 123, "name": "test", "request_id": "req1"}',
            'Another message with different JSON: {"status": "error", "code": 404, "request_id": "req2"}',
            'Message with no JSON'
        ],
        'request_id': ['req1', 'req2', 'req3']
    }
    df = pd.DataFrame(data)
    
    # Extract JSON
    result = processor.extract_json_from_logs(df)
    
    # Check that the original columns are preserved
    assert 'message' in result.columns
    assert 'request_id' in result.columns
    
    # Check that JSON fields were extracted
    assert 'id' in result.columns
    assert 'name' in result.columns
    assert 'status' in result.columns
    assert 'code' in result.columns
    
    # Check specific values
    assert result[result['request_id'] == 'req1']['id'].iloc[0] == 123
    assert result[result['request_id'] == 'req1']['name'].iloc[0] == 'test'
    assert result[result['request_id'] == 'req2']['status'].iloc[0] == 'error'
    assert result[result['request_id'] == 'req2']['code'].iloc[0] == 404
