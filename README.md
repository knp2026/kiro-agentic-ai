# AI-Driven Banking Contract Retrieval with Human-in-the-Loop (HITL)

This repository contains the source code for the AI-Driven Banking Contract Retrieval with Human-in-the-Loop (HITL) project. The project aims to provide an efficient and seamless user experience for bank customers to access and understand their contract information using natural language interaction.

## Technology Stack

- Language: Python
- Framework: FastAPI
- Database: PostgreSQL
- Auth: Keycloak
- AsyncProcessing: Apache Kafka
- Container: Docker
- Cloud: Amazon Web Services (AWS)
- IaC: Terraform
- Testing: Pytest with Coverage
- Documentation: Sphinx
- SourceControl: GitLab

## Project Structure

```
ai-banking-contract-retrieval/
|-- app/
| |-- api/
| | |-- controllers/
| | |-- models/
| | |-- services/
| |-- chatbot/
| | |-- intents/
| | |-- nlu/
| | |-- responses/
| |-- infrastructure/
| | |-- databases/
| | |-- mail/
| | |-- notifications/
| |-- utils/
|-- tests/
| |-- unit/
| |-- integration/
|-- .gitignore
|-- README.md
|-- requirements.txt
```

## Getting Started

1. Clone the repository: `git clone https://gitlab.com/your-organization/ai-banking-contract-retrieval.git`
2. Set up the development environment (see [Development Workflow](docs/development-workflow.md))
3. Install dependencies: `pip install -r requirements.txt`
4. Run tests: `pytest`
5. Start the application: `uvicorn app.main:app --reload`

## Documentation

For detailed documentation, refer to the [Documentation](docs/) directory.