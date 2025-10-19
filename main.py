"""
AgustoGPT - AI Research Assistant
Simple Streamlit Interface with Dummy Data
"""

import streamlit as st
from datetime import datetime
import time
import os

# Page Configuration
st.set_page_config(
    page_title="AgustoGPT - AI Research Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
def load_css():
    """Load custom CSS styling"""
    css_file = "styles/main.css"
    if os.path.exists(css_file):
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Initialize Session State
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'search_mode' not in st.session_state:
    st.session_state.search_mode = 'auto'

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"id": "1", "title": "What are the key risks in the electricity sector?", "date": "Jan 15, 2025"},
        {"id": "2", "title": "Compare banking performance 2024 vs 2025", "date": "Jan 14, 2025"},
        {"id": "3", "title": "Telecommunications market outlook", "date": "Jan 13, 2025"},
        {"id": "4", "title": "Oil & Gas Investment trends", "date": "Jan 12, 2025"},
    ]

if 'filters' not in st.session_state:
    st.session_state.filters = {
        'industry_sector': '',
        'report_year': '',
        'report_type': ''
    }

# Dummy Data
DUMMY_RESPONSE = """Based on our analysis of the Nigerian electricity sector, the main challenges facing the industry in 2025 include:

**1. Infrastructure Deficits:** Nigeria continues to face significant generation, transmission, and distribution infrastructure gaps. The country's installed capacity remains below demand requirements, with frequent grid collapses affecting power supply reliability.

**2. Revenue Collection Challenges:** Distribution companies continue to struggle with collection efficiency, averaging around 67% in 2024. This impacts their ability to invest in network improvements and maintenance.

**3. Regulatory Uncertainty:** Policy inconsistencies and regulatory uncertainty continue to deter long-term investment commitments from international players. The lack of clear regulatory frameworks creates additional risks for investors.

**4. Gas Supply Issues:** The power sector continues to face challenges with gas supply reliability, affecting generation capacity utilization.

More detailed analysis available in our comprehensive reports..."""

DUMMY_SOURCES = [
    {
        "title": "2025 Nigerian Electricity Supply Industry Report - Page 15",
        "excerpt": "Infrastructure deficits remain the primary constraint to sector growth, with generation capacity utilization below 60%...",
        "report": "Nigerian Electricity Supply Industry Report 2025",
        "page": 15
    },
    {
        "title": "2025 Nigerian Electricity Supply Industry Report - Page 32",
        "excerpt": "DisCos reported average collection efficiency of 67% in 2024, indicating persistent revenue challenges...",
        "report": "Nigerian Electricity Supply Industry Report 2025",
        "page": 32
    },
    {
        "title": "Nigerian Power Sector Outlook 2025 - Page 8",
        "excerpt": "Regulatory uncertainty continues to deter long-term investment commitments from international players...",
        "report": "Nigerian Power Sector Outlook 2025",
        "page": 8
    }
]

# Filter Options
INDUSTRY_SECTORS = ['', 'Electricity', 'Banking', 'Telecommunications', 'Oil & Gas', 'Insurance']
REPORT_YEARS = ['', '2025', '2024', '2023', '2022']
REPORT_TYPES = ['', 'Industry Report', 'Sector Outlook', 'Market Analysis', 'Risk Assessment']

# Functions
def get_dummy_response(query, search_mode):
    """
    Simulate API call to backend
    In production, this will call your Azure Function App
    """
    # Simulate processing time
    time.sleep(2)
    
    return {
        "response": DUMMY_RESPONSE,
        "sources": DUMMY_SOURCES,
        "timestamp": datetime.now().isoformat()
    }

def display_message(message):
    """Display a single message (user or assistant)"""
    if message['type'] == 'user':
        st.markdown(f"""
        <div class="user-message">
            <div class="message-label">You asked:</div>
            <div class="message-content">{message['content']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            <div class="message-label">AgustoGPT:</div>
            <div class="message-content">{message['content']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display sources
        if 'sources' in message and message['sources']:
            st.markdown('<div class="sources-container"><h4>Sources from your reports:</h4>', unsafe_allow_html=True)
            for source in message['sources']:
                st.markdown(f"""
                <div class="source-item">
                    <div class="source-title">{source['title']}</div>
                    <div class="source-excerpt">{source['excerpt']}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ===== SIDEBAR =====
with st.sidebar:
    # Logo and Title
    st.markdown("""
    <div class="sidebar-header">
        <div class="logo-container">
            <div class="logo-icon">
                <div class="logo-square gray"></div>
                <div class="logo-square navy"></div>
                <div class="logo-square navy"></div>
                <div class="logo-square gray"></div>
            </div>
            <span class="logo-text">AgustoGPT</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Search Mode Selection
    st.subheader("Search Mode")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Auto", use_container_width=True, 
                    type="primary" if st.session_state.search_mode == 'auto' else "secondary"):
            st.session_state.search_mode = 'auto'
    with col2:
        if st.button("🎯 Tailored", use_container_width=True,
                    type="primary" if st.session_state.search_mode == 'tailored' else "secondary"):
            st.session_state.search_mode = 'tailored'
    
    # Search Mode Description
    if st.session_state.search_mode == 'auto':
        st.info("**Auto Search:** Intelligently finding the most relevant information from all reports.")
    else:
        st.success("**Tailored Search:** Search within selected scope using filters below.")
    
    st.markdown("---")
    
    # Filters (only show in tailored mode)
    if st.session_state.search_mode == 'tailored':
        st.subheader("Report Filters")
        
        st.session_state.filters['industry_sector'] = st.selectbox(
            "Industry Sector:",
            INDUSTRY_SECTORS
        )
        
        st.session_state.filters['report_year'] = st.selectbox(
            "Report Year:",
            REPORT_YEARS
        )
        
        st.session_state.filters['report_type'] = st.selectbox(
            "Report Type:",
            REPORT_TYPES
        )
        
        # Current Selection
        st.markdown("**Current Selection**")
        st.markdown("""
        <div class="selected-report">Nigerian Electricity (2025)</div>
        <div class="selected-report">Banking Sector (2025)</div>
        <div class="selected-report-more">+ 12 more reports</div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Chat History
    st.subheader("Chat History")
    for chat in st.session_state.chat_history:
        if st.button(chat['title'], key=chat['id'], use_container_width=True):
            st.info(f"Loading conversation: {chat['title']}")
            # In production, load the actual chat

# ===== MAIN CONTENT =====
st.markdown('<div class="main-header">AgustoGPT - AI Research Assistant</div>', unsafe_allow_html=True)

# Chat Container
chat_container = st.container()

with chat_container:
    if len(st.session_state.messages) == 0:
        # Welcome Message
        st.markdown("""
        <div class="welcome-container">
            <div class="welcome-icon">🔍</div>
            <h2>Welcome to AgustoGPT</h2>
            <p>Ask questions about your reports and get intelligent insights.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display all messages
        for message in st.session_state.messages:
            display_message(message)

# Input Area
st.markdown("---")

# Query Input
col1, col2 = st.columns([5, 1])

with col1:
    query = st.text_input(
        "Ask a question",
        placeholder="Ask a question about your reports...",
        label_visibility="collapsed",
        key="query_input"
    )

with col2:
    submit = st.button("Ask", use_container_width=True, type="primary")

# Handle Submit
if submit and query:
    # Add user message
    st.session_state.messages.append({
        "type": "user",
        "content": query,
        "timestamp": datetime.now().isoformat()
    })
    
    # Show loading
    with st.spinner("AgustoGPT is thinking..."):
        # Get response (dummy data for now)
        response = get_dummy_response(query, st.session_state.search_mode)
    
    # Add assistant message
    st.session_state.messages.append({
        "type": "assistant",
        "content": response['response'],
        "sources": response['sources'],
        "timestamp": response['timestamp']
    })
    
    # Rerun to display new messages
    st.rerun()

# Footer with Brand Bar
st.markdown("""
<div class="brand-bar">
    <div class="brand-bar-navy"></div>
    <div class="brand-bar-gray"></div>
</div>
""", unsafe_allow_html=True)

# Future Azure Function App Integration Comment
# """
# FUTURE INTEGRATION:
# Replace get_dummy_response() function with actual API call:

# import requests
# import os

# API_ENDPOINT = os.getenv('AZURE_FUNCTION_URL', 'https://your-app.azurewebsites.net/api')

# def call_azure_function(query, search_mode, filters=None):
#     response = requests.post(
#         f"{API_ENDPOINT}/chat/query",
#         json={
#             "query": query,
#             "search_mode": search_mode,
#             "filters": filters
#         }
#     )
#     return response.json()
# """