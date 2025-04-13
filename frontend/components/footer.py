import streamlit as st
import datetime

def render_footer():
    """
    Renders the application footer with copyright information and helpful links.
    """
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Contact Us")
        st.markdown("📧 admissions@university.edu")
        st.markdown("📞 (555) 123-4567")
    
    with col2:
        st.markdown("#### Quick Links")
        st.markdown("[University Homepage](https://example.com)")
        st.markdown("[Student Resources](https://example.com/resources)")
        st.markdown("[FAQ](https://example.com/faq)")
    
    with col3:
        st.markdown("#### Help & Support")
        st.markdown("[Schedule a Counseling Session](https://example.com/counseling)")
        st.markdown("[Technical Support](https://example.com/support)")
    
    current_year = datetime.datetime.now().year
    st.markdown(f"<p style='text-align: center; color: gray;'>© {current_year} University Admissions Portal. All rights reserved.</p>", unsafe_allow_html=True)