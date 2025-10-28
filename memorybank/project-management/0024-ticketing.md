<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Epic 0024 - Ticketing Tool
> **Last Updated**: October 28, 2025

Implement Pydantic AI-powered ticketing tool that enables agents to help users search, select, and purchase tickets for events, classes, courses, or sessions. The tool provides conversational ticket discovery and purchase workflows, integrating with existing session management and payment processing to deliver a seamless booking experience directly within the chat interface.

## High-Level Requirements

### 1. Ticket Tiers
- Multiple pricing tiers per event (e.g., General Admission, VIP, Early Bird)
- Each tier has:
  - **Name**: Descriptive tier name
  - **Price**: Fixed price per ticket
  - **Capacity Cap**: Maximum number of tickets available for this tier
- Tiers enable flexible pricing strategies and inventory management per event

### 2. Events
- Events are the core entity that tickets belong to
- Event metadata:
  - **Title**: Event name
  - **Description**: Detailed event information
  - **Schedule**: Date and timing information
  - **Start Time**: When the event begins
  - **End Time**: When the event concludes
  - **Performers/Speakers**: Who will be presenting (talks, performances, classes)
- Events can have multiple ticket tiers (one-to-many relationship)

### 3. Payment Processing
- **Primary Provider**: Stripe integration for payment processing
- **Architecture**: Payment provider abstraction to support multiple providers in future
- **Future Providers**: PayPal, Square, other payment processors (deferred)
- Secure payment handling with PCI compliance via provider APIs

### 4. Data Storage & Administration
- **Storage**: PostgreSQL tables for events, ticket tiers, and purchases
- **Administration**: No frontend UI for event configuration in v1
- **Data Entry**: Event and tier configuration via database scripts or SQL
- **Future**: Admin UI for event management (deferred to later phase)

## Detailed Requirements

### Inventory Management
- **Reservation Strategy**: First-come-first-served at payment completion (no temporary holds)
- **Real-Time Updates**: Ticket availability refreshed every 30 seconds (configurable interval)
- **Sold Out Detection**: Automatic tier and event status updates when capacity reached

### User Information & Profile Integration
- **Contact Collection**: Integrate with Profile Builder tool (Epic 0018) for name/email/phone
- **Multiple Ticket Purchases**: Users can purchase multiple tickets in single transaction
- **Attendee Information**: Configurable per event:
  - Require attendee names (on/off)
  - Require attendee email addresses (on/off)
  - Require attendee phone numbers for SMS (on/off)
- **Profile Association**: Link purchases to user profile for history and preferences

### Ticket Delivery & Confirmation
- **Delivery Method**: Email confirmation with ticket details and unique codes
- **Ticket Codes**: 16-character alphanumeric format (e.g., `DH3K-FK32-NPDR-S8K9`)
  - Excludes confusing characters: `I`, `1`, `O`, `0`
  - Generated at ticket creation during event initialization
- **Ticket Initialization**: Script to create event and pre-generate all tickets with codes
- **Confirmation Email**: Sent immediately after successful payment

### Event Lifecycle & Status
Event states:
- **Draft**: Event created but not published
- **Published**: Event visible and tickets available for sale
- **Sold Out**: All tickets sold (or all tiers sold out)
- **Cancelled**: Event cancelled (triggers refund process)
- **Completed**: Event has concluded

### Sales Period Configuration
All timing features are optional and configurable per event:
- **Early Bird Period**: Optional early pricing tier with start/end dates
- **Sales Cutoff**: Optional stop-selling date/time before event (e.g., 24 hours before)
- **Timezone Handling**: Store timezone with event start/end times for global audiences
- **Sales Window**: General sales start/end dates (optional)

### Refunds & Cancellations
- **Policy**: Follow payment provider (Stripe) refund policies
- **Event Cancellation**: Automatic full refunds when event cancelled
- **User Cancellation**: Support per provider capabilities and business rules
- **Refund Tracking**: Record refund transactions in database

### Agent Tool & Frontend Integration
- **Agent Tool**: Implement as `@agent.tool` (similar to `vector_search`, `directory_search`)
- **Astro Integration**: Event pages built with Astro framework
  - Each event gets dedicated page (`/events/{event-slug}`)
  - Event search/listing page available
- **Conversation Flow**:
  1. User asks: "What events are coming up?"
  2. Agent calls `search_events` tool, presents options
  3. User selects event and tier
  4. Agent collects attendee info (via Profile Builder integration)
  5. Agent initiates Stripe checkout session
  6. After payment: Generate tickets, send confirmation email
- **Private Events**: Configurable per event:
  - Private events hidden from general search
  - Default: Events are private (opt-in to public listing)

### Multi-Tenancy & Account Quotas
- **Account Association**: Events belong to specific accounts (multi-tenant)
- **Account Limits** (configurable per account):
  - Maximum number of active events
  - Maximum event capacity (total tickets per event)
  - Maximum ticket tiers per event
- **Free Events**: Support zero-price events (no payment processing)
- **Use Cases**:
  - PrepExcellence: SAT course sessions as events with limited seats
  - Conference organizers: Multi-day events with various session types
  - Webinars: Free virtual events with registration tracking

### SMS Notifications (Future Enhancement)
- **Provider**: Twilio integration for SMS confirmations
- **Triggers**: Purchase confirmation, event reminders, updates
- **Opt-in**: User consent required for SMS communications

## Implementation Decisions

### Payment Integration
- **Provider**: Stripe Checkout Sessions (hosted checkout page)
- **Benefits**: PCI-compliant, automatic webhook handling, simpler integration
- **Checkout Flow**: Agent generates Checkout Session URL → User redirects → Stripe handles payment

### Event Configuration
- **Location**: Account-specific event folders
  - Path: `backend/config/agent_configs/{account}/events/{event-slug}.yaml`
  - Example: `backend/config/agent_configs/prepexcellence/events/sat-winter-2026.yaml`
- **Format**: YAML configuration with essential parameters (see format below)
- **Versioning**: Config files tracked in git for audit trail

### Event & Ticket Initialization Scripts
- **Script 1**: `backend/scripts/create_event_config.py` (interactive)
  - Prompts for event details (title, dates, performers, etc.)
  - Prompts for tier information (name, price, capacity)
  - Generates YAML config file in account's events folder
  - User reviews and confirms config before proceeding
  
- **Script 2**: `backend/scripts/generate_tickets.py` (reads config)
  - Reads confirmed YAML config
  - Creates event record in database
  - Pre-generates all tickets with unique 16-character codes
  - Sets initial ticket status to "available"
  - Creates ticket tier records with capacity tracking
  
- **Script 3**: `backend/scripts/add_tickets_to_tier.py` (tier expansion)
  - Adds additional tickets to existing tier
  - Generates new unique codes for new tickets
  - Updates tier capacity in database

### Database Schema Conventions
- **Primary Keys**: UUID (GUID) for all tables
- **Foreign Keys**: UUID references to maintain consistency
- **Ticket Statuses**: `available`, `purchased`, `cancelled`, `refunded`, `checked_in`
- **Core Tables**:
  - `events` (id, account_id, event_slug, title, description, start_time, end_time, timezone, status, config, created_at, updated_at)
  - `ticket_tiers` (id, event_id, tier_name, price, capacity, available_count, sort_order, created_at, updated_at)
  - `tickets` (id, tier_id, ticket_code, status, created_at, updated_at)
  - `ticket_purchases` (id, ticket_id, purchaser_profile_id, stripe_session_id, amount_paid, purchased_at)
  - `event_attendees` (id, ticket_id, attendee_name, attendee_email, attendee_phone, checked_in_at)
  - `account_checkin_users` (id, account_id, email, name, is_active, created_at, updated_at)
  - `checkin_sessions` (id, checkin_user_id, session_token, last_activity_at, expires_at, created_at)

### Email Service
- **Provider**: Mailgun (configurable for future providers)
- **Templates**: Purchase confirmation, event updates, cancellations, reminders
- **Configuration**: Email provider settings in account config or global config

### Frontend Pages (Astro + Preact)
- **Event Listing**: `/events` (public events only, respects privacy settings)
- **Event Detail**: `/events/{event-slug}` (static shell + dynamic availability API)
- **Event Check-in**: `/events/{event-slug}/checkin` (password-protected)
- **Component Strategy**: 
  - Static Astro pages for event information
  - Preact islands for interactive elements (ticket selection, availability updates, check-in form)
  - Server-side rendering for real-time ticket availability

### Webhook Processing
- **Strategy**: Process Stripe webhooks immediately (simple approach)
- **Events**: `checkout.session.completed`, `charge.refunded`
- **Idempotency**: Track processed webhook IDs to prevent duplicate processing
- **Error Handling**: Log failed webhooks for manual review

### Check-in System
- **Check-in Page**: Account-level authentication for event check-in access
- **Authorization Model**:
  - Authorized users (by email) associated with account
  - Access to all events within their account
  - Session timeout: 30 minutes of inactivity
- **Check-in Methods**: 
  - Manual entry of 16-character ticket code
  - QR code scanning (future enhancement)
- **Validation**: 
  - Verify ticket exists and belongs to event
  - Check ticket status (must be "purchased", not "checked_in", "cancelled", or "refunded")
  - Update ticket status to "checked_in" with timestamp
- **Access Control**: Email-based login with session management
- **Astro Security**: Use middleware for authentication and session timeout

## Event Configuration Format

### Essential Parameters YAML Structure

```yaml
# backend/config/agent_configs/prepexcellence/events/sat-winter-2026.yaml

event:
  # Basic Information
  slug: "sat-winter-2026"                    # URL-friendly identifier
  title: "SAT Winter Prep Course 2026"      # Display name
  description: |
    12-week comprehensive SAT preparation course with Dr. Kaisar Alam.
    Includes practice tests, personalized feedback, and score guarantee.
  
  # Schedule (all times in specified timezone)
  timezone: "America/New_York"
  start_time: "2026-01-15T18:00:00"         # ISO 8601 format
  end_time: "2026-04-15T21:00:00"
  
  # Performers/Instructors
  performers:
    - name: "Dr. Kaisar Alam"
      role: "Lead Instructor"
      bio: "Expert SAT instructor with 15+ years experience"
  
  # Event Settings
  status: "draft"                           # draft, published, sold_out, cancelled, completed
  is_private: true                          # Hide from public event listing (default: true)
  
  # Sales Period (optional)
  sales_start: "2025-11-01T00:00:00"       # Optional: When tickets go on sale
  sales_end: "2026-01-14T23:59:59"         # Optional: Sales cutoff before event
  
  # Attendee Information Requirements
  require_attendee_names: true
  require_attendee_emails: false
  require_attendee_phones: false

# Ticket Tiers (created by script based on capacity input)
ticket_tiers:
  - name: "Early Bird"
    price: 1200.00                          # USD (use 0.00 for free events)
    capacity: 20                            # Total tickets for this tier
    description: "Register by December 1st for early bird pricing"
    sales_start: "2025-11-01T00:00:00"     # Optional: Tier-specific sales window
    sales_end: "2025-12-01T23:59:59"
    sort_order: 1                           # Display order
  
  - name: "Standard"
    price: 1500.00
    capacity: 30
    description: "Full course access with all materials"
    sales_start: "2025-12-02T00:00:00"
    sort_order: 2
  
  - name: "Late Registration"
    price: 1800.00
    capacity: 10
    description: "Join after course start (limited availability)"
    sales_start: "2026-01-16T00:00:00"
    sales_end: "2026-01-31T23:59:59"
    sort_order: 3

# Account Metadata (for quota enforcement)
account:
  account_slug: "prepexcellence"
  max_events: 10                            # Account limit
  max_event_capacity: 100                   # Max tickets per event
  max_tiers_per_event: 5                    # Max pricing tiers

# Generated Metadata (added by generate_tickets.py script)
metadata:
  config_version: "1.0"
  created_at: "2025-10-28T12:00:00Z"
  created_by: "admin@prepexcellence.com"
  last_modified: "2025-10-28T12:00:00Z"
  tickets_generated: false                  # Set to true after running generate_tickets.py
  total_tickets: 60                         # Sum of all tier capacities
```

### Minimal Free Event Example

```yaml
# backend/config/agent_configs/wyckoff/events/health-fair-2026.yaml

event:
  slug: "health-fair-2026"
  title: "Community Health Fair 2026"
  description: "Free health screenings and wellness information"
  timezone: "America/New_York"
  start_time: "2026-05-15T10:00:00"
  end_time: "2026-05-15T16:00:00"
  performers:
    - name: "Wyckoff Medical Staff"
      role: "Health Educators"
  status: "draft"
  is_private: false                         # Public event
  require_attendee_names: true
  require_attendee_emails: true
  require_attendee_phones: false

ticket_tiers:
  - name: "General Admission"
    price: 0.00                             # Free event
    capacity: 200
    description: "Free admission to health fair"
    sort_order: 1

account:
  account_slug: "wyckoff"
  max_events: 20
  max_event_capacity: 500
  max_tiers_per_event: 3

metadata:
  config_version: "1.0"
  created_at: "2025-10-28T12:00:00Z"
  tickets_generated: false
  total_tickets: 200
```

## Account-Level Check-in Authentication

### Authentication Architecture

**Email-Based Login with Session Management**

1. **Authorized User Management**:
   - Account admins can add/remove authorized check-in users
   - Each authorized user identified by email address
   - Stored in `account_checkin_users` table with account_id FK
   - `is_active` flag for enabling/disabling access

2. **Session Management**:
   - Session duration: 30 minutes of inactivity
   - Session token stored in HTTP-only cookie: `salient_checkin_session`
   - `last_activity_at` updated on each check-in action
   - Automatic logout after 30 minutes of no activity
   - Session data in `checkin_sessions` table

3. **Access Scope**:
   - Authorized user can access all events within their account
   - Single login grants access to all account events
   - No per-event passwords needed

### Astro Implementation (Middleware-Based)

```typescript
// src/middleware/checkin-auth.ts
import type { MiddlewareHandler } from 'astro';

export const onRequest: MiddlewareHandler = async ({ request, locals, redirect }, next) => {
  const url = new URL(request.url);
  
  // Only protect /events/{slug}/checkin pages
  if (url.pathname.endsWith('/checkin')) {
    const sessionToken = request.headers.get('cookie')
      ?.split(';')
      .find(c => c.trim().startsWith('salient_checkin_session='))
      ?.split('=')[1];
    
    if (!sessionToken) {
      return redirect(`/checkin-login?redirect=${encodeURIComponent(url.pathname)}`);
    }
    
    // Verify session via backend API
    const sessionValid = await fetch(`${API_BASE}/api/checkin/verify-session`, {
      headers: { 'Authorization': `Bearer ${sessionToken}` }
    });
    
    if (!sessionValid.ok) {
      // Session expired or invalid
      return redirect(`/checkin-login?redirect=${encodeURIComponent(url.pathname)}&error=session_expired`);
    }
    
    const sessionData = await sessionValid.json();
    
    // Check 30-minute inactivity timeout
    const lastActivity = new Date(sessionData.last_activity_at);
    const now = new Date();
    const minutesSinceActivity = (now.getTime() - lastActivity.getTime()) / (1000 * 60);
    
    if (minutesSinceActivity > 30) {
      // Session timed out due to inactivity
      await fetch(`${API_BASE}/api/checkin/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}` }
      });
      return redirect(`/checkin-login?redirect=${encodeURIComponent(url.pathname)}&error=timeout`);
    }
    
    // Update last_activity_at
    await fetch(`${API_BASE}/api/checkin/update-activity`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${sessionToken}` }
    });
    
    // Store session data for page access
    locals.checkinUser = sessionData.user;
    locals.checkinAccount = sessionData.account;
  }
  
  return next();
};
```

### Backend API Endpoints

**POST /api/checkin/login**
- Request: `{ email: string, account_slug: string }`
- Verify email exists in `account_checkin_users` for account
- Verify `is_active = true`
- Generate session token (UUID)
- Create record in `checkin_sessions` table
- Set `expires_at = now + 8 hours` (absolute max)
- Return session token in HTTP-only cookie

**GET /api/checkin/verify-session**
- Request: `Authorization: Bearer {session_token}`
- Verify session exists and not expired
- Return session data with user and account info

**POST /api/checkin/update-activity**
- Request: `Authorization: Bearer {session_token}`
- Update `last_activity_at = now()`

**POST /api/checkin/logout**
- Request: `Authorization: Bearer {session_token}`
- Delete session record from `checkin_sessions`
- Clear cookie

### Check-in Login Page

```astro
---
// src/pages/checkin-login.astro
const { redirect, error } = Astro.url.searchParams;
---
<html>
  <body>
    <h1>Event Check-in Login</h1>
    {error === 'timeout' && <p class="error">Session expired due to inactivity</p>}
    {error === 'session_expired' && <p class="error">Your session has expired</p>}
    
    <form method="POST" action="/api/checkin/login">
      <input type="email" name="email" placeholder="Your email" required />
      <input type="hidden" name="redirect" value={redirect || '/events'} />
      <button type="submit">Login to Check-in System</button>
    </form>
    
    <p class="info">
      ⏱️ Sessions expire after 30 minutes of inactivity<br/>
      🔒 Maximum session length: 8 hours
    </p>
  </body>
</html>
```

### Security Features

- ✅ Email-based authorization (no passwords exposed in configs)
- ✅ HTTP-only cookies (prevent XSS attacks)
- ✅ Session tokens (UUID v4, cryptographically random)
- ✅ Inactivity timeout (30 minutes)
- ✅ Absolute session expiration (8 hours max)
- ✅ Account-scoped access (user can only access their account's events)
- ✅ Activity tracking (last_activity_at updated on each action)

