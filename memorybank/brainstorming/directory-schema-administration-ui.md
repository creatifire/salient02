# Directory Schema Administration UI

## Problem

Currently, directory data (classes, medical professionals, locations, etc.) must be managed via CSV imports. Users need a web-based admin interface to create, edit, and manage directory entries directly.

## Solution

Build a single, schema-driven admin UI that dynamically generates forms and validation rules from YAML schema files. One interface manages all 13 directory types without type-specific code.

## Architecture

### Backend: Schema Metadata API

New endpoints expose schema definitions and provide CRUD for directory entries:

```python
# backend/app/api/admin/directory_schemas.py
from fastapi import APIRouter, Depends
from ...services.directory_importer import DirectoryImporter

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/directory-schemas")
async def list_schemas():
    """Return all available schema files with metadata."""
    schema_dir = Path(__file__).parent.parent.parent / "config" / "directory_schemas"
    schemas = []
    for schema_file in schema_dir.glob("*.yaml"):
        schema = DirectoryImporter.load_schema(schema_file.name)
        schemas.append({
            "entry_type": schema["entry_type"],
            "version": schema.get("version", "1.0"),
            "description": schema.get("description"),
            "schema_file": schema_file.name
        })
    return {"schemas": schemas}

@router.get("/directory-schemas/{entry_type}")
async def get_schema(entry_type: str):
    """Return full schema definition including field types and validation."""
    schema_file = f"{entry_type}.yaml"
    schema = DirectoryImporter.load_schema(schema_file)
    return {
        "entry_type": schema["entry_type"],
        "required_fields": schema.get("required_fields", []),
        "optional_fields": schema.get("optional_fields", []),
        "fields": schema.get("fields", {}),
        "contact_info_fields": schema.get("contact_info_fields", {}),
        "tags_usage": schema.get("tags_usage", {})
    }
```

```python
# backend/app/api/admin/directory_entries.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...models.directory import DirectoryList, DirectoryEntry
from ...deps import get_session, get_current_account

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/directory-lists")
async def list_directory_lists(
    session: AsyncSession = Depends(get_session),
    account = Depends(get_current_account)
):
    """Get all directory lists for current account."""
    result = await session.execute(
        select(DirectoryList)
        .where(DirectoryList.account_id == account.id)
        .order_by(DirectoryList.list_name)
    )
    lists = result.scalars().all()
    return {"lists": [lst.to_dict() for lst in lists]}

@router.get("/directory-lists/{list_id}/entries")
async def list_entries(
    list_id: str,
    offset: int = 0,
    limit: int = 50,
    search: str = None,
    session: AsyncSession = Depends(get_session),
    account = Depends(get_current_account)
):
    """Get entries with pagination and search."""
    query = (
        select(DirectoryEntry)
        .join(DirectoryList)
        .where(DirectoryList.id == list_id)
        .where(DirectoryList.account_id == account.id)
    )
    
    if search:
        query = query.where(DirectoryEntry.name.ilike(f"%{search}%"))
    
    query = query.offset(offset).limit(limit).order_by(DirectoryEntry.name)
    result = await session.execute(query)
    entries = result.scalars().all()
    
    return {
        "entries": [entry.to_dict() for entry in entries],
        "offset": offset,
        "limit": limit
    }

@router.post("/directory-lists/{list_id}/entries")
async def create_entry(
    list_id: str,
    entry_data: dict,
    session: AsyncSession = Depends(get_session),
    account = Depends(get_current_account)
):
    """Create new directory entry with schema validation."""
    # Verify list ownership
    directory_list = await session.get(DirectoryList, list_id)
    if not directory_list or directory_list.account_id != account.id:
        raise HTTPException(404, "Directory list not found")
    
    # Validate against schema
    schema = DirectoryImporter.load_schema(directory_list.schema_file)
    if not DirectoryImporter.validate_entry(entry_data, schema, 0):
        raise HTTPException(400, "Entry validation failed")
    
    # Create entry
    entry = DirectoryEntry(
        directory_list_id=list_id,
        name=entry_data["name"],
        tags=entry_data.get("tags", []),
        contact_info=entry_data.get("contact_info", {}),
        entry_data=entry_data.get("entry_data", {})
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    
    return {"entry": entry.to_dict()}

@router.put("/directory-lists/{list_id}/entries/{entry_id}")
async def update_entry(
    list_id: str,
    entry_id: str,
    entry_data: dict,
    session: AsyncSession = Depends(get_session),
    account = Depends(get_current_account)
):
    """Update existing entry."""
    # Verify ownership through join
    result = await session.execute(
        select(DirectoryEntry)
        .join(DirectoryList)
        .where(DirectoryEntry.id == entry_id)
        .where(DirectoryList.id == list_id)
        .where(DirectoryList.account_id == account.id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    # Validate
    directory_list = await session.get(DirectoryList, list_id)
    schema = DirectoryImporter.load_schema(directory_list.schema_file)
    if not DirectoryImporter.validate_entry(entry_data, schema, 0):
        raise HTTPException(400, "Entry validation failed")
    
    # Update fields
    entry.name = entry_data["name"]
    entry.tags = entry_data.get("tags", [])
    entry.contact_info = entry_data.get("contact_info", {})
    entry.entry_data = entry_data.get("entry_data", {})
    
    await session.commit()
    await session.refresh(entry)
    
    return {"entry": entry.to_dict()}

@router.delete("/directory-lists/{list_id}/entries/{entry_id}")
async def delete_entry(
    list_id: str,
    entry_id: str,
    session: AsyncSession = Depends(get_session),
    account = Depends(get_current_account)
):
    """Delete entry."""
    result = await session.execute(
        select(DirectoryEntry)
        .join(DirectoryList)
        .where(DirectoryEntry.id == entry_id)
        .where(DirectoryList.id == list_id)
        .where(DirectoryList.account_id == account.id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    await session.delete(entry)
    await session.commit()
    
    return {"deleted": entry_id}
```

### Frontend: Dynamic Form Generator

React components that read schema metadata and generate appropriate form controls:

```tsx
// web/src/components/admin/DirectorySchemaForm.tsx
import { useQuery } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

interface SchemaFormProps {
  entryType: string;
  initialData?: DirectoryEntry;
  onSubmit: (data: any) => Promise<void>;
}

export function DirectorySchemaForm({ entryType, initialData, onSubmit }: SchemaFormProps) {
  // Fetch schema definition
  const { data: schema } = useQuery({
    queryKey: ['schema', entryType],
    queryFn: () => fetch(`/api/admin/directory-schemas/${entryType}`).then(r => r.json())
  });

  // Generate Zod schema from YAML schema
  const validationSchema = React.useMemo(() => {
    if (!schema) return null;
    
    const schemaShape: any = {
      name: z.string().min(1, 'Name is required'),
      tags: z.array(z.string()).optional(),
      contact_info: z.object({
        phone: z.string().optional(),
        email: z.string().email().optional(),
        location: z.string().optional(),
        product_url: z.string().url().optional(),
      }).optional(),
      entry_data: z.object({})
    };

    // Add required fields
    schema.required_fields?.forEach((fieldName: string) => {
      const field = schema.fields[fieldName];
      schemaShape.entry_data = schemaShape.entry_data.extend({
        [fieldName]: generateZodField(field, true)
      });
    });

    // Add optional fields
    schema.optional_fields?.forEach((fieldName: string) => {
      const field = schema.fields[fieldName];
      schemaShape.entry_data = schemaShape.entry_data.extend({
        [fieldName]: generateZodField(field, false)
      });
    });

    return z.object(schemaShape);
  }, [schema]);

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: validationSchema ? zodResolver(validationSchema) : undefined,
    defaultValues: initialData
  });

  if (!schema) return <div>Loading schema...</div>;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Name field - always present */}
      <div>
        <label className="block text-sm font-medium">Name *</label>
        <input
          {...register('name')}
          className="mt-1 block w-full border rounded px-3 py-2"
        />
        {errors.name && <p className="text-red-600 text-sm">{errors.name.message}</p>}
      </div>

      {/* Dynamic fields from schema */}
      {renderFieldGroups(schema, register, errors)}

      {/* Contact info section */}
      <fieldset className="border p-4 rounded">
        <legend className="font-medium">Contact Information</legend>
        {renderContactFields(schema.contact_info_fields, register, errors)}
      </fieldset>

      {/* Tags */}
      <div>
        <label className="block text-sm font-medium">Tags</label>
        <TagsInput {...register('tags')} />
        <p className="text-gray-500 text-sm">{schema.tags_usage?.description}</p>
      </div>

      <div className="flex gap-2">
        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">
          Save Entry
        </button>
        <button type="button" className="px-4 py-2 border rounded">
          Cancel
        </button>
      </div>
    </form>
  );
}

function generateZodField(field: any, required: boolean) {
  let zodType;
  
  switch (field.type) {
    case 'string':
      zodType = z.string();
      break;
    case 'number':
    case 'integer':
      zodType = z.number();
      break;
    case 'boolean':
      zodType = z.boolean();
      break;
    case 'array':
      zodType = z.array(z.string());
      break;
    case 'text':
      zodType = z.string();
      break;
    default:
      zodType = z.string();
  }
  
  return required ? zodType : zodType.optional();
}

function renderFieldGroups(schema: any, register: any, errors: any) {
  const allFields = [
    ...(schema.required_fields || []),
    ...(schema.optional_fields || [])
  ];

  return allFields.map(fieldName => {
    const field = schema.fields[fieldName];
    const isRequired = schema.required_fields?.includes(fieldName);
    
    return (
      <div key={fieldName}>
        <label className="block text-sm font-medium">
          {formatFieldLabel(fieldName)} {isRequired && '*'}
        </label>
        {renderFieldInput(fieldName, field, register, errors)}
        {field.description && (
          <p className="text-gray-500 text-sm mt-1">{field.description}</p>
        )}
        {field.examples && (
          <p className="text-gray-400 text-xs">Examples: {field.examples.join(', ')}</p>
        )}
      </div>
    );
  });
}

function renderFieldInput(fieldName: string, field: any, register: any, errors: any) {
  const registerPath = `entry_data.${fieldName}`;
  
  switch (field.type) {
    case 'text':
      return (
        <textarea
          {...register(registerPath)}
          rows={4}
          className="mt-1 block w-full border rounded px-3 py-2"
        />
      );
    
    case 'array':
      return (
        <ArrayInput {...register(registerPath)} />
      );
    
    case 'boolean':
      return (
        <input
          type="checkbox"
          {...register(registerPath)}
          className="mt-1 h-4 w-4"
        />
      );
    
    case 'number':
    case 'integer':
      return (
        <input
          type="number"
          {...register(registerPath, { valueAsNumber: true })}
          className="mt-1 block w-full border rounded px-3 py-2"
        />
      );
    
    default:
      return (
        <input
          type="text"
          {...register(registerPath)}
          className="mt-1 block w-full border rounded px-3 py-2"
        />
      );
  }
}
```

```tsx
// web/src/pages/admin/directory-admin.astro
---
import AdminLayout from '../../layouts/AdminLayout.astro';
---

<AdminLayout title="Directory Administration">
  <div id="directory-admin-root"></div>
</AdminLayout>

<script>
  import { createRoot } from 'react-dom/client';
  import DirectoryAdmin from '../../components/admin/DirectoryAdmin';
  
  const root = document.getElementById('directory-admin-root');
  if (root) {
    createRoot(root).render(<DirectoryAdmin />);
  }
</script>
```

```tsx
// web/src/components/admin/DirectoryAdmin.tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export default function DirectoryAdmin() {
  const [selectedList, setSelectedList] = useState<string | null>(null);
  const [editingEntry, setEditingEntry] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const queryClient = useQueryClient();

  // Fetch directory lists
  const { data: lists } = useQuery({
    queryKey: ['directory-lists'],
    queryFn: () => fetch('/api/admin/directory-lists').then(r => r.json())
  });

  // Fetch entries for selected list
  const { data: entries } = useQuery({
    queryKey: ['entries', selectedList, searchTerm],
    queryFn: () => 
      fetch(`/api/admin/directory-lists/${selectedList}/entries?search=${searchTerm}`)
        .then(r => r.json()),
    enabled: !!selectedList
  });

  // Create/update mutation
  const saveMutation = useMutation({
    mutationFn: (data: any) => {
      const url = editingEntry
        ? `/api/admin/directory-lists/${selectedList}/entries/${editingEntry}`
        : `/api/admin/directory-lists/${selectedList}/entries`;
      return fetch(url, {
        method: editingEntry ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entries', selectedList] });
      setEditingEntry(null);
    }
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (entryId: string) =>
      fetch(`/api/admin/directory-lists/${selectedList}/entries/${entryId}`, {
        method: 'DELETE'
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entries', selectedList] });
    }
  });

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Directory Administration</h1>

      {/* Directory list selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Directory Type</label>
        <select
          value={selectedList || ''}
          onChange={(e) => setSelectedList(e.target.value)}
          className="border rounded px-3 py-2 w-64"
        >
          <option value="">Select directory...</option>
          {lists?.lists.map((list: any) => (
            <option key={list.id} value={list.id}>
              {list.list_name} ({list.entry_count} entries)
            </option>
          ))}
        </select>
      </div>

      {selectedList && (
        <>
          {/* Toolbar */}
          <div className="flex gap-4 mb-6">
            <input
              type="text"
              placeholder="Search entries..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="border rounded px-3 py-2 flex-1 max-w-md"
            />
            <button
              onClick={() => setEditingEntry('new')}
              className="px-4 py-2 bg-blue-600 text-white rounded"
            >
              + Add Entry
            </button>
          </div>

          {/* Entry list */}
          <div className="grid gap-4">
            {entries?.entries.map((entry: any) => (
              <div key={entry.id} className="border rounded p-4 flex justify-between">
                <div>
                  <h3 className="font-medium">{entry.name}</h3>
                  <div className="text-sm text-gray-600">
                    {entry.tags.map((tag: string) => (
                      <span key={tag} className="inline-block bg-gray-200 px-2 py-1 rounded mr-2">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditingEntry(entry.id)}
                    className="text-blue-600 hover:underline"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(entry.id)}
                    className="text-red-600 hover:underline"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Edit modal */}
          {editingEntry && (
            <Modal onClose={() => setEditingEntry(null)}>
              <DirectorySchemaForm
                entryType={lists.lists.find((l: any) => l.id === selectedList).entry_type}
                initialData={editingEntry === 'new' ? null : entries.entries.find((e: any) => e.id === editingEntry)}
                onSubmit={(data) => saveMutation.mutate(data)}
              />
            </Modal>
          )}
        </>
      )}
    </div>
  );
}
```

## Tech Stack

**Backend**
- FastAPI for REST endpoints
- Existing `DirectoryImporter.load_schema()` for YAML parsing
- SQLAlchemy async for database operations
- Existing auth middleware for account isolation

**Frontend**
- Astro for page framework
- React for dynamic UI components
- TanStack Query for API state management
- React Hook Form for form handling
- Zod for schema validation (generated from YAML)
- Tailwind CSS for styling

## Data Flow

1. User selects directory type from dropdown
2. Frontend fetches schema via `/api/admin/directory-schemas/{entry_type}`
3. Frontend generates form fields dynamically based on schema metadata
4. User fills form, Zod validates against generated schema
5. On submit, POST/PUT to `/api/admin/directory-lists/{list_id}/entries`
6. Backend validates against YAML schema using existing `DirectoryImporter.validate_entry()`
7. Entry saved to database, UI refreshes

## Key Design Decisions

**Single Form Component**: `DirectorySchemaForm` generates all form fields dynamically, eliminating the need for 13 separate form components.

**Schema-Driven Validation**: Both frontend (Zod) and backend (existing validator) use the same YAML schema as source of truth.

**Reuse Existing Code**: Leverages `DirectoryImporter.load_schema()` and `validate_entry()` rather than duplicating schema parsing logic.

**Account Isolation**: All queries join through `DirectoryList.account_id` to enforce multi-tenancy.

**Progressive Enhancement**: Keep CSV import/export for bulk operations, add UI for individual entry management.

## Field Type Mappings

```typescript
// YAML type → Form control mapping
{
  'string': 'text input',
  'text': 'textarea',
  'number': 'number input',
  'integer': 'number input',
  'boolean': 'checkbox',
  'array': 'multi-value input (chips)',
  'date': 'date picker'
}
```

## Security Considerations

**Authentication & Authorization** (see [Architecture Decision](directory-admin-architecture-decision.md)):
- JWT token-based authentication for human users
- Role-based access control (owner, admin, editor, viewer)
- Directory-level permission overrides
- Super admin access for internal staff

**Multi-Tenant Isolation**:
- Account-scoped queries prevent cross-tenant access
- User-to-account mapping via `account_users` table
- Directory permissions checked on every request

**Data Security**:
- Schema validation prevents malformed data
- No direct YAML file writes (read-only base schemas)
- Account customizations stored in database, not filesystem
- Input sanitization on all text fields

**Token Security**:
- HTTP-only cookies for refresh tokens
- Short-lived access tokens (15 minutes)
- Token revocation via blacklist

## Future Enhancements

- Bulk edit operations (update multiple entries)
- CSV export from UI
- Schema editor for admins (modify YAML through UI)
- Entry duplication detection
- Audit log (track who changed what)
- Field-level permissions (some fields read-only)
