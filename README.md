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
cp .env.example .env
```
Edit `.env` to set `AGENT_API_URL=http://localhost:8000`

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

3. Run the application:
```bash
streamlit run main.py
```

4. Open browser at `http://localhost:8501`

### How It Works

1. **Auto Search Mode**: Sends query to agent API with current year and all industries
2. **Tailored Search Mode**: Sends query with selected industry and year filters
3. Agent API uses Azure Cognitive Search with hybrid search (vector + keyword)
4. Results are formatted with source citations showing document name, page, industry, and year

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

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AGENT_API_URL` | URL of the agent API endpoint | `http://localhost:8000` | Yes |
| `ENVIRONMENT` | Application environment | `development` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### API Payload Format

The UI sends requests to the agent API with the following structure:

```json
{
  "user_query": "What are the key trends in the oil and gas industry?",
  "year_to_search": 2023,
  "industry_to_search": "Oil & Gas Upstream"
}
```

**Auto Search Mode**: Uses current year and empty industry (searches all)

**Tailored Search Mode**: Uses selected filters from sidebar

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
  "current_date": "2025-10-25"
}
```

The UI formats this into user-friendly source citations.

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
