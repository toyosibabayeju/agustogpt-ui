# AgustoGPT UI

Frontend for the AgustoGPT AI Research Assistant that premium clients will interact with.

## Features

- AI-powered research assistant interface powered by PydanticAI
- Streamlit-based interactive UI
- Auto and Tailored search modes
- Report filtering by industry and year
- Source citation with document references
- Azure Cognitive Search integration via Agent API
- Agusto & Co. branded design

## Tech Stack

- Python 3.12
- Streamlit
- Docker
- Azure Container Web App

## Local Development

### Prerequisites

1. Ensure the **agent-api** is running on `http://localhost:8000`
   - Navigate to your agent-api directory
   - Run: `uvicorn api_server:app --reload`

2. Configure environment variables:
```bash
cp env.example .env
```
Edit `.env` file:
- Set `AGENT_API_URL=http://localhost:8000`
- Set `ENABLE_DEV_MODE=true` to use test client API endpoint
- Set `DEBUG_COOKIES=true` to see JWT token source

### Running the UI

1. Create virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set JWT token for development:
```bash
# Run the JWT cookie setter tool
streamlit run set_jwt_cookie.py
```
This opens a utility to set the JWT token cookie for testing. In production, this cookie should be set by your authentication system.

4. Run the application:
```bash
streamlit run main.py
```

5. Open browser at `http://localhost:8501`

### How It Works

1. **Client Authentication**: On startup, the app fetches user details from the client API using JWT authentication
2. **User Context**: The user's ID, company, and available industry reports are retrieved and stored in session
3. **Chat History Context**: Automatically includes the last 2 messages in the conversation for context-aware responses
4. **Auto Search Mode**: Sends query to agent API with current year and user's industry reports in the `industry_to_search` field
5. **Tailored Search Mode**: Sends query with selected filters; if no specific industry is selected, includes user's industry reports in `industry_to_search`
6. Agent API uses Azure Cognitive Search with hybrid search (vector + keyword)
7. Results are formatted with source citations showing document name, page, industry, and year

### Conversational Context

The application maintains conversation context by including the most recent 2 chat messages with each query. This allows the AI to:
- Answer follow-up questions intelligently
- Reference previous responses
- Maintain context across the conversation

**Important**: The chat history is sent to the API internally but **is NOT displayed in the UI**. Users see only their original queries in the chat interface, keeping it clean and readable.

**Example:**
- User: "What are the key risks in the banking sector?"
- Assistant: [Provides detailed answer about banking risks]
- User: "How does this compare to 2023?"
- System automatically includes the previous Q&A, so the AI knows "this" refers to banking sector risks
- **UI displays**: Only "How does this compare to 2023?"
- **API receives**: "Chat History is: - user: What are the key risks..., assistant: The main risks... How does this compare to 2023?"

### Client API Integration

The application integrates with the client API to retrieve user-specific information:

- **Endpoint**: `GET https://ami-be.ag-apps.agusto.com/api/current-client`
- **Authentication**: Bearer token (JWT) from multiple sources (priority order):
  1. **URL query parameter** `jwt_token` (for iframe embedding) ⭐ Recommended for iframes
  2. **Manual input** via Development Mode UI
  3. **HTTP cookie** named `jwt_token`
  4. **Environment variable** `JWT_TOKEN` (for local development)
- **Response**: User ID, company, country, and available industry reports
- **Fallback**: If the API fails or JWT is not found, uses "default_user" as fallback

#### iFrame Embedding (Recommended)

For embedding AgustoGPT in an iframe, pass the JWT token via URL:

```html
<iframe 
  src="https://your-streamlit-app.com/?jwt_token=YOUR_JWT_TOKEN_HERE"
  width="100%" 
  height="800px"
  allow="clipboard-write">
</iframe>
```

**JavaScript Example:**
```javascript
const iframe = document.getElementById('agustogpt-iframe');
const jwtToken = getYourJWTToken(); // Your auth function
iframe.src = `https://your-app.com/?jwt_token=${encodeURIComponent(jwtToken)}`;
```

For detailed iframe integration guide, see `config_jwt_token.md`.

**Testing Locally:**
- Open `test_iframe_integration.html` in your browser
- Paste your JWT token
- Click "Load with Token"
- The iframe will embed AgustoGPT with authentication

#### Other Authentication Methods

The application also supports:
- **Cookie**: `jwt_token` cookie (set by your authentication system)
- **Manual Input**: Development Mode UI (enable with `ENABLE_DEV_MODE=true`)
- **Environment Variable**: `JWT_TOKEN` in `.env` file (for local development)

The industry reports from the client API are automatically included in the `industry_to_search` field of the agent API payload:
- In **Auto Search Mode**: Always sends the comma-separated list of user's industry reports
- In **Tailored Search Mode**: Sends the selected industry filter if specified, otherwise sends the user's industry reports
- If no industry reports are available or the client API fails, an empty string `""` is sent as the default

## Docker Build & Run

Build the Docker image:
```bash
docker build -t agustogpt-ui .
```

Run the container:
```bash
docker run -p 8000:8000 agustogpt-ui
```

Access at `http://localhost:8000`

## Deployment to Azure

This application is configured for automatic deployment to Azure Container Web App via GitHub Actions.

### Prerequisites

1. Azure Web App created (Container type)
2. GitHub repository secrets configured:
   - `AZURE_WEBAPP_PUBLISH_PROFILE`: Download from Azure Portal

### Automatic Deployment

Every push to the `main` branch triggers:
1. Docker image build
2. Push to GitHub Container Registry (ghcr.io)
3. Deployment to Azure Web App

### Manual Deployment

Trigger manually via GitHub Actions tab → "Deploy to Azure Container Web App" → Run workflow

## Environment Variables

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

Edit the `.env` file with your actual values.

### Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AGENT_API_URL` | URL of the agent API endpoint | `http://localhost:8000` | Yes |
| `CLIENT_API_URL` | URL of the production client API endpoint | `https://ami-be.ag-apps.agusto.com` | Yes |
| `CLIENT_API_URL_DEV` | URL of the test/dev client API endpoint | `https://ami-be.ag-test.agusto.com` | No |
| `JWT_TOKEN` | JWT token for client API authentication (dev fallback) | - | No |
| `ENABLE_DEV_MODE` | Enable development features and use test API endpoint | `false` | No |
| `DEBUG_COOKIES` | Show debug info about JWT token sources | `false` | No |
| `DEBUG_QUERIES` | Show debug info about API payloads | `false` | No |
| `DEFAULT_USER_ID` | Fallback user ID when client API fails | `default_user` | No |

**Client API Endpoint Selection:**
- When `ENABLE_DEV_MODE=true`: Uses `CLIENT_API_URL_DEV` (test endpoint: `https://ami-be.ag-test.agusto.com`)
- When `ENABLE_DEV_MODE=false` or not set: Uses `CLIENT_API_URL` (production endpoint: `https://ami-be.ag-apps.agusto.com`)

For detailed information about environment-based endpoints, see `ENVIRONMENT_ENDPOINTS.md`.

**Note**: The JWT token is primarily read from HTTP cookies (`jwt_token` cookie). The environment variable `JWT_TOKEN` is only used as a fallback for local development.

### API Payload Format

The UI sends requests to the agent API with the following structure:

```json
{
  "user_query": "What are the key trends in the oil and gas industry?",
  "year_to_search": 2023,
  "industry_to_search": "Oil & Gas Upstream"
}
```

**Auto Search Mode**: 
- Always uses current year (e.g., 2025) for `year_to_search`
- Sends user's industry reports (comma-separated) in `industry_to_search` field

**Tailored Search Mode**: 
- Uses selected year filter, or defaults to current year if not selected
- If specific industry is selected: sends that in `industry_to_search` 
- If no specific industry selected: sends user's industry reports in `industry_to_search`

**Industry Reports Context**: The UI automatically fetches the user's available industry reports from the client API and includes them as a comma-separated string in the `industry_to_search` field when no specific industry filter is selected. If the client API returns no industry reports or fails, an empty string "" is used as the default.

**Chat History Context** (Enabled by default): 
- The system automatically includes the last 2 messages from the conversation in the query
- Format: `"Chat History is: - user: <message>, assistant: <response>. See if the current user query relates to one of the chat history and answer accordingly. <actual query>"`
- This enables context-aware responses and intelligent follow-up questions
- Can be toggled on/off in Development Mode (set `ENABLE_DEV_MODE=true`)
- Long messages (>200 characters) are truncated in the context

**Example with Chat History:**
```json
{
  "user_query": "Chat History is: - user: What are the key risks in banking?, assistant: The main risks include credit risk, liquidity risk, and operational risk.... How does this compare to insurance?",
  "year_to_search": 2025,
  "industry_to_search": "Banking, Insurance"
}
```

### API Response Format

The agent API returns responses in this format:

```json
{
  "user_query": "What are the key trends in the oil and gas industry?",
  "document_information": [
    {
      "document_name": "Agusto & Co. 2023 Oil and Gas Upstream Industry Report.pdf",
      "year": 2023,
      "industry": "Oil & Gas Upstream",
      "page_number": 46,
      "chunk_index": 0
    }
  ],
  "response": "Based on our analysis...",
  "current_date": "2025-10-25",
  "recommended_queries": [
    "What are the growth projections for the oil and gas sector?",
    "How do these trends compare to the downstream sector?",
    "What are the key challenges facing the industry?"
  ]
}
```

The UI formats this into:
- User-friendly source citations
- Interactive recommended query buttons that users can click to continue the conversation

### Recommended Queries Feature

The AI agent can suggest follow-up questions to help users explore topics more deeply. These appear as clickable buttons below each response:

**Features:**
- 💡 Intelligent suggestions based on the current response
- 💬 One-click to ask the recommended question
- 🔄 Automatically includes conversation context
- 📝 Previous response is added to chat history for context

**Example Flow:**
1. User asks: "What are the key risks in banking?"
2. AI responds with analysis
3. Recommended buttons appear:
   - "How do these risks compare to 2023?"
   - "What mitigation strategies are recommended?"
   - "How does this affect insurance sector?"
4. User clicks a button → Query is automatically sent with full context

## Project Structure

```
.
├── main.py              # Main Streamlit application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── .dockerignore       # Docker build exclusions
├── styles/
│   └── main.css        # Custom styling
├── assets/
│   └── agusto_logo.png # Branding assets
└── .github/
    └── workflows/
        └── azure-container-deploy.yml  # CI/CD pipeline
```

## License

Proprietary - Agusto & Co.
