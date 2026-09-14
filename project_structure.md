
# Project Structure

This document outlines the project structure for the AI-Driven Banking Contract Retrieval with Human-in-the-Loop (HITL) project. The project is built using Python, FastAPI, PostgreSQL, Keycloak, Apache Kafka, Docker, AWS, Terraform, Pytest, Sphinx, and GitHub.

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
|-- Dockerfile
|-- docker-compose.yml
|-- main.tf
|-- variables.tf
|-- outputs.tf
|-- Makefile
|-- docs/
| |-- source/
| |-- build/
|-- scripts/
| |-- setup.sh
| |-- start.sh
| |-- stop.sh
|-- terraform/
| |-- modules/
| |-- environments/
|-- k8s/
| |-- deployments/
| |-- services/
| |-- ingress/
|-- .env
|-- .env.example
|-- .env.test
|-- .env.production
|-- .env.staging
```