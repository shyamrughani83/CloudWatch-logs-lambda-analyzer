"""
Theme Toggle component for CloudWatch Logs Analyzer.
Provides a toggle button to switch between light and dark themes.
"""

import streamlit as st
import os

def render_theme_toggle():
    """
    Render a theme toggle button in the sidebar.
    
    This function creates a toggle button that allows users to switch
    between light and dark themes.
    """
    # Initialize theme in session state if not present
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    # Create a container for the theme toggle
    with st.sidebar:
        st.markdown("### 🎨 Appearance")
        
        # Create columns for the toggle
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Display the current theme icon
            if st.session_state.theme == 'light':
                st.markdown("☀️")
            else:
                st.markdown("🌙")
        
        with col2:
            # Create the toggle button
            if st.button("Toggle Dark Mode" if st.session_state.theme == 'light' else "Toggle Light Mode"):
                # Toggle the theme
                st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
                st.experimental_rerun()
    
    # Apply the selected theme
    apply_theme(st.session_state.theme)

def apply_theme(theme):
    """
    Apply the selected theme by injecting the appropriate CSS.
    
    Args:
        theme (str): The theme to apply ('light' or 'dark')
    """
    if theme == 'dark':
        # Load dark theme CSS
        css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static/dark_theme.css")
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Load light theme CSS (default)
        css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static/style.css")
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
