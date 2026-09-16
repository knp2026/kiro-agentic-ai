# Project Structure

This document outlines the project structure for the Patient Health Care System (PHCS), a comprehensive solution designed to automate patient onboarding, facilitate collaboration among healthcare partners, and support patient registration, consent capture, and lifecycle tracking. The project structure is organized into modules based on functional areas, with each module containing packages for services, repositories, controllers, and utilities.

```
patient_health_care_system/
|-- patient_registration/
|   |-- services/
|   |-- repositories/
|   |-- controllers/
|   |-- utils/
|-- consent_management/
|   |-- services/
|   |-- repositories/
|   |-- controllers/
|   |-- utils/
|-- appointment_scheduling/
|   |-- services/
|   |-- repositories/
|   |-- controllers/
|   |-- utils/
|-- integration/
|   |-- services/
|   |-- repositories/
|   |-- controllers/
|   |-- utils/
|-- reporting/
|   |-- services/
|   |-- repositories/
|   |-- controllers/
|   |-- utils/
|-- common/
|   |-- exceptions/
|   |-- interceptors/
|   |-- validators/
|   |-- utils/
|-- config/
|-- docs/
|-- scripts/
|-- tests/
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
|-- README.md
```