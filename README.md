# AIDeployer - Automated App Builder

---

## Overview

**LLM Code Deployment** is an intelligent backend system that automates the process of building, deploying, and updating web applications from structured JSON requests.  
It leverages leading **Large Language Models (OpenAI, Anthropic, Gemini and OpenRouter)** to generate production-ready code.

The service runs asynchronously, ensuring high performance and scalability for multi-round build workflows.
---

## Features

- **LLM-Driven Code Generation** – Converts natural-language briefs into functional applications.  
- **Multi-Provider Fallback** – Dynamic selection between OpenAI, Anthropic, Gemini, and more.  
- **Automated GitHub Integration** – Handles repo creation, commits, and GitHub Pages deployment.  
- **Asynchronous Task Handling** – Background processing ensures non-blocking execution.  
- **Secure Task Validation** – Nonce-based and secret-token authentication for all requests.  
- **Two-Round Workflow** – Supports iterative refinement through Round 1 (initial) and Round 2 (revision).  
- **Attachment & Metadata Support** – Handles base64/data URI assets and evaluation callbacks.  
- **Robust Logging & Retry** – Includes exponential retry logic and structured request logging.

---

## Project Structure

```
AIDeployer/
│
├── app/
│   ├── api/
│   │   └── endpoints.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── code_generator.py
│   │   ├── deployment.py
│   │   ├── github/
│   │   │   └── github_service.py
│   │   └── llm/
│   │       ├── base.py
│   │       ├── manager.py
│   │       └── providers.py
│   ├── utils/
│   │   └── attachments.py
│   ├── config.py
│   └── main.py
│
├── Dockerfile
└── requirements.txt
```

---

## Quick Start

### Prerequisites
- Python 3.10+  
- Docker (optional, for containerized deployments)  
- GitHub Personal Access Token with scopes: `public_repo`, `workflow`, `pages:write`  
- LLM API keys (OpenAI, Anthropic, Gemini, OpenRouter.)  

### Environment Configuration

Create a `.env` file in the root directory with the following values:

```env
# Required
SECRET_TOKEN=your-shared-secret
GITHUB_TOKEN=ghp_your_github_token
GITHUB_USERNAME=your-github-username

# LLM Providers
OPENROUTER_API_KEY=your-openrouter-key
ANTHROPIC_API_KEY=sk-anthropic-key
OPENAI_API_KEY=sk-your-openai-key
GEMINI_API_KEY=your-gemini-key


# Optional
PORT=8000
HOST=0.0.0.0
```

### Local Development

```bash
git clone https://github.com/Srivastava-Shrestha/AIDeployer.git
cd AIDeployer
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Deployment

```bash
docker build -t ai-deployer:latest .
docker run --env-file .env -p 8000:8000 ai-deployer:latest
```

---

## API Endpoints

### POST /build  
Initiates the full build and deployment workflow.

#### Example Request
```json
{
  "email": "student@example.com",
  "secret": "your-shared-secret",
  "task": "captcha-solver-abc12",
  "round": 1,
  "nonce": "ab12-ef34",
  "brief": "Create a captcha solver that handles ?url=https://.../image.png",
  "evaluation_url": "https://example.com/notify",
  "attachments": []
}
```

#### Example Response
```json
{
  "status": "success",
  "message": "Build request received for task captcha-solver-abc12, round 1. Processing in background."
}
```

### GET /health  
Health monitoring endpoint.

```json
{
  "status": "healthy",
  "service": "LLM Code Deployment"
}
```

---

## Workflow

**Round 1 – Initial Build**
1. Validate request and authenticate via `SECRET_TOKEN`  
2. Generate code with selected LLM provider  
3. Initialize GitHub repository and push code  
4. Deploy to GitHub Pages  
5. Notify evaluation endpoint with metadata  

**Round 2 – Revision Cycle**
1. Receive new brief for existing task  
2. Update and redeploy application  
3. Notify evaluation system with refreshed status  

---


## License

Licensed under the **MIT License**. See the [LICENSE](LICENSE) file for full details.

---

## Author

**Shrestha Srivastava**  
[GitHub Profile](https://github.com/srivastava-shrestha)

---


<div align="center">
  
  ** Thankyou 🐻**
  
</div>

