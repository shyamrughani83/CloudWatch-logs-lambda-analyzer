"""
Metrics Dashboard component for CloudWatch Logs Analyzer.
Displays performance metrics and key indicators.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any


def render_metrics_dashboard(metrics: Dict[str, Any]) -> None:
    """
    Render the metrics dashboard with key performance indicators.
    
    Args:
        metrics: Dictionary with calculated metrics
    """
    if not metrics:
        st.info("No metrics available. Please fetch log data first.")
        return
    
    st.markdown("""
    <div class="stcard">
        <h3>📊 Performance Overview</h3>
        <div class="dashboard-metrics">
    """, unsafe_allow_html=True)
    
    # Create metrics cards in a grid
    col1, col2, col3, col4 = st.columns(4)
    
    # Invocations
    with col1:
        render_metric_card(
            "Total Invocations",
            metrics.get('count', 0),
            "",
            "blue",
            "📈"
        )
    
    # Success Rate
    with col2:
        success_rate = (1 - metrics.get('error_rate', 0)) * 100
        color = "green" if success_rate >= 99 else "orange" if success_rate >= 95 else "red"
        render_metric_card(
            "Success Rate",
            f"{success_rate:.2f}%",
            f"{metrics.get('error_rate', 0) * 100:.2f}% errors",
            color,
            "✅"
        )
    
    # Avg Duration
    with col3:
        avg_duration = metrics.get('avg_duration', 0)
        color = "green" if avg_duration < 100 else "orange" if avg_duration < 500 else "red"
        render_metric_card(
            "Avg Duration",
            f"{avg_duration:.2f} ms",
            f"P95: {metrics.get('p95_duration', 0):.2f} ms",
            color,
            "⏱️"
        )
    
    # Memory Utilization
    with col4:
        memory_util = metrics.get('avg_memory_utilization', 0)
        color = "orange" if memory_util < 40 else "green" if memory_util < 80 else "red"
        render_metric_card(
            "Memory Utilization",
            f"{memory_util:.2f}%",
            f"Max: {metrics.get('max_memory_utilization', 0):.2f}%",
            color,
            "🧠"
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Second row of metrics
    st.markdown("""
    <div class="dashboard-metrics" style="margin-top: 20px;">
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Cold Starts
    with col1:
        cold_start_count = metrics.get('cold_starts', 0)
        cold_start_rate = cold_start_count / metrics.get('count', 1) * 100 if metrics.get('count', 0) > 0 else 0
        color = "green" if cold_start_rate < 5 else "orange" if cold_start_rate < 15 else "red"
        render_metric_card(
            "Cold Starts",
            f"{cold_start_count}",
            f"{cold_start_rate:.2f}% of invocations",
            color,
            "❄️"
        )
    
    # Max Duration
    with col2:
        max_duration = metrics.get('max_duration', 0)
        color = "green" if max_duration < 1000 else "orange" if max_duration < 5000 else "red"
        render_metric_card(
            "Max Duration",
            f"{max_duration:.2f} ms",
            "",
            color,
            "🚀"
        )
    
    # Error Count
    with col3:
        error_count = int(metrics.get('count', 0) * metrics.get('error_rate', 0))
        color = "green" if error_count == 0 else "orange" if error_count < 5 else "red"
        render_metric_card(
            "Error Count",
            f"{error_count}",
            f"{metrics.get('error_rate', 0) * 100:.2f}% error rate",
            color,
            "⚠️"
        )
    
    # Memory Size
    with col4:
        memory_size = metrics.get('current_memory', 0)
        if memory_size > 0:
            render_metric_card(
                "Memory Size",
                f"{memory_size} MB",
                "",
                "blue",
                "💾"
            )
        else:
            render_metric_card(
                "Memory Size",
                "N/A",
                "",
                "gray",
                "💾"
            )
    
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_metric_card(title: str, value: Any, subtitle: str = "", color: str = "blue", icon: str = "") -> None:
    """
    Render a metric card with title, value, and optional subtitle.
    
    Args:
        title: Title of the metric
        value: Value to display
        subtitle: Optional subtitle or additional context
        color: Color for the value (green, orange, red, blue, gray)
        icon: Optional icon to display
    """
    # Define colors
    colors = {
        "green": "#28a745",
        "orange": "#fd7e14",
        "red": "#dc3545",
        "blue": "#007bff",
        "gray": "#6c757d"
    }
    
    # Create card with custom HTML/CSS
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
            <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 500;">{title}</div>
            <div style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0.25rem; color: {colors.get(color, colors['blue'])};">{value}</div>
            <div style="font-size: 0.8rem; color: #6c757d;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_performance_recommendations(metrics: Dict[str, Any]) -> None:
    """
    Render performance recommendations based on metrics.
    
    Args:
        metrics: Dictionary with calculated metrics
    """
    if not metrics:
        return
    
    st.markdown("""
    <div class="stcard">
        <h3>💡 Performance Recommendations</h3>
    """, unsafe_allow_html=True)
    
    recommendations = []
    
    # Memory recommendations
    memory_optimization = metrics.get('memory_optimization', {})
    if memory_optimization:
        current_memory = memory_optimization.get('current_memory', 0)
        recommended_memory = memory_optimization.get('recommended_memory', 0)
        potential_savings = memory_optimization.get('potential_savings', 0)
        
        if potential_savings > 0.1:  # More than 10% savings
            recommendations.append({
                'title': '🧠 Memory Optimization',
                'description': f"Consider decreasing memory from {current_memory} MB to {recommended_memory} MB to save costs.",
                'impact': f"Potential savings: {potential_savings * 100:.1f}%",
                'priority': 'high'
            })
        elif recommended_memory > current_memory:
            recommendations.append({
                'title': '🧠 Memory Optimization',
                'description': f"Consider increasing memory from {current_memory} MB to {recommended_memory} MB to improve performance.",
                'impact': "May reduce duration and improve overall performance",
                'priority': 'medium'
            })
    
    # Cold start recommendations
    cold_starts = metrics.get('cold_starts', 0)
    count = metrics.get('count', 0)
    if count > 0 and cold_starts / count > 0.1:  # More than 10% cold starts
        recommendations.append({
            'title': '❄️ Cold Start Optimization',
            'description': "Consider using Provisioned Concurrency to reduce cold starts.",
            'impact': f"Cold starts: {cold_starts} ({cold_starts / count * 100:.1f}% of invocations)",
            'priority': 'high' if cold_starts / count > 0.2 else 'medium'
        })
    
    # Duration recommendations
    p95_duration = metrics.get('p95_duration', 0)
    if p95_duration > 1000:  # More than 1 second
        recommendations.append({
            'title': '⏱️ Duration Optimization',
            'description': "Function duration is high. Consider optimizing code or increasing memory.",
            'impact': f"P95 duration: {p95_duration:.2f} ms",
            'priority': 'medium' if p95_duration < 3000 else 'high'
        })
    
    # Error recommendations
    error_rate = metrics.get('error_rate', 0)
    if error_rate > 0.01:  # More than 1% errors
        recommendations.append({
            'title': '🚨 Error Handling',
            'description': "Function has a high error rate. Review error patterns and implement better error handling.",
            'impact': f"Error rate: {error_rate * 100:.2f}%",
            'priority': 'high' if error_rate > 0.05 else 'medium'
        })
    
    # Display recommendations
    if recommendations:
        for i, rec in enumerate(recommendations):
            priority_colors = {
                'high': {
                    'bg': '#fdeded',
                    'border': '#dc3545',
                    'icon': '🔴'
                },
                'medium': {
                    'bg': '#fff3e0',
                    'border': '#fd7e14',
                    'icon': '🟠'
                },
                'low': {
                    'bg': '#e6f4ea',
                    'border': '#28a745',
                    'icon': '🟢'
                }
            }.get(rec['priority'], {
                'bg': '#f8f9fa',
                'border': '#6c757d',
                'icon': 'ℹ️'
            })
            
            st.markdown(
                f"""
                <div style="
                    border-left: 4px solid {priority_colors['border']};
                    padding: 1.2rem;
                    margin-bottom: 1.2rem;
                    background-color: {priority_colors['bg']};
                    border-radius: 8px;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.05);
                    animation: fadeIn 0.5s ease-out forwards;
                    animation-delay: {i * 0.1}s;
                    opacity: 0;
                ">
                    <h4 style="margin-top: 0; display: flex; align-items: center; gap: 8px; font-size: 1.2rem;">
                        {rec['title']}
                        <span style="
                            font-size: 0.8rem;
                            background-color: {priority_colors['border']};
                            color: white;
                            padding: 3px 10px;
                            border-radius: 20px;
                            text-transform: uppercase;
                            letter-spacing: 0.5px;
                        ">{rec['priority']}</span>
                    </h4>
                    <p style="margin-bottom: 0.8rem; font-size: 1rem; line-height: 1.5;">{rec['description']}</p>
                    <p style="
                        font-size: 0.9rem;
                        color: #555;
                        margin-bottom: 0;
                        display: flex;
                        align-items: center;
                        gap: 5px;
                        background-color: rgba(0,0,0,0.03);
                        padding: 8px 12px;
                        border-radius: 6px;
                    ">
                        <strong>Impact:</strong> {rec['impact']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.markdown("""
        <div style="
            padding: 2rem;
            text-align: center;
            background-color: #e6f4ea;
            border-radius: 8px;
            border: 1px solid #d4edda;
            margin: 1rem 0;
            animation: fadeIn 0.5s ease-out forwards;
        ">
            <span style="font-size: 3rem;">✅</span>
            <h4 style="margin-top: 1rem; color: #28a745; font-size: 1.4rem;">All Good!</h4>
            <p style="color: #555; font-size: 1.1rem;">No performance recommendations at this time.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
