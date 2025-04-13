import streamlit as st
import chromadb
import os
import hashlib
import secrets
import uuid
from chromadb.utils import embedding_functions
import pandas as pd
from datetime import datetime

# Initialize ChromaDB for authentication
def initialize_auth_db():
    # Create a persistent client
    client = chromadb.PersistentClient("./chromadb_data")
    
    # Define a simple embedding function (not using real embeddings since this is for auth)
    ef = embedding_functions.DefaultEmbeddingFunction()
    
    # Create or get collections for users
    try:
        users_collection = client.get_collection("users")
    except:
        users_collection = client.create_collection(
            name="users",
            embedding_function=ef,
            metadata={"description": "University portal users"}
        )
    
    return client, users_collection

# Password hashing with salt
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Hash password with salt
    hash_obj = hashlib.sha256((password + salt).encode())
    password_hash = hash_obj.hexdigest()
    
    return password_hash, salt

# User Authentication
def authenticate_user(username, password, users_collection):
    # Query the collection for the username
    results = users_collection.get(
        where={"username": username},
        include=["metadatas"]
    )
    
    if not results["ids"]:
        return False, None
    
    user_data = results["metadatas"][0]
    stored_hash = user_data["password_hash"]
    salt = user_data["salt"]
    
    # Hash the provided password with the stored salt
    calc_hash, _ = hash_password(password, salt)
    
    if calc_hash == stored_hash:
        return True, user_data
    
    return False, None

# Register new user
def register_user(user_data, users_collection):
    # Check if username exists
    results = users_collection.get(
        where={"username": user_data["username"]},
    )
    
    if results["ids"]:
        return False, "Username already exists"
    
    # Hash password
    password_hash, salt = hash_password(user_data["password"])
    
    # Generate user ID
    user_id = str(uuid.uuid4())
    student_id = f"S{int(pd.util.hash_pandas_object(pd.Series([user_data['email']])).iloc[0])}"
    
    # Create metadata with all user info
    metadata = {
        "username": user_data["username"],
        "email": user_data["email"],
        "first_name": user_data["first_name"],
        "last_name": user_data["last_name"],
        "password_hash": password_hash,
        "salt": salt,
        "role": user_data["role"],
        "phone": user_data.get("phone", ""),
        "created_at": datetime.now().isoformat(),
        "student_id": student_id if user_data["role"] == "student" else ""
    }
    
    # Add dummy embedding (since we're not really using embeddings for this purpose)
    users_collection.add(
        ids=[user_id],
        embeddings=[[0.0] * 1536],  # Dummy embedding
        metadatas=[metadata]
    )
    
    return True, student_id if user_data["role"] == "student" else None

# Create seed users if they don't exist
def create_seed_users(users_collection):
    # Check if admin exists
    results = users_collection.get(
        where={"username": "admin"},
    )
    
    if not results["ids"]:
        admin_data = {
            "username": "admin",
            "email": "admin@university.edu",
            "first_name": "Admin",
            "last_name": "User",
            "password": "admin123",
            "role": "admin",
            "phone": "555-1234"
        }
        register_user(admin_data, users_collection)
    
    # Check if demo student exists
    results = users_collection.get(
        where={"username": "student"},
    )
    
    if not results["ids"]:
        student_data = {
            "username": "student",
            "email": "student@university.edu",
            "first_name": "Demo",
            "last_name": "Student",
            "password": "student123",
            "role": "student",
            "phone": "555-5678"
        }
        register_user(student_data, users_collection)

# Login page
def login_page(users_collection):
    st.title("University Portal Login")
    
    # Create seed users (ensure we have demo accounts)
    create_seed_users(users_collection)
    
    # Create columns for a cleaner layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="btn_login"):
            if username and password:
                authenticated, user_data = authenticate_user(username, password, users_collection)
                if authenticated:
                    st.session_state["user_role"] = user_data["role"]
                    st.session_state["username"] = username
                    
                    if user_data["role"] == "student":
                        st.session_state["student_id"] = user_data["student_id"]
                    
                    st.success(f"Logged in as {user_data['role'].capitalize()}")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter both username and password")
    
    with col2:
        st.subheader("Don't have an account?")
        st.info("Register as a new student to start your application process")
        
        if st.button("Register as Student"):
            st.session_state["show_registration"] = True
    
    # Simple registration form that appears when button is clicked
    if st.session_state.get("show_registration", False):
        st.subheader("Student Registration")
        
        reg_col1, reg_col2 = st.columns(2)
        
        with reg_col1:
            first_name = st.text_input("First Name")
            email = st.text_input("Email Address")
            username = st.text_input("Username")
            new_password = st.text_input("Create Password", type="password")
        
        with reg_col2:
            last_name = st.text_input("Last Name")
            phone = st.text_input("Phone Number")
            confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Complete Registration"):
            # Validate inputs
            if not first_name or not last_name or not email or not username or not new_password:
                st.error("Please fill out all required fields")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                # Register the user in ChromaDB
                user_data = {
                    "username": username,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "password": new_password,
                    "role": "student",
                    "phone": phone
                }
                
                success, student_id = register_user(user_data, users_collection)
                
                if success:
                    st.session_state["user_role"] = "student"
                    st.session_state["username"] = username
                    st.session_state["student_id"] = student_id
                    st.success("Registration successful! You are now logged in.")
                    st.rerun()
                else:
                    st.error(f"Registration failed: {student_id}")

# Add logout functionality to sidebar
def add_logout_to_sidebar():
    if "user_role" in st.session_state:
        st.sidebar.write(f"Logged in as: {st.session_state.get('username', 'User')}")
        st.sidebar.write(f"Role: {st.session_state.get('user_role', 'Unknown').capitalize()}")
        
    