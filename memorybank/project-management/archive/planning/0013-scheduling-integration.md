<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Epic 0013 - Scheduling Integration

> Goal: Implement comprehensive appointment scheduling capabilities using Nylas (primary), Calendly, and CRM-based scheduling to enable seamless meeting booking directly from chat conversations.

## Scope & Approach

### Scheduling Capabilities
- **Nylas Integration**: Primary calendar API for Google Calendar, Outlook, and Exchange
- **Calendly Integration**: Self-service scheduling with professional booking pages
- **CRM Scheduling**: Direct integration with Zoho, Salesforce, and HubSpot calendars
- **Multi-Platform Support**: Unified scheduling across different calendar providers
- **Intelligent Booking**: Context-aware scheduling based on conversation content

### Target Use Cases
- **Sales Appointments**: Direct booking from sales conversations
- **Product Demos**: Schedule demonstrations based on customer interests
- **Consultation Calls**: Book technical or service consultations
- **Follow-up Meetings**: Schedule next steps and check-ins
- **Team Coordination**: Internal scheduling for sales team collaboration

## Features & Requirements

### [ ] 0013-001 - FEATURE - Nylas Calendar Integration

#### [ ] 0013-001-001 - TASK - Nylas Setup & Authentication
- [ ] 0013-001-001-01 - CHUNK - Nylas account and API configuration
  - SUB-TASKS:
    - Set up Nylas account and application registration
    - Configure OAuth authentication for calendar providers
    - Implement secure token storage and refresh logic
    - Add support for Google Calendar, Outlook, and Exchange
    - Create calendar provider detection and routing
    - Acceptance: Nylas fully configured with multi-provider calendar access

- [ ] 0013-001-001-02 - CHUNK - Calendar service implementation
  - SUB-TASKS:
    - Create `backend/app/services/calendar_service.py`
    - Implement calendar CRUD operations via Nylas API
    - Add availability checking and conflict detection
    - Create timezone handling and conversion utilities
    - Add calendar synchronization and update handling
    - Acceptance: Complete calendar service with full Nylas integration

#### [ ] 0013-001-002 - TASK - Availability Management
- [ ] 0013-001-002-01 - CHUNK - Real-time availability checking
  - SUB-TASKS:
    - Implement free/busy time lookup across calendars
    - Add working hours and time zone preferences
    - Create buffer time and meeting preparation periods
    - Add conflict detection and resolution
    - Implement availability caching for performance
    - Acceptance: Accurate, real-time availability checking

- [ ] 0013-001-002-02 - CHUNK - Scheduling intelligence
  - SUB-TASKS:
    - Implement smart time slot suggestions
    - Add meeting type-specific duration handling
    - Create optimal timing recommendations
    - Add consideration for participant time zones
    - Implement scheduling preferences and constraints
    - Acceptance: Intelligent scheduling recommendations improve booking success

### [ ] 0013-002 - FEATURE - Calendly Integration

#### [ ] 0013-002-001 - TASK - Calendly API Integration
- [ ] 0013-002-001-01 - CHUNK - Calendly setup and embedding
  - SUB-TASKS:
    - Set up Calendly account and API access
    - Implement Calendly widget embedding in chat
    - Create dynamic event type selection based on conversation
    - Add Calendly webhook handling for booking events
    - Implement booking confirmation and cancellation handling
    - Acceptance: Seamless Calendly integration within chat interface

- [ ] 0013-002-001-02 - CHUNK - Calendly workflow automation
  - SUB-TASKS:
    - Implement automatic event type recommendation
    - Add custom questions and intake forms
    - Create follow-up automation for booked meetings
    - Add integration with conversation context
    - Implement booking analytics and optimization
    - Acceptance: Automated Calendly workflows enhance booking experience

#### [ ] 0013-002-002 - TASK - Hybrid Scheduling Strategy
- [ ] 0013-002-002-01 - CHUNK - Nylas vs Calendly routing
  - SUB-TASKS:
    - Create intelligent routing between Nylas and Calendly
    - Add user preference detection and selection
    - Implement fallback strategies for failed bookings
    - Create unified booking experience across platforms
    - Add booking method analytics and optimization
    - Acceptance: Seamless user experience regardless of underlying platform

### [ ] 0013-003 - FEATURE - CRM Calendar Integration

#### [ ] 0013-003-001 - TASK - Zoho Calendar Integration
- [ ] 0013-003-001-01 - CHUNK - Zoho CRM calendar access
  - SUB-TASKS:
    - Implement Zoho CRM calendar API integration
    - Add sales rep availability checking
    - Create automatic meeting creation in Zoho
    - Add lead association and opportunity linking
    - Implement Zoho-specific scheduling workflows
    - Acceptance: Direct scheduling through Zoho CRM calendars

#### [ ] 0013-003-002 - TASK - Salesforce & HubSpot Calendar Integration
- [ ] 0013-003-002-01 - CHUNK - Multi-CRM calendar support
  - SUB-TASKS:
    - Implement Salesforce calendar integration
    - Add HubSpot meeting scheduling capabilities
    - Create unified CRM calendar interface
    - Add cross-CRM availability checking
    - Implement CRM-specific meeting workflows
    - Acceptance: Comprehensive CRM calendar integration

### [ ] 0013-004 - FEATURE - Chat-Integrated Scheduling

#### [ ] 0013-004-001 - TASK - In-Chat Booking Interface
- [ ] 0013-004-001-01 - CHUNK - Scheduling UI components
  - SUB-TASKS:
    - Create in-chat calendar widget for time selection
    - Add meeting type selection and duration options
    - Implement timezone detection and conversion
    - Create booking confirmation and details collection
    - Add meeting preparation and agenda setting
    - Acceptance: Professional in-chat scheduling interface

- [ ] 0013-004-001-02 - CHUNK - Context-aware scheduling
  - SUB-TASKS:
    - Use conversation context to suggest meeting types
    - Add automatic agenda generation from chat history
    - Create personalized meeting invitations
    - Implement follow-up scheduling based on outcomes
    - Add meeting analytics and success tracking
    - Acceptance: Intelligent scheduling based on conversation content

#### [ ] 0013-004-002 - TASK - Meeting Management
- [ ] 0013-004-002-01 - CHUNK - Meeting lifecycle management
  - SUB-TASKS:
    - Implement meeting confirmation and reminder system
    - Add rescheduling and cancellation capabilities
    - Create meeting preparation and material sharing
    - Add post-meeting follow-up automation
    - Implement meeting outcome tracking and analysis
    - Acceptance: Complete meeting lifecycle management

### [ ] 0013-005 - FEATURE - Scheduling Analytics & Optimization

#### [ ] 0013-005-001 - TASK - Booking Analytics
- [ ] 0013-005-001-01 - CHUNK - Scheduling performance metrics
  - SUB-TASKS:
    - Track booking conversion rates and abandonment
    - Add time-to-book and scheduling friction analysis
    - Create availability utilization metrics
    - Implement meeting show-up and cancellation tracking
    - Add customer satisfaction scoring for scheduling
    - Acceptance: Comprehensive scheduling performance insights

- [ ] 0013-005-001-02 - CHUNK - Optimization recommendations
  - SUB-TASKS:
    - Implement optimal time slot recommendations
    - Add scheduling flow optimization suggestions
    - Create capacity planning and availability optimization
    - Add A/B testing for scheduling interfaces
    - Implement predictive analytics for booking success
    - Acceptance: Data-driven scheduling optimization improving conversion

## Technical Architecture

### Scheduling Service Flow
```
Chat Request → Availability Check → Platform Selection → Booking Interface → Confirmation
                      ↓                    ↓                ↓               ↓
               Calendar APIs ←→ Scheduling Logic ←→ Meeting Creation ←→ Notifications
```

### Database Schema Extensions
```sql
-- Meeting and appointment management
appointments:
  id (GUID, PK)
  session_id (GUID, FK → sessions.id)
  conversation_id (GUID, FK → conversations.id)
  platform (VARCHAR) -- nylas, calendly, zoho, salesforce, hubspot
  external_event_id (VARCHAR)
  attendee_email (VARCHAR)
  attendee_name (VARCHAR)
  meeting_type (VARCHAR) -- sales_call, demo, consultation, follow_up
  scheduled_datetime (TIMESTAMP)
  duration_minutes (INTEGER)
  timezone (VARCHAR)
  status (VARCHAR) -- scheduled, confirmed, cancelled, completed, no_show
  meeting_url (VARCHAR) -- for virtual meetings
  agenda (TEXT)
  preparation_notes (TEXT)
  created_at (TIMESTAMP)
  updated_at (TIMESTAMP)

-- Calendar integration tracking
calendar_integrations:
  id (GUID, PK)
  user_email (VARCHAR)
  platform (VARCHAR) -- nylas, calendly, zoho
  external_calendar_id (VARCHAR)
  access_token (TEXT, encrypted)
  refresh_token (TEXT, encrypted)
  token_expires_at (TIMESTAMP)
  is_active (BOOLEAN)
  last_sync_at (TIMESTAMP)
  sync_status (VARCHAR)

-- Scheduling preferences and availability
scheduling_preferences:
  id (GUID, PK)
  user_identifier (VARCHAR) -- email or user ID
  platform_preference (VARCHAR) -- nylas, calendly, crm
  default_duration (INTEGER)
  buffer_time_minutes (INTEGER)
  working_hours (JSONB) -- day-specific working hours
  timezone (VARCHAR)
  auto_confirm (BOOLEAN)
  reminder_preferences (JSONB)
  updated_at (TIMESTAMP)
```

### Configuration Schema (app.yaml)
```yaml
scheduling:
  nylas:
    enabled: true
    client_id: "nylas_client_id"
    redirect_uri: "https://yourdomain.com/auth/nylas/callback"
    
  calendly:
    enabled: true
    organization_uri: "https://calendly.com/your-org"
    default_event_type: "sales-consultation"
    
  crm_calendars:
    zoho:
      enabled: true
      calendar_module: "Events"
    salesforce:
      enabled: false
    hubspot:
      enabled: false
      
  defaults:
    meeting_duration: 30  # minutes
    buffer_time: 15  # minutes between meetings
    advance_booking_days: 14
    cancellation_policy_hours: 24
    reminder_times: [24, 1]  # hours before meeting
    
  working_hours:
    monday: { start: "09:00", end: "17:00" }
    tuesday: { start: "09:00", end: "17:00" }
    wednesday: { start: "09:00", end: "17:00" }
    thursday: { start: "09:00", end: "17:00" }
    friday: { start: "09:00", end: "17:00" }
    saturday: { enabled: false }
    sunday: { enabled: false }
    
  meeting_types:
    sales_call:
      duration: 30
      buffer: 15
      description: "Sales consultation call"
    product_demo:
      duration: 45
      buffer: 15
      description: "Product demonstration"
    technical_consultation:
      duration: 60
      buffer: 30
      description: "Technical consultation"
```

### Integration Points
- **Nylas API**: Primary calendar integration for Google, Outlook, Exchange
- **Calendly API**: Self-service scheduling platform
- **CRM APIs**: Zoho, Salesforce, HubSpot calendar integration
- **0012**: Email service for confirmations and reminders
- **0008**: Sales agent for context-aware scheduling
- **Chat Endpoints**: In-chat scheduling interface

### Dependencies
- **0012**: Outbound Email (for confirmations and reminders)
- **0008**: Sales Agent (for meeting context and follow-up)
- **Calendar Providers**: Google Calendar, Outlook, Exchange access
- **CRM Systems**: Zoho, Salesforce, HubSpot integration

### Performance Considerations
- **Availability Caching**: Cache calendar data for faster availability checks
- **Rate Limiting**: Respect calendar API limits and quotas
- **Timezone Handling**: Accurate timezone conversion and display
- **Concurrent Booking**: Handle simultaneous booking attempts gracefully
- **Webhook Processing**: Asynchronous handling of calendar events

## Success Criteria
1. **Booking Conversion**: 80%+ conversion from scheduling intent to confirmed meeting
2. **Platform Integration**: Seamless experience across Nylas, Calendly, and CRM calendars
3. **Availability Accuracy**: 99%+ accuracy in availability checking and conflict prevention
4. **User Experience**: Intuitive in-chat scheduling requiring minimal clicks
5. **Meeting Success**: High show-up rates and positive meeting outcomes
6. **Integration Reliability**: Robust calendar synchronization with minimal errors
7. **Performance**: Sub-second availability checks and smooth booking flow

This epic creates professional scheduling capabilities that remove friction from the sales process and enable immediate conversion from conversation to committed meetings.
