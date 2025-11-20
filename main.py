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
import extra_streamlit_components as stx

# Load environment variables
load_dotenv()

# Initialize Cookie Manager
# Note: Cookie manager should not be cached as it needs to read cookies on each request
cookie_manager = stx.CookieManager()

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

# API Configuration
AGENT_API_URL = os.getenv('AGENT_API_URL', 'http://localhost:8000')
CLIENT_API_URL = os.getenv('CLIENT_API_URL', 'https://ami-be.ag-apps.agusto.com')

# Functions
def get_jwt_token():
    """
    Get JWT token from multiple sources (priority order):
    1. Manual input (development mode)
    2. HTTP cookies
    3. Environment variables
    """
    # First check for manual JWT token input (development mode)
    if st.session_state.get('manual_jwt_token'):
        return st.session_state.manual_jwt_token
    
    # Try to get from cookies
    try:
        cookies = cookie_manager.get_all()
        jwt_from_cookie = cookies.get('jwt_token') if cookies else None
        
        # Debug: Show available cookies (remove in production)
        if os.getenv('DEBUG_COOKIES', 'false').lower() == 'true':
            st.sidebar.caption(f"🔍 Available cookies: {list(cookies.keys()) if cookies else 'None'}")
        
        if jwt_from_cookie:
            return jwt_from_cookie
    except Exception as e:
        # If cookie reading fails, log and continue to fallback
        if os.getenv('DEBUG_COOKIES', 'false').lower() == 'true':
            st.sidebar.error(f"Cookie read error: {str(e)}")
    
    # Fallback to environment variable (for development)
    env_token = os.getenv('JWT_TOKEN', '')
    if env_token and os.getenv('DEBUG_COOKIES', 'false').lower() == 'true':
        st.sidebar.info("Using JWT from environment variable")
    
    return env_token

def get_client_details() -> Dict[str, Any]:
    """
    Fetch client details from the client API using JWT from cookies
    Returns client data including ID, company, country, and industry reports
    Falls back to default user if API fails
    """
    try:
        # Get JWT token from cookies
        jwt_token = get_jwt_token()
        
        # Check if JWT token is available
        if not jwt_token:
            st.warning("No JWT token found in cookies. Using default user.")
            return {
                "id": "default_user",
                "company": "Default Company",
                "country": "Nigeria",
                "industryReports": []
            }
        
        # Make API request with JWT authentication
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{CLIENT_API_URL}/api/current-client",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        # Parse and return client data
        client_data = response.json()
        return client_data
        
    except requests.exceptions.RequestException as e:
        # Handle API errors gracefully
        st.warning(f"Failed to fetch client details: {str(e)}. Using default user.")
        return {
            "id": "default_user",
            "company": "Default Company",
            "country": "Nigeria",
            "industryReports": []
        }
    except Exception as e:
        st.warning(f"Unexpected error fetching client details: {str(e)}. Using default user.")
        return {
            "id": "default_user",
            "company": "Default Company",
            "country": "Nigeria",
            "industryReports": []
        }

# Initialize Session State
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'search_mode' not in st.session_state:
    st.session_state.search_mode = 'auto'

if 'chat_id' not in st.session_state:
    st.session_state.chat_id = None

if 'user_id' not in st.session_state or 'client_data' not in st.session_state:
    # Fetch client details from API
    client_data = get_client_details()
    st.session_state.client_data = client_data
    st.session_state.user_id = client_data.get('id', 'default_user')
    st.session_state.user_company = client_data.get('company', 'Default Company')
    st.session_state.user_country = client_data.get('country', 'Nigeria')
    st.session_state.user_reports = client_data.get('industryReports', [])

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

if 'manual_jwt_token' not in st.session_state:
    st.session_state.manual_jwt_token = ''  # For development: manual JWT token input

if 'enable_chat_history' not in st.session_state:
    st.session_state.enable_chat_history = True  # Include chat history in queries by default

if 'recommended_query' not in st.session_state:
    st.session_state.recommended_query = None  # Store recommended query to be processed

if 'trigger_recommended_query' not in st.session_state:
    st.session_state.trigger_recommended_query = False  # Flag to trigger recommended query

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

# Functions

def get_recent_chat_history(num_messages: int = 2) -> str:
    """
    Get the most recent chat messages for context
    Returns formatted chat history string
    """
    messages = st.session_state.get('messages', [])
    
    if not messages:
        return ""
    
    # Get the last N messages (excluding the current one being sent)
    recent_messages = messages[-num_messages:] if len(messages) >= num_messages else messages
    
    # Format chat history
    history_parts = []
    for i, msg in enumerate(recent_messages, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        # Truncate very long messages
        if len(content) > 200:
            content = content[:197] + "..."
        history_parts.append(f"{role}: {content}")
    
    if history_parts:
        return "Chat History is: - " + ", ".join(history_parts) + ". See if the current user query relates to one of the chat history and answer accordingly. "
    
    return ""

def call_agent_api(query: str, search_mode: str, filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Call the agent API to get response
    Supports both auto and tailored search modes
    Includes recent chat history for context
    """
    try:
        # Get client details and industry reports
        client_data = st.session_state.get('client_data', {})
        industry_reports = client_data.get('industryReports', [])
        
        # Convert industry reports list to a string, use empty string as fallback
        industry_reports_str = ", ".join(industry_reports) if industry_reports else ""
        
        # Get recent chat history for context (if enabled)
        chat_history = ""
        if st.session_state.get('enable_chat_history', True):
            chat_history = get_recent_chat_history(num_messages=2)
        
        # Append chat history to the query if it exists
        # NOTE: This enhanced query is ONLY sent to the API, never displayed in UI
        # The user sees only their original query in the chat interface
        enhanced_query = chat_history + 'the current user query is: ' + query + ' ' if chat_history else query
        
        # Debug: Show what's being sent (if debug mode is enabled)
        if os.getenv('DEBUG_QUERIES', 'false').lower() == 'true' and chat_history:
            st.sidebar.info(f"📝 Query with history: {enhanced_query[:150]}...")
        
        # Prepare base payload
        payload = {
            "user_query": enhanced_query
        }

        # Add filters for tailored search
        if search_mode == 'tailored' and filters:
            # Add year filter if specified, otherwise use current year
            if filters.get('report_year'):
                payload['year_to_search'] = int(filters['report_year'])
            else:
                payload['year_to_search'] = datetime.now().year

            # Add industry filter if specified
            # Use selected industry sector in tailored mode if available
            if filters.get('industry_sector'):
                payload['industry_to_search'] = filters['industry_sector']
            else:
                # If no specific industry selected in tailored mode, use industry reports string
                payload['industry_to_search'] = industry_reports_str
        else:
            # Auto search - use current year and industry reports string
            payload['year_to_search'] = datetime.now().year
            # In auto mode, always use the industry reports string for context
            payload['industry_to_search'] = industry_reports_str

        # Debug: Log payload before sending (if debug mode enabled)
        if os.getenv('DEBUG_QUERIES', 'false').lower() == 'true':
            st.sidebar.json(payload)
        
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
            "recommended_queries": data.get('recommended_queries', []),
            "timestamp": data.get('current_date', datetime.now().isoformat())
        }

    except requests.exceptions.RequestException as e:
        # Handle API errors gracefully
        error_msg = f"Error connecting to agent API: {str(e)}\n\nPlease ensure the agent API is running at {AGENT_API_URL}"
        
        # If it's a 422 error, provide more details
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 422:
                try:
                    error_detail = e.response.json()
                    error_msg += f"\n\n**Validation Error Details:**\n```json\n{error_detail}\n```"
                    error_msg += f"\n\n**Payload Sent:**\n```json\n{payload}\n```"
                except:
                    error_msg += f"\n\nResponse: {e.response.text}"
        
        return {
            "response": error_msg,
            "sources": [],
            "recommended_queries": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "response": f"Unexpected error: {str(e)}",
            "sources": [],
            "recommended_queries": [],
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
        "recommended_queries": [],
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
        
        # Display recommended queries as buttons (for assistant messages)
        if role == 'assistant' and 'recommended_queries' in message and message['recommended_queries']:
            st.markdown('<div class="sources-header">💡 You might also want to ask:</div>', unsafe_allow_html=True)
            
            # Display recommended queries as buttons
            for idx, query in enumerate(message['recommended_queries']):
                # Create unique key for each button
                button_key = f"recommended_{message.get('timestamp', '')}_{idx}"
                
                if st.button(
                    f"💬 {query}",
                    key=button_key,
                    use_container_width=True,
                    type="secondary"
                ):
                    # Store the recommended query to be processed
                    st.session_state.recommended_query = query
                    st.session_state.trigger_recommended_query = True
                    st.rerun()


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
    
    # User Info
    user_display_id = st.session_state.user_id
    # Truncate long user IDs for display
    if len(user_display_id) > 20:
        user_display_id = user_display_id[:17] + "..."
    
    st.info(f"👤 User: {user_display_id}")
    
    # Show company if available
    if st.session_state.get('user_company') and st.session_state.user_company != 'Default Company':
        st.caption(f"🏢 {st.session_state.user_company}")
    
    # Show available reports count
    if st.session_state.get('user_reports'):
        reports_count = len(st.session_state.user_reports)
        st.caption(f"📚 {reports_count} report{'s' if reports_count != 1 else ''} available")

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
    
    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        start_new_chat()
        st.rerun()
    
    st.markdown("---")
    
    # Storage Status
    if st.session_state.storage_enabled:
        st.success("☁️")
    else:
        st.warning("💾")
    
    if st.session_state.chat_id:
        st.caption(f"💬 Chat ID: {st.session_state.chat_id[:12]}...")
    
    st.markdown("---")
    
    # Chat History
    st.subheader("Chat History")
    
    if st.session_state.chat_history:
        for chat in st.session_state.chat_history:
            chat_id = chat.get('chat_id', chat.get('id', ''))
            chat_title = chat.get('title', 'Untitled Chat')
            
            # Truncate long titles
            if len(chat_title) > 40:
                chat_title = chat_title[:37] + "..."
            
            # Format date
            created_at = chat.get('created_at', chat.get('date', ''))
            if created_at:
                try:
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime("%b %d, %Y")
                except:
                    formatted_date = created_at[:10] if len(created_at) > 10 else created_at
            else:
                formatted_date = ""
            
            # Create button with date
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"💬 {chat_title}", key=f"chat_{chat_id}", use_container_width=True):
                    if storage_manager.enabled:
                        with st.spinner("Loading chat..."):
                            if load_chat_session(chat_id):
                                st.success(f"Loaded: {chat_title}")
                                st.rerun()
                            else:
                                st.error("Failed to load chat")
                    else:
                        st.info(f"Would load: {chat_title}")
            with col2:
                st.caption(formatted_date)
    else:
        st.info("No chat history available")
    
    # Development Mode: Manual JWT Token Input
    if os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true':
        st.markdown("---")
        st.subheader("🔧 Development Mode")
        
        with st.expander("Manual JWT Token", expanded=False):
            st.caption("For testing when cookies don't work")
            manual_token = st.text_area(
                "JWT Token",
                value=st.session_state.manual_jwt_token,
                placeholder="Paste JWT token here...",
                height=100,
                key="jwt_input_field"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Set Token", use_container_width=True, type="primary"):
                    st.session_state.manual_jwt_token = manual_token
                    # Clear cached client data to force re-fetch
                    if 'client_data' in st.session_state:
                        del st.session_state.client_data
                        del st.session_state.user_id
                    st.success("Token set! Reloading...")
                    st.rerun()
            
            with col2:
                if st.button("Clear Token", use_container_width=True):
                    st.session_state.manual_jwt_token = ''
                    if 'client_data' in st.session_state:
                        del st.session_state.client_data
                        del st.session_state.user_id
                    st.success("Token cleared! Reloading...")
                    st.rerun()
            
            if st.session_state.manual_jwt_token:
                st.success("✅ Manual token is active")
            else:
                st.info("No manual token set")
        
        # Chat History Context Toggle
        with st.expander("Chat History Context", expanded=False):
            st.caption("Include recent chat messages for context-aware responses")
            
            enable_history = st.checkbox(
                "Include last 2 messages in queries",
                value=st.session_state.enable_chat_history,
                key="chat_history_toggle"
            )
            
            if enable_history != st.session_state.enable_chat_history:
                st.session_state.enable_chat_history = enable_history
                st.rerun()
            
            if st.session_state.enable_chat_history:
                st.success("✅ Chat history context is enabled")
                # Show preview of what will be included
                if st.session_state.messages:
                    preview = get_recent_chat_history(num_messages=2)
                    if preview:
                        st.caption("Preview of context:")
                        st.code(preview[:150] + "..." if len(preview) > 150 else preview)
            else:
                st.info("Chat history context is disabled")

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

# Handle recommended query trigger
if st.session_state.get('trigger_recommended_query', False):
    prompt = st.session_state.recommended_query
    st.session_state.trigger_recommended_query = False
    st.session_state.recommended_query = None
else:
    prompt = None

# Chat Input
if prompt or (prompt := st.chat_input("Ask a question about your reports...")):
    # Generate chat ID if this is a new chat
    if not st.session_state.chat_id and storage_manager.enabled:
        st.session_state.chat_id = storage_manager.generate_chat_id()
    
    # Add user message (store only the original prompt, not enhanced version)
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,  # Original query only
        "timestamp": datetime.now().isoformat()
    })

    # Display user message (show only original query to user)
    with st.chat_message("user"):
        st.markdown(prompt)  # Display original query, not enhanced version

    # Show loading and get response
    with st.chat_message("assistant"):
        # Show indicator if using chat history context
        if st.session_state.get('enable_chat_history', True) and len(st.session_state.messages) > 1:
            st.caption("💬 Using conversation context...")
        
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
        
        # Display recommended queries as buttons
        if response.get('recommended_queries'):
            st.markdown('<div class="sources-header">💡 You might also want to ask:</div>', unsafe_allow_html=True)
            
            # Get current message count for unique keys
            msg_count = len(st.session_state.messages)
            
            # Display recommended queries as buttons
            for idx, query in enumerate(response['recommended_queries']):
                # Create unique key for each button
                button_key = f"rec_current_{msg_count}_{idx}"
                
                if st.button(
                    f"💬 {query}",
                    key=button_key,
                    use_container_width=True,
                    type="secondary"
                ):
                    # Store the recommended query to be processed
                    st.session_state.recommended_query = query
                    st.session_state.trigger_recommended_query = True
                    st.rerun()

    # Add assistant message to chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response['response'],
        "sources": response['sources'],
        "recommended_queries": response.get('recommended_queries', []),
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