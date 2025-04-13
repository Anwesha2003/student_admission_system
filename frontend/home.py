import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import requests
import uuid
from components.sidebar import render_sidebar
from components.header import render_header
from components.footer import render_footer
from streamlit_option_menu import option_menu
from components.login import login_page, add_logout_to_sidebar, initialize_auth_db

# Configure the page
st.set_page_config(
    page_title="University Admissions Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for chat if needed
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False

# Initialize ChromaDB for authentication
client, users_collection = initialize_auth_db()

# Check if user is logged in
if "user_role" not in st.session_state:
    # User is not logged in, show login page
    login_page(users_collection)
else:
    # User is logged in, show normal content
    
    # Modified sidebar to include logout
    add_logout_to_sidebar()
    selected_page = render_sidebar()
    
    # Main page content
    render_header("Welcome to University Admissions Portal", "Your gateway to academic excellence")
    
    # Display welcome message with username
    st.write(f"Welcome, {st.session_state.get('username', 'User')}!")
    
    # Home page content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Start Your Academic Journey")
        st.markdown("""
            Welcome to our University Admissions Portal! This platform streamlines the entire admissions process, 
            from application submission to enrollment. Our AI-powered system provides personalized guidance 
            at every step of your journey.
            
            ### What you can do:
            - Complete your admission application
            - Upload required documents
            - Track your application status
            - Apply for financial aid and scholarships
            - Get personalized counseling from our AI advisors
        """)
        
        # Call-to-action buttons - adjusted based on user role
        col_a, col_b = st.columns(2)
        with col_a:
            if st.session_state["user_role"] == "student":
                if st.button("My Application", use_container_width=True, key="btn_my_application"):
                    switch_page("admission form")
            elif st.session_state["user_role"] == "admin":
                if st.button("Admin Dashboard", use_container_width=True, key="btn_admin_dashboard"):
                    switch_page("admin dashboard")
            else:
                if st.button("Get Started", use_container_width=True, key="btn_get_started"):
                    switch_page("pages/admission_form.py")
        
        with col_b:
            if st.button("Learn More", use_container_width=True, key="btn_learn_more"):
                st.markdown("[University Website](https://example.com)", unsafe_allow_html=True)
    
    with col2:
        st.subheader("Important Dates")
        
        st.info("**Application Deadline**\nFall Semester: June 30, 2025")
        st.info("**Document Submission**\nWithin 14 days of application")
        st.info("**Admission Results**\nWithin 30 days of complete application")
        st.info("**Financial Aid Deadline**\nJuly 15, 2025")
        
        st.markdown("---")
        
        st.subheader("Need Help?")
        st.markdown("""
            Our AI-powered Student Counselor is available 24/7 to answer your questions.
        """)
        
        if st.button("Chat with Counselor", use_container_width=True, key="btn_chat_counselor"):
            st.session_state.show_chat = True
    
    # Display chat interface if requested
    if st.session_state.get("show_chat", False):
        with st.container():
            st.subheader("Student Counselor")
            
            if "messages" not in st.session_state:
                st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm your AI Student Counselor. How can I help with your admission process today?"}]
            
            # Display chat messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Chat input
            prompt = st.chat_input("Ask a question about admissions...")
            if prompt:
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Display user message in chat
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Add assistant response (would connect to backend in production)
                with st.chat_message("assistant"):
                    response = "Thank you for your question. Our admissions team will be processing applications on a rolling basis. You can expect to hear back within 2-3 weeks after submitting all required documents."
                    st.markdown(response)
                
                # Add assistant message to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Render footer
    render_footer()

# Add a debug expander in development
if st.session_state.get("debug_mode", False) or st.experimental_get_query_params().get("debug", ["false"])[0].lower() == "true":
    with st.expander("Debug Information"):
        st.write("Session State:", st.session_state)
        debug_col1, debug_col2, debug_col3 = st.columns(3)
        with debug_col1:
            if st.button("Set Admin Role", key="debug_set_admin"):
                st.session_state["user_role"] = "admin"
                st.session_state["username"] = "admin"
                st.rerun()
        with debug_col2:
            if st.button("Set Student Role", key="debug_set_student"):
                st.session_state["user_role"] = "student"
                st.session_state["username"] = "student"
                st.session_state["student_id"] = "S12345"
                st.rerun()
        with debug_col3:
            if st.button("Clear Role", key="debug_clear_role"):
                for key in ["user_role", "username", "student_id"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()