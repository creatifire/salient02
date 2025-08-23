# Project Brief

## Purpose of System
    - Answer questions about a company's products and services, based on:
        - Company's Website Content (HTML)
        - Other Website Content (HTML)
        - Company provided white papers (PDF)
        - Company provided data sheets (PDF)
    - Collect preferences and build a profile of the customer
    - Maintain session history
    - Maintain Chat history
    - Connect the customer to the local sales rep
    - Send a conversation summary to the customer after:
        - a period of inactivity
        - when the conversation ends

## A Sales Bot powered by:
    - Large Language Model (LLM)
        - OpenRouter
    - Memory
        - Chat History
        - Chat Summary
        - Customer Profile
            - Products of Interest
            - Services of Interest
            - Customer Name
            - Customer Contact Information
                - Phone Number
                - Email Address
                - Physical Address
                    - Street Address
                    - City
                    - State
                    - Zip
        - Past emails
    - Knowledge
        - Indexed from Vector Database

## Config File
    - YAML
        - Which LLM to use
        - Which Agent to Use
        - Which Vector Database
            - Pinecone
            - Which Pinecone Database
    - Environment Variables
        - OpenRouter API Key
        - Pinecone API Key

## Architecture
    - RAG Application
    - Memories in a Relational Database (Postgres)
    - Knowledge Indexed in a Vector Database (Pinecone)
- [Technology Stack](./architecture/technology-stack.md)
- [Technical Constraints](./architecture/technical-constraints.md)
- [Code Organization](./architecture/code-organization.md)
- [Data Model & ER Diagram](./architecture/datamodel.md)
- [SalesBot Integration Options](./architecture/salesbot-integration.md)
- [Demo Integration Strategy](./architecture/demo-integrations.md)

## Planning
- [Plans](./project-management/0000-epics.md) contains the high level plans, with each file getting its own epic file
    - [Preliminary Design](./project-management/0001-preliminary-design.md)
    - [Baseline Connectivity](./project-management/0002-baseline-connectivity.md)
    - [Website & HTMX Chatbot](./project-management/0003-website-htmx-chatbot.md)
    - [Chat Memory & Persistence](./project-management/0004-chat-memory.md)

## Project Standards

### Coding Standards
- [Python Coding Standards](./standards/coding-standards-py.md)
- [JavaScript Coding Standards](./standards/coding-standards-js.md)
- [TypeScript Coding Standards](./standards/coding-standards-ts.md)

### Documentation Standards
- [Commit Message Conventions](./standards/commit-messages.md)
- [Python Code Commenting Best Practices](./standards/code-comments-py.md)
- [JavaScript/TypeScript Code Commenting Best Practices](./standards/code-comments-ts.md)