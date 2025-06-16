"""
Tests for the UI components.
"""

import pytest
import pandas as pd
import datetime
import streamlit as st
from unittest.mock import patch, MagicMock

# Import components
from components.sidebar import render_sidebar
from components.metrics_dashboard import render_metrics_dashboard, render_performance_recommendations
from components.timeline_chart import render_timeline_chart, render_invocation_patterns
from components.memory_chart import render_memory_chart
from components.error_analysis import render_error_analysis, render_error_correlation
from components.log_explorer import render_log_explorer


# Mock streamlit
class MockDelta:
    def __init__(self, color="normal"):
        self.color = color


@pytest.fixture
def mock_streamlit():
    """Fixture to mock streamlit functions."""
    with patch('streamlit.sidebar') as mock_sidebar:
        with patch('streamlit.title') as mock_title:
            with patch('streamlit.header') as mock_header:
                with patch('streamlit.subheader') as mock_subheader:
                    with patch('streamlit.markdown') as mock_markdown:
                        with patch('streamlit.caption') as mock_caption:
                            with patch('streamlit.text') as mock_text:
                                with patch('streamlit.info') as mock_info:
                                    with patch('streamlit.success') as mock_success:
                                        with patch('streamlit.warning') as mock_warning:
                                            with patch('streamlit.error') as mock_error:
                                                with patch('streamlit.metric') as mock_metric:
                                                    with patch('streamlit.dataframe') as mock_dataframe:
                                                        with patch('streamlit.plotly_chart') as mock_plotly_chart:
                                                            with patch('streamlit.columns') as mock_columns:
                                                                with patch('streamlit.expander') as mock_expander:
                                                                    with patch('streamlit.selectbox') as mock_selectbox:
                                                                        with patch('streamlit.radio') as mock_radio:
                                                                            with patch('streamlit.slider') as mock_slider:
                                                                                with patch('streamlit.text_input') as mock_text_input:
                                                                                    with patch('streamlit.date_input') as mock_date_input:
                                                                                        with patch('streamlit.time_input') as mock_time_input:
                                                                                            with patch('streamlit.button') as mock_button:
                                                                                                with patch('streamlit.progress') as mock_progress:
                                                                                                    with patch('streamlit.spinner') as mock_spinner:
                                                                                                        with patch('streamlit.empty') as mock_empty:
                                                                                                            with patch('streamlit.tabs') as mock_tabs:
                                                                                                                yield {
                                                                                                                    'sidebar': mock_sidebar,
                                                                                                                    'title': mock_title,
                                                                                                                    'header': mock_header,
                                                                                                                    'subheader': mock_subheader,
                                                                                                                    'markdown': mock_markdown,
                                                                                                                    'caption': mock_caption,
                                                                                                                    'text': mock_text,
                                                                                                                    'info': mock_info,
                                                                                                                    'success': mock_success,
                                                                                                                    'warning': mock_warning,
                                                                                                                    'error': mock_error,
                                                                                                                    'metric': mock_metric,
                                                                                                                    'dataframe': mock_dataframe,
                                                                                                                    'plotly_chart': mock_plotly_chart,
                                                                                                                    'columns': mock_columns,
                                                                                                                    'expander': mock_expander,
                                                                                                                    'selectbox': mock_selectbox,
                                                                                                                    'radio': mock_radio,
                                                                                                                    'slider': mock_slider,
                                                                                                                    'text_input': mock_text_input,
                                                                                                                    'date_input': mock_date_input,
                                                                                                                    'time_input': mock_time_input,
                                                                                                                    'button': mock_button,
                                                                                                                    'progress': mock_progress,
                                                                                                                    'spinner': mock_spinner,
                                                                                                                    'empty': mock_empty,
                                                                                                                    'tabs': mock_tabs
                                                                                                                }


@pytest.fixture
def sample_metrics():
    """Fixture providing sample metrics data."""
    return {
        'total_invocations': 100,
        'success_rate': 0.95,
        'error_rate': 0.05,
        'avg_duration_ms': 120.5,
        'p95_duration_ms': 250.3,
        'max_duration_ms': 500.1,
        'avg_memory_used_mb': 75.2,
        'max_memory_used_mb': 120.8,
        'memory_utilization': 0.6,
        'cold_start_count': 10,
        'cold_start_rate': 0.1,
        'time_series': pd.DataFrame({
            'datetime': [datetime.datetime.now() - datetime.timedelta(minutes=i*5) for i in range(10)],
            'invocations': [10, 12, 8, 15, 20, 18, 14, 10, 9, 11],
            'avg_duration_ms': [110, 115, 125, 130, 140, 120, 110, 105, 115, 125],
            'errors': [0, 1, 0, 2, 0, 1, 0, 0, 1, 0],
            'success_rate': [1.0, 0.92, 1.0, 0.87, 1.0, 0.94, 1.0, 1.0, 0.89, 1.0]
        }),
        'error_analysis': {
            'error_count': 5,
            'error_rate': 0.05,
            'error_types': [
                {'type': 'TypeError', 'count': 2},
                {'type': 'ValueError', 'count': 1},
                {'type': 'KeyError', 'count': 1},
                {'type': 'AccessDeniedException', 'count': 1}
            ],
            'top_errors': [
                {'message': 'TypeError: Cannot read property \'id\' of undefined', 'count': 2, 'percentage': 0.4},
                {'message': 'ValueError: Invalid parameter value', 'count': 1, 'percentage': 0.2},
                {'message': 'KeyError: \'user_id\'', 'count': 1, 'percentage': 0.2},
                {'message': 'AccessDeniedException: User is not authorized', 'count': 1, 'percentage': 0.2}
            ]
        },
        'memory_analysis': {
            'avg_memory_used_mb': 75.2,
            'max_memory_used_mb': 120.8,
            'p95_memory_used_mb': 110.5,
            'memory_utilization': 0.6,
            'recommendation': {
                'action': 'decrease',
                'current_size': 128,
                'recommended_size': 128,
                'savings_percentage': 0.0
            },
            'potential_savings': 0.0
        },
        'cold_start_analysis': {
            'cold_start_count': 10,
            'cold_start_rate': 0.1,
            'avg_cold_start_duration': 180.5,
            'avg_warm_start_duration': 110.2,
            'cold_start_impact': 0.64
        },
        'invocation_patterns': {
            'hourly_pattern': [
                {'hour': 0, 'invocations': 5},
                {'hour': 1, 'invocations': 3},
                {'hour': 2, 'invocations': 2},
                {'hour': 3, 'invocations': 4},
                {'hour': 4, 'invocations': 6}
            ],
            'daily_pattern': [
                {'day_of_week': 0, 'invocations': 15, 'day_name': 'Monday'},
                {'day_of_week': 1, 'invocations': 20, 'day_name': 'Tuesday'},
                {'day_of_week': 2, 'invocations': 18, 'day_name': 'Wednesday'},
                {'day_of_week': 3, 'invocations': 22, 'day_name': 'Thursday'},
                {'day_of_week': 4, 'invocations': 25, 'day_name': 'Friday'}
            ],
            'peak_hour': 4,
            'peak_day': 'Friday'
        }
    }


@pytest.fixture
def sample_log_data():
    """Fixture providing sample log data."""
    return pd.DataFrame({
        'timestamp': [1623456789000 + i*1000 for i in range(10)],
        'datetime': [datetime.datetime.now() - datetime.timedelta(minutes=i*5) for i in range(10)],
        'message': [f'Log message {i}' for i in range(10)],
        'log_stream': ['test-stream' for _ in range(10)],
        'event_id': [f'event-{i}' for i in range(10)],
        'request_id': [f'req-{i//2}' for i in range(10)],
        'duration_ms': [100 + i*10 for i in range(10)],
        'billed_duration_ms': [100 + i*10 for i in range(10)],
        'memory_size_mb': [128 for _ in range(10)],
        'memory_used_mb': [70 + i*5 for i in range(10)],
        'cold_start': [i % 5 == 0 for i in range(10)],
        'error': [i % 5 == 1 for i in range(10)],
        'error_message': [f'Error message {i}' if i % 5 == 1 else None for i in range(10)],
        'version': ['$LATEST' for _ in range(10)]
    })


def test_render_sidebar(mock_streamlit):
    """Test rendering the sidebar."""
    # Mock the AWS client
    mock_client = MagicMock()
    mock_client.get_available_regions.return_value = ['us-east-1', 'us-east-2']
    mock_client.is_authenticated.return_value = True
    mock_client.get_log_groups.return_value = [
        {'logGroupName': '/aws/lambda/test-function-1'},
        {'logGroupName': '/aws/lambda/test-function-2'}
    ]
    
    # Mock the get_aws_profiles function
    with patch('components.sidebar.get_aws_profiles', return_value=['default', 'test-profile']):
        # Mock streamlit components
        mock_streamlit['radio'].return_value = 'AWS'
        mock_streamlit['selectbox'].side_effect = [
            'Last 24 hours',  # time range
            'us-east-1',      # region
            'default',        # profile
            '/aws/lambda/test-function-1'  # log group
        ]
        mock_streamlit['text_input'].return_value = 'ERROR'  # filter pattern
        mock_streamlit['button'].return_value = True  # fetch button
        
        # Render the sidebar
        filters = render_sidebar(mock_client)
        
        # Check that the sidebar was rendered
        mock_streamlit['sidebar'].assert_called()
        
        # Check that the filters were returned correctly
        assert filters['mode'] == 'AWS'
        assert filters['time_range'] == '24h'
        assert filters['region'] == 'us-east-1'
        assert filters['profile'] is None  # 'default' becomes None
        assert filters['log_group'] == '/aws/lambda/test-function-1'
        assert filters['filter_pattern'] == 'ERROR'
        assert filters['fetch_clicked'] == True


def test_render_metrics_dashboard(mock_streamlit, sample_metrics):
    """Test rendering the metrics dashboard."""
    # Render the metrics dashboard
    render_metrics_dashboard(sample_metrics)
    
    # Check that the subheader was rendered
    mock_streamlit['subheader'].assert_called_with("Performance Overview")
    
    # Check that metrics were rendered
    assert mock_streamlit['metric'].call_count > 0


def test_render_metrics_dashboard_empty(mock_streamlit):
    """Test rendering the metrics dashboard with empty data."""
    # Render the metrics dashboard with empty data
    render_metrics_dashboard({})
    
    # Check that the info message was rendered
    mock_streamlit['info'].assert_called_with("No metrics available. Please fetch log data first.")


def test_render_performance_recommendations(mock_streamlit, sample_metrics):
    """Test rendering performance recommendations."""
    # Render performance recommendations
    render_performance_recommendations(sample_metrics)
    
    # Check that the subheader was rendered
    mock_streamlit['subheader'].assert_called_with("Performance Recommendations")


def test_render_timeline_chart(mock_streamlit, sample_metrics):
    """Test rendering the timeline chart."""
    # Render the timeline chart
    render_timeline_chart(sample_metrics['time_series'])
    
    # Check that the subheader was rendered
    mock_streamlit['subheader'].assert_called_with("Invocation Timeline")
    
    # Check that the plotly chart was rendered
    assert mock_streamlit['plotly_chart'].call_count > 0


def test_render_timeline_chart_empty(mock_streamlit):
    """Test rendering the timeline chart with empty data."""
    # Render the timeline chart with empty data
    render_timeline_chart(pd.DataFrame())
    
    # Check that the info message was rendered
    mock_streamlit['info'].assert_called_with("No time-series data available. Please fetch log data first.")


def test_render_invocation_patterns(mock_streamlit, sample_metrics):
    """Test rendering invocation patterns."""
    # Render invocation patterns
    render_invocation_patterns(sample_metrics['invocation_patterns'])
    
    # Check that the subheader was rendered
    mock_streamlit['subheader'].assert_called_with("Invocation Patterns")
    
    # Check that plotly charts were rendered
    assert mock_streamlit['plotly_chart'].call_count > 0


def test_render_memory_chart(mock_streamlit, sample_log_data, sample_metrics):
    """Test rendering the memory chart."""
    # Render the memory chart
    render_memory_chart(sample_log_data, sample_metrics['memory_analysis'])
    
    # Check that the subheader was rendered
    mock_streamlit['subheader'].assert_called_with("Memory Usage Analysis")
    
    # Check that the plotly chart was rendered
    assert mock_streamlit['plotly_chart'].call_count > 0


def test_render_memory_chart_empty(mock_streamlit):
    """Test rendering the memory chart with empty data."""
    # Render the memory chart with empty data
    render_memory_chart(pd.DataFrame(), {})
    
    # Check that the info message was rendered
    mock_streamlit['info'].assert_called_with("No memory usage data available.")


def test_render_error_analysis(mock_streamlit, sample_log_data, sample_metrics):
    """Test rendering error analysis."""
    # Render error analysis
    render_error_analysis(sample_metrics['error_analysis'], sample_log_data)
    
    # Check that the subheader was rendered
    mock_streamlit['subheader'].assert_called_with("Error Analysis")
    
    # Check that the plotly chart was rendered
    assert mock_streamlit['plotly_chart'].call_count > 0


def test_render_error_analysis_empty(mock_streamlit):
    """Test rendering error analysis with empty data."""
    # Render error analysis with empty data
    render_error_analysis({}, pd.DataFrame())
    
    # Check that the info message was rendered
    mock_streamlit['info'].assert_called_with("No error analysis data available.")


def test_render_error_analysis_no_errors(mock_streamlit):
    """Test rendering error analysis with no errors."""
    # Render error analysis with no errors
    render_error_analysis({'error_count': 0, 'error_rate': 0}, pd.DataFrame())
    
    # Check that the success message was rendered
    mock_streamlit['success'].assert_called_with("No errors detected in the analyzed logs.")


def test_render_error_correlation(mock_streamlit, sample_log_data):
    """Test rendering error correlation."""
    # Render error correlation
    render_error_correlation(sample_log_data)
    
    # Check that the subheader was rendered
    mock_streamlit['subheader'].assert_called_with("Error Correlation Analysis")
    
    # Check that plotly charts were rendered
    assert mock_streamlit['plotly_chart'].call_count > 0


def test_render_log_explorer(mock_streamlit, sample_log_data):
    """Test rendering the log explorer."""
    # Mock streamlit components
    mock_streamlit['selectbox'].side_effect = [
        'All',           # status filter
        'Newest First',  # sort by
        'req-0'          # selected request ID
    ]
    mock_streamlit['text_input'].side_effect = [
        '',  # request ID filter
        ''   # text filter
    ]
    
    # Render the log explorer
    render_log_explorer(sample_log_data)
    
    # Check that the subheader was rendered
    mock_streamlit['subheader'].assert_called_with("Log Explorer")
    
    # Check that the dataframe was rendered
    assert mock_streamlit['dataframe'].call_count > 0


def test_render_log_explorer_empty(mock_streamlit):
    """Test rendering the log explorer with empty data."""
    # Render the log explorer with empty data
    render_log_explorer(pd.DataFrame())
    
    # Check that the info message was rendered
    mock_streamlit['info'].assert_called_with("No log data available. Please fetch log data first.")
