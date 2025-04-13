import streamlit as st
import os
from pathlib import Path
from PIL import Image
import uuid
from streamlit_option_menu import option_menu

def render_sidebar():
    """
    Renders the application sidebar with navigation options based on user role.
    """
    with st.sidebar:
         try:
            script_dir = Path(__file__).parent
         except NameError:
            script_dir = Path.cwd()
    
    image_path = script_dir / "static" / "university_logo.png"
    
    try:
            st.sidebar.image(str(image_path), width=300)
           # Uncomment for debugging if needed
           # st.sidebar.write(f"Attempting to load from: {image_path}")
    except Exception as e:
        # Uncomment for debugging if needed
        # st.sidebar.error(f"Error loading image: {e}")
            st.sidebar.title("University")
        
    st.title("Admission Portal")
        
        # Navigation options based on role
    if "user_role" in st.session_state:
            if st.session_state["user_role"] == "admin":
                selected = option_menu(
                    "Admin Navigation", 
                    ["Dashboard", "Review Applications", "Document Verification", "Loan Requests"],
                    icons=["bar-chart", "file-earmark-text", "file-earmark-check", "currency-dollar"],
                    menu_icon="cast", 
                    default_index=0
                )
                
                # Add logout button at the bottom
                st.markdown("---")
                if st.button("Logout", key="btn_logout_admin"):
                    for key in ["user_role", "username", "student_id"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
                
                return selected
                
            elif st.session_state["user_role"] == "student":
                selected = option_menu(
                    "Student Navigation", 
                    ["My Dashboard", "Application Status", "My Documents", "Financial Aid"],
                    icons=["house", "file-earmark-text", "file-earmark-check", "currency-dollar"],
                    menu_icon="cast", 
                    default_index=0
                )
                
                # Add logout button at the bottom
                st.markdown("---")
                if st.button("Logout", key="btn_logout_student"):
                    for key in ["user_role", "username", "student_id"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
                
                return selected
        
        # Default return for when no user is logged in
    return None