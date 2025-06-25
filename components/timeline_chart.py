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
    
    st.markdown("""
    <div class="stcard">
        <h3>📈 Invocation Timeline</h3>
    """, unsafe_allow_html=True)
    
    # Create a figure with secondary y-axis
    fig = go.Figure()
    
    # Ensure datetime column is timezone-naive
    time_series_data = ensure_timezone_naive(time_series_data)
    
    # Add invocations as a bar chart
    if len(time_series_data) > 0:
        # Check if the DataFrame has the expected columns
        if 'timestamp' in time_series_data.columns:
            # Rename columns to match expected names
            time_series_data = time_series_data.rename(columns={
                'timestamp': 'datetime',
                'count': 'invocations',
                'mean': 'avg_duration_ms'
            })
            
            # Add errors column if it doesn't exist
            if 'errors' not in time_series_data.columns:
                time_series_data['errors'] = 0
            
            # Check if there's more than one unique datetime value
            if len(time_series_data['datetime'].unique()) > 1:
                # Add invocations as a bar chart with gradient color
                fig.add_trace(go.Bar(
                    x=time_series_data['datetime'],
                    y=time_series_data['invocations'],
                    name='Invocations',
                    marker=dict(
                        color='#007bff',
                        opacity=0.8,
                        line=dict(width=1, color='#0056b3')
                    ),
                    hovertemplate='<b>Time:</b> %{x}<br><b>Invocations:</b> %{y}<extra></extra>'
                ))
                
                # Add errors as a bar chart
                fig.add_trace(go.Bar(
                    x=time_series_data['datetime'],
                    y=time_series_data['errors'],
                    name='Errors',
                    marker=dict(
                        color='#dc3545',
                        opacity=0.8,
                        line=dict(width=1, color='#bd2130')
                    ),
                    hovertemplate='<b>Time:</b> %{x}<br><b>Errors:</b> %{y}<extra></extra>'
                ))
                
                # Add average duration as a line on secondary y-axis
                fig.add_trace(go.Scatter(
                    x=time_series_data['datetime'],
                    y=time_series_data['avg_duration_ms'],
                    name='Avg Duration (ms)',
                    yaxis='y2',
                    line=dict(
                        color='#fd7e14', 
                        width=3,
                        shape='spline',
                        smoothing=0.3,
                        dash='solid'
                    ),
                    mode='lines+markers',
                    marker=dict(
                        size=8,
                        color='#fd7e14',
                        line=dict(width=2, color='#ffffff')
                    ),
                    hovertemplate='<b>Time:</b> %{x}<br><b>Avg Duration:</b> %{y:.2f} ms<extra></extra>'
                ))
                
                # Update layout with secondary y-axis - Fix the anchor issue
                fig.update_layout(
                    title={
                        'text': 'Invocations and Performance Over Time',
                        'font': {'size': 22, 'color': '#232F3E', 'family': 'Arial, sans-serif'},
                        'y': 0.95,
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    xaxis=dict(
                        title='Time',
                        titlefont=dict(size=14, color='#444'),
                        showgrid=True,
                        gridcolor='rgba(230, 230, 230, 0.8)'
                    ),
                    yaxis=dict(
                        title=dict(text='Count', font=dict(size=14, color='#007bff')),
                        tickfont=dict(color='#007bff'),
                        showgrid=True,
                        gridcolor='rgba(230, 230, 230, 0.8)'
                    ),
                    yaxis2=dict(
                        title=dict(text='Duration (ms)', font=dict(size=14, color='#fd7e14')),
                        tickfont=dict(color='#fd7e14'),
                        overlaying='y',
                        side='right',
                        showgrid=False
                    ),
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='center',
                        x=0.5,
                        bgcolor='rgba(255, 255, 255, 0.8)',
                        bordercolor='rgba(0, 0, 0, 0.1)',
                        borderwidth=1
                    ),
                    margin=dict(l=20, r=20, t=60, b=20),
                    hovermode='x unified',
                    barmode='stack',
                    plot_bgcolor='rgba(255, 255, 255, 0.95)',
                    paper_bgcolor='rgba(255, 255, 255, 0.95)',
                    font=dict(family="Arial, sans-serif"),
                    hoverlabel=dict(
                        bgcolor="white",
                        font_size=12,
                        font_family="Arial, sans-serif"
                    ),
                    shapes=[
                        # Add a subtle grid
                        dict(
                            type='rect',
                            xref='paper', yref='paper',
                            x0=0, y0=0, x1=1, y1=1,
                            line=dict(color="rgba(0,0,0,0)", width=0),
                            fillcolor="rgba(255,255,255,0)"
                        )
                    ]
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
                
                # Display metrics for the single time point in a more attractive way
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                        <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 500;">Invocations</div>
                        <div style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0.25rem; color: #007bff;">{invocations}</div>
                        <div style="font-size: 0.8rem; color: #6c757d;">at {single_time.strftime('%H:%M:%S')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
                        <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 500;">Errors</div>
                        <div style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0.25rem; color: #dc3545;">{errors}</div>
                        <div style="font-size: 0.8rem; color: #6c757d;">at {single_time.strftime('%H:%M:%S')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⏱️</div>
                        <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 500;">Avg Duration</div>
                        <div style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0.25rem; color: #fd7e14;">{duration:.2f} ms</div>
                        <div style="font-size: 0.8rem; color: #6c757d;">at {single_time.strftime('%H:%M:%S')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("Time series data does not have the expected format. Please check the data structure.")
    else:
        st.info("No time-series data available. Please fetch log data first.")
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_invocation_patterns(invocation_patterns: Dict[str, Any]) -> None:
    """
    Render charts showing invocation patterns by hour and day.
    
    Args:
        invocation_patterns: Dictionary with invocation pattern data
    """
    if not invocation_patterns:
        return
    
    st.markdown("""
    <div class="stcard">
        <h3>🔄 Invocation Patterns</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    # Hourly pattern
    with col1:
        hourly_data = invocation_patterns.get('hourly_pattern', [])
        if hourly_data:
            hourly_df = pd.DataFrame(hourly_data)
            
            # Check if the expected columns exist
            if 'hour' in hourly_df.columns and 'count' in hourly_df.columns:
                # Rename count to invocations if needed
                if 'invocations' not in hourly_df.columns:
                    hourly_df['invocations'] = hourly_df['count']
                
                fig = px.bar(
                    hourly_df,
                    x='hour',
                    y='invocations',
                    title='Invocations by Hour of Day',
                    labels={'hour': 'Hour', 'invocations': 'Invocations'},
                    color_discrete_sequence=['#007bff'],
                    template='plotly_white'
                )
                
                # Add a gradient effect to bars
                fig.update_traces(
                    marker=dict(
                        color='#007bff',
                        line=dict(width=1, color='#0056b3'),
                        opacity=0.8
                    ),
                    hovertemplate='<b>Hour:</b> %{x}:00<br><b>Invocations:</b> %{y}<extra></extra>'
                )
                
                fig.update_layout(
                    xaxis=dict(
                        tickmode='linear', 
                        tick0=0, 
                        dtick=1,
                        title=dict(text='Hour of Day', font=dict(size=14)),
                        showgrid=True,
                        gridcolor='rgba(230, 230, 230, 0.8)'
                    ),
                    yaxis=dict(
                        title=dict(text='Invocations', font=dict(size=14)),
                        showgrid=True,
                        gridcolor='rgba(230, 230, 230, 0.8)'
                    ),
                    margin=dict(l=20, r=20, t=40, b=20),
                    plot_bgcolor='rgba(255, 255, 255, 0.95)',
                    paper_bgcolor='rgba(255, 255, 255, 0.95)',
                    title=dict(
                        text='Invocations by Hour of Day',
                        font=dict(size=18, color='#232F3E'),
                        x=0.5,
                        xanchor='center'
                    ),
                    hoverlabel=dict(
                        bgcolor="white",
                        font_size=12,
                        font_family="Arial, sans-serif"
                    )
                )
                
                # Add peak hour marker
                peak_hour = hourly_df['invocations'].idxmax()
                if peak_hour is not None:
                    peak_hour_value = hourly_df.iloc[peak_hour]['hour']
                    peak_invocations = hourly_df.iloc[peak_hour]['invocations']
                    
                    fig.add_trace(go.Scatter(
                        x=[peak_hour_value],
                        y=[peak_invocations],
                        mode='markers',
                        marker=dict(
                            color='#FF9900',
                            size=12,
                            line=dict(width=2, color='white'),
                            symbol='star'
                        ),
                        name='Peak Hour',
                        hovertemplate='<b>Peak Hour:</b> %{x}:00<br><b>Invocations:</b> %{y}<extra></extra>'
                    ))
                
                st.plotly_chart(fig, use_container_width=True)
                
                peak_hour = invocation_patterns.get('peak_hour')
                if peak_hour is not None:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 12px; background-color: #e9f7fe; border-radius: 8px; margin-top: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                        <span style="font-weight: 600; color: #007bff;">Peak hour:</span> {peak_hour}:00 - {peak_hour + 1}:00
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Hourly pattern data does not have the expected format.")
        else:
            st.info("No hourly pattern data available.")
    
    # Daily pattern
    with col2:
        daily_data = invocation_patterns.get('daily_pattern', [])
        if daily_data:
            daily_df = pd.DataFrame(daily_data)
            
            # Check if the expected columns exist
            if 'day' in daily_df.columns or 'day_of_week' in daily_df.columns:
                # Ensure day_name is present
                if 'day_name' not in daily_df.columns:
                    if 'day' in daily_df.columns:
                        daily_df['day_name'] = daily_df['day']
                    elif 'day_of_week' in daily_df.columns:
                        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        daily_df['day_name'] = daily_df['day_of_week'].apply(lambda x: day_names[int(x) if isinstance(x, (int, float)) else 0])
                
                # Ensure invocations column exists
                if 'invocations' not in daily_df.columns and 'count' in daily_df.columns:
                    daily_df['invocations'] = daily_df['count']
                
                # Sort by day of week if possible
                if 'day_of_week' in daily_df.columns:
                    daily_df['day_order'] = daily_df['day_of_week']
                    daily_df = daily_df.sort_values('day_order')
                
                fig = px.bar(
                    daily_df,
                    x='day_name',
                    y='invocations',
                    title='Invocations by Day of Week',
                    labels={'day_name': 'Day', 'invocations': 'Invocations'},
                    color_discrete_sequence=['#007bff'],
                    template='plotly_white'
                )
                
                # Add a gradient effect to bars
                fig.update_traces(
                    marker=dict(
                        color='#007bff',
                        line=dict(width=1, color='#0056b3'),
                        opacity=0.8
                    ),
                    hovertemplate='<b>Day:</b> %{x}<br><b>Invocations:</b> %{y}<extra></extra>'
                )
                
                fig.update_layout(
                    xaxis=dict(
                        title=dict(text='Day of Week', font=dict(size=14)),
                        showgrid=True,
                        gridcolor='rgba(230, 230, 230, 0.8)'
                    ),
                    yaxis=dict(
                        title=dict(text='Invocations', font=dict(size=14)),
                        showgrid=True,
                        gridcolor='rgba(230, 230, 230, 0.8)'
                    ),
                    margin=dict(l=20, r=20, t=40, b=20),
                    plot_bgcolor='rgba(255, 255, 255, 0.95)',
                    paper_bgcolor='rgba(255, 255, 255, 0.95)',
                    title=dict(
                        text='Invocations by Day of Week',
                        font=dict(size=18, color='#232F3E'),
                        x=0.5,
                        xanchor='center'
                    ),
                    hoverlabel=dict(
                        bgcolor="white",
                        font_size=12,
                        font_family="Arial, sans-serif"
                    )
                )
                
                # Add peak day marker
                peak_day_idx = daily_df['invocations'].idxmax()
                if peak_day_idx is not None:
                    peak_day = daily_df.iloc[peak_day_idx]['day_name']
                    peak_invocations = daily_df.iloc[peak_day_idx]['invocations']
                    
                    fig.add_trace(go.Scatter(
                        x=[peak_day],
                        y=[peak_invocations],
                        mode='markers',
                        marker=dict(
                            color='#FF9900',
                            size=12,
                            line=dict(width=2, color='white'),
                            symbol='star'
                        ),
                        name='Peak Day',
                        hovertemplate='<b>Peak Day:</b> %{x}<br><b>Invocations:</b> %{y}<extra></extra>'
                    ))
                
                st.plotly_chart(fig, use_container_width=True)
                
                peak_day = invocation_patterns.get('peak_day')
                if peak_day:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 12px; background-color: #e9f7fe; border-radius: 8px; margin-top: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                        <span style="font-weight: 600; color: #007bff;">Peak day:</span> {peak_day}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Daily pattern data does not have the expected format.")
        else:
            st.info("No daily pattern data available.")
    
    st.markdown("</div>", unsafe_allow_html=True)
