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

## Planning
- [Plans](./project-management/0000-epics.md) contains the high level plans, with each file getting its own epic file

## Project Standards
- [Commit Message Conventions](./commit-messages.md)