# CMS Static Site Architecture

Headless CMS for authoring content that exports to Astro static sites with RAG-enabled chatbot integration.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│  CMS Admin UI (Authoring)                                │
│  - Content creation/editing                              │
│  - Media upload and management                           │
│  - User roles and permissions                            │
│  - Workflow (draft/review/published)                     │
└─────────────────┬────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────┐
│  PostgreSQL Database                                     │
│  - Content tables (directory_entries, etc.)              │
│  - Media metadata (assets table)                         │
│  - User/auth tables                                      │
│  - One database per customer site                        │
└─────────────────┬────────────────────────────────────────┘
                  │
                  │ Manual "Publish" trigger
                  ▼
┌──────────────────────────────────────────────────────────┐
│  Build Service                                           │
│  1. Export content as markdown files                     │
│  2. Export assets to centralized directory               │
│  3. Index content + documents into Pinecone             │
│  4. Run Astro build                                      │
│  5. Commit to git branch                                 │
└─────────────────┬────────────────────────────────────────┘
                  │
                  ├─→ Preview Branch ─→ Cloudflare (staging)
                  └─→ Main Branch ─→ Cloudflare (production)
                  
┌──────────────────────────────────────────────────────────┐
│  Static Site (Cloudflare/Vercel/Netlify)                │
│  - Pre-rendered HTML/CSS/JS pages                        │
│  - Embedded images and media                             │
│  - RAG-enabled chatbot UI                                │
└─────────────────┬────────────────────────────────────────┘
                  │
                  │ User feedback (upvote/downvote/comments)
                  ▼
┌──────────────────────────────────────────────────────────┐
│  Feedback API (Backend)                                  │
│  - Store ratings, votes, comments                        │
│  - Read-only for public content queries (optional)       │
└──────────────────────────────────────────────────────────┘
```

## Content Export Process

### 1. Markdown Export with Frontmatter

Content exported from database as markdown files:

```markdown
---
id: "550e8400-e29b-41d4-a716-446655440000"
type: "medical_professional"
title: "Dr. Jane Smith"
specialty: "Cardiology"
department: "Heart Center"
tags: ["Spanish", "Telehealth"]
published_at: "2026-02-03T10:00:00Z"
updated_at: "2026-02-03T15:30:00Z"
---

Dr. Jane Smith is a board-certified cardiologist specializing in...

## Education
- MD, Johns Hopkins University
- Residency, Massachusetts General Hospital

## Contact
- Phone: (555) 123-4567
- Location: Main Hospital, 3rd Floor
```

**Export Location**: `content/{content_type}/{id}.md`

### 2. Asset Organization

Centralized asset directory structure:

```
assets/
├── images/
│   ├── doctors/
│   │   ├── jane-smith.jpg
│   │   └── john-doe.jpg
│   ├── facilities/
│   └── general/
├── documents/
│   ├── pdfs/
│   │   ├── patient-guide.pdf
│   │   └── procedures.pdf
│   ├── word/
│   └── presentations/
└── media/
    └── videos/
```

**Asset URL Pattern**: `/assets/{category}/{filename}`

### 3. Vector Database Indexing

Content and documents indexed into Pinecone for RAG chatbot:

**Indexed Content**:
- Markdown content (extracted text)
- PDF documents (text extraction)
- Word documents (.docx text)
- PowerPoint (.pptx text)
- Plain text files

**Metadata Stored**:
```json
{
  "id": "doc-uuid",
  "content_type": "medical_professional",
  "title": "Dr. Jane Smith",
  "source_file": "content/doctors/jane-smith.md",
  "asset_refs": ["assets/images/doctors/jane-smith.jpg"],
  "tags": ["Spanish", "Cardiology"],
  "last_updated": "2026-02-03T15:30:00Z"
}
```

## Astro Build Configuration

### Content Collections

```typescript
// src/content.config.ts
import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

export const collections = {
  doctors: defineCollection({
    loader: glob({ pattern: '**/*.md', base: './content/doctors' }),
    schema: z.object({
      title: z.string(),
      specialty: z.string(),
      department: z.string(),
      tags: z.array(z.string()),
      published_at: z.string(),
    })
  }),
  locations: defineCollection({
    loader: glob({ pattern: '**/*.md', base: './content/locations' }),
    schema: z.object({
      title: z.string(),
      address: z.string(),
      hours: z.string(),
    })
  }),
  // ... other content types
};
```

### Build Authentication

Astro build needs access to CMS API for dynamic data queries:

**Environment Variables**:
```bash
# .env.production
CMS_API_URL=https://admin-api.yourdomain.com
CMS_API_KEY=sk_prod_abc123...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=customer-site-1
```

**API Client in Astro**:
```typescript
// src/lib/cms-client.ts
export async function fetchPublishedContent(contentType: string) {
  const response = await fetch(
    `${import.meta.env.CMS_API_URL}/api/content/${contentType}`,
    {
      headers: {
        'Authorization': `Bearer ${import.meta.env.CMS_API_KEY}`
      }
    }
  );
  return response.json();
}
```

## Build Service Implementation

### Build Pipeline

```typescript
// build-service/pipeline.ts

async function publishSite(accountId: string, branch: 'preview' | 'main') {
  // 1. Export content from database
  const content = await exportContentAsMarkdown(accountId);
  const assets = await exportAssets(accountId);
  
  // 2. Write to git repo branch
  await git.checkout(branch);
  await writeMarkdownFiles(content);
  await writeAssets(assets);
  
  // 3. Index into Pinecone
  await indexContentToPinecone(content, assets.documents);
  
  // 4. Run Astro build
  await exec('npm run build');
  
  // 5. Commit and push
  await git.add('.');
  await git.commit(`Publish: ${new Date().toISOString()}`);
  await git.push('origin', branch);
  
  // 6. Trigger deployment (automatic via git push)
  // Cloudflare/Vercel/Netlify watches git repo
}
```

### Export Functions

```typescript
async function exportContentAsMarkdown(accountId: string) {
  const entries = await db.query(`
    SELECT * FROM directory_entries 
    WHERE account_id = $1 
    AND status = 'published'
  `, [accountId]);
  
  return entries.map(entry => ({
    path: `content/${entry.type}/${entry.id}.md`,
    content: generateMarkdown(entry)
  }));
}

function generateMarkdown(entry: DirectoryEntry): string {
  const frontmatter = yaml.dump({
    id: entry.id,
    type: entry.type,
    title: entry.name,
    ...entry.entry_data,
    tags: entry.tags,
    published_at: entry.published_at,
    updated_at: entry.updated_at
  });
  
  const body = entry.entry_data.description || '';
  
  return `---\n${frontmatter}---\n\n${body}`;
}
```

## Multi-Tenant Site Management

### Database Organization

**PostgreSQL Instance**: Single server
**Databases**: One per customer site

```
postgresql://...
├── customer_a_site_1    (database)
│   ├── directory_lists
│   ├── directory_entries
│   ├── assets
│   └── users
├── customer_a_site_2    (database)
└── customer_b_site_1    (database)
```

**Site Configuration**:
```typescript
sites: [
  {
    id: "site-1",
    customer: "customer_a",
    database: "customer_a_site_1",
    git_repo: "github.com/org/customer-a-site-1",
    domain: "customersite1.com",
    preview_domain: "preview.customersite1.com"
  },
  {
    id: "site-2",
    customer: "customer_a", 
    database: "customer_a_site_2",
    git_repo: "github.com/org/customer-a-site-2",
    domain: "anothercustomersite.com",
    preview_domain: "preview.anothercustomersite.com"
  }
]
```

## Git Branch Strategy

### Preview Branch
- Content committed to `preview` branch
- Cloudflare/Vercel auto-deploys to staging URL
- Allows content review before production

### Main Branch
- Content committed to `main` branch after approval
- Cloudflare/Vercel auto-deploys to production URL
- Public-facing site

**Workflow**:
1. Author publishes content → triggers build to `preview` branch
2. Review preview site at `preview.customersite.com`
3. Approve → triggers build to `main` branch
4. Live at `customersite.com`

## Feedback API

### Read-Write Endpoints

Static site sends feedback to backend API:

```typescript
// POST /api/feedback/upvote
{
  "content_type": "medical_professional",
  "content_id": "uuid",
  "vote": "up" | "down"
}

// POST /api/feedback/rating
{
  "content_type": "faq",
  "content_id": "uuid",
  "rating": 5  // 1-5 stars
}

// POST /api/feedback/comment
{
  "content_type": "location",
  "content_id": "uuid",
  "comment": "Very helpful information!",
  "author_name": "John Doe",
  "author_email": "john@example.com"
}
```

### Database Tables

```sql
feedback_votes (
  id, site_id, content_type, content_id, 
  vote_type, session_id, created_at
)

feedback_ratings (
  id, site_id, content_type, content_id,
  rating, session_id, created_at
)

feedback_comments (
  id, site_id, content_type, content_id,
  comment, author_name, author_email,
  status, created_at, approved_at
)
```

## Chatbot Integration

### RAG Query Flow

```
User Query → Chatbot UI (on static site)
    ↓
OpenRouter LLM + Pinecone Vector Search
    ↓
Retrieve relevant content chunks
    ↓
Generate response with embedded links
    ↓
Display to user with asset references
```

**Asset References in Responses**:
```markdown
Based on your question, here are relevant doctors:

**Dr. Jane Smith** - Cardiologist
![Dr. Smith](https://customersite.com/assets/images/doctors/jane-smith.jpg)

For more details, see our [Patient Guide (PDF)](https://customersite.com/assets/documents/pdfs/patient-guide.pdf)
```

## Static Site Generator Support

### Current: Astro

Content collections with markdown loader.

### Future: Add Support For

**Next.js**:
- Markdown → MDX conversion
- `getStaticProps` reads markdown files
- Image optimization with Next/Image

**Hugo**:
- Markdown files in `content/` directory
- Frontmatter matches Hugo conventions
- Taxonomies map to Hugo's taxonomy system

**Gatsby**:
- GraphQL queries against markdown files
- Plugins for image optimization
- MDX support

**11ty**:
- Markdown with frontmatter
- Data files for structured content
- Nunjucks/Liquid templates

**Key Requirement**: Markdown + frontmatter export format is compatible with all major SSGs.

## Build Optimization

### Incremental Builds

**Challenge**: Full site rebuild on every change is slow.

**Solutions**:
- **Vercel**: Incremental Static Regeneration (ISR)
- **Cloudflare**: Build cache between deploys
- **Custom**: Track changed content, only rebuild affected pages

### Asset Optimization

**Images**:
- Resize and compress during export
- Multiple formats (WebP, AVIF) for modern browsers
- Responsive image srcsets

**Documents**:
- PDF compression
- Text extraction during export (for indexing)

## Security Considerations

### CMS API Keys
- Stored as build secrets (Vercel/Cloudflare env vars)
- Rotated quarterly
- Scoped to read-only published content

### Feedback API
- Rate limiting (prevent spam)
- CORS configured for customer domains only
- Comment moderation before display

### Asset Access
- Public read access (served by CDN)
- Write access only via CMS admin (authenticated)

## Deployment Checklist

### Per Site Setup

1. **Create PostgreSQL database** for site
2. **Create git repository** for site content
3. **Configure Cloudflare Pages** (or Vercel/Netlify)
   - Connect git repo
   - Set build command: `npm run build`
   - Set publish directory: `dist`
   - Add environment variables (CMS_API_KEY, etc.)
4. **Configure preview branch** deployment
5. **Set up custom domain** and SSL
6. **Initialize Pinecone index** for site
7. **Test build pipeline** with sample content

### Content Publishing Flow

1. Author creates/edits content in CMS admin
2. Content in "draft" state (not exported)
3. Author clicks "Publish to Preview"
   - Build service exports to markdown
   - Indexes into Pinecone
   - Commits to `preview` branch
   - Cloudflare builds preview site
4. Review preview at `preview.customersite.com`
5. Author clicks "Publish to Production"
   - Build service commits to `main` branch
   - Cloudflare builds production site
6. Live at `customersite.com`

## Required Database Tables

Based on static site architecture, simplified from full CMS:

### Essential (Phase 1)
```sql
-- Content (existing)
directory_lists
directory_entries
directory_permissions

-- Users & Auth
users
account_users
roles
permissions

-- Media
assets
asset_folders
asset_metadata

-- Workflow (simplified)
workflow_states (draft, review, published)
```

### Needed for Publishing (Phase 1)
```sql
-- Build tracking
site_builds (
  id, site_id, branch, status, started_at, 
  completed_at, commit_hash, error_message
)

-- Feedback from static site
feedback_votes
feedback_ratings  
feedback_comments
```

### Not Needed
- ❌ `webhooks` (manual trigger only)
- ❌ `content_schedule` (manual publish)
- ❌ `workflow_transitions` (simple draft→published)
- ❌ `content_relations` (handled in markdown frontmatter)
- ❌ `api_key_usage` (build uses single API key)

### Deferred to Phase 2
- `content_versions` (git provides versioning)
- `taxonomies`, `terms` (can use tags in frontmatter)
- `locales`, `content_translations` (add when needed)
- `audit_log` (git commits provide audit trail)
