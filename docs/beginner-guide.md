# Beginner Guide – AI-on-Demand Metadata Catalogue

A beginner-friendly guide to help new contributors get started with the AI-on-Demand Metadata Catalogue.

---

## Overview
The AI-on-Demand Metadata Catalogue is a platform that provides a unified REST API to access metadata of AI resources such as datasets, models, and research papers. It integrates with platforms like Hugging Face, OpenML, and Zenodo.

This guide helps new contributors understand the project and start contributing easily.

---

## Project Structure (High-Level)
- `src/` → Core backend logic (FastAPI)
- `docs/` → Documentation
- `scripts/` → Utility scripts (setup, export, etc.)
- `docker-compose.yaml` → Multi-service setup (DB, Keycloak, etc.)

---

## How to Get Started

### 🔹 Option 1: Quick Contribution (Recommended)
If you are new:
1. Fork the repository  
2. Explore the `docs/` folder  
3. Make small improvements (typos, explanations, examples)  
4. Submit a Pull Request  

Example:
- Fix a typo in documentation  
- Improve explanation of an API endpoint  

👉 This does not require setting up the full local environment.

---

### 🔹 Option 2: Full Development Setup (Advanced)
For backend contributions:
- Requires Docker, MySQL, Keycloak, Elasticsearch  
- Follow the Hosting documentation for setup  

---

## Contribution Workflow

1. Fork the repository  
2. Create a new branch  
3. Make your changes  
4. Commit and push  
5. Open a Pull Request  

For more details, see the contributing guide.

---

## Tips for Beginners

- Start with documentation contributions  
- Avoid complex backend or infrastructure issues initially  
- Check if an issue is already assigned before working on it  
- Read existing documentation before making changes  

---

## Common Challenges

- Docker setup can be complex  
- Windows users may face dependency issues (e.g., mysqlclient)  
- The project uses multiple services, which can be overwhelming at first  

---

## Useful Links

- Contributing Guide → `docs/contributing.md`  
- Hosting Guide → `docs/hosting`  
- API Usage → `docs/using`  

---

## Recommended Path

Start with small contributions like:
- Improving documentation  
- Fixing typos  
- Adding beginner-friendly explanations  

Once comfortable, move to backend features and API improvements.
