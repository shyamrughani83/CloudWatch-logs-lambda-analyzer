"""
Sidebar component for CloudWatch Logs Analyzer.
Provides filters and controls for the application.
"""

import streamlit as st
import datetime
from typing import Tuple, List, Dict, Any, Optional
import pytz

from utils.aws_client import CloudWatchLogsClient, get_aws_profiles
from utils.logger import get_logger

# Initialize logger
logger = get_logger("sidebar")


def render_sidebar(aws_client: Optional[CloudWatchLogsClient] = None) -> Dict[str, Any]:
    """
    Render the sidebar with filters and controls.
    
    Args:
        aws_client: Optional CloudWatchLogsClient instance
        
    Returns:
        Dictionary with selected filter values
    """
    with st.sidebar:
        st.title("Filters & Controls")
        
        # Mode selection (AWS or Demo)
        mode = st.radio("Mode", ["AWS", "Demo"], horizontal=True)
        
        filters = {
            'mode': mode,
            'time_range': None,
            'start_time': None,
            'end_time': None,
            'log_groups': [],
            'filter_pattern': None,
            'region': None,
            'connect_aws': False
        }
        
        # Time range selection
        st.subheader("Time Range")
        time_range_option = st.selectbox(
            "Select time range",
            ["Last 30 minutes", "Last hour", "Last 3 hours", "Last 24 hours", "Last 7 days", "Custom"]
        )
        
        # Set time range based on selection
        now = datetime.datetime.now(pytz.UTC)
        if time_range_option == "Last 30 minutes":
            filters['start_time'] = now - datetime.timedelta(minutes=30)
            filters['end_time'] = now
            filters['time_range'] = "30m"
        elif time_range_option == "Last hour":
            filters['start_time'] = now - datetime.timedelta(hours=1)
            filters['end_time'] = now
            filters['time_range'] = "1h"
        elif time_range_option == "Last 3 hours":
            filters['start_time'] = now - datetime.timedelta(hours=3)
            filters['end_time'] = now
            filters['time_range'] = "3h"
        elif time_range_option == "Last 24 hours":
            filters['start_time'] = now - datetime.timedelta(days=1)
            filters['end_time'] = now
            filters['time_range'] = "24h"
        elif time_range_option == "Last 7 days":
            filters['start_time'] = now - datetime.timedelta(days=7)
            filters['end_time'] = now
            filters['time_range'] = "7d"
        else:  # Custom time range
            st.caption("Select custom time range")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start date", value=now.date() - datetime.timedelta(days=1))
                start_time = st.time_input("Start time", value=now.time())
            
            with col2:
                end_date = st.date_input("End date", value=now.date())
                end_time = st.time_input("End time", value=now.time())
            
            filters['start_time'] = datetime.datetime.combine(start_date, start_time)
            filters['end_time'] = datetime.datetime.combine(end_date, end_time)
            filters['time_range'] = "custom"
        
        # AWS specific controls
        if mode == "AWS":
            # AWS Region selection
            st.subheader("AWS Region")
            
            # Get available regions
            available_regions = []
            if aws_client:
                available_regions = aws_client.get_available_regions()
            else:
                # Fallback to common regions
                available_regions = [
                    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
                    'ca-central-1',
                    'eu-north-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
                    'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3',
                    'ap-southeast-1', 'ap-southeast-2',
                    'ap-south-1',
                    'sa-east-1'
                ]
            
            # Get current region from client or default
            current_region = aws_client.region if aws_client else "us-east-1"
            
            # Region dropdown
            selected_region = st.selectbox(
                "Select AWS Region",
                options=available_regions,
                index=available_regions.index(current_region) if current_region in available_regions else 0,
                help="Select the AWS region to query CloudWatch logs from"
            )
            
            # Store selected region in filters
            filters['region'] = selected_region
            
            # Check if region changed and needs client refresh
            if aws_client and selected_region != aws_client.region:
                st.info(f"Region changed to {selected_region}. Click 'Connect to AWS' to refresh.")
            
            # AWS Profile selection
            st.subheader("AWS Profile")
            available_profiles = get_aws_profiles()
            selected_profile = st.selectbox(
                "Select AWS Profile",
                options=available_profiles,
                index=0,
                help="Select the AWS profile to use for authentication"
            )
            filters['profile'] = selected_profile
            
            # Connect to AWS button
            connect_button = st.button("Connect to AWS", type="primary", use_container_width=True)
            if connect_button:
                filters['connect_aws'] = True
                st.success(f"Connecting to AWS using profile '{selected_profile}' in region '{selected_region}'...")
            
            # Authentication status - only show if user has explicitly connected
            if aws_client and 'aws_connected' in st.session_state and st.session_state.aws_connected:
                is_authenticated = aws_client.is_authenticated()
                if is_authenticated:
                    st.success("✅ Connected to AWS")
                else:
                    st.error("❌ Failed to connect to AWS. Please check your credentials.")
            
            # Log group selection
            st.subheader("Log Groups")
            
            # Search box for log groups
            log_group_search = st.text_input("Search log groups", "")
            
            # Fetch log groups if client is available
            log_groups = []
            if aws_client and aws_client.is_authenticated():
                with st.spinner("Fetching log groups..."):
                    log_groups = aws_client.get_log_groups(prefix=log_group_search)
            
            if log_groups:
                log_group_names = [lg['logGroupName'] for lg in log_groups]
                
                # Multi-select for log groups
                selected_log_groups = st.multiselect(
                    "Select log groups",
                    log_group_names,
                    help="Select one or more log groups to analyze"
                )
                
                if selected_log_groups:
                    logger.info(f"Selected {len(selected_log_groups)} log groups: {selected_log_groups}")
                    filters['log_groups'] = selected_log_groups
                else:
                    st.warning("Please select at least one log group")
            else:
                st.info("No log groups found or AWS client not authenticated.")
            
            # Filter pattern
            st.subheader("Filter Pattern (Optional)")
            filter_pattern = st.text_input(
                "CloudWatch Logs filter pattern",
                placeholder="e.g., ERROR or ?Exception"
            )
            filters['filter_pattern'] = filter_pattern if filter_pattern else None
        
        # Demo mode controls
        else:
            st.subheader("Demo Settings")
            
            # Number of entries
            num_entries = st.slider("Number of log entries", 100, 5000, 1000, 100)
            filters['num_entries'] = num_entries
            
            # Error rate
            error_rate = st.slider("Error rate (%)", 0, 100, 5, 1)
            filters['error_rate'] = error_rate
            
            # Cold start rate
            cold_start_rate = st.slider("Cold start rate (%)", 0, 100, 10, 1)
            filters['cold_start_rate'] = cold_start_rate
            
            # Memory size
            memory_size = st.select_slider(
                "Memory size (MB)",
                options=[128, 256, 512, 1024, 2048, 4096, 8192, 10240],
                value=1024
            )
            filters['memory_size'] = memory_size
        
        # Fetch button
        fetch_button = st.button("Fetch Logs", type="primary", use_container_width=True)
        
        if fetch_button:
            filters['fetch'] = True
        else:
            filters['fetch'] = False
        
        return filters
