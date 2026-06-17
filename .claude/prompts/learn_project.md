You are an expert software engineering assistant. Your task is to study this codebase deeply and create a high-quality CLAUDE.md file that will help future AI coding agents understand and work on this project safely.

First, inspect the repository structure, source files, config files, package/dependency files, scripts, tests, docs, environment examples, CI/CD files, and any architecture-relevant folders.

Do not modify code yet. Only analyze.

Create a CLAUDE.md file at the repository root.

The CLAUDE.md should be accurate, practical, and specific to this project. Avoid generic advice. If something is uncertain, say so clearly.

Include the following sections:

# CLAUDE.md

## Project Overview
Explain what this project does, who/what it is for, and the main domain concepts.

## Tech Stack
List the languages, frameworks, libraries, runtime versions, package managers, databases, queues, external APIs, and infrastructure tools used.

## Repository Structure
Explain the important folders and files, including what each major directory is responsible for.

## How to Run the Project
Include exact commands for:
- installing dependencies
- setting up environment variables
- running the app locally
- running in development mode
- building for production
- starting production mode

## Environment Variables
Document all required and optional environment variables found in the codebase.
For each variable, explain:
- purpose
- required/optional
- example value if safe
- where it is used

Do not expose secrets.

## Common Development Commands
List commands for:
- linting
- formatting
- type checking
- testing
- database migrations
- seeding
- code generation
- cleaning/resetting local state

## Architecture
Describe the main architecture:
- frontend/backend structure
- routing
- data flow
- state management
- API boundaries
- database access layer
- authentication/authorization
- background jobs
- integrations
- error handling
- logging

## Key Files and Modules
List the most important files/modules and explain their responsibilities.

## Coding Conventions
Infer and document project-specific conventions:
- naming
- folder organization
- import style
- component/service patterns
- API patterns
- testing style
- error-handling style

## Testing Guide
Explain how tests are organized and how to run them.
Mention test frameworks, mock strategy, fixtures, and any known gaps.

## Database and Data Model
If the project uses a database, document:
- ORM/query tool
- schema location
- migration workflow
- main models/tables
- relationships
- seed data

## API Documentation
If APIs exist, document:
- route structure
- key endpoints
- request/response patterns
- auth requirements
- validation approach

## Deployment
Explain how the project appears to be deployed:
- hosting platform
- build command
- start command
- CI/CD
- Docker usage
- environment requirements

## Security Notes
Document important security considerations:
- auth
- secrets
- permissions
- input validation
- unsafe areas to avoid changing casually

## AI Agent Instructions
Give specific instructions for future AI assistants working on this repo:
- what to inspect before making changes
- how to run checks
- what files are sensitive
- what patterns to follow
- what not to do
- how to make safe changes

## Known Issues / Uncertainties
List anything unclear, missing, outdated, or inferred from limited evidence.

## Quick Start for Future Agents
Provide a short checklist an AI agent should follow before editing code.

Important rules:
- Be specific to this repository.
- Cite file paths when explaining behavior.
- Prefer facts from code over assumptions.
- Do not invent commands.
- If a command is not present, say “No explicit command found.”
- Keep the file concise but complete.
- After creating CLAUDE.md, summarize what you learned and mention any uncertainties.

Recommended CLAUDE.md structure:

# CLAUDE.md

## Project Overview
## Tech Stack
## Repository Structure
## How to Run the Project
## Environment Variables
## Common Development Commands
## Architecture
## Key Files and Modules
## Coding Conventions
## Testing Guide
## Database and Data Model
## API Documentation
## Deployment
## Security Notes
## AI Agent Instructions
## Known Issues / Uncertainties
## Quick Start for Future Agents