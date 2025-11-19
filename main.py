"""
AgustoGPT - AI Research Assistant
Simple Streamlit Interface with Dummy Data
"""

import streamlit as st
from datetime import datetime
import time
import os
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from st_copy import copy_button
import re
from azure_storage import storage_manager

# Load environment variables
load_dotenv()

# Helper Functions
def stream_text(text: str, delay: float = 0.02):
    """
    Generator function to stream text character by character
    """
    for char in text:
        yield char
        time.sleep(delay)

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

if 'chat_id' not in st.session_state:
    st.session_state.chat_id = None

if 'user_id' not in st.session_state:
    # Use a placeholder user ID - in production, this would come from authentication
    st.session_state.user_id = os.getenv('DEFAULT_USER_ID', 'default_user')

if 'chat_history' not in st.session_state:
    # Load chat history from Azure if available
    if storage_manager.enabled:
        st.session_state.chat_history = storage_manager.list_user_chats(st.session_state.user_id, limit=20)
    else:
        # Fallback to dummy data if Azure is not configured
        st.session_state.chat_history = [
            {"chat_id": "1", "title": "What are the key risks in the electricity sector?", "created_at": "2025-01-15"},
            {"chat_id": "2", "title": "Compare banking performance 2024 vs 2025", "created_at": "2025-01-14"},
            {"chat_id": "3", "title": "Telecommunications market outlook", "created_at": "2025-01-13"},
            {"chat_id": "4", "title": "Oil & Gas Investment trends", "created_at": "2025-01-12"},
        ]

if 'filters' not in st.session_state:
    st.session_state.filters = {
        'industry_sector': '',
        'report_year': ''
    }

if 'storage_enabled' not in st.session_state:
    st.session_state.storage_enabled = storage_manager.enabled

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

def save_current_chat():
    """Save current chat session to Azure Storage"""
    if not storage_manager.enabled or not st.session_state.messages:
        return False
    
    # Generate chat ID if not exists
    if not st.session_state.chat_id:
        st.session_state.chat_id = storage_manager.generate_chat_id()
    
    # Prepare metadata
    metadata = {
        'search_mode': st.session_state.search_mode,
        'filters': st.session_state.filters
    }
    
    # Save to Azure
    success = storage_manager.save_chat_session(
        chat_id=st.session_state.chat_id,
        user_id=st.session_state.user_id,
        messages=st.session_state.messages,
        metadata=metadata
    )
    
    if success:
        # Update chat history in session state
        st.session_state.chat_history = storage_manager.list_user_chats(
            st.session_state.user_id, 
            limit=20
        )
    
    return success

def load_chat_session(chat_id: str):
    """Load a chat session from Azure Storage"""
    if not storage_manager.enabled:
        return False
    
    chat_data = storage_manager.load_chat_session(
        chat_id=chat_id,
        user_id=st.session_state.user_id
    )
    
    if chat_data:
        st.session_state.messages = chat_data.get('messages', [])
        st.session_state.chat_id = chat_id
        
        # Restore metadata if available
        metadata = chat_data.get('metadata', {})
        if 'search_mode' in metadata:
            st.session_state.search_mode = metadata['search_mode']
        if 'filters' in metadata:
            st.session_state.filters = metadata['filters']
        
        return True
    return False

def start_new_chat():
    """Start a new chat session"""
    st.session_state.messages = []
    st.session_state.chat_id = storage_manager.generate_chat_id() if storage_manager.enabled else None
    st.session_state.search_mode = 'auto'
    st.session_state.filters = {
        'industry_sector': '',
        'report_year': ''
    }

def display_message(message):
    """Display a single message (user or assistant)"""
    role = message.get('role', message.get('type', 'user'))  # Support both 'role' and 'type' keys

    with st.chat_message(role):
        st.markdown(message['content'])

        # Add copy button for assistant messages
        if role == 'assistant':
            # Strip markdown formatting for plain text copy
            plain_text = message['content']
            plain_text = re.sub(r'\*\*(.+?)\*\*', r'\1', plain_text)  # Remove bold
            plain_text = re.sub(r'\*(.+?)\*', r'\1', plain_text)  # Remove italics
            plain_text = re.sub(r'#{1,6}\s*(.+)', r'\1', plain_text)  # Remove headers

            copy_button(
                plain_text,
                tooltip="Copy response",
                copied_label="Copied!",
                icon="content_copy"
            )

        # Display sources if available (for assistant messages)
        if role == 'assistant' and 'sources' in message and message['sources']:
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
    # User Info - Injected into Header via CSS
    chat_display_id = st.session_state.chat_id[:12] if st.session_state.chat_id else 'None'
    
    header_css_hack = f"""
    <style>
        /* Target the Sidebar Content to allow overflow for our hoisted element */
        div[data-testid="stSidebarContent"] {{
            position: relative;
            overflow-x: visible !important;
            overflow-y: auto !important;
        }}

        /* Create the container that floats up into the header */
        .header-overlay-container {{
            position: absolute;
            top: -3.75rem; /* Moves it up into the stSidebarHeader area */
            left: 0;
            width: 100%;
            padding: 0 1rem;
            z-index: 10000;
            pointer-events: none;
        }}

        /* Style the user info box */
        .custom-header-alert {{
            background-color: transparent;
            border: none;
            color: var(--agusto-navy);
            padding: 0.75rem 1rem;
            font-size: 1rem;
            line-height: 1.4;
            pointer-events: auto;
            transition: all 0.3s ease;
        }}

        .header-user-text {{
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.25rem;
            transition: all 0.3s ease;
            cursor: pointer;
            text-align: center;
        }}

        .custom-header-alert:hover .header-user-text {{
            color: var(--agusto-blue);
        }}
    </style>

    <div class="header-overlay-container">
        <div class="custom-header-alert" role="alert">
            <div class="header-user-text">
                Welcome, {st.session_state.user_id}
            </div>
        </div>
    </div>
    """
    
    # Inject the HTML/CSS
    st.markdown(header_css_hack, unsafe_allow_html=True)
    
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
            
    # New Chat Button
    if st.button("New Chat", icon=":material/edit_square:", use_container_width=True, type="primary"):
        start_new_chat()
        st.rerun()
    
    # Chat History
    st.subheader("Chat History")
    
    if st.session_state.chat_history:
        for chat in st.session_state.chat_history:
            chat_id = chat.get('chat_id', chat.get('id', ''))
            chat_title = chat.get('title', 'Untitled Chat')
            
            # Truncate long titles
            if len(chat_title) > 50:
                chat_title = chat_title[:47] + "..."
            
            # Create button with just the title
            if st.button(chat_title, key=f"chat_{chat_id}", use_container_width=True):
                if storage_manager.enabled:
                    with st.spinner("Loading chat..."):
                        if load_chat_session(chat_id):
                            st.success(f"Loaded: {chat_title}")
                            st.rerun()
                        else:
                            st.error("Failed to load chat")
                else:
                    st.info(f"Would load: {chat_title}")
    else:
        st.info("No chat history available")

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
            <p><span class="typewriter-text">Your AI Research Assistant, Ask questions about your reports and get intelligent insights.</span></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display all messages
        for message in st.session_state.messages:
            display_message(message)

# Chat Input
if prompt := st.chat_input("Ask a question about your reports..."):
    # Generate chat ID if this is a new chat
    if not st.session_state.chat_id and storage_manager.enabled:
        st.session_state.chat_id = storage_manager.generate_chat_id()
    
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now().isoformat()
    })

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Show loading and get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Get response from agent API
            response = call_agent_api(
                prompt,
                st.session_state.search_mode,
                st.session_state.filters
            )

        # Display assistant response with streaming effect
        response_placeholder = st.empty()
        full_response = ""
        
        # Stream the response
        for chunk in stream_text(response['response'], delay=0.003):
            full_response += chunk
            response_placeholder.markdown(full_response + "|")
        
        # Final display without cursor
        response_placeholder.markdown(response['response'])

        # Add copy button
        plain_text = response['response']
        plain_text = re.sub(r'\*\*(.+?)\*\*', r'\1', plain_text)  # Remove bold
        plain_text = re.sub(r'\*(.+?)\*', r'\1', plain_text)  # Remove italics
        plain_text = re.sub(r'#{1,6}\s*(.+)', r'\1', plain_text)  # Remove headers

        copy_button(
            plain_text,
            tooltip="Copy response",
            copied_label="Copied!",
            icon="content_copy"
        )

        # Display sources if available
        if response['sources']:
            # Group sources by report name
            grouped_sources = {}
            for source in response['sources']:
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

    # Add assistant message to chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response['response'],
        "sources": response['sources'],
        "timestamp": response['timestamp']
    })
    
    # Save chat session to Azure Storage
    if storage_manager.enabled:
        # Log the query/response interaction
        storage_manager.log_query(
            chat_id=st.session_state.chat_id,
            user_id=st.session_state.user_id,
            query=prompt,
            response=response['response'],
            search_mode=st.session_state.search_mode,
            filters=st.session_state.filters,
            sources=response.get('sources', [])
        )
        
        # Save the full chat session
        save_success = save_current_chat()
        if save_success:
            st.toast("Chat saved to cloud ☁️", icon="✅")
        else:
            st.toast("Failed to save chat", icon="⚠️")

    # Rerun to display new messages
    st.rerun()

# Footer with Brand Bar
st.markdown("""
<div class="brand-bar">
    <div class="brand-bar-navy"></div>
    <div class="brand-bar-gray"></div>
</div>
""", unsafe_allow_html=True)