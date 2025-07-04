"""
CloudWatch Logs & Lambda Function Analyzer - Main Application

A comprehensive Streamlit application for analyzing AWS CloudWatch logs and managing Lambda functions.
Provides visual analytics, insights, and direct Lambda function management to help developers and DevOps engineers
understand performance patterns, identify errors, optimize resource usage, and test Lambda functions.
Features include log analysis, metrics visualization, Lambda function management, function invocation with logs,
error analysis, and performance recommendations.
"""

import streamlit as st
import pandas as pd
import datetime
import time
import traceback
import os
import base64
from typing import Dict, Any, Optional, List

# Import utility modules
from utils.aws_client import CloudWatchLogsClient, get_aws_profiles
from utils.lambda_client import LambdaClient
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
from components.lambda_functions import render_lambda_functions, render_lambda_metrics
from components.log_groups import render_log_groups
from components.theme_toggle import render_theme_toggle

# Set page configuration
st.set_page_config(
    page_title="CloudWatch Logs & Lambda Function Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


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
        
        # Use static methods of MetricsCalculator
        
        # Calculate basic metrics
        basic_metrics = MetricsCalculator.calculate_basic_metrics(log_data)
        
        # Calculate Lambda performance metrics
        lambda_metrics = MetricsCalculator.calculate_lambda_performance_metrics(log_data)
        
        # Calculate memory optimization
        memory_optimization = MetricsCalculator.calculate_memory_optimization(log_data)
        
        # Calculate error metrics
        error_metrics = MetricsCalculator.calculate_error_metrics(log_data)
        
        # Calculate time-series metrics
        time_series_metrics = MetricsCalculator.calculate_time_series_metrics(
            log_data, 
            time_column='timestamp', 
            value_column='duration', 
            freq='1min'
        )
        
        # Analyze memory usage
        memory_analysis = MetricsCalculator.analyze_memory_usage(log_data)
        
        # Analyze errors
        error_analysis = MetricsCalculator.analyze_errors(log_data)
        
        # Analyze cold starts
        cold_start_analysis = MetricsCalculator.analyze_cold_starts(log_data)
        
        # Get invocation patterns
        invocation_patterns = MetricsCalculator.get_invocation_patterns(log_data)
        
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
    
    if 'lambda_client' not in st.session_state:
        st.session_state.lambda_client = None
    
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
    
    if 'aws_connected' not in st.session_state:
        st.session_state.aws_connected = False


def load_css():
    """Load custom CSS."""
    # Load main CSS
    css_file = os.path.join(os.path.dirname(__file__), "static/style.css")
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Load enhanced UI CSS
    enhanced_ui_css_file = os.path.join(os.path.dirname(__file__), "static/enhanced_ui.css")
    with open(enhanced_ui_css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Load custom footer CSS
    footer_css_file = os.path.join(os.path.dirname(__file__), "static/custom_footer.css")
    with open(footer_css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def get_aws_logo_base64():
    """Get AWS logo as base64 string."""
    logo_path = os.path.join(os.path.dirname(__file__), "static/aws-logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

def main():
    """Main application function."""
    try:
        app_logger.info("Starting CloudWatch Logs & Lambda Function Analyzer application")
        
        # Initialize session state
        initialize_session_state()
        
        # Load custom CSS
        try:
            load_css()
        except Exception as e:
            app_logger.warning(f"Failed to load custom CSS: {str(e)}")
        
        # Application header with custom styling
        st.markdown("""
        <div class="main-header">
            <h1>📊 CloudWatch Logs & Lambda Function Analyzer</h1>
            <p>Analyze AWS CloudWatch logs and manage Lambda functions to identify performance patterns, test functions, and optimize resources.</p>
            <p style="font-size: 0.9rem; opacity: 0.8;">Powered by AWS</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Logo box with white text
        st.markdown("""
        <div class="logo-box">
            <h2>CloudWatch Logs & Lambda Function Analyzer</h2>
            <p>Powered by AWS</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize or update AWS clients if needed
        if st.session_state.aws_client is None:
            st.session_state.aws_client = CloudWatchLogsClient(
                region_name=st.session_state.aws_region,
                profile_name=None if st.session_state.aws_profile == "default" else st.session_state.aws_profile
            )
            
        # Initialize Lambda client if not already initialized
        if st.session_state.lambda_client is None:
            st.session_state.lambda_client = LambdaClient(
                region_name=st.session_state.aws_region,
                profile_name=None if st.session_state.aws_profile == "default" else st.session_state.aws_profile
            )
        
        # Render sidebar and get filter values
        filters = render_sidebar(st.session_state.aws_client)
        
        # Handle AWS connection button
        if filters['mode'] == 'AWS' and filters.get('connect_aws'):
            with st.spinner("Connecting to AWS..."):
                # Update region in session state
                if filters.get('region') and filters['region'] != st.session_state.aws_region:
                    st.session_state.aws_region = filters['region']
                
                # Update profile in session state
                if filters.get('profile') and filters['profile'] != st.session_state.aws_profile:
                    st.session_state.aws_profile = filters['profile']
                
                # Create new AWS clients with updated settings
                st.session_state.aws_client = CloudWatchLogsClient(
                    region_name=st.session_state.aws_region,
                    profile_name=None if st.session_state.aws_profile == "default" else st.session_state.aws_profile
                )
                
                st.session_state.lambda_client = LambdaClient(
                    region_name=st.session_state.aws_region,
                    profile_name=None if st.session_state.aws_profile == "default" else st.session_state.aws_profile
                )
                
                # Check authentication
                if st.session_state.aws_client.is_authenticated():
                    # Set the aws_connected flag to true
                    st.session_state.aws_connected = True
                    st.success(f"Successfully connected to AWS in region {st.session_state.aws_region}")
                else:
                    st.session_state.aws_connected = False
                    st.error("Failed to connect to AWS. Please check your credentials and region.")
                
                st.experimental_rerun()
        
        # Check if region has changed and update client if needed
        elif filters['mode'] == 'AWS' and filters.get('region') and filters['region'] != st.session_state.aws_region:
            st.session_state.aws_region = filters['region']
            st.info(f"Region changed to {filters['region']}. Click 'Connect to AWS' to apply.")
        
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
        
        # Create tabs for different views with attractive styling
        st.markdown("""
        <div class='stcard'>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 **Dashboard**", 
            "📚 **Log Groups**",
            "⚡ **Lambda Functions**",
            "📈 **Lambda Metrics**",
            "⚙️ **Settings**"
        ])
        
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
        
        # Log Groups tab
        with tab2:
            render_log_groups(st.session_state.aws_client)
        
        # Lambda Functions tab
        with tab3:
            render_lambda_functions(st.session_state.lambda_client)
        
        # Lambda Metrics tab
        with tab4:
            render_lambda_metrics(st.session_state.lambda_client)
        
        # Settings tab
        with tab5:
            st.header("Settings")
            
            # About section
            st.subheader("About CloudWatch Logs & Lambda Function Analyzer")
            
            st.markdown("""
            <div class="stcard">
                <h3>🚀 Features</h3>
                <ul>
                    <li><strong>CloudWatch Logs Analysis</strong>: Analyze logs from multiple log groups with advanced filtering</li>
                    <li><strong>Log Group Management</strong>: Browse, search, and manage CloudWatch Log Groups with detailed metrics</li>
                    <li><strong>Lambda Function Management</strong>: View, manage, and test Lambda functions directly from the UI</li>
                    <li><strong>Function Invocation with Logs</strong>: Invoke Lambda functions and view both responses and execution logs</li>
                    <li><strong>Performance Metrics</strong>: Visualize invocation patterns, durations, and memory usage</li>
                    <li><strong>Error Analysis</strong>: Identify and analyze errors in your logs with correlation analysis</li>
                    <li><strong>Performance Recommendations</strong>: Get actionable recommendations for optimizing Lambda functions</li>
                    <li><strong>Timeline Visualization</strong>: View invocation patterns over time with interactive charts</li>
                    <li><strong>Memory Utilization Analysis</strong>: Optimize Lambda memory settings based on actual usage</li>
                    <li><strong>Lambda Metrics Dashboard</strong>: Monitor Lambda function performance metrics</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
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
            
        # Add a footer with custom styling
        st.markdown("""
        <div class="footer">
            <p>CloudWatch Logs & Lambda Function Analyzer | Powered by AWS</p>
            <p>© 2025 | Shyam Rughani (Cloud Man)</p>
        </div>
        """, unsafe_allow_html=True)
        
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
