<div align="center">

<img src="./static/image/MiroFish_logo_compressed.jpeg" alt="MiroFish Logo" width="75%"/>

**Multi-Agent Swarm Intelligence Simulation Engine**

English translation of [MiroFish](https://github.com/666ghj/MiroFish)

</div>

## What is MiroFish?

MiroFish is an AI-powered simulation engine that takes any document -- a project spec, a BDR playbook, a policy draft, a news report -- and turns it into a living multi-agent simulation. It extracts entities and relationships, builds a knowledge graph, generates agent personas, and lets them interact across simulated social platforms. Then it produces an analysis report you can interrogate through chat.

**The pipeline:**

```
Upload documents --> Knowledge graph --> Agent personas --> Multi-agent simulation --> Analysis report --> Interactive chat
```

## Use Cases

### Prompt & Output Quality Testing
Upload your prompt templates or playbooks as seed documents. Run simulations to see how agents interpret and respond. Compare outputs across different local models to find which produces the best results.

### Project Spec Validation
Upload a project spec or PRD. MiroFish extracts entities, relationships, and requirements into a knowledge graph. The simulation surfaces gaps, contradictions, and edge cases by having agents interact around the spec -- things you'd normally only catch during implementation.

### BDR Skill & Script Testing
Upload BDR playbooks, objection handling guides, or sales scripts. Generate agent personas representing different prospect types. Run simulations to see how conversations unfold, identify weak scripts, and iterate on messaging.

### Scenario Planning & "What If" Analysis
Upload market reports, competitive intel, or policy documents. Inject variables and watch how simulated agents react. Test multiple scenarios without real-world risk.

### Content & Messaging Stress Testing
Upload marketing copy, communication plans, or PR drafts. Simulate public reception across different audience personas. Identify potential backlash or messaging gaps before launch.

## Quick Start (Local Development)

### Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| **Node.js** | 18+ | `node -v` |
| **Python** | 3.11 - 3.12 | `python --version` |
| **uv** | Latest | `uv --version` |
| **Local LLM** | Ollama, LM Studio, or vLLM | `ollama --version` |

### 1. Set up a local model

```bash
# Using Ollama (recommended)
ollama pull llama3.1:8b
ollama serve
```

Or use [LM Studio](https://lmstudio.ai/) (GUI, runs on port 1234) or [vLLM](https://docs.vllm.ai/) (port 8000).

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` -- the defaults point to Ollama:

```env
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=llama3.1:8b

ZEP_API_KEY=your_zep_api_key    # Free tier at https://app.getzep.com/
```

For other local model servers, see the examples in `.env.example`.

### 3. Install dependencies

```bash
npm run setup:all
```

Or step by step:

```bash
npm run setup          # Node dependencies (root + frontend)
npm run setup:backend  # Python dependencies (auto-creates venv)
```

### 4. Start

```bash
npm run dev
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5001`
- Health check: `http://localhost:5001/health`

Start individually:

```bash
npm run backend    # Backend only
npm run frontend   # Frontend only
```

### Docker

```bash
cp .env.example .env
# Edit .env with your config
docker compose up -d
```

Exposes ports 3000 (frontend) and 5001 (backend). Uploads persist via volume mount.

## Workflow

### Step 1: Graph Building
Upload documents (PDF, Markdown, TXT). MiroFish extracts text, generates an ontology of entity types and relationships, then builds a knowledge graph via Zep.

### Step 2: Environment Setup
Review extracted entities and relationships. Filter which entities become simulation agents. Each agent gets a generated persona with personality traits, memory, and behavioral logic.

### Step 3: Simulation
Agents interact on simulated platforms (Twitter-style, Reddit-style, or both in parallel). You configure the number of rounds, available actions, and can inject variables mid-simulation.

### Step 4: Report Generation
A ReportAgent analyzes the simulation results using tools to query the knowledge graph, read agent actions, and compute statistics. Produces a structured markdown report.

### Step 5: Deep Interaction
Chat with the ReportAgent to ask follow-up questions. Interview individual agents about their decisions and reasoning during the simulation.

## API Reference

All endpoints are under `http://localhost:5001/api/`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/graph/ontology/generate` | POST | Upload files and generate ontology |
| `/api/graph/build` | POST | Build knowledge graph |
| `/api/graph/task/<task_id>` | GET | Check build progress |
| `/api/graph/data/<graph_id>` | GET | Get graph nodes and edges |
| `/api/graph/project/list` | GET | List all projects |
| `/api/simulation/entities/<graph_id>` | GET | Get entities for simulation |
| `/api/simulation/<sim_id>/run` | POST | Start simulation |
| `/api/report/generate` | POST | Generate analysis report |
| `/api/report/chat` | POST | Chat with ReportAgent |
| `/health` | GET | Health check |

### Connecting from other local apps

The API accepts requests from any `localhost` or `127.0.0.1` origin by default. Just point your app at `http://localhost:5001/api/` -- no CORS config needed for local development.

## Configuration Reference

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_API_KEY` | API key for your LLM provider | `ollama` |
| `LLM_BASE_URL` | OpenAI-compatible API endpoint | `http://localhost:11434/v1` |
| `LLM_MODEL_NAME` | Model to use | `llama3.1:8b` |
| `ZEP_API_KEY` | Zep Cloud API key | `z_abc123...` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_DEBUG` | `False` | Enable debug mode (hot-reload, verbose errors) |
| `FLASK_HOST` | `0.0.0.0` | Backend bind address |
| `FLASK_PORT` | `5001` | Backend port |
| `CORS_ALLOWED_ORIGINS` | All localhost | Comma-separated allowed origins |
| `SECRET_KEY` | Auto-generated | Flask secret key |
| `LLM_BOOST_API_KEY` | - | Separate API key for intensive tasks |
| `LLM_BOOST_BASE_URL` | - | Separate endpoint for intensive tasks |
| `LLM_BOOST_MODEL_NAME` | - | Larger model for report generation |

### Local Model Setup Examples

**Ollama:**
```env
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=llama3.1:8b
```

**LM Studio:**
```env
LLM_API_KEY=lm-studio
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL_NAME=your-loaded-model
```

**vLLM:**
```env
LLM_API_KEY=vllm
LLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL_NAME=your-model
```

## Security

This codebase includes the following security measures:

- **No stack trace leakage**: Error responses only include tracebacks when `FLASK_DEBUG=True`
- **XSS protection**: HTML is escaped before rendering in the frontend
- **Path traversal protection**: Project IDs are validated to prevent directory traversal
- **CORS**: Restricted to localhost by default; configurable via `CORS_ALLOWED_ORIGINS`
- **No hardcoded secrets**: Flask `SECRET_KEY` is auto-generated if not set
- **Non-root Docker**: Container runs as unprivileged user

**Note**: There is no authentication on the API. This is intended for local development only. Do not expose the API to the public internet without adding auth.

## Project Structure

```
MicroFish-En/
├── backend/
│   ├── app/
│   │   ├── api/              # Flask route handlers (graph, simulation, report)
│   │   ├── models/           # Project and task data models
│   │   ├── services/         # Core logic (graph builder, simulation runner, report agent)
│   │   └── utils/            # File parsing, LLM client, logging
│   ├── scripts/              # Simulation runner scripts
│   └── pyproject.toml        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios API clients
│   │   ├── components/       # Vue step components (graph, simulation, report, chat)
│   │   ├── views/            # Page-level Vue components
│   │   └── router/           # Vue Router config
│   └── package.json          # Frontend dependencies
├── .env.example              # Environment variable template
├── Dockerfile                # Multi-stage Docker build
└── docker-compose.yml        # Docker Compose config
```

## Acknowledgments

MiroFish's simulation engine is powered by [OASIS (Open Agent Social Interaction Simulations)](https://github.com/camel-ai/oasis) from the CAMEL-AI team.

## License

[AGPL-3.0](LICENSE)
