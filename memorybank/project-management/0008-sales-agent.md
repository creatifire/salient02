# Epic 0008 - Sales Agent (Milestone 1)

> Goal: Implement Milestone 1 sales agent with essential CRM integration, customer profile capture, conversation summaries, and appointment scheduling to establish the foundation for a complete sales automation system.

## Scope & Approach

### Milestone 1 Core Capabilities
- **Page Source Tracking**: Track which website page initiated each conversation
- **Customer Profile Capture**: Collect and store customer information during conversations
- **Conversation Summaries**: Generate and send summaries to customers and sales team
- **Appointment Scheduling**: Enable booking of sales appointments
- **CRM Integration**: Log leads and conversations into Zoho, Salesforce, and HubSpot
- **RAG-Powered Responses**: Use ingested website content to provide accurate product information

### Target Workflows
- **Lead Capture**: Track page source and capture customer details during conversation
- **Content-Informed Responses**: Use website content from vector database for accurate answers
- **Summary Generation**: Create conversation summaries for follow-up
- **Appointment Booking**: Schedule sales meetings directly from chat
- **CRM Sync**: Automatically log leads and conversations to CRM systems

## Features & Requirements

### [ ] 0008-001 - FEATURE - Page Source & Lead Tracking

#### [ ] 0008-001-001 - TASK - Request Source Tracking
- [ ] 0008-001-001-01 - CHUNK - Page referrer capture
  - SUB-TASKS:
    - Add `referrer_page` field to sessions table
    - Track `document.referrer` and custom page parameters in chat widgets
    - Store page source in session metadata for all chat integration strategies
    - Add API endpoints to retrieve lead source analytics
    - Acceptance: Every conversation tracks the originating website page

#### [ ] 0008-001-002 - TASK - Customer Profile Integration
- [ ] 0008-001-002-01 - CHUNK - Enhanced profile capture
  - SUB-TASKS:
    - Extend existing `profiles` table with company and industry fields
    - Build on 0004-006 Profile Data Collection functionality
    - Add real-time profile extraction during conversations
    - Create profile completion prompts and validation
    - Acceptance: Customer profiles captured and linked to conversations
    - Dependencies: Requires 0004-006 completion

### [ ] 0008-002 - FEATURE - RAG-Powered Sales Responses

#### [ ] 0008-002-001 - TASK - Vector Database Integration
- [ ] 0008-002-001-01 - CHUNK - Pinecone sales knowledge base
  - SUB-TASKS:
    - Configure Pinecone namespace for sales agent content
    - Integrate retrieval into chat endpoints for contextual responses
    - Add citation tracking for website source attribution
    - Implement relevance scoring and content ranking
    - Acceptance: Sales agent provides accurate, website-sourced responses
    - Dependencies: Requires 0010 Website Content Ingestion completion

### [ ] 0008-003 - FEATURE - Conversation Summaries & Communication

#### [ ] 0008-003-001 - TASK - Summary Generation & Distribution
- [ ] 0008-003-001-01 - CHUNK - Conversation summarization
  - SUB-TASKS:
    - Build on 0004-012-003 Conversation Summarization functionality
    - Create sales-specific summary templates (lead info, interests, next steps)
    - Add email delivery capability for summary distribution
    - Implement summary customization for customer vs. sales team
    - Acceptance: Automated conversation summaries sent to relevant parties
    - Dependencies: Requires 0004-012 Conversation Hierarchy completion

### [ ] 0008-004 - FEATURE - Appointment Scheduling

#### [ ] 0008-004-001 - TASK - Calendar Integration
- [ ] 0008-004-001-01 - CHUNK - Scheduling system implementation
  - SUB-TASKS:
    - Integrate with Google Calendar API for availability checking
    - Add Calendly integration for seamless booking flow
    - Create appointment booking interface within chat
    - Add timezone handling and confirmation emails
    - Implement appointment modification and cancellation
    - Acceptance: Customers can book sales appointments directly from chat

### [ ] 0008-005 - FEATURE - CRM Integration

#### [ ] 0008-005-001 - TASK - Core CRM Connectivity
- [ ] 0008-005-001-01 - CHUNK - Zoho CRM integration
  - SUB-TASKS:
    - Implement Zoho CRM API integration for lead creation
    - Add contact and opportunity logging functionality
    - Create conversation history sync to CRM activities
    - Add custom field mapping for profile data
    - Acceptance: Leads and conversations automatically logged to Zoho CRM

- [ ] 0008-005-001-02 - CHUNK - Salesforce integration
  - SUB-TASKS:
    - Implement Salesforce API integration for lead management
    - Add opportunity creation and activity logging
    - Create conversation attachment and note sync
    - Add profile data mapping to Salesforce fields
    - Acceptance: Complete lead lifecycle tracked in Salesforce

- [ ] 0008-005-001-03 - CHUNK - HubSpot integration
  - SUB-TASKS:
    - Implement HubSpot API integration for contact and deal creation
    - Add conversation history as HubSpot activities
    - Create custom property mapping for captured profile data
    - Add deal pipeline automation based on conversation outcomes
    - Acceptance: Leads and conversations fully integrated with HubSpot

## Technical Architecture

### Sales Agent Infrastructure
```
Prospect → Sales Agent → Lead Qualification → Product Recommendations
                ↓              ↓                       ↓
         Pricing Engine → Quote Generation → CRM Integration → Sales Team
                                                    ↓
Marketing Automation ← Follow-up Sequences ← Pipeline Management
```

### CRM Integration Schema
```sql
-- CRM system mappings
crm_integrations:
  id (GUID, PK)
  tenant_id (GUID, FK → tenants.id)
  crm_type (VARCHAR) -- salesforce, hubspot, dynamics, pipedrive
  api_credentials (JSONB, encrypted)
  field_mappings (JSONB)
  sync_settings (JSONB)
  last_sync (TIMESTAMP)

-- Lead and opportunity tracking
sales_leads:
  id (GUID, PK)
  session_id (GUID, FK → sessions.id)
  conversation_id (GUID, FK → conversations.id)
  crm_lead_id (VARCHAR)
  qualification_score (INTEGER)
  lead_source (VARCHAR)
  company_size (VARCHAR)
  budget_range (VARCHAR)
  timeline (VARCHAR)
  decision_maker (BOOLEAN)
  created_at (TIMESTAMP)
  qualified_at (TIMESTAMP)

-- Product interactions and recommendations
product_interactions:
  id (GUID, PK)
  lead_id (GUID, FK → sales_leads.id)
  product_id (VARCHAR)
  interaction_type (VARCHAR) -- viewed, configured, quoted
  requirements (JSONB)
  recommendations (JSONB)
  created_at (TIMESTAMP)
```

### Configuration Schema (app.yaml)
```yaml
sales_agent:
  page_tracking:
    enabled: true
    track_utm_parameters: true
    track_referrer_domain: true
  
  profile_capture:
    required_fields:
      - customer_name
      - email
    optional_fields:
      - phone
      - company
      - industry
  
  vector_database:
    provider: "pinecone"  # pinecone, pgvector
    namespace: "sales_content"
    similarity_threshold: 0.7
    max_results: 5
  
  conversation_summaries:
    auto_generate: true
    email_enabled: true
    send_to_customer: true
    send_to_sales_team: true
    template_style: "professional"  # professional, casual, detailed
  
  appointment_scheduling:
    enabled: true
    calendar_provider: "google"  # google, calendly, outlook
    default_duration: 30  # minutes
    advance_booking_days: 14
    timezone_handling: "auto_detect"
  
  crm_integration:
    zoho:
      enabled: false
      api_domain: "www.zohoapis.com"
    salesforce:
      enabled: false
      sandbox_mode: true
    hubspot:
      enabled: false
      portal_id: null
```

### Integration Points
- **Vector Database**: Pinecone for website content retrieval and response generation
- **CRM Platforms**: Zoho CRM, Salesforce, HubSpot for lead and opportunity management
- **Calendar Systems**: Google Calendar, Calendly for appointment scheduling
- **Email Services**: SMTP, SendGrid, or Mailgun for summary distribution
- **Content Sources**: WordPress XML dumps and Astro websites via Epic 0010

### Dependencies
- **0004-006**: Profile Data Collection (foundation for customer capture)
- **0004-012**: Conversation Hierarchy & Management (required for summaries)
- **0010**: Website Content Ingestion (provides content for RAG)
- **0011**: Vector Database Integration (required for RAG responses)
- **0012**: Outbound Email Integration (required for summary distribution)
- **0013**: Scheduling Integration (required for appointment booking)
- **Multi-Agent Infrastructure**: Basic agent routing from Epic 0005

### Performance & Analytics
- **Lead Source Tracking**: Conversion rates by website page
- **Profile Completion**: Percentage of conversations with complete customer data
- **Summary Delivery**: Success rates for email distribution
- **Appointment Booking**: Conversion from chat to scheduled meetings
- **CRM Sync Health**: Success rates and error tracking for CRM integrations

## Success Criteria (Milestone 1)
1. **Page Source Tracking**: 100% of conversations track originating website page
2. **Profile Capture**: 80% of qualified conversations capture customer contact information
3. **RAG Responses**: Sales agent provides accurate, website-sourced answers
4. **Summary Generation**: Automated summaries sent to customers and sales team
5. **Appointment Booking**: Customers can schedule meetings directly from chat
6. **CRM Integration**: At least one CRM system (Zoho, Salesforce, or HubSpot) fully operational
7. **Response Quality**: Agent responses are contextually relevant using ingested website content

This milestone establishes the foundation for a complete sales automation system by implementing core lead capture, content-aware responses, and essential CRM integration.
