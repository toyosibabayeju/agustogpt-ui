# AgustoGPT UI

Frontend for the AgustoGPT AI Research Assistant that premium clients will interact with.

## Features

- AI-powered research assistant interface
- Streamlit-based interactive UI
- Auto and Tailored search modes
- Report filtering and source citation
- Agusto & Co. branded design

## Tech Stack

- Python 3.12
- Streamlit
- Docker
- Azure Container Web App

## Local Development

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

See `.env.example` for available configuration options.

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
