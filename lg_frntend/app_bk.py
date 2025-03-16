import streamlit as st
import requests
import json

# Backend API URL
BACKEND_URL = "http://server1.sureshwizard.com:4001"  # Update with your actual backend URL

# Streamlit Page Configuration
st.set_page_config(page_title="LegalAI", page_icon="⚖️", layout="wide")

# Sidebar Navigation
st.sidebar.title("LegalAI Navigation")
page = st.sidebar.radio("Go to", ["📄 Upload Document", "💡 Ask LegalAI", "⚠️ Contract Risk Analysis"])

# 1️⃣ 📄 Upload PDF Document for Summarization
if page == "📄 Upload Document":
    st.title("📄 Upload Legal Document for AI Summarization")
    uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])

    if uploaded_file is not None:
        try:
            st.info("Processing document, please wait...")

            # ✅ Convert file into proper format for API request
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            
            response = requests.post(f"{BACKEND_URL}/upload/", files=files)

            if response.status_code == 200:
                data = response.json()
                st.success("✅ Document processed successfully!")
                st.subheader("Summary:")
                st.write(data.get("summary", "⚠️ No summary returned."))
            else:
                st.error(f"❌ Error uploading document! (HTTP {response.status_code})")
                st.write(response.text)  # Display backend error message

        except Exception as e:
            st.error(f"⚠️ An error occurred: {str(e)}")

# 2️⃣ 💡 Ask LegalAI a Question
elif page == "💡 Ask LegalAI":
    st.title("💡 Ask LegalAI a Question")
    question = st.text_area("Enter your legal question:")

    if st.button("Submit Question"):
        if question:
            with st.spinner("Fetching legal insights..."):
                response = requests.post(f"{BACKEND_URL}/query/", json={"question": question})

            if response.status_code == 200:
                data = response.json()
                st.success("✅ Answer retrieved successfully!")
                st.subheader("LegalAI Answer:")
                st.write(data.get("answer", "⚠️ No answer returned."))
            else:
                st.error(f"❌ Error retrieving answer! (HTTP {response.status_code})")
                st.write(response.text)

# 3️⃣ ⚠️ Contract Risk Analysis
elif page == "⚠️ Contract Risk Analysis":
    st.title("⚠️ Contract Risk Analysis")
    contract_file = st.file_uploader("Upload a contract PDF", type=["pdf"])

    if contract_file is not None:
        try:
            st.info("Analyzing contract, please wait...")

            # ✅ Convert file into proper format for API request
            files = {"file": (contract_file.name, contract_file.getvalue(), "application/pdf")}
            
            response = requests.post(f"{BACKEND_URL}/contract-risk/", files=files)

            if response.status_code == 200:
                data = response.json()
                st.success("✅ Contract analysis complete!")
                st.subheader("Risk Assessment:")
                st.write(data.get("risks", "⚠️ No risks found."))
            else:
                st.error(f"❌ Error analyzing contract! (HTTP {response.status_code})")
                st.write(response.text)

        except Exception as e:
            st.error(f"⚠️ An error occurred: {str(e)}")

