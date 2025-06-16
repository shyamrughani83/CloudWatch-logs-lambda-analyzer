"""
Timeline Chart component for CloudWatch Logs Analyzer.
Displays invocation patterns over time.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional
from utils.helpers import ensure_timezone_naive, convert_for_streamlit_display, ensure_arrow_compatible, safe_display


def render_timeline_chart(time_series_data: pd.DataFrame) -> None:
    """
    Render a timeline chart showing invocation patterns over time.
    
    Args:
        time_series_data: DataFrame with time-series metrics
    """
    if time_series_data.empty:
        st.info("No time-series data available. Please fetch log data first.")
        return
    
    st.subheader("Invocation Timeline")
    
    # Create a figure with secondary y-axis
    fig = go.Figure()
    
    # Ensure datetime column is timezone-naive
    time_series_data = ensure_timezone_naive(time_series_data)
    
    # Add invocations as a bar chart
    if len(time_series_data) > 0:
        # Check if there's more than one unique datetime value
        if len(time_series_data['datetime'].unique()) > 1:
            fig.add_trace(go.Bar(
                x=time_series_data['datetime'],
                y=time_series_data['invocations'],
                name='Invocations',
                marker_color='#007bff',
                opacity=0.7
            ))
            
            # Add errors as a bar chart
            fig.add_trace(go.Bar(
                x=time_series_data['datetime'],
                y=time_series_data['errors'],
                name='Errors',
                marker_color='#dc3545',
                opacity=0.7
            ))
            
            # Add average duration as a line on secondary y-axis
            fig.add_trace(go.Scatter(
                x=time_series_data['datetime'],
                y=time_series_data['avg_duration_ms'],
                name='Avg Duration (ms)',
                yaxis='y2',
                line=dict(color='#fd7e14', width=2)
            ))
            
            # Update layout with secondary y-axis
            fig.update_layout(
                title='Invocations and Performance Over Time',
                xaxis_title='Time',
                yaxis=dict(
                    title=dict(text='Count', font=dict(color='#007bff')),
                    tickfont=dict(color='#007bff')
                ),
                yaxis2=dict(
                    title=dict(text='Duration (ms)', font=dict(color='#fd7e14')),
                    tickfont=dict(color='#fd7e14'),
                    anchor='x',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1
                ),
                margin=dict(l=20, r=20, t=40, b=20),
                hovermode='x unified',
                barmode='stack'
            )
            
            # Display the figure
            st.plotly_chart(fig, use_container_width=True)
        else:
            # If there's only one datetime point, create a simple bar chart
            st.info("Only one time point available. Cannot create a timeline chart.")
            
            # Create a simple bar chart for the single time point
            single_time = time_series_data['datetime'].iloc[0]
            invocations = time_series_data['invocations'].iloc[0]
            errors = time_series_data['errors'].iloc[0]
            duration = time_series_data['avg_duration_ms'].iloc[0]
            
            # Display metrics for the single time point
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Invocations", invocations)
            with col2:
                st.metric("Errors", errors)
            with col3:
                st.metric("Avg Duration (ms)", f"{duration:.2f}")
    else:
        st.info("No time-series data available. Please fetch log data first.")


def render_invocation_patterns(invocation_patterns: Dict[str, Any]) -> None:
    """
    Render charts showing invocation patterns by hour and day.
    
    Args:
        invocation_patterns: Dictionary with invocation pattern data
    """
    if not invocation_patterns:
        return
    
    st.subheader("Invocation Patterns")
    
    col1, col2 = st.columns(2)
    
    # Hourly pattern
    with col1:
        hourly_data = invocation_patterns.get('hourly_pattern', [])
        if hourly_data:
            hourly_df = pd.DataFrame(hourly_data)
            
            fig = px.bar(
                hourly_df,
                x='hour',
                y='invocations',
                title='Invocations by Hour of Day',
                labels={'hour': 'Hour', 'invocations': 'Invocations'},
                color_discrete_sequence=['#007bff']
            )
            
            fig.update_layout(
                xaxis=dict(tickmode='linear', tick0=0, dtick=1),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            peak_hour = invocation_patterns.get('peak_hour')
            if peak_hour is not None:
                st.caption(f"Peak hour: {peak_hour}:00 - {peak_hour + 1}:00")
        else:
            st.info("No hourly pattern data available.")
    
    # Daily pattern
    with col2:
        daily_data = invocation_patterns.get('daily_pattern', [])
        if daily_data:
            daily_df = pd.DataFrame(daily_data)
            
            # Ensure day_name is present
            if 'day_name' not in daily_df.columns:
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                daily_df['day_name'] = daily_df['day_of_week'].apply(lambda x: day_names[int(x)])
            
            # Sort by day of week
            daily_df['day_order'] = daily_df['day_of_week']
            daily_df = daily_df.sort_values('day_order')
            
            fig = px.bar(
                daily_df,
                x='day_name',
                y='invocations',
                title='Invocations by Day of Week',
                labels={'day_name': 'Day', 'invocations': 'Invocations'},
                color_discrete_sequence=['#007bff']
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            peak_day = invocation_patterns.get('peak_day')
            if peak_day:
                st.caption(f"Peak day: {peak_day}")
        else:
            st.info("No daily pattern data available.")
