"""
CloudWatch Logs Analyzer - Main Application

A Streamlit application for analyzing AWS Lambda function logs from CloudWatch.
Provides visual analytics and insights to help developers and DevOps engineers
understand performance patterns, identify errors, and optimize resource usage.
"""

import streamlit as st
import pandas as pd
import datetime
import time
import traceback
from typing import Dict, Any, Optional, List

# Import utility modules
from utils.aws_client import CloudWatchLogsClient, get_aws_profiles
from utils.log_processor import LogProcessor
from utils.metrics import MetricsCalculator
from utils.helpers import ensure_timezone_naive, convert_for_streamlit_display, ensure_arrow_compatible, safe_display
from utils.logger import app_logger

# Import UI components
from components.sidebar import render_sidebar
from components.metrics_dashboard import render_metrics_dashboard, render_performance_recommendations
from components.timeline_chart import render_timeline_chart, render_invocation_patterns
from components.memory_chart import render_memory_chart
from components.error_analysis import render_error_analysis, render_error_correlation
from components.log_explorer import render_log_explorer


def fetch_aws_logs(aws_client: CloudWatchLogsClient, log_groups: List[str], 
                  start_time: datetime.datetime, end_time: datetime.datetime,
                  filter_pattern: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch logs from AWS CloudWatch for multiple log groups and process them.
    
    Args:
        aws_client: CloudWatchLogsClient instance
        log_groups: List of log group names to fetch logs from
        start_time: Start time for log retrieval
        end_time: End time for log retrieval
        filter_pattern: Optional CloudWatch Logs filter pattern
        
    Returns:
        DataFrame with processed log data
    """
    try:
        app_logger.info(f"Fetching logs from {len(log_groups)} log groups between {start_time} and {end_time}")
        if filter_pattern:
            app_logger.info(f"Using filter pattern: {filter_pattern}")
        
        # Convert datetime to milliseconds since epoch
        start_time_ms = int(start_time.timestamp() * 1000)
        end_time_ms = int(end_time.timestamp() * 1000)
        
        all_log_events = []
        total_processed = 0
        
        # Create a progress bar for multiple log groups
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Process each log group
        for i, log_group in enumerate(log_groups):
            status_text.text(f"Fetching logs from {log_group} ({i+1}/{len(log_groups)})...")
            progress_bar.progress((i) / len(log_groups))
            
            # Fetch log events for this log group
            log_events, group_processed = aws_client.get_log_events(
                log_group_name=log_group,
                start_time=start_time_ms,
                end_time=end_time_ms,
                filter_pattern=filter_pattern
            )
            
            # Add log group name to each event
            for event in log_events:
                event['logGroupName'] = log_group
            
            all_log_events.extend(log_events)
            total_processed += group_processed
            
            app_logger.info(f"Fetched {len(log_events)} log events from {log_group}")
        
        # Complete the progress bar
        progress_bar.progress(1.0)
        status_text.text(f"Completed! Fetched {len(all_log_events)} log events from {len(log_groups)} log groups.")
        time.sleep(0.5)
        status_text.empty()
        progress_bar.empty()
        
        app_logger.info(f"Total log events fetched: {len(all_log_events)} (processed {total_processed} events)")
        
        if not all_log_events:
            app_logger.warning(f"No log events found in the specified time range for the selected log groups")
            st.warning(f"No log events found in the specified time range for the selected log groups")
            return pd.DataFrame()
        
        # Process log events
        log_processor = LogProcessor()
        df = log_processor.process_log_events(all_log_events)
        
        app_logger.info(f"Processed {len(df)} log entries")
        
        # Keep the original DataFrame with datetime objects for calculations
        # We'll only convert to strings when displaying in Streamlit
        
        return df
    except Exception as e:
        app_logger.exception(f"Error fetching log events: {str(e)}")
        st.error(f"Error fetching log events: {str(e)}")
        return pd.DataFrame()


def generate_demo_data(num_entries: int, start_time: datetime.datetime, 
                      end_time: datetime.datetime,
                      error_rate: float = 0.05,
                      cold_start_rate: float = 0.1,
                      memory_size: int = 1024) -> pd.DataFrame:
    """
    Generate demo data for users without AWS credentials.
    
    Args:
        num_entries: Number of log entries to generate
        start_time: Start time for generated logs
        end_time: End time for generated logs
        error_rate: Percentage of entries that should be errors (0-1)
        cold_start_rate: Percentage of entries that should be cold starts (0-1)
        memory_size: Memory size in MB
        
    Returns:
        DataFrame with generated log data
    """
    try:
        app_logger.info(f"Generating {num_entries} demo log entries between {start_time} and {end_time}")
        
        log_processor = LogProcessor()
        df = log_processor.generate_demo_data(
            num_entries=num_entries,
            start_time=start_time,
            end_time=end_time,
            error_rate=error_rate,
            cold_start_rate=cold_start_rate,
            memory_size=memory_size
        )
        
        app_logger.info(f"Generated {len(df)} demo log entries")
        
        # Keep the original DataFrame with datetime objects for calculations
        # We'll only convert to strings when displaying in Streamlit
        
        return df
    except Exception as e:
        app_logger.exception(f"Error generating demo data: {str(e)}")
        st.error(f"Error generating demo data: {str(e)}")
        return pd.DataFrame()


def calculate_metrics(log_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate metrics from log data.
    
    Args:
        log_data: DataFrame with processed log data
        
    Returns:
        Dictionary with calculated metrics
    """
    if log_data.empty:
        return {}
    
    try:
        app_logger.info("Calculating metrics from log data")
        
        metrics_calculator = MetricsCalculator(log_data)
        
        # Calculate basic metrics
        basic_metrics = metrics_calculator.calculate_basic_metrics()
        
        # Calculate time-series metrics
        time_series_metrics = metrics_calculator.calculate_time_series_metrics()
        
        # Analyze errors
        error_analysis = metrics_calculator.analyze_errors()
        
        # Analyze memory usage
        memory_analysis = metrics_calculator.analyze_memory_usage()
        
        # Analyze cold starts
        cold_start_analysis = metrics_calculator.analyze_cold_starts()
        
        # Get invocation patterns
        invocation_patterns = metrics_calculator.get_invocation_patterns()
        
        # Add log group information if available
        log_groups_info = {}
        if 'log_group' in log_data.columns:
            log_groups = log_data['log_group'].unique()
            log_groups_info['log_groups'] = log_groups.tolist()
            
            # Count entries per log group
            log_group_counts = log_data['log_group'].value_counts().to_dict()
            log_groups_info['log_group_counts'] = log_group_counts
            
            app_logger.info(f"Log data contains {len(log_groups)} log groups")
        
        metrics = {
            **basic_metrics,
            'time_series': time_series_metrics,
            'error_analysis': error_analysis,
            'memory_analysis': memory_analysis,
            'cold_start_analysis': cold_start_analysis,
            'invocation_patterns': invocation_patterns,
            'log_groups_info': log_groups_info
        }
        
        app_logger.info("Metrics calculation completed")
        return metrics
    except Exception as e:
        app_logger.exception(f"Error calculating metrics: {str(e)}")
        st.error(f"Error calculating metrics: {str(e)}")
        return {}


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'aws_client' not in st.session_state:
        st.session_state.aws_client = None
    
    if 'log_data' not in st.session_state:
        st.session_state.log_data = None
    
    if 'metrics' not in st.session_state:
        st.session_state.metrics = None
    
    if 'last_fetch_time' not in st.session_state:
        st.session_state.last_fetch_time = None
    
    if 'aws_region' not in st.session_state:
        st.session_state.aws_region = 'us-east-1'
    
    if 'aws_profile' not in st.session_state:
        st.session_state.aws_profile = 'default'


def main():
    """Main application function."""
    try:
        app_logger.info("Starting CloudWatch Logs Analyzer application")
        
        # Initialize session state
        initialize_session_state()
        
        # Custom CSS
        st.markdown("""
            <style>
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 24px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: pre-wrap;
                background-color: transparent;
                border-radius: 4px 4px 0px 0px;
                gap: 1px;
                padding-top: 10px;
                padding-bottom: 10px;
            }
            .stTabs [aria-selected="true"] {
                background-color: #f0f2f6;
                border-bottom: 2px solid #FF9900;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Application header
        st.title("CloudWatch Logs Analyzer")
        st.markdown(
            "Analyze AWS Lambda function logs to identify performance patterns, errors, and optimization opportunities."
        )
        
        # Initialize or update AWS client if needed
        if st.session_state.aws_client is None:
            st.session_state.aws_client = CloudWatchLogsClient(
                region_name=st.session_state.aws_region,
                profile_name=None if st.session_state.aws_profile == "default" else st.session_state.aws_profile
            )
        
        # Render sidebar and get filter values
        filters = render_sidebar(st.session_state.aws_client)
        
        # Handle fetch button click
        if filters.get('fetch'):
            with st.spinner("Processing logs..."):
                if filters['mode'] == 'AWS':
                    # Check if required filters are selected
                    if not filters.get('log_groups'):
                        st.error("Please select at least one log group.")
                        return
                    
                    # Fetch logs from AWS
                    log_data = fetch_aws_logs(
                        aws_client=st.session_state.aws_client,
                        log_groups=filters['log_groups'],
                        start_time=filters['start_time'],
                        end_time=filters['end_time'],
                        filter_pattern=filters.get('filter_pattern')
                    )
                else:
                    # Generate demo data
                    log_data = generate_demo_data(
                        num_entries=filters.get('num_entries', 1000),
                        start_time=filters['start_time'],
                        end_time=filters['end_time'],
                        error_rate=filters.get('error_rate', 5) / 100,
                        cold_start_rate=filters.get('cold_start_rate', 10) / 100,
                        memory_size=filters.get('memory_size', 1024)
                    )
                
                # Calculate metrics
                if not log_data.empty:
                    metrics = calculate_metrics(log_data)
                    
                    # Update session state
                    st.session_state.log_data = log_data
                    st.session_state.metrics = metrics
                    st.session_state.last_fetch_time = datetime.datetime.now()
                    
                    # Success message
                    st.success(f"Successfully processed {len(log_data)} log entries.")
                else:
                    st.warning("No log data found for the selected filters.")
        
        # Display last fetch time if available
        if st.session_state.last_fetch_time:
            st.caption(f"Last updated: {st.session_state.last_fetch_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Log Explorer", "⚙️ Settings"])
        
        # Dashboard tab
        with tab1:
            if st.session_state.log_data is not None and not st.session_state.log_data.empty:
                # Display log group information if available
                if 'log_groups_info' in st.session_state.metrics and st.session_state.metrics['log_groups_info']:
                    log_groups_info = st.session_state.metrics['log_groups_info']
                    if 'log_groups' in log_groups_info:
                        st.subheader("Log Groups Analysis")
                        log_groups = log_groups_info['log_groups']
                        
                        if len(log_groups) > 1:
                            st.info(f"Analyzing data from {len(log_groups)} log groups")
                            
                            # Display log group distribution
                            if 'log_group_counts' in log_groups_info:
                                counts = log_groups_info['log_group_counts']
                                
                                # Create a DataFrame for the counts
                                counts_df = pd.DataFrame({
                                    'Log Group': list(counts.keys()),
                                    'Count': list(counts.values())
                                }).sort_values('Count', ascending=False)
                                
                                # Display as a bar chart
                                st.bar_chart(counts_df.set_index('Log Group'))
                
                # Metrics dashboard
                render_metrics_dashboard(st.session_state.metrics)
                
                # Timeline chart
                render_timeline_chart(st.session_state.metrics.get('time_series', pd.DataFrame()))
                
                # Create two columns for memory and error analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    # Memory chart
                    render_memory_chart(
                        st.session_state.log_data,
                        st.session_state.metrics.get('memory_analysis', {})
                    )
                
                with col2:
                    # Error analysis
                    render_error_analysis(
                        st.session_state.metrics.get('error_analysis', {}),
                        st.session_state.log_data
                    )
                
                # Invocation patterns
                render_invocation_patterns(st.session_state.metrics.get('invocation_patterns', {}))
                
                # Performance recommendations
                render_performance_recommendations(st.session_state.metrics)
                
                # Error correlation
                render_error_correlation(st.session_state.log_data)
            else:
                st.info(
                    "No log data available. Please fetch logs using the sidebar controls."
                )
        
        # Log Explorer tab
        with tab2:
            if st.session_state.log_data is not None and not st.session_state.log_data.empty:
                render_log_explorer(st.session_state.log_data)
            else:
                st.info(
                    "No log data available. Please fetch logs using the sidebar controls."
                )
        
        # Settings tab
        with tab3:
            st.header("Settings")
            
            # AWS Settings
            st.subheader("AWS Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Region selection
                available_regions = st.session_state.aws_client.get_available_regions()
                selected_region = st.selectbox(
                    "AWS Region",
                    available_regions,
                    index=available_regions.index(st.session_state.aws_region) if st.session_state.aws_region in available_regions else 0
                )
                
                # Update session state if region changed
                if selected_region != st.session_state.aws_region:
                    st.session_state.aws_region = selected_region
            
            with col2:
                # Profile selection
                available_profiles = get_aws_profiles()
                selected_profile = st.selectbox(
                    "AWS Profile",
                    ["default"] + available_profiles,
                    index=0 if st.session_state.aws_profile == "default" else 
                          available_profiles.index(st.session_state.aws_profile) + 1 if st.session_state.aws_profile in available_profiles else 0
                )
                
                # Update session state if profile changed
                if selected_profile != st.session_state.aws_profile:
                    st.session_state.aws_profile = selected_profile
            
            if st.button("Update AWS Configuration"):
                st.session_state.aws_client = CloudWatchLogsClient(
                    region_name=selected_region,
                    profile_name=None if selected_profile == "default" else selected_profile
                )
                st.success("AWS configuration updated.")
                app_logger.info(f"AWS configuration updated: region={selected_region}, profile={selected_profile}")
            
            # Application Settings
            st.subheader("Application Settings")
            
            # Theme selection
            theme = st.selectbox(
                "Theme",
                ["Light", "Dark"],
                index=0
            )
            
            # Clear data button
            if st.button("Clear All Data"):
                st.session_state.log_data = None
                st.session_state.metrics = None
                st.session_state.last_fetch_time = None
                st.success("All data cleared.")
                time.sleep(1)
                st.experimental_rerun()
            
            # About section
            st.subheader("About")
            st.markdown("""
                **CloudWatch Logs Analyzer** helps you analyze AWS Lambda function logs to identify 
                performance patterns, errors, and optimization opportunities.
                
                Features:
                - Performance metrics visualization
                - Error analysis and correlation
                - Memory usage optimization
                - Cold start analysis
                - Log exploration and filtering
                - Multi-log group analysis
                
                Version: 1.1.0
            """)
    except Exception as e:
        app_logger.exception(f"Unhandled exception in main application: {str(e)}")
        st.error(f"An unexpected error occurred: {str(e)}")
        st.error("Please check the logs for more details.")


if __name__ == "__main__":
    try:
        app_logger.info("Starting CloudWatch Logs Analyzer application")
        main()
        app_logger.info("CloudWatch Logs Analyzer application completed successfully")
    except Exception as e:
        app_logger.exception(f"Unhandled exception in main application: {str(e)}")
        st.error(f"An unexpected error occurred: {str(e)}")
        st.error("Please check the logs for more details.")
