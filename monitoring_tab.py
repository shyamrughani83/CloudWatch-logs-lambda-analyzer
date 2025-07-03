    # Lambda Monitoring tab
    with tab5:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        render_lambda_monitoring(st.session_state.lambda_client)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Settings tab
    with tab6:
