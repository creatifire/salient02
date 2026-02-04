# CMS Database Schema Analysis

Analysis of WordPress, Drupal, Strapi, Contentful, Sanity, and Ghost to identify database tables needed for a headless CMS that exports to static sites (Astro, Next.js, Hugo, etc.).

**Publishing Model**: CMS for authoring → Export to markdown → Static site generation (not runtime database queries).

## 1. WordPress Database Schema (11 Core Tables)

### User Management (2 tables)
- **`wp_users`** - Core user data (username, password, email, registration date)
- **`wp_usermeta`** - Extended user metadata (first name, last name, custom fields)

### Content (2 tables)
- **`wp_posts`** - All content (posts, pages, custom post types)
  - Columns: ID, post_author, post_date, post_content, post_title, post_excerpt, post_status (publish/draft/pending/trash), post_name (slug), post_modified, comment_status, ping_status
- **`wp_postmeta`** - Flexible metadata extension using key-value pairs
  - Columns: meta_id, post_id, meta_key, meta_value (serialized)
  - Enables custom fields without schema changes

### Taxonomy System (3 tables)
- **`wp_terms`** - Basic term info (term_id, name, slug, term_group)
- **`wp_term_taxonomy`** - Context for terms (assigns to categories, tags, custom taxonomies)
- **`wp_term_relationships`** - Links content to terms (many-to-many)

### Comments (2 tables)
- **`wp_comments`** - Comment content and author info
- **`wp_commentmeta`** - Extended comment metadata

### Configuration (2 tables)
- **`wp_options`** - Site settings (URL, title, plugins, configurations)
- **`wp_links`** - Blogroll links

**Key Pattern**: Flexible meta tables (postmeta, usermeta, commentmeta) allow extending any entity with custom fields without schema changes

---

## 2. Drupal Database Schema (Entity-Centric)

### Core Approach
- **Entity-based architecture**: Content, users, taxonomy terms are all "entities"
- **Bundle system**: Content types are "bundles" of an entity type
- **Field storage**: Each custom field gets its own table

### Key Tables (Drupal 8+)
- **`node_field_data`** - Base fields for all content (title, created, changed, published status)
- **`node_access`** - Permissions (nid, langcode, gid, realm, grant_view, grant_update, grant_delete)
- **`[entity]__field_name`** - Separate table per custom field
  - Example: `node__field_image`, `node__field_tags`
  - Columns: entity_id, revision_id, langcode, delta (for multi-value), field_value

### Field Architecture Benefits
- Fields reusable across multiple content types
- Revision tracking per field when enabled
- Shared fields between different entity types (nodes, users, etc.)

**Key Pattern**: One table per field allows maximum flexibility but creates many tables. Fields are shared across bundles.

---

## 3. Strapi Database Schema (Auto-Generated)

### Approach
- Schema-driven: Define content types in `schema.json` files
- Automatic table creation from schemas
- Tables auto-sync on startup
- Supports PostgreSQL, MySQL, SQLite

### Content Structure
- **Content Types**: Collection types (multiple entries) or Single types (one entry)
- **Components**: Reusable structures across content types
- Automatic timestamps (createdAt, updatedAt)
- Relation support (one-to-one, one-to-many, many-to-many)

### Migration System
- Files in `./database/migrations`
- Run alphabetically on startup
- No down migrations (manual rollback)

**Key Pattern**: Configuration-over-code. Schema files drive everything. CMS generates tables automatically.

---

## 4. Contentful Data Model (API-First)

### Core Concepts
- **Spaces**: Top-level container for all content
- **Content Types**: Templates with up to 50 fields
- **Entries**: Individual instances of content types
- **Assets**: Media files referenced by entries
- **Locales**: Multi-language support built-in

### Content Type Structure
```json
{
  "sys": {},
  "name": "Blog Post",
  "description": "",
  "displayField": "title",
  "fields": [...]
}
```

### Field Types
- Text, Rich Text, Integer, Decimal, Boolean, Date
- Media (Asset references)
- Location (Geographic coordinates)
- JSON Object
- References (to other entries)
- Array (multiple values)

**Key Pattern**: Completely flexible modeling. No predefined types. Build exactly what you need.

---

## 5. Sanity.io Schema (Document-Based)

### Storage Model
- **Content Lake**: Schema-less JSON document store
- **Schemas**: Define structure, validation, UI generation
- Documents include: `_id`, `_createdAt`, `_updatedAt`, `_rev`

### Field Types
- **Basic**: String, Text, Number, Boolean, Date, Datetime, URL
- **Complex**: Array, Object, Block (rich text), Reference
- **Media**: Image, File, Geopoint
- **Specialized**: Slug, Cross-dataset references

### Schema Philosophy
- Schemas align with workflows, not technical constraints
- Can evolve over time
- TypeScript type generation from schemas
- Power AI agents through structured content

**Key Pattern**: Document-oriented with schema for validation/UI, not storage. Maximum flexibility.

---

## 6. Ghost Database Schema (Simple, Focused)

### Core Tables
- **`posts`** - Blog content
- **`posts_meta`** - Post metadata
- **`tags`** - Tag definitions
- **`posts_tags`** - Junction table (many-to-many)
- **`users`** - Authors/staff
- **`posts_authors`** - Multi-author support (junction table)

### Design Philosophy
- Simple, focused on blogging/publishing
- Clean relationships via junction tables
- Metadata extension via separate meta table

**Key Pattern**: Traditional relational design. Clean and minimal.

---

## 7. Common CMS Features (Cross-Platform Analysis)

### A. Media/Asset Management (Required for Any CMS)

**Core Tables Needed**:
```
assets
├── id (PK)
├── filename
├── file_path
├── file_type (image/video/document)
├── file_size
├── mime_type
├── title
├── description
├── alt_text (for images)
├── created_at
├── updated_at
├── uploaded_by (FK to users)
└── folder_id (FK to asset_folders)

asset_metadata
├── id (PK)
├── asset_id (FK)
├── meta_key
└── meta_value

asset_folders
├── id (PK)
├── name
├── parent_id (FK self-reference for nesting)
└── account_id (multi-tenant)

asset_tags (many-to-many)
├── asset_id (FK)
└── tag_id (FK)
```

**Features**:
- Version control (track asset versions)
- Transformations (resize, crop, optimize)
- CDN integration
- Search by metadata
- Folder organization
- Access control per asset

---

### B. Roles & Permissions (RBAC)

**Core Tables Needed**:
```
roles
├── id (PK)
├── name (admin, editor, contributor, viewer)
├── description
└── account_id (multi-tenant)

permissions
├── id (PK)
├── resource (posts, assets, users)
├── action (create, read, update, delete, publish)
└── description

role_permissions (many-to-many)
├── role_id (FK)
└── permission_id (FK)

user_roles (already have account_users)
├── user_id (FK)
├── account_id (FK)
└── role_id (FK)
```

**Permission Types**:
- Resource-based (what entities can be accessed)
- Action-based (what operations are allowed)
- Field-level (which fields can be edited)
- Conditional (based on content status/ownership)

---

### C. Content Workflow & Publishing

**Core Tables Needed**:
```
workflow_states
├── id (PK)
├── name (draft, review, published)
├── color (for UI)
└── account_id

content_versions
├── id (PK)
├── content_type
├── content_id
├── version_number
├── data (JSONB - full content snapshot)
├── created_by (FK to users)
├── created_at
└── change_summary
```

**Note**: Scheduled publishing not needed (manual trigger). Git provides version history for published content.

---

### D. Internationalization (i18n) / Localization

**Approach 1: Separate Translation Tables** (Recommended)
```
locales
├── id (PK)
├── code (en, es, fr, de)
├── name (English, Español)
├── is_default
└── account_id

content_translations
├── id (PK)
├── content_type (directory_entry, asset, etc.)
├── content_id
├── locale_id (FK)
├── translated_fields (JSONB)
└── translation_status (draft, published)
```

**Approach 2: Localized Columns** (Simple but Limited)
```
directory_entries
├── name_en
├── name_es
├── name_fr
├── description_en
├── description_es
└── description_fr
```

**Features Needed**:
- Locale management (add/remove languages)
- Default locale selection
- Fallback behavior (if translation missing)
- Translation workflow (send for translation, track status)
- Content syncing across locales

---

### E. Taxonomies & Classification

**Core Tables** (WordPress Pattern):
```
taxonomies
├── id (PK)
├── name (category, tag, topic)
├── slug
├── hierarchical (boolean)
├── account_id
└── content_types (which content types use this taxonomy)

terms
├── id (PK)
├── taxonomy_id (FK)
├── name
├── slug
├── parent_id (FK self-reference for hierarchical)
└── description

content_terms (many-to-many)
├── content_type (directory_entry, asset)
├── content_id
└── term_id (FK)
```

**Note**: For static site generation, can use simple tags array in markdown frontmatter. Full taxonomy system optional.

---

### F. Static Site Build Tracking

**Core Tables**:
```
site_builds
├── id (PK)
├── site_id (FK)
├── branch (preview, main)
├── status (pending, building, success, failed)
├── started_at
├── completed_at
├── commit_hash
├── error_message
└── triggered_by (FK to users)

feedback_votes
├── id (PK)
├── site_id (FK)
├── content_type
├── content_id
├── vote_type (up, down)
├── session_id
└── created_at

feedback_ratings
├── id (PK)
├── site_id (FK)
├── content_type
├── content_id
├── rating (1-5)
├── session_id
└── created_at

feedback_comments
├── id (PK)
├── site_id (FK)
├── content_type
├── content_id
├── comment
├── author_name
├── author_email
├── status (pending, approved, rejected)
├── created_at
└── approved_at
```

**Note**: Webhooks not needed (manual build trigger). Feedback API allows static site to send user interactions back to CMS.

---

### G. API Keys & Access Tokens

**Core Tables**:
```
api_keys
├── id (PK)
├── account_id (FK)
├── name (Production Key, Staging Key)
├── key_hash (bcrypt)
├── key_prefix (for display: "sk_prod_abc...")
├── permissions (array or JSON)
├── rate_limit_tier
├── created_at
├── expires_at
├── last_used_at
└── is_active

api_key_usage
├── id (PK)
├── api_key_id (FK)
├── endpoint
├── method
├── status_code
├── response_time_ms
├── timestamp
└── ip_address
```

**Note**: For static site builds, single API key per site sufficient. Usage tracking optional.

---

### H. Content Relations

**Core Tables**:
```
content_relations
├── id (PK)
├── from_content_type
├── from_content_id
├── to_content_type
├── to_content_id
├── relation_type (one-to-one, one-to-many, many-to-many)
└── relation_name (author, related_posts, featured_items)
```

**Note**: For static sites, can store references in markdown frontmatter. Database relations optional.

---

### I. Search & Indexing

**Note**: For static sites with RAG chatbot:
- Content indexed into Pinecone vector database during build
- Static site search can use client-side libraries (Pagefind, Lunr.js)
- Database-level search not needed for published content

---

## 8. Comparison Matrix

| Feature | WordPress | Drupal | Strapi | Contentful | Sanity | Ghost | **Needed?** |
|---------|-----------|--------|--------|------------|--------|-------|-------------|
| **Core Content** | ✅ posts | ✅ nodes | ✅ collections | ✅ entries | ✅ documents | ✅ posts | ✅ Have (directory_entries) |
| **Flexible Metadata** | ✅ postmeta | ✅ field tables | ✅ components | ✅ field types | ✅ schema fields | ✅ posts_meta | ✅ Have (entry_data JSONB) |
| **User Management** | ✅ users + usermeta | ✅ users + fields | ✅ built-in | ✅ built-in | ✅ built-in | ✅ users | ⚠️ Need improvement |
| **Roles & Permissions** | ✅ capabilities | ✅ permissions | ✅ RBAC | ✅ spaces/roles | ✅ GROQ rules | ✅ roles | ❌ **Need to add** |
| **Taxonomies** | ✅ terms system | ✅ taxonomy | ✅ relations | ✅ references | ✅ references | ✅ tags | ❌ **Need to add** |
| **Media/Assets** | ✅ uploads | ✅ files | ✅ media library | ✅ assets | ✅ assets | ❌ external | ❌ **Need to add** |
| **Versioning** | ✅ revisions | ✅ revisions | ✅ versions | ✅ versions | ✅ revisions | ❌ no | ❌ **Need to add** |
| **Workflow** | ⚠️ plugins | ⚠️ contrib | ✅ draft/publish | ✅ workflow | ⚠️ custom | ⚠️ basic | ❌ **Need to add** |
| **Localization** | ⚠️ plugins | ✅ built-in | ✅ i18n plugin | ✅ locales | ✅ localization | ❌ no | ❌ **Need to add** |
| **Webhooks** | ⚠️ plugins | ⚠️ contrib | ✅ built-in | ✅ webhooks | ✅ webhooks | ✅ webhooks | ❌ Not needed (manual build) |
| **API Keys** | ⚠️ plugins | ⚠️ OAuth | ✅ API tokens | ✅ API keys | ✅ tokens | ✅ tokens | ⚠️ Basic sufficient (build API) |
| **Comments** | ✅ comments | ✅ comments | ⚠️ custom | ❌ external | ⚠️ custom | ❌ external | ✅ Feedback API needed |
| **Scheduled Publish** | ⚠️ plugins | ⚠️ contrib | ✅ built-in | ✅ scheduling | ⚠️ custom | ⚠️ basic | ❌ Not needed (manual) |
| **Search** | ⚠️ basic | ✅ Search API | ⚠️ basic | ✅ GraphQL | ✅ GROQ | ⚠️ basic | ✅ Pinecone (RAG chatbot) |

---

## 9. Gap Analysis: Current System vs Full CMS

### What We Have
✅ **Directory Lists** - Content collections (like content types)
✅ **Directory Entries** - Individual content items
✅ **Flexible Schema** - YAML-driven, JSONB storage
✅ **Tags** - Simple classification
✅ **Multi-Tenant** - Account isolation
✅ **Basic Search** - Full-text search with PostgreSQL
✅ **Contact Info** - Structured contact fields
✅ **Account Users** - Basic user management (planned)
✅ **Authentication** - JWT-based (planned)

### Missing Features

#### Priority 1: Essential for Static Site CMS
1. **Media/Asset Management** - Centralized assets directory
2. **Roles & Permissions** - RBAC for authoring
3. **Content Workflow** - Draft/Published states (no scheduling needed)
4. **Build Tracking** - Track static site builds
5. **Feedback API** - Collect user interactions from static sites

#### Priority 2: Quality of Life
6. **Taxonomies** - Hierarchical categories (or use frontmatter tags)
7. **Content Versioning** - History before git (optional, git provides versioning after publish)
8. **Multi-Site Management** - One database per site

#### Not Needed for Static Site Architecture
- ❌ **Webhooks** (manual build trigger)
- ❌ **Scheduled Publishing** (manual publish workflow)
- ❌ **Workflow Transitions** (simple draft→published)
- ❌ **Database Search** (Pinecone for RAG, client-side for static site)
- ❌ **Content Schedule** (no automatic publishing)

#### Deferred
- **Localization/i18n** - Add when multi-language needed
- **Content Relations** - Can use markdown frontmatter initially
- **Audit Trail** - Git commits provide audit after publish

---

## 10. Database Tables for Static Site CMS

### Phase 1: Core Authoring

```sql
-- Assets/Media Management
assets (
  id, account_id, filename, file_path, file_type, file_size, 
  mime_type, title, description, alt_text, width, height,
  uploaded_by, folder_id, created_at, updated_at
)

asset_folders (
  id, account_id, name, parent_id, path
)

asset_metadata (
  id, asset_id, meta_key, meta_value
)

-- Roles & Permissions
roles (
  id, account_id, name, description, is_system_role
)

permissions (
  id, resource, action, description
)

role_permissions (
  role_id, permission_id
)

-- Workflow (simplified for static site)
workflow_states (
  id, account_id, name, color, order
)

-- Versioning (optional - git provides versioning after publish)
content_versions (
  id, content_type, content_id, version_number, data, 
  created_by, created_at, change_summary
)
```

### Phase 1: Static Site Publishing

```sql
-- Build tracking
site_builds (
  id, site_id, branch, status, started_at, completed_at,
  commit_hash, error_message, triggered_by
)

-- Multi-site management
sites (
  id, account_id, name, database_name, git_repo,
  domain, preview_domain, astro_config
)

-- Feedback from static sites
feedback_votes (
  id, site_id, content_type, content_id, vote_type,
  session_id, created_at
)

feedback_ratings (
  id, site_id, content_type, content_id, rating,
  session_id, created_at
)

feedback_comments (
  id, site_id, content_type, content_id, comment,
  author_name, author_email, status, created_at, approved_at
)
```

### Phase 2: Enhanced Features

```sql
-- Taxonomies (or use tags in frontmatter)
taxonomies (
  id, account_id, name, slug, hierarchical, content_types
)

terms (
  id, taxonomy_id, name, slug, parent_id, description
)

content_terms (
  content_type, content_id, term_id
)
```

### Phase 3: Enterprise (Deferred)

```sql
-- Localization (when needed)
locales (
  id, account_id, code, name, is_default
)

content_translations (
  id, content_type, content_id, locale_id, 
  translated_fields, translation_status
)

-- Content Relations (or use frontmatter)
content_relations (
  id, from_content_type, from_content_id, 
  to_content_type, to_content_id, relation_type, relation_name
)
```

---

## 11. Architectural Patterns Observed

### Pattern 1: Meta Tables (WordPress Style)
- Main table + separate meta table for extensions
- Flexible but can be slow with many meta queries
- Good for: Unpredictable custom fields

### Pattern 2: Field Tables (Drupal Style)
- Separate table per custom field
- Maximum flexibility, fields reusable
- Good for: Complex field types, multilingual

### Pattern 3: JSONB Storage (Modern Approach)
- Store flexible data in JSONB columns
- Fast queries with GIN indexes
- Good for: Schema flexibility, rapid development

### Pattern 4: Document Store (Sanity/Contentful)
- Schema-less storage with schema validation layer
- Ultimate flexibility
- Good for: Headless CMS, API-first

**Our Current Approach**: Pattern 3 (JSONB) - supports CMS features without creating hundreds of tables.

## 11. Key Insights

1. **Use existing patterns**: WordPress taxonomies are well-designed
2. **JSONB supports most features**: Current approach works without hundreds of tables
3. **Static site simplifies architecture**: No runtime database queries, manual publish workflow
4. **Markdown export is portable**: Compatible with all major SSGs (Astro, Next.js, Hugo, 11ty, Gatsby)
5. **Git provides versioning**: After publish, git commit history tracks changes
6. **Pinecone for search**: Vector database handles RAG chatbot, client-side search for static site
7. **Feedback API completes loop**: Static sites send user interactions back to CMS
