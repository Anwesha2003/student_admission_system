import streamlit as st

def render_header(title="University Admissions Portal", subtitle=None):
    """
    Renders the application header with title and optional subtitle.
    
    Args:
        title: The main title to display
        subtitle: Optional subtitle or description
    """
    st.markdown(f"<h1 style='text-align: center;'>{title}</h1>", unsafe_allow_html=True)
    
    if subtitle:
        st.markdown(f"<h3 style='text-align: center;'>{subtitle}</h3>", unsafe_allow_html=True)
    
    # Display user information if logged in
    if "user_role" in st.session_state and st.session_state.user_role:
        if st.session_state.user_role == "student":
            st.info(f"Logged in as Student (ID: {st.session_state.student_id})")
        elif st.session_state.user_role == "admin":
            st.info("Logged in as Administrator")
    
    st.markdown("---")