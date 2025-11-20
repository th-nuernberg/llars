# LLARS Documentation

Welcome to the LLARS (LLM-Assisted Rating System) Platform documentation.

## Overview

LLARS is a comprehensive platform for email rating and analysis using Large Language Models (LLMs). The system provides:

- **Email Thread Management**: Organize and rate email conversations
- **LLM Integration**: Leverage advanced AI models for content analysis
- **User Management**: Keycloak-based authentication and authorization
- **Collaborative Editing**: Real-time document collaboration with Yjs
- **RAG Pipeline**: Retrieval-Augmented Generation for contextual responses

## Architecture

The LLARS platform consists of multiple microservices:

- **Flask Backend** (Port 55081): REST API and business logic
- **Vue Frontend** (Port 55173): User interface
- **Keycloak** (Port 55090): Authentication and authorization
- **MariaDB** (Port 55306): Primary database
- **YJS Server** (Port 55082): Real-time collaboration
- **Nginx** (Port 55080): Reverse proxy and static file serving
- **MkDocs** (Port 55800): Documentation server

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Run `docker compose up -d`
4. Access the application at `http://localhost:55080`

## Development

See the [Getting Started](getting-started/installation.md) section for detailed installation and configuration instructions.
