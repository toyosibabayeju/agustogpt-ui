"""
AgustoGPT - AI Research Assistant
Simple Streamlit Interface with Dummy Data
"""

import streamlit as st
from datetime import datetime
import time
import os
import json
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

# Remove default Streamlit padding/margins at top
st.markdown("""
    <style>
    /* Remove top padding from main content */
    .stMainBlockContainer {
        padding-top: 0 !important;
    }

    /* Remove top padding from sidebar */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
    }

    /* Remove sidebar content padding */
    [data-testid="stSidebarContent"] {
        padding-top: 0.0rem !important;
    }

    /* Remove default block spacing */
    .block-container {
        padding-top: 0 !important;
    }

    /* Hide header completely */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* Remove app view container top padding */
    .stAppViewContainer {
        padding-top: 0 !important;
    }

    /* Remove main container top margin */
    .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* Reduce sidebar header height and margin */
    [data-testid="stSidebarHeader"] {
        height: 0rem !important;
        margin-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Splash Screen / Loader
if 'splash_shown' not in st.session_state:
    splash = st.empty()
    with splash.container():
        st.markdown("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            logo_path = "assets/agusto_logo.png"
            if os.path.exists(logo_path):
                st.image(logo_path, use_container_width=True)
            else:
                st.header("AgustoGPT")
            
            st.markdown("""
                <div style='text-align: center; font-size: 1.0rem; color: #666; margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 500;'>
                    Powered By
                </div>
            """, unsafe_allow_html=True)

            vizyx_logo_path = "assets/vizyx-brand.png"
            if os.path.exists(vizyx_logo_path):
                # Use nested columns to center and control size of Vizyx logo
                v_col1, v_col2, v_col3 = st.columns([1, 2, 1])
                with v_col2:
                    st.image(vizyx_logo_path, use_container_width=True)
            else:
                st.markdown("<div style='text-align: center; font-weight: bold;'>Vizyx.Ltd</div>", unsafe_allow_html=True)
            
    time.sleep(3)
    splash.empty()
    st.session_state.splash_shown = True

# API Configuration
AGENT_API_URL = os.getenv('AGENT_API_URL', 'http://localhost:8000')

# Client API URL - use test endpoint in dev mode, production endpoint otherwise
if os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true':
    CLIENT_API_URL = os.getenv('CLIENT_API_URL_DEV', 'https://ami-be.ag-test.agusto.com')
else:
    CLIENT_API_URL = os.getenv('CLIENT_API_URL', 'https://ami-be.ag-apps.agusto.com')

# Functions
def get_jwt_token():
    """
    Get JWT token from multiple sources (priority order):
    1. URL query parameters (for iframe embedding)
    2. Manual input (development mode)
    3. HTTP cookies
    4. Environment variables
    """
    # First check URL query parameters (for iframe embedding)
    try:
        # Get query parameters from URL
        if hasattr(st, 'query_params'):
            query_params = st.query_params
            if 'jwt_token' in query_params:
                jwt_from_url = query_params['jwt_token']
                if jwt_from_url:
                    # Debug: Show that JWT came from URL
                    if os.getenv('DEBUG_COOKIES', 'false').lower() == 'true':
                        st.sidebar.success("🔗 Using JWT from URL parameter (iframe)")
                    return jwt_from_url
    except Exception as e:
        # If query param reading fails, log and continue to fallback
        if os.getenv('DEBUG_COOKIES', 'false').lower() == 'true':
            st.sidebar.error(f"Query param read error: {str(e)}")
    
    # Then check for manual JWT token input (development mode)
    if st.session_state.get('manual_jwt_token'):
        if os.getenv('DEBUG_COOKIES', 'false').lower() == 'true':
            st.sidebar.info("📝 Using manual JWT token")
        return st.session_state.manual_jwt_token
    
    # Try to get from cookies
    try:
        cookies = cookie_manager.get_all()
        jwt_from_cookie = cookies.get('jwt_token') if cookies else None
        
        # Debug: Show available cookies (remove in production)
        if os.getenv('DEBUG_COOKIES', 'false').lower() == 'true':
            st.sidebar.caption(f"🔍 Available cookies: {list(cookies.keys()) if cookies else 'None'}")
        
        if jwt_from_cookie:
            if os.getenv('DEBUG_COOKIES', 'false').lower() == 'true':
                st.sidebar.info("🍪 Using JWT from cookie")
            return jwt_from_cookie
    except Exception as e:
        # If cookie reading fails, log and continue to fallback
        if os.getenv('DEBUG_COOKIES', 'false').lower() == 'true':
            st.sidebar.error(f"Cookie read error: {str(e)}")
    
    # Fallback to environment variable (for development)
    env_token = os.getenv('JWT_TOKEN', '')
    if env_token and os.getenv('DEBUG_COOKIES', 'false').lower() == 'true':
        st.sidebar.info("⚙️ Using JWT from environment variable")
    
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
        
        # Debug: Show which endpoint is being used
        if os.getenv('DEBUG_COOKIES', 'false').lower() == 'true':
            endpoint_type = "TEST" if os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true' else "PRODUCTION"
            st.sidebar.caption(f"🌐 Using {endpoint_type} client API: {CLIENT_API_URL}")
        
        # Check if JWT token is available
        if not jwt_token:
            if os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true':
                st.warning("⚠️ Not authenticated. Using guest access.\n\n**Dev Mode:** No JWT token found.")
            else:
                st.info("👤 Using guest access.")
            
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
        # Handle API errors gracefully with user-friendly message
        if os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true':
            st.warning(f"⚠️ Unable to verify credentials. Using guest access.\n\n**Dev Mode:** {str(e)}")
        else:
            st.warning("⚠️ Unable to verify credentials. Using guest access.")
        
        return {
            "id": "default_user",
            "company": "Default Company",
            "country": "Nigeria",
            "industryReports": []
        }
    except Exception as e:
        # Handle unexpected errors
        if os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true':
            st.warning(f"⚠️ Authentication issue. Using guest access.\n\n**Dev Mode:** {type(e).__name__}: {str(e)}")
        else:
            st.warning("⚠️ Authentication issue. Using guest access.")
        
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
    
    # For storage operations, use company name instead of user_id
    # This groups chats by company rather than individual user IDs
    if st.session_state.user_company and st.session_state.user_company != 'Default Company':
        st.session_state.storage_user_id = st.session_state.user_company
    else:
        # For default/non-JWT sessions, keep using "default_user"
        st.session_state.storage_user_id = 'default_user'

# Ensure storage_user_id is always set (safeguard for session state edge cases)
if 'storage_user_id' not in st.session_state:
    if st.session_state.get('user_company') and st.session_state.user_company != 'Default Company':
        st.session_state.storage_user_id = st.session_state.user_company
    else:
        st.session_state.storage_user_id = 'default_user'

if 'chat_history' not in st.session_state:
    # Load chat history from Azure if available
    if storage_manager.enabled:
        st.session_state.chat_history = storage_manager.list_user_chats(st.session_state.storage_user_id, limit=20)
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
        'selected_documents': []
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

# Filter Options
INDUSTRY_SECTORS = ['', 'Oil & Gas Upstream', 'Oil & Gas Downstream', 'Insurance', 'Banking', 'Electricity', 'Telecommunications', 'HMO']
REPORT_YEARS = ['', '2025', '2024', '2023', '2022', '2021', '2020', '2019', '2018']

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
    Includes recent chat history and available industry reports for context
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
        
        # Build enhanced query with chat history and industry reports
        # NOTE: This enhanced query is ONLY sent to the API, never displayed in UI
        # The user sees only their original query in the chat interface
        enhanced_query = query
        
        # Append chat history if available
        if chat_history:
            enhanced_query = chat_history + 'the current user query is: ' + query + ' '
        
        # Determine context and query modification
        industry_context = industry_reports_str
        
        if search_mode == 'tailored':
            if filters and filters.get('selected_documents'):
                selected_docs_str = ", ".join([f"{doc}.pdf" for doc in filters['selected_documents']])
                enhanced_query = enhanced_query + ' documents available are ' + selected_docs_str + '.' + 'If document is not found in search or relavent information is not found, inform the user that the info is not available in the documents <documant name>. Make sure to use the full name along with extension .pdf for calling the document.'
                industry_context = selected_docs_str
        elif industry_reports_str:
            # Auto mode
            enhanced_query = enhanced_query + ' The available industry reports are: ' + industry_reports_str + '.' + 'If document is not found in search or relavent information is not found, inform the user that the info is not available in the documents <documant name>. Make sure to use the full name along with extension .pdf for calling the document.'

        # Debug: Show what's being sent (if debug mode is enabled)
        if os.getenv('DEBUG_QUERIES', 'false').lower() == 'true':
            st.sidebar.info(f"📝 Enhanced query: {enhanced_query[:200]}...")
        
        # Prepare payload
        payload = {
            "user_query": enhanced_query,
            "year_to_search": datetime.now().year,
            "industry_to_search": industry_context
        }

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
        # Handle API errors gracefully with user-friendly messages
        
        # Generic user-friendly error message
        error_msg = "⚠️ **Unable to reach our AI agent at the moment.**\n\n"
        error_msg += "Please try again in a few moments. If the problem persists, contact support."
        
        # Add technical details only in development mode
        if os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true':
            error_msg += f"\n\n---\n**Technical Details (Dev Mode Only):**\n"
            error_msg += f"- Error: {str(e)}\n"
            error_msg += f"- API URL: {AGENT_API_URL}\n"
            
            # If it's a 422 error, provide more details
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"- Status Code: {e.response.status_code}\n"
                
                if e.response.status_code == 422:
                    try:
                        error_detail = e.response.json()
                        error_msg += f"\n**Validation Error:**\n```json\n{json.dumps(error_detail, indent=2)}\n```"
                        error_msg += f"\n**Payload Sent:**\n```json\n{json.dumps(payload, indent=2)}\n```"
                    except:
                        error_msg += f"\n**Response:** {e.response.text}"
        
        return {
            "response": error_msg,
            "sources": [],
            "recommended_queries": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        # Generic error message for unexpected errors
        error_msg = "⚠️ **An unexpected error occurred.**\n\n"
        error_msg += "Please try again. If the problem persists, contact support."
        
        # Add technical details only in development mode
        if os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true':
            error_msg += f"\n\n---\n**Technical Details (Dev Mode Only):**\n"
            error_msg += f"- Error Type: {type(e).__name__}\n"
            error_msg += f"- Error: {str(e)}"
        
        return {
            "response": error_msg,
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
    
    # Save to Azure (using company name as storage identifier)
    success = storage_manager.save_chat_session(
        chat_id=st.session_state.chat_id,
        user_id=st.session_state.storage_user_id,
        messages=st.session_state.messages,
        metadata=metadata
    )
    
    if success:
        # Update chat history in session state
        st.session_state.chat_history = storage_manager.list_user_chats(
            st.session_state.storage_user_id, 
            limit=20
        )
    
    return success

def load_chat_session(chat_id: str):
    """Load a chat session from Azure Storage"""
    if not storage_manager.enabled:
        return False
    
    chat_data = storage_manager.load_chat_session(
        chat_id=chat_id,
        user_id=st.session_state.storage_user_id
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
    # Keep the current search mode, don't reset to 'auto'
    # st.session_state.search_mode = 'auto'
    st.session_state.filters = {
        'selected_documents': []
    }

def display_message(message, message_index=None):
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
                # Create unique key using message index and query index
                # Use timestamp as fallback if message_index is not provided
                if message_index is not None:
                    button_key = f"recommended_msg{message_index}_q{idx}"
                else:
                    # Fallback: use timestamp with replacements to avoid special chars
                    timestamp_key = message.get('timestamp', '').replace(':', '').replace('.', '').replace('-', '')
                    button_key = f"recommended_{timestamp_key}_{idx}"
                
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
    # Welcome User at Top of Sidebar (in stSidebarHeader)
    user_display_company = st.session_state.get('user_company', 'Guest')
    # Truncate long company names for display
    if len(user_display_company) > 20:
        user_display_company = user_display_company[:17] + "..."
    
    # Display welcome message in sidebar header
    st.markdown(f"""
    <div class="sidebar-welcome-header">
        <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.25rem; text-align: center;">Welcome</div>
        <div style="font-size: 1.1rem; font-weight: 700; text-align: center;">{user_display_company}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show available reports count
    if st.session_state.get('user_reports'):
        reports_count = len(st.session_state.user_reports)
        st.caption(f"📚 {reports_count} report{'s' if reports_count != 1 else ''} available")

    # Search Mode Selection
    st.subheader("Search Mode")
    
    # Initialize timestamp for search mode changes
    if 'search_mode_changed_at' not in st.session_state:
        st.session_state.search_mode_changed_at = time.time()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Auto", icon=":material/search:", use_container_width=True,
                    type="primary" if st.session_state.search_mode == 'auto' else "secondary"):
            st.session_state.search_mode = 'auto'
            st.session_state.search_mode_changed_at = time.time()
            st.rerun()
    with col2:
        if st.button("Tailored", icon=":material/my_location:", use_container_width=True,
                    type="primary" if st.session_state.search_mode == 'tailored' else "secondary"):
            st.session_state.search_mode = 'tailored'
            st.session_state.search_mode_changed_at = time.time()
            st.rerun()
    
    # Timed Search Mode Description (auto-hide after 5 seconds using JS)
    description_placeholder = st.empty()
    if 'search_mode_msg_id' not in st.session_state:
        st.session_state.search_mode_msg_id = 0
    # Increment id whenever search mode changes (already captured above on button click)
    current_id = int(st.session_state.search_mode_changed_at)
    if st.session_state.search_mode_msg_id != current_id:
        st.session_state.search_mode_msg_id = current_id
    
    # Always render message immediately after change; JS hides it after 5s
    message_html = ""
    if st.session_state.search_mode == 'auto':
        message_html = "<strong>Auto Search:</strong> Intelligently finding the relevant information from all reports."
    else:
        message_html = "<strong>Tailored Search:</strong> Search within selected scope using filters below."
    
    description_placeholder.markdown(f"""
    <div id="search-mode-msg-{st.session_state.search_mode_msg_id}" style="background:#EFF6FF;padding:0.75rem;border-radius:0.5rem;margin:0.5rem 0;font-size:0.85rem;color:#001B44;">{message_html}</div>
    <script>
    (function(){{
        const id = 'search-mode-msg-{st.session_state.search_mode_msg_id}';
        setTimeout(function(){{
            const el = window.parent.document.getElementById(id);
            if(el) el.style.display = 'none';
        }}, 5000);
    }})();
    </script>
    """, unsafe_allow_html=True)
    
    # New Chat Button
    if st.button("New Chat", icon=":material/edit_square:", use_container_width=True, type="primary"):
        start_new_chat()
        st.rerun()
        
    # Storage Status (only show in dev mode)
    if os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true':
        if st.session_state.storage_enabled:
            st.success("☁️ Storage: Enabled")
        else:
            st.warning("💾 Storage: Session Only")
    
    if os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true' and st.session_state.chat_id:
        st.caption(f"💬 Chat ID: {st.session_state.chat_id[:12]}...")
            
    # Filters (only show in tailored mode)
    if st.session_state.search_mode == 'tailored':
        with st.expander("Report Selection", expanded=True):
            st.session_state.filters['selected_documents'] = st.multiselect(
                "Select Documents:",
                options=st.session_state.user_reports,
                default=st.session_state.filters.get('selected_documents', [])
            )

            # Show selected filters count
            if st.session_state.filters['selected_documents']:
                count = len(st.session_state.filters['selected_documents'])
                st.caption(f"{count} document{'s' if count != 1 else ''} selected")
            else:
                st.caption("No documents selected")
    
    # Chat History
    with st.expander("Chat History", expanded=True):
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
        for idx, message in enumerate(st.session_state.messages):
            display_message(message, message_index=idx)

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
            # Add timestamp to ensure uniqueness
            import hashlib
            unique_id = hashlib.md5(f"{msg_count}_{time.time()}".encode()).hexdigest()[:8]
            
            # Display recommended queries as buttons
            for idx, query in enumerate(response['recommended_queries']):
                # Create unique key for each button
                button_key = f"rec_current_{unique_id}_{idx}"
                
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
        # Log the query/response interaction (using company name as storage identifier)
        storage_manager.log_query(
            chat_id=st.session_state.chat_id,
            user_id=st.session_state.storage_user_id,
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