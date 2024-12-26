
# Merge Conflict Resolver

This project provides a merge conflict resolution tool enhanced with FastAPI, machine learning, and LLM integration. It can parse and resolve merge conflicts automatically, validate results, and test for correctness.

## Features
- Automatic conflict resolution using heuristic strategies and LLMs.
- FastAPI service for visualization and API-based interaction.
- GitHub-compatible integration for seamless use.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the API server:
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Access the API at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Usage
- Upload a file containing merge conflicts via the `/resolve` endpoint.
- View resolved conflicts, unresolved conflicts, and validation/test results.

## Integration
This tool can be used in GitHub Actions, Git hooks, or any CI/CD pipeline.
