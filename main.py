"""
AgustoGPT - AI Research Assistant
Simple Streamlit Interface with Dummy Data
"""

import streamlit as st
from datetime import datetime
import time
import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AgustoGPT - AI Research Assistant",
    page_icon=":material/search:",
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
        'report_year': ''
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

# Filter Options - Aligned with Azure Search Index
INDUSTRY_SECTORS = ['', 'Oil & Gas Upstream', 'Oil & Gas Downstream', 'Insurance', 'Banking', 'Electricity', 'Telecommunications']
REPORT_YEARS = ['', '2025', '2024', '2023', '2022', '2021']

# API Configuration
AGENT_API_URL = os.getenv('AGENT_API_URL', 'http://localhost:8000')

# Functions
def call_agent_api(query: str, search_mode: str, filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Call the agent API to get response
    Supports both auto and tailored search modes
    """
    try:
        # Prepare payload
        payload = {
            "user_query": query
        }

        # Add filters for tailored search
        if search_mode == 'tailored' and filters:
            # Add year filter if specified
            if filters.get('report_year'):
                payload['year_to_search'] = int(filters['report_year'])
            else:
                payload['year_to_search'] = datetime.now().year

            # Add industry filter if specified
            if filters.get('industry_sector'):
                payload['industry_to_search'] = filters['industry_sector']
            else:
                payload['industry_to_search'] = ""
        else:
            # Auto search - use current year and empty industry
            payload['year_to_search'] = datetime.now().year
            payload['industry_to_search'] = ""

        # Make API request
        response = requests.post(
            f"{AGENT_API_URL}/query",
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        # Parse response
        data = response.json()

        # Format sources for UI
        sources = []
        if 'document_information' in data and data['document_information']:
            for doc in data['document_information']:
                # Create readable title
                doc_name = doc.get('document_name', 'Unknown Document')
                page_num = doc.get('page_number', 0)

                sources.append({
                    "title": f"{doc_name} - Page {page_num}",
                    "excerpt": f"From {doc.get('industry', 'N/A')} ({doc.get('year', 'N/A')}), Chunk {doc.get('chunk_index', 0)}",
                    "report": doc_name,
                    "page": page_num
                })

        return {
            "response": data.get('response', 'No response generated'),
            "sources": sources,
            "timestamp": data.get('current_date', datetime.now().isoformat())
        }

    except requests.exceptions.RequestException as e:
        # Handle API errors gracefully
        return {
            "response": f"Error connecting to agent API: {str(e)}\n\nPlease ensure the agent API is running at {AGENT_API_URL}",
            "sources": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "response": f"Unexpected error: {str(e)}",
            "sources": [],
            "timestamp": datetime.now().isoformat()
        }

def get_dummy_response(query, search_mode):
    """
    Simulate API call to backend (DEPRECATED - for fallback only)
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
        # Display assistant message with markdown support
        # Use a container and add custom class via HTML wrapper
        st.markdown('<div class="assistant-msg-start"></div>', unsafe_allow_html=True)
        st.markdown('<div class="message-label assistant-label">AgustoGPT:</div>', unsafe_allow_html=True)

        # Render markdown content with proper formatting
        st.markdown(message['content'])

        st.markdown('<div class="assistant-msg-end"></div>', unsafe_allow_html=True)

        # Display sources - grouped by report
        if 'sources' in message and message['sources']:
            # Group sources by report name
            grouped_sources = {}
            for source in message['sources']:
                report_name = source.get('report', 'Unknown Report')
                if report_name not in grouped_sources:
                    grouped_sources[report_name] = {
                        'pages': [],
                        'excerpt': source.get('excerpt', '')
                    }
                page_num = source.get('page', 0)
                if page_num not in grouped_sources[report_name]['pages']:
                    grouped_sources[report_name]['pages'].append(page_num)

            # Display grouped sources
            st.markdown('<div class="sources-header">Sources from your reports:</div>', unsafe_allow_html=True)
            for report_name, data in grouped_sources.items():
                pages = sorted(data['pages'])
                pages_text = ', '.join([f"Page {p}" for p in pages])

                st.markdown("""
                    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined"
                        rel="stylesheet" />
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="source-item">
                    <div class="source-report-name">
                        <span class="material-symbols-outlined source-icon">description</span>
                        {report_name}
                    </div>
                    <div class="source-pages">{pages_text}</div>
                </div>
                """, unsafe_allow_html=True)


# ===== SIDEBAR =====
with st.sidebar:
    # Logo and Title (commented out)
    # st.markdown("""
    # <div class="sidebar-header">
    #     <div class="logo-container">
    #         <div class="logo-icon">
    #             <div class="logo-square gray"></div>
    #             <div class="logo-square navy"></div>
    #             <div class="logo-square navy"></div>
    #             <div class="logo-square gray"></div>
    #         </div>
    #         <span class="logo-text">AgustoGPT</span>
    #     </div>
    # </div>
    # """, unsafe_allow_html=True)

    # st.markdown("---")

    # Search Mode Selection
    st.subheader("Search Mode")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Auto", icon=":material/search:", use_container_width=True,
                    type="primary" if st.session_state.search_mode == 'auto' else "secondary"):
            st.session_state.search_mode = 'auto'
            st.rerun()
    with col2:
        if st.button("Tailored", icon=":material/my_location:", use_container_width=True,
                    type="primary" if st.session_state.search_mode == 'tailored' else "secondary"):
            st.session_state.search_mode = 'tailored'
            st.rerun()
    
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

        # Show selected filters
        st.markdown("**Active Filters**")
        active_filters = []
        if st.session_state.filters.get('industry_sector'):
            active_filters.append(st.session_state.filters['industry_sector'])
        if st.session_state.filters.get('report_year'):
            active_filters.append(st.session_state.filters['report_year'])

        if active_filters:
            for filter_val in active_filters:
                st.markdown(f'<div class="selected-report">{filter_val}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="selected-report-more">No filters selected</div>', unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Chat History
    st.subheader("Chat History")
    for chat in st.session_state.chat_history:
        if st.button(chat['title'], key=chat['id'], use_container_width=True):
            st.info(f"Loading conversation: {chat['title']}")
            # In production, load the actual chat

# ===== MAIN CONTENT =====
# st.markdown('<div class="main-header">AgustoGPT - AI Research Assistant</div>', unsafe_allow_html=True)

# Chat Container
chat_container = st.container()

with chat_container:
    if len(st.session_state.messages) == 0:
        # Welcome Message
        st.markdown("""
        <div class="welcome-container">
            <h2>Welcome to AgustoGPT</h2>
            <p>Your AI Research Assistant, Ask questions about your reports and get intelligent insights.</p>
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
        # Get response from agent API
        response = call_agent_api(
            query,
            st.session_state.search_mode,
            st.session_state.filters
        )
    
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