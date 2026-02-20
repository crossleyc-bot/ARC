# ARC - Analytics Rationalization & Canonicalization

**Intelligent Consolidation. Trusted Standardization. Measurable Impact.**

ARC is a full-stack platform that identifies redundant BI reports, detects overlapping semantic models, and recommends canonical datasets to standardize and certify enterprise reporting across Power BI and IBM Cognos environments.

## What ARC Does

1. **Harvest** - Connects to Power BI and Cognos, extracts metadata (reports, datasets, measures, usage)
2. **Analyze** - Detects exact duplicates, near-duplicates, report families, and KPI conflicts using hybrid rule-based + AI analysis
3. **Canonicalize** - Recommends canonical datasets with standardized KPIs, gap analysis per report
4. **Rationalize** - Generates a migration/retirement roadmap with estimated cost savings

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend      │────▶│  PostgreSQL     │
│  (TypeScript)   │     │  (Python)             │     │                 │
│  - Dashboard    │     │  - REST API           │     │  - Projects     │
│  - Inventory    │     │  - BI Connectors      │     │  - Reports      │
│  - Clusters     │     │  - Analysis Engine    │     │  - Datasets     │
│  - Canonical    │     │  - Canonicalization   │     │  - Clusters     │
│  - KPI Register │     │  - Export Services    │     │  - Canonical    │
│  - Roadmap      │     │  - Claude AI          │     │  - KPI Conflicts│
└─────────────────┘     └──────────────────────┘     └─────────────────┘
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy (async), PostgreSQL, Alembic
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, D3.js, Recharts
- **Analysis**: scikit-learn (TF-IDF, clustering), Claude API (semantic analysis)
- **Export**: openpyxl (Excel), weasyprint (PDF)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Docker & Docker Compose (optional)

### Using Docker Compose

```bash
cp .env.example .env
# Edit .env with your credentials
docker-compose up
```

The app will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Manual Setup

**Backend:**

```bash
cd backend
pip install -e ".[dev]"
# Start PostgreSQL and set DATABASE_URL in .env
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
ARC/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI route handlers
│   │   ├── connectors/    # Power BI & Cognos API connectors
│   │   ├── engine/        # Analysis engine (similarity, clustering, KPI detection, AI)
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   └── services/      # Business logic (harvest, analyze, export)
│   ├── alembic/           # Database migrations
│   └── tests/             # Unit tests (55 tests)
├── frontend/
│   └── src/
│       ├── api/           # Axios API client
│       ├── components/    # Reusable UI components
│       ├── hooks/         # React Query hooks
│       ├── pages/         # Page components (8 pages)
│       └── types/         # TypeScript type definitions
└── docker-compose.yml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/projects` | Create project |
| GET | `/api/projects` | List projects |
| POST | `/api/projects/{id}/connections` | Add BI connection |
| POST | `/api/connections/{id}/sync` | Trigger metadata harvest |
| GET | `/api/projects/{id}/reports` | List reports (paginated) |
| POST | `/api/projects/{id}/analyze` | Run analysis pipeline |
| GET | `/api/projects/{id}/clusters` | List report clusters |
| GET | `/api/projects/{id}/kpi-conflicts` | List KPI conflicts |
| POST | `/api/projects/{id}/canonicalize` | Generate canonical recommendations |
| GET | `/api/projects/{id}/canonical-datasets` | List canonical datasets |
| GET | `/api/projects/{id}/export/excel` | Download Excel report |
| GET | `/api/projects/{id}/export/pdf` | Download PDF summary |
| GET | `/api/projects/{id}/dashboard` | Dashboard metrics |

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `POWERBI_CLIENT_ID` | Azure AD app client ID |
| `POWERBI_CLIENT_SECRET` | Azure AD app client secret |
| `POWERBI_TENANT_ID` | Azure AD tenant ID |
| `COGNOS_BASE_URL` | Cognos Analytics server URL |
| `COGNOS_NAMESPACE` | Cognos authentication namespace |
| `COGNOS_USERNAME` | Cognos username |
| `COGNOS_PASSWORD` | Cognos password |
| `ANTHROPIC_API_KEY` | Claude API key for AI analysis |

## License

Proprietary - All rights reserved.
