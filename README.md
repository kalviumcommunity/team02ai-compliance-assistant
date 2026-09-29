# Squad 69 — AI-Powered Compliance Assistant

## Run
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Open http://127.0.0.1:8000 (API docs at /docs).

## Demo
1. Click Load demo documents.
2. Ask: “What is the approval requirement for high value transfers?”
3. Show citations and the warning that the demo corpus includes historical/current versions.
4. Upload a TXT or text-based PDF.
5. Submit a fictional transaction.
6. Show audit trail.

## Team split
Part 1 / branch `feature/backend-data`: backend/main.py and requirements.txt — API, document ingestion, retrieval, version labels, transaction review, audit.
Part 2 / branch `feature/frontend-ui`: frontend/ — interface and API integration.
Merge each branch through a PR to main. Do not commit secrets or real/confidential data.

## Limitations
Local JSON store; simple keyword retrieval; no OCR for image-only PDFs; demo role selection is not production authentication; no live banking integration. Clearly state human review is required.
