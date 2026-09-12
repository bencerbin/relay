# Relay

Relay is an AI-assisted community referral platform that helps people find relevant local social services. Users describe what they need in natural language, and the backend collects the required information, converts it into structured referral data, and ranks matching community resources.

The project is currently implemented as a Django REST Framework API. It supports conversational intake, optional LLM-powered field extraction through Groq, a deterministic keyword-based fallback for local development, and rule-based eligibility scoring across food, housing, healthcare, transportation, and food-delivery resources.

## Current capabilities

- Conversational referral intake with persistent sessions.
- Structured extraction of needs, county, city, language, insurance, age, accessibility requirements, healthcare specialties, service modalities, and program purpose.
- Context-aware follow-up questions when required information is missing.
- Resource matching based on location, service type, age requirements, accessibility, language, insurance, specialty, population, modality, and program purpose.
- Ranked recommendations with eligibility status, matching reasons, warnings, and source metadata.
- Transaction-safe session finalization to prevent duplicate referral requests.

## Tech stack

- Python
- Django 5.2+
- Django REST Framework
- SQLite for local development
- Groq structured outputs for optional LLM extraction
- Python `unittest`/Django test framework

## Getting started

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Apply migrations and start the development server:

```bash
python manage.py migrate
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/api/`.

## Configuration

By default, Relay uses deterministic extraction so it can run without an external API key. To enable Groq structured extraction, create a `.env` file in the project root:

```env
EXTRACTION_BACKEND=groq
GROQ_API_KEY=your_api_key_here
# Optional:
# GROQ_MODEL=openai/gpt-oss-20b
# GROQ_REASONING_EFFORT=low
```

Do not commit `.env` files or API keys to version control.

## API endpoints

### `POST /api/intake/`

Send a natural-language message to begin or continue a referral session.

```json
{
  "message": "I need food delivery in Montgomery County."
}
```

For an existing session, include its UUID:

```json
{
  "session_id": "00000000-0000-0000-0000-000000000000",
  "message": "I am in Rockville."
}
```

The response includes the session status, the structured draft, missing fields, and the next follow-up question when more information is needed. A session becomes `ready` once the required information has been collected.

### `POST /api/intake/sessions/<session_id>/search/`

Finalize a ready session and return ranked community-resource recommendations. If required information is missing, the endpoint returns a `409 Conflict` response with the missing fields.

### `POST /api/recommendations/`

Create a structured referral directly and return ranked recommendations without conversational intake. The request accepts fields such as `county`, `city`, `needs`, `healthcare_specialties`, `service_modalities`, and `program_purposes`.

## Data model

The main entities are:

- `ReferralSession`: stores the conversational draft and tracks intake status.
- `ReferralRequest`: stores the finalized referral criteria.
- `CommunityResource`: stores service descriptions, geographic coverage, eligibility information, supported languages, source URLs, and verification metadata.

## Roadmap: Retrieval-Augmented Generation

The next major step is to add a Retrieval-Augmented Generation (RAG) pipeline for community-resource discovery. Resource records and trusted source documents will be chunked, embedded, and indexed for semantic search so the system can retrieve the most relevant programs for each referral. A generation layer will then use the retrieved evidence to explain recommendations, include source citations, and avoid unsupported claims. Future iterations may also add automated source ingestion and verification, freshness checks, and hybrid retrieval that combines semantic similarity with structured eligibility filters.

## Running tests

```bash
python manage.py test
```
