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

### Ticket Code Format
- **Format**: `DH3K-FK32-NPDR-S8K9` (4 groups of 4 alphanumeric characters)
- **Character Set**: A-Z, 2-9 (excluding I, 1, O, 0 to prevent confusion)
- **Storage**: Store with hyphens in database (19 characters including hyphens)
- **Display**: Use stored format as-is for consistency
- **Generation**: Random unique codes validated against existing tickets

### Account Quotas Management
- **Storage**: Dedicated `account_quotas` table
- **Schema**: 
  - `id` (UUID primary key)
  - `account_id` (UUID foreign key)
  - `max_events` (integer)
  - `max_event_capacity` (integer, max tickets per event)
  - `max_tiers_per_event` (integer)
  - `created_at`, `updated_at` (timestamps)
- **Benefits**: Allows quota versioning, history tracking, easy updates without schema changes

### Real-Time Ticket Availability Updates
- **Primary**: Server-Sent Events (SSE) for real-time push updates
- **Fallback**: Client-side polling if SSE implementation adds complexity
- **Update Frequency**: Configurable, default 30 seconds for polling
- **Endpoint**: `/api/events/{slug}/availability-stream` (SSE) or `/api/events/{slug}/availability` (polling)
- **Data**: Current available count per tier, sold_out status

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
  - `events` (id GUID, account_id FK, event_slug, title, description, start_time, end_time, timezone, status, config JSONB, created_at, updated_at)
  - `ticket_tiers` (id GUID, event_id FK, tier_name, price DECIMAL, capacity INT, available_count INT, sort_order INT, created_at, updated_at)
  - `tickets` (id GUID, tier_id FK, ticket_code VARCHAR(19) unique, status VARCHAR, created_at, updated_at)
  - `ticket_purchases` (id GUID, ticket_id FK unique, purchaser_user_id FK, stripe_session_id VARCHAR unique, amount_paid DECIMAL, purchased_at TIMESTAMP)
  - `event_attendees` (id GUID, ticket_id FK unique, attendee_name VARCHAR, attendee_email VARCHAR, attendee_phone VARCHAR, checked_in_at TIMESTAMP nullable)
  - `account_quotas` (id GUID, account_id FK unique, max_events INT, max_event_capacity INT, max_tiers_per_event INT, created_at, updated_at)
  - `event_access_whitelist` (id GUID, event_id FK, email VARCHAR, created_at) - unique constraint on (event_id, email)
  - `staff_magic_links` (id GUID, user_id FK, token VARCHAR(64) unique, expires_at TIMESTAMP, created_at, used_at TIMESTAMP nullable)

**Note**: User management tables (`users`, `sessions`, etc.) are part of a unified user architecture documented separately (see User Management Architecture section below).

### Email Service
- **Provider**: Mailgun (configurable for future providers)
- **Templates**: Purchase confirmation, event updates, cancellations, reminders
- **Configuration**: Email provider settings in account config or global config

### Profile Builder Integration
- **Purpose**: Collect and verify purchaser information before ticket checkout
- **Trigger**: Chatbot checks if user profile has essential info (name, email)
- **Flow**:
  1. User expresses intent to purchase tickets
  2. Agent checks `sessions.user_id` and linked `profiles` data
  3. If missing essential info, agent uses Profile Builder tool to collect
  4. Collected info creates/updates `users` and `profiles` records
  5. Session linked to user: `sessions.user_id = user.id`
  6. Proceed with ticket selection and attendee information collection
- **Essential Fields**: name, email (phone if configured)
- **Conversational**: Agent asks naturally within chat flow, not form-based

### Attendee Information Collection
- **Configuration**: Per-event settings in event config YAML
  - `require_attendee_names: true/false`
  - `require_attendee_emails: true/false`
  - `require_attendee_phones: true/false`
- **Collection Strategy**: All information collected upfront before payment
- **Multi-Ticket Example**: Purchasing 3 tickets
  - Agent confirms: "I'll need information for all 3 attendees"
  - Collects sequentially:
    * "Name for ticket 1?" → "Email for ticket 1?" → "Phone for ticket 1?"
    * "Name for ticket 2?" → "Email for ticket 2?" → "Phone for ticket 2?"
    * "Name for ticket 3?" → "Email for ticket 3?" → "Phone for ticket 3?"
  - Stores in temporary session data or Stripe metadata
- **Validation**: Ensures all required fields collected before generating checkout URL
- **Purchaser vs Attendees**: Purchaser (user) can be one of the attendees or separate

### Frontend Pages (Astro + Preact)
- **Event Listing**: `/events` (public events only, respects privacy settings)
- **Event Detail**: `/events/{event-slug}` (static shell + dynamic availability API)
- **Event Check-in**: `/events/{event-slug}/checkin` (staff authentication required)
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
  
  # Purchase Restrictions
  max_tickets_per_purchase: 5           # Maximum tickets one person can buy
  
  # Access Control (optional)
  access_control:
    enabled: true
    whitelist_type: "both"              # "email", "domain", or "both"
    allowed_domains:                    # Exact domain matches
      - "students.prepexcellence.edu"
      - "alumni.prepexcellence.edu"
    whitelist_source: "database"        # Email whitelist stored in event_access_whitelist table
  
  # Staff Check-in Settings
  checkin_session_duration: 30          # Minutes before check-in session expires

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
  max_tickets_per_purchase: 4               # Max 4 tickets per person
  access_control:
    enabled: false                          # Open event, no restrictions
  checkin_session_duration: 60              # 60 minutes for check-in session

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

## User Management Architecture

### Overview

Ticketing requires a unified user management system that distinguishes between:
- **Public Users**: Customers purchasing tickets, chatting with agents (no account affiliation)
- **Account Staff**: Check-in personnel, admins, managers (affiliated with specific account)

### Proposed User Table Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    user_type VARCHAR(50) NOT NULL,  -- 'public', 'account_staff', 'system_admin'
    account_id UUID REFERENCES accounts(id),  -- NULL for public users, required for account_staff
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_account_id ON users(account_id);
CREATE INDEX ix_users_type_account ON users(user_type, account_id);
```

### User Types

1. **`public`** (account_id = NULL):
   - Customers purchasing tickets
   - Users chatting with agents
   - Profile data stored in `profiles` table
   - Can have multiple sessions across different accounts/agents

2. **`account_staff`** (account_id required):
   - Check-in personnel
   - Event coordinators
   - Account administrators
   - Access limited to their account's resources

3. **`system_admin`** (account_id = NULL):
   - Platform administrators
   - Access to all accounts (future enhancement)

### Integration with Existing Tables

**sessions table** (already has user_id field):
```sql
-- Current structure (user_id already exists but unused)
sessions.user_id → users.id

-- Migration: Populate user_id from email
-- 1. Create user records for existing session emails
-- 2. Update sessions.user_id to link to new user records
-- 3. Keep email column for backward compatibility during transition
```

**profiles table** (currently links to session_id):
```sql
-- Current: profiles.session_id → sessions.id
-- Proposed: profiles.user_id → users.id

-- Migration steps:
-- 1. Add user_id column to profiles
-- 2. Populate profiles.user_id from sessions.user_id via session_id join
-- 3. Make user_id NOT NULL after data migration
-- 4. Eventually deprecate session_id (or keep for historical reference)
```

**ticket_purchases table**:
```sql
ticket_purchases.purchaser_user_id → users.id
```

**Check-in sessions** (simplified):
```sql
-- Remove account_checkin_users table
-- Remove checkin_sessions table
-- Instead, use existing architecture:

-- Account staff in users table with user_type='account_staff'
-- Check-in authentication reuses existing session management
-- Add role/permission checking in middleware
```

### Purchase & Attendee Information Flow

**Scenario**: User purchasing 3 tickets with `require_attendee_names: true`

1. **Purchaser Identification**:
   - Check if `sessions.user_id` is populated
   - If NULL, chatbot prompts for essential info (name, email, phone if needed)
   - Create or retrieve `users` record (user_type='public', account_id=NULL)
   - Link session to user: `UPDATE sessions SET user_id = ? WHERE session_key = ?`
   - Create/update `profiles` record linked to user_id

2. **Ticket Selection**:
   - User selects tier and quantity (e.g., "3 Standard tickets")
   - Check availability in real-time

3. **Attendee Information Collection** (all upfront):
   - Collect 3 sets of attendee information:
     * Attendee 1 name (required), email (if configured), phone (if configured)
     * Attendee 2 name (required), email (if configured), phone (if configured)
     * Attendee 3 name (required), email (if configured), phone (if configured)
   - Store temporarily in session or pass to Stripe metadata

4. **Stripe Checkout**:
   - Create Stripe Checkout Session
   - Pass user_id and attendee info in metadata
   - Redirect to Stripe hosted checkout

5. **Webhook Processing** (`checkout.session.completed`):
   - Extract user_id from metadata
   - Mark tickets as 'purchased'
   - Create `ticket_purchases` records (purchaser_user_id)
   - Create `event_attendees` records (one per ticket)
   - Send confirmation email via Mailgun

### Check-in Authorization Model (Simplified)

**Using Existing Infrastructure**:
- Account staff are `users` with `user_type='account_staff'` and `account_id` set
- Check-in pages use existing session management
- Middleware checks:
  1. Valid session exists
  2. `sessions.user_id` is populated
  3. `users.user_type = 'account_staff'`
  4. `users.account_id` matches event's account_id
  5. 30-minute inactivity check (reuse existing last_activity_at logic)

**Benefits**:
- No new tables needed (account_checkin_users, checkin_sessions)
- Reuses proven session management
- Unified user model across all features
- Single authentication flow for all user types

### Migration Strategy

**Phase 1**: Create users table and populate from existing data
```sql
-- Create users table
-- Insert public users from unique session emails
INSERT INTO users (email, name, user_type, account_id)
SELECT DISTINCT email, NULL, 'public', NULL
FROM sessions
WHERE email IS NOT NULL AND email != '';

-- Update sessions to link to users
UPDATE sessions s
SET user_id = u.id
FROM users u
WHERE s.email = u.email AND s.user_id IS NULL;
```

**Phase 2**: Migrate profiles to user_id
```sql
-- Add user_id column to profiles
ALTER TABLE profiles ADD COLUMN user_id UUID REFERENCES users(id);

-- Populate from sessions
UPDATE profiles p
SET user_id = s.user_id
FROM sessions s
WHERE p.session_id = s.id AND s.user_id IS NOT NULL;

-- Make user_id NOT NULL (after data validation)
ALTER TABLE profiles ALTER COLUMN user_id SET NOT NULL;
```

**Phase 3**: Add account staff users (manual or script)
```sql
-- Example: Add check-in staff for PrepExcellence
INSERT INTO users (email, name, user_type, account_id, is_active)
VALUES 
  ('staff@prepexcellence.com', 'Check-in Staff', 'account_staff', 
   (SELECT id FROM accounts WHERE slug = 'prepexcellence'), true);
```

### Benefits of Unified User Model

- ✅ Single source of truth for user identity
- ✅ Clean separation between public and account-affiliated users
- ✅ Reuses existing session management infrastructure
- ✅ Profiles persist across sessions (user-centric vs session-centric)
- ✅ Ticket purchase history tied to user (cross-session tracking)
- ✅ Simpler authorization model (one table, one foreign key)
- ✅ Easier future enhancements (user dashboards, purchase history, saved preferences)

---

## Feature Breakdown

### 0024-001 - FEATURE - User Management Foundation
**Priority**: Critical (prerequisite for all ticketing features)

Foundation for unified user management system supporting public customers and account staff.

#### 0024-001-001 - TASK - Create Users Table and Migration Scripts
**Status**: 📋 Planned

Create users table with user_type distinction and migration from existing session data.

##### 0024-001-001-001 - CHUNK - Database schema and migration SQL
**SUB-TASKS**:
- Create `users` table schema with GUID id, email (unique), name, user_type, account_id (nullable FK), is_active, timestamps
- Create indexes: email, account_id, (user_type, account_id)
- Create migration script to populate users from sessions.email
- Add constraint: account_id required when user_type='account_staff'
- Update sessions.user_id with new user records

**MANUAL-TESTS**:
- Run migration script on dev database
- Verify user records created for all unique session emails
- Verify sessions.user_id populated correctly
- Test user_type constraints (public vs account_staff)
- Verify indexes created

**AUTOMATED-TESTS**:
- Test users table schema (columns, types, constraints)
- Test migration idempotency (safe to run multiple times)
- Test user_type constraint validation
- Test account_id FK integrity

##### 0024-001-001-002 - CHUNK - Profiles migration to user-based
**SUB-TASKS**:
- Add user_id column to profiles table (UUID FK to users.id)
- Create migration to populate profiles.user_id from sessions.user_id
- Update Profile SQLAlchemy model to include user_id
- Add index on profiles.user_id
- Keep session_id for backward compatibility (mark for future deprecation)

**MANUAL-TESTS**:
- Verify profiles.user_id populated from sessions
- Test profile queries via user_id work correctly
- Verify existing profile data intact after migration

**AUTOMATED-TESTS**:
- Test profiles.user_id FK integrity
- Test profile retrieval by user_id
- Test profile updates maintain user_id link

##### 0024-001-001-003 - CHUNK - User service layer and API
**SUB-TASKS**:
- Create User SQLAlchemy model in `backend/app/models/user.py`
- Create UserService in `backend/app/services/user_service.py`
  - `get_or_create_user(email, name, user_type='public')` 
  - `get_user_by_id(user_id)` 
  - `get_user_by_email(email)`
  - `update_user(user_id, **kwargs)`
  - `link_session_to_user(session_id, user_id)`
- Update SessionDependencies to include user_id resolution
- Create unit tests for UserService

**MANUAL-TESTS**:
- Create test user via service
- Retrieve user by email and id
- Update user attributes
- Link session to user

**AUTOMATED-TESTS**:
- Test get_or_create_user idempotency
- Test user retrieval methods
- Test session linking
- Test user_type validation

---

### 0024-002 - FEATURE - Event Management Core
**Priority**: Critical (core data structures)

Event configuration, database schema, and initialization tooling.

#### 0024-002-001 - TASK - Event Database Schema
**Status**: 📋 Planned

##### 0024-002-001-001 - CHUNK - Events and tiers tables
**SUB-TASKS**:
- Create `events` table (id GUID, account_id FK, event_slug, title, description, start_time, end_time, timezone, status, config JSONB, timestamps)
- Create `ticket_tiers` table (id GUID, event_id FK, tier_name, price DECIMAL, capacity INT, available_count INT, sort_order INT, timestamps)
- Create `account_quotas` table (id GUID, account_id FK unique, max_events INT, max_event_capacity INT, max_tiers_per_event INT, timestamps)
- Add indexes: event_slug, account_id, status, (account_id, event_slug) unique
- Create SQLAlchemy models for Event, TicketTier, AccountQuota

**MANUAL-TESTS**:
- Create test event with multiple tiers
- Verify constraints (unique event_slug per account)
- Test account quota enforcement
- Verify JSONB config storage

**AUTOMATED-TESTS**:
- Test event creation and retrieval
- Test tier relationship to events
- Test account quota constraints
- Test event status transitions

##### 0024-002-001-002 - CHUNK - Tickets and purchases tables
**SUB-TASKS**:
- Create `tickets` table (id GUID, tier_id FK, ticket_code VARCHAR(19) unique, status VARCHAR, timestamps)
- Create `ticket_purchases` table (id GUID, ticket_id FK unique, purchaser_user_id FK, stripe_session_id VARCHAR unique, amount_paid DECIMAL, purchased_at TIMESTAMP)
- Create `event_attendees` table (id GUID, ticket_id FK unique, attendee_name VARCHAR, attendee_email VARCHAR, attendee_phone VARCHAR, checked_in_at TIMESTAMP nullable)
- Add indexes: ticket_code unique, ticket status, purchaser_user_id, stripe_session_id
- Create SQLAlchemy models for Ticket, TicketPurchase, EventAttendee

**MANUAL-TESTS**:
- Generate test tickets with codes
- Create test purchase
- Link attendee to ticket
- Verify FK relationships

**AUTOMATED-TESTS**:
- Test ticket creation with valid codes
- Test ticket status transitions
- Test purchase creation
- Test attendee linkage

#### 0024-002-002 - TASK - Event Configuration System
**Status**: 📋 Planned

##### 0024-002-002-001 - CHUNK - Event config YAML loader
**SUB-TASKS**:
- Create event config schema validator using Pydantic
- Create `get_event_config(account_slug, event_slug)` function
- Load from `backend/config/agent_configs/{account}/events/{event-slug}.yaml`
- Validate required fields, tier structure, date formats
- Return EventConfig Pydantic model

**MANUAL-TESTS**:
- Create test event config YAML
- Load and validate config
- Test validation errors for invalid configs
- Verify timezone and datetime parsing

**AUTOMATED-TESTS**:
- Test config loader for valid YAML
- Test validation for missing required fields
- Test tier validation
- Test datetime parsing

##### 0024-002-002-002 - CHUNK - Account quota enforcement
**SUB-TASKS**:
- Create quota validation service
- Check max_events before event creation
- Check max_event_capacity before ticket generation
- Check max_tiers_per_event in config validation
- Seed initial quotas for existing accounts

**MANUAL-TESTS**:
- Test quota enforcement on event creation
- Test capacity limit enforcement
- Test tier limit enforcement
- Update quota and verify new limits apply

**AUTOMATED-TESTS**:
- Test quota validation logic
- Test quota exceeded errors
- Test quota updates

##### 0024-002-002-003 - CHUNK - Event access control system
**SUB-TASKS**:
- Create `event_access_whitelist` table (id GUID, event_id FK, email VARCHAR unique per event, created_at)
- Add access_control section to event config YAML schema
  - `enabled: true/false`
  - `whitelist_type: "email" | "domain" | "both"`
  - `allowed_domains: ["domain1.edu", "domain2.org"]` (exact match list)
  - `whitelist_source: "database"` (emails in db table)
- Create access control validation service
  - Check domain match (exact, from list)
  - Check email whitelist (query database)
- Return clear error messages for unauthorized users

**MANUAL-TESTS**:
- Create event with domain restrictions
- Test authorized domain access
- Test unauthorized domain rejection
- Add emails to whitelist via script
- Test email whitelist authorization
- Test combined domain + email whitelist

**AUTOMATED-TESTS**:
- Test domain matching logic (exact match, multiple domains)
- Test email whitelist queries
- Test error message generation
- Test access control disabled (open events)

#### 0024-002-003 - TASK - Event Initialization Scripts
**Status**: 📋 Planned

##### 0024-002-003-001 - CHUNK - create_event_config.py interactive script
**SUB-TASKS**:
- Create `backend/scripts/create_event_config.py`
- Interactive prompts for event details (title, description, dates, performers)
- Interactive tier collection (name, price, capacity for each tier)
- Attendee info requirements (names, emails, phones)
- Generate YAML file in correct account/events folder
- Validate quota limits before creation

**MANUAL-TESTS**:
- Run script interactively
- Generate event config for PrepExcellence SAT course
- Verify YAML format matches schema
- Test quota validation

**AUTOMATED-TESTS**:
- Test YAML generation from event data
- Test file path creation
- Test quota validation in script

##### 0024-002-003-002 - CHUNK - generate_tickets.py script
**SUB-TASKS**:
- Create `backend/scripts/generate_tickets.py --config path/to/event.yaml`
- Load event config YAML
- Create event record in database
- Generate unique 19-char ticket codes (A-Z,2-9, format DH3K-FK32-NPDR-S8K9)
- Create ticket_tier records with capacity tracking
- Pre-generate all tickets with status='available'
- Update config metadata: tickets_generated=true
- Validate tickets don't already exist for event

**MANUAL-TESTS**:
- Generate tickets for test event
- Verify all ticket codes unique and valid format
- Verify tier capacities match config
- Test idempotency (can't regenerate for same event)

**AUTOMATED-TESTS**:
- Test ticket code generation algorithm
- Test code uniqueness validation
- Test tier capacity calculations
- Test idempotency checks

##### 0024-002-003-003 - CHUNK - add_tickets_to_tier.py script
**SUB-TASKS**:
- Create `backend/scripts/add_tickets_to_tier.py --account-slug X --event-slug Y --tier-name Z --count N`
- Load existing event and tier
- Generate additional unique ticket codes
- Create new ticket records with status='available'
- Update tier capacity and available_count
- Validate account quotas not exceeded

**MANUAL-TESTS**:
- Add 10 tickets to existing tier
- Verify new tickets created
- Verify capacity updated
- Test quota enforcement

**AUTOMATED-TESTS**:
- Test ticket addition logic
- Test capacity updates
- Test quota validation

##### 0024-002-003-004 - CHUNK - manage_event_whitelist.py script
**SUB-TASKS**:
- Create `backend/scripts/manage_event_whitelist.py`
- Commands:
  - `--account-slug X --event-slug Y --add-emails email1,email2,email3`
  - `--account-slug X --event-slug Y --remove-emails email1,email2`
  - `--account-slug X --event-slug Y --import-csv path/to/emails.csv`
  - `--account-slug X --event-slug Y --list` (show current whitelist)
  - `--account-slug X --event-slug Y --clear` (remove all)
- Validate event exists before modifying whitelist
- Handle duplicates gracefully
- Bulk operations for large lists

**MANUAL-TESTS**:
- Add individual emails to whitelist
- Import CSV with 100 emails
- List whitelist for event
- Remove specific emails
- Clear entire whitelist

**AUTOMATED-TESTS**:
- Test email addition
- Test CSV import
- Test duplicate handling
- Test removal operations

---

### 0024-003 - FEATURE - Purchase Flow and Stripe Integration
**Priority**: High (core functionality)

Complete ticket purchase workflow from profile to payment confirmation.

#### 0024-003-001 - TASK - Profile Integration for Purchaser Info
**Status**: 📋 Planned

##### 0024-003-001-001 - CHUNK - Purchaser info validation in agent
**SUB-TASKS**:
- Update simple_chat agent to check user_id and profile before purchase
- If user_id NULL, invoke profile builder tool to collect name, email
- Create/update user record (user_type='public')
- Link session to user
- Validate essential fields present (name, email)

**MANUAL-TESTS**:
- Start ticket purchase conversation without profile
- Verify agent prompts for info conversationally
- Verify user and profile created
- Verify session linked to user

**AUTOMATED-TESTS**:
- Test profile validation logic
- Test user creation flow
- Test session linking

##### 0024-003-001-002 - CHUNK - Purchase authorization check
**SUB-TASKS**:
- After profile collected, check event access control
- Validate user email against:
  - Domain whitelist (if configured): exact match from allowed_domains list
  - Email whitelist (if configured): query event_access_whitelist table
- If authorized, proceed with ticket selection
- If unauthorized, return clear error message:
  - Domain restriction: "This event is only available to users with @domain.edu email addresses"
  - Email whitelist: "This event is restricted to invited attendees"
- Block purchase flow early to avoid wasted time

**MANUAL-TESTS**:
- Purchase ticket with authorized domain
- Purchase ticket with unauthorized domain
- Purchase ticket with whitelisted email
- Purchase ticket with non-whitelisted email
- Test access control disabled (open event)

**AUTOMATED-TESTS**:
- Test domain authorization logic
- Test email whitelist queries
- Test error message generation
- Test bypass when access control disabled

#### 0024-003-002 - TASK - Ticketing Agent Tool (Pydantic AI)
**Status**: 📋 Planned

##### 0024-003-002-001 - CHUNK - Core ticketing tool structure
**SUB-TASKS**:
- Create `backend/app/agents/tools/ticketing_tool.py`
- Register `@agent.tool` for ticket search, availability, purchase initiation
- Tool functions:
  - `search_events(account_slug, query)` - find events
  - `get_event_details(event_slug)` - event info
  - `check_availability(event_slug, tier_name)` - real-time availability
  - `initiate_purchase(event_slug, tier_name, quantity, attendees)` - start purchase
- Return structured data for agent to present conversationally

**MANUAL-TESTS**:
- Search for events via agent
- Check ticket availability
- Get event details
- Initiate purchase flow

**AUTOMATED-TESTS**:
- Test event search logic
- Test availability checking
- Test purchase initiation

##### 0024-003-002-002 - CHUNK - Attendee information collection
**SUB-TASKS**:
- Agent prompts for attendee info based on event config
- Collect sequentially: "Name for ticket 1?", "Email for ticket 1?", etc.
- Store in session metadata temporarily
- Validate all required fields collected before proceeding
- Return structured attendee data to purchase flow

**MANUAL-TESTS**:
- Purchase 3 tickets with require_attendee_names=true
- Verify agent collects all 3 names
- Test with require_attendee_emails=true
- Verify validation of missing info

**AUTOMATED-TESTS**:
- Test attendee collection logic
- Test validation for missing fields
- Test session storage

##### 0024-003-002-003 - CHUNK - Stripe checkout session creation
**SUB-TASKS**:
- Create `backend/app/services/stripe_service.py`
- `create_checkout_session(event, tier, quantity, user_id, attendees)`
- Mark tickets as 'reserved' temporarily (or skip reservation)
- Pass user_id and attendee data in Stripe metadata
- Return Stripe Checkout URL
- Agent presents URL to user: "Click here to complete payment: [URL]"

**MANUAL-TESTS**:
- Create checkout session
- Verify Stripe session created in test mode
- Verify metadata includes user_id and attendees
- Test checkout URL redirect

**AUTOMATED-TESTS**:
- Test checkout session creation
- Test metadata population
- Test URL generation

#### 0024-003-003 - TASK - Webhook Processing
**Status**: 📋 Planned

##### 0024-003-003-001 - CHUNK - Stripe webhook endpoint
**SUB-TASKS**:
- Create `POST /api/webhooks/stripe` endpoint
- Verify webhook signature
- Handle `checkout.session.completed` event
- Handle `charge.refunded` event
- Log webhook events for debugging
- Track processed webhook IDs for idempotency

**MANUAL-TESTS**:
- Send test webhook from Stripe CLI
- Verify signature validation
- Test idempotency (duplicate webhooks ignored)

**AUTOMATED-TESTS**:
- Test webhook signature validation
- Test idempotency logic
- Test event routing

##### 0024-003-003-002 - CHUNK - Purchase completion logic
**SUB-TASKS**:
- Extract user_id and attendee data from webhook metadata
- Mark tickets as 'purchased'
- Create ticket_purchase records (purchaser_user_id FK)
- Create event_attendee records (one per ticket)
- Update tier available_count
- Trigger confirmation email
- Handle errors gracefully (log and alert)

**MANUAL-TESTS**:
- Complete test purchase via Stripe
- Verify webhook processes successfully
- Verify tickets marked as purchased
- Verify attendees created
- Verify email sent

**AUTOMATED-TESTS**:
- Test purchase completion logic
- Test ticket status updates
- Test attendee creation
- Test available_count updates

---

### 0024-004 - FEATURE - Email Integration (Mailgun)
**Priority**: Medium

Email confirmations for ticket purchases.

#### 0024-004-001 - TASK - Mailgun Service Setup
**Status**: 📋 Planned

##### 0024-004-001-001 - CHUNK - Mailgun client and configuration
**SUB-TASKS**:
- Create `backend/app/services/mailgun_service.py`
- Load Mailgun API key from environment
- Create `send_email(to, subject, text, html)` function
- Configure sender domain and from address
- Handle Mailgun API errors

**MANUAL-TESTS**:
- Send test email via service
- Verify email delivered
- Test error handling

**AUTOMATED-TESTS**:
- Test email sending (mocked)
- Test error handling

##### 0024-004-001-002 - CHUNK - Purchase confirmation email template
**SUB-TASKS**:
- Create plain text email template for purchase confirmation
- Include: event details, ticket codes, attendee names, check-in info
- Dynamic template rendering with event/ticket data
- Send via mailgun_service

**MANUAL-TESTS**:
- Complete test purchase
- Verify confirmation email received
- Verify all ticket codes included
- Verify formatting

**AUTOMATED-TESTS**:
- Test template rendering
- Test email data population

---

### 0024-005 - FEATURE - Frontend Event Pages (Astro + Preact)
**Priority**: Medium

Event listing, detail pages, and real-time availability updates.

#### 0024-005-001 - TASK - Event Pages Structure
**Status**: 📋 Planned

##### 0024-005-001-001 - CHUNK - Event detail page
**SUB-TASKS**:
- Create `web/src/pages/[account]/events/[slug].astro`
- Load event data from backend API
- Display event info, schedule, performers, tiers
- Embed chat widget for ticket purchase
- Static page with dynamic data loading

**MANUAL-TESTS**:
- Access event page
- Verify event details displayed
- Test chat widget integration
- Test responsive layout

##### 0024-005-001-002 - CHUNK - Ticket availability API and display
**SUB-TASKS**:
- Create `GET /api/events/{slug}/availability` endpoint
- Return available_count per tier
- Create Preact component for availability display
- Client-side polling every 30 seconds (configurable)
- Update tier availability in real-time

**MANUAL-TESTS**:
- View event page
- Verify availability updates every 30 seconds
- Simulate ticket purchase, verify count updates
- Test sold out display

**AUTOMATED-TESTS**:
- Test availability endpoint
- Test polling logic
- Test sold out detection

---

### 0024-006 - FEATURE - Check-in System
**Priority**: Medium

Staff authentication and ticket check-in functionality.

#### 0024-006-001 - TASK - Check-in Authentication
**Status**: 📋 Planned

##### 0024-006-001-001 - CHUNK - Staff user management
**SUB-TASKS**:
- Create script to add account staff users
- `backend/scripts/add_checkin_staff.py --account X --email Y --name Z`
- Insert user with user_type='account_staff'
- Create API endpoint to list staff for account (admin)

**MANUAL-TESTS**:
- Add staff user via script
- Verify user created with correct type
- Test account_id linkage

**AUTOMATED-TESTS**:
- Test staff user creation
- Test user_type validation

##### 0024-006-001-002 - CHUNK - Magic link authentication for check-in
**SUB-TASKS**:
- Create `web/src/pages/[account]/checkin-login.astro` page (email input form)
- Create `POST /api/checkin/request-magic-link` endpoint
  - Verify email is account staff for account
  - Generate unique magic link token (64-char random string)
  - Store in `staff_magic_links` table with expiry (configurable, default 15 min)
  - Send magic link via Mailgun: `/api/checkin/verify/{token}`
- Create `GET /api/checkin/verify/{token}` endpoint
  - Verify token exists and not expired
  - Verify not already used (used_at IS NULL)
  - Mark token as used (set used_at timestamp)
  - Create session, set cookie
  - Set session expiry based on event checkin_session_duration config
  - Redirect to check-in page or event selector

**MANUAL-TESTS**:
- Request magic link for staff email
- Verify email received with link
- Click link, verify auto-login
- Test expired token rejection
- Test already-used token rejection
- Test unauthorized email rejection
- Test session timeout based on event config

**AUTOMATED-TESTS**:
- Test magic link token generation
- Test token uniqueness
- Test expiry validation
- Test one-time use enforcement
- Test staff authorization
- Test session creation with configurable duration

#### 0024-006-002 - TASK - Check-in Page Functionality
**Status**: 📋 Planned

##### 0024-006-002-001 - CHUNK - Check-in page and ticket validation
**SUB-TASKS**:
- Create `web/src/pages/[account]/events/[slug]/checkin.astro`
- Middleware to verify staff authentication
- Preact component for ticket code entry
- `POST /api/events/{slug}/checkin` endpoint
  - Verify ticket exists for event
  - Check ticket status (must be 'purchased')
  - Update status to 'checked_in'
  - Set checked_in_at timestamp
  - Return attendee info
- Display success/error feedback

**MANUAL-TESTS**:
- Login as staff
- Access check-in page
- Enter valid ticket code
- Verify check-in recorded
- Test invalid code handling
- Test already checked-in ticket

**AUTOMATED-TESTS**:
- Test check-in logic
- Test ticket validation
- Test status updates
- Test duplicate check-in prevention

---

## Implementation Decisions - Finalized

### Core Decisions
1. ✅ **Polling** - Client-side polling for availability updates (30s default, configurable)
2. ✅ **Direct links only** - Skip public event listing, focus on direct event page links
3. ✅ **Simple chat integration** - Add ticketing tool to existing simple_chat agent
4. ✅ **Free events Phase 1** - Implement free events first, paid events Phase 2
5. ✅ **First-come-first-served** - No ticket reservation, payment completion claims tickets
6. ✅ **Plain text emails** - HTML templates deferred to later phase
7. ✅ **Basic CRUD APIs** - Build APIs now, admin UI later; scripts interact with APIs
8. ✅ **Stripe test mode** - Use test mode throughout development
9. ✅ **User management first** - Complete foundational user tables before other features
10. ✅ **Magic link authentication** - Email-based magic link for staff check-in login (simpler than OTP)

### Access Control Requirements
- **Whitelist by email**: Database table (`event_access_whitelist`) for large lists (hundreds of emails)
- **Whitelist by domain**: Event config YAML for domain restrictions (exact match, multiple domains supported)
- **Validation timing**: Check after profile collected, before purchase flow starts
- **Error messaging**: Clear rejection messages, no "request access" option in MVP
- **Whitelist management**: Database + script to add/remove emails
- **Domain matching**: Exact match only (e.g., `["profs.university.edu", "students.university.edu"]`)
- **Scope**: Optional per-event configuration
- **Multi-ticket purchases**: Authorized purchaser can buy tickets for non-authorized attendees
- **Purchase limits**: Add `max_tickets_per_purchase` to event config
- **Phasing**: Implement in Phase 1 if needed for PrepExcellence, otherwise Phase 2

### Staff Authentication (Magic Link)
- **Method**: Email-based magic link (click link → auto-login)
- **Session duration**: Configurable per event in event config YAML
- **Expiry storage**: Store session expiry timestamp in database
- **No passwords**: Passwordless authentication for MVP

