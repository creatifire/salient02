# Full-Text Search (FTS) Example Queries

Example queries for testing the directory service FTS functionality with Wyckoff Hospital medical professionals.

## Word Variation Queries

These queries test FTS's ability to match word variations and stems:

```python
# Query: "cardio" - should match "cardiologist", "cardiology", "cardiovascular"
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="cardio",
    search_mode="fts"
)
# Expected: Doctors in Cardiology department or with Cardiology specialty

# Query: "surgery" - should match "surgeon", "surgery", "surgical"
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="surgery",
    search_mode="fts"
)
# Expected: Doctors in Surgery department or with surgical specialties

# Query: "pediatric" - should match "pediatrics", "pediatrician"
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="pediatric",
    search_mode="fts"
)
# Expected: Doctors in Pediatrics department
```

## Multi-Word Queries

These queries test FTS's AND logic for multiple words:

```python
# Query: "plastic surgery" - should match doctors with BOTH "plastic" AND "surgery"
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="plastic surgery",
    search_mode="fts"
)
# Expected: Doctors with "Plastic Surgery" specialty (ranked higher)

# Query: "emergency medicine" - should match emergency department doctors
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="emergency medicine",
    search_mode="fts"
)
# Expected: Doctors in Emergency Medicine department

# Query: "heart doctor" - should match cardiologists
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="heart doctor",
    search_mode="fts"
)
# Expected: Doctors with "cardiology" or "heart" in their data
```

## Combined Filter Queries

These queries test FTS with additional filters:

```python
# FTS + Tag filter: Spanish-speaking doctors in medicine
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="medicine",
    tags=["Spanish"],
    search_mode="fts"
)
# Expected: Spanish-speaking doctors with "medicine" in their data

# FTS + JSONB filter: Female surgeons
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="surgery",
    jsonb_filters={"gender": "female"},
    search_mode="fts"
)
# Expected: Female doctors in Surgery department or with surgical specialty

# FTS + Department filter: Pediatricians
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="doctor",
    jsonb_filters={"department": "Pediatrics"},
    search_mode="fts"
)
# Expected: Doctors in Pediatrics department
```

## Relevance Ranking Tests

These queries test FTS's weighted relevance ranking:

```python
# Query: "surgery" - should rank by relevance
# Expected ranking (highest to lowest):
# 1. Name contains "surgery" (Weight A)
# 2. Tags contain "surgery" (Weight B)
# 3. entry_data contains "surgery" in department/specialty (Weight C)

await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="surgery",
    search_mode="fts",
    limit=10
)
```

## Edge Cases

These queries test FTS error handling:

```python
# Empty query - should return entries without name filter
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query=None,
    search_mode="fts"
)
# Expected: Up to max_results entries

# Single character - may not produce meaningful results
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="a",
    search_mode="fts"
)
# Expected: Fallback to substring or no results

# Special characters - should be handled gracefully
await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="ob/gyn",
    search_mode="fts"
)
# Expected: Fallback to substring search if tsquery fails
```

## Search Mode Comparison

Compare all three search modes with the same query:

```python
query = "smith"

# Exact match (case-sensitive)
exact_results = await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="Dr. Smith",
    search_mode="exact"
)
# Expected: Only exact matches

# Substring match (default)
substring_results = await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="smith",
    search_mode="substring"
)
# Expected: Any name containing "smith" (case-insensitive)

# Full-text search
fts_results = await DirectoryService.search(
    session=session,
    accessible_list_ids=[doctors_list_id],
    name_query="smith",
    search_mode="fts"
)
# Expected: Names with "smith", ranked by relevance (name > tags > entry_data)
```

## Agent Tool Usage

Example natural language queries that the LLM agent would translate to tool calls:

| User Query | Tool Call |
|------------|-----------|
| "Find me a cardiologist" | `search_directory(list_name="doctors", query="cardio", search_mode="fts")` |
| "Spanish-speaking surgeon" | `search_directory(list_name="doctors", query="surgery", tag="Spanish", search_mode="fts")` |
| "Female pediatrician" | `search_directory(list_name="doctors", query="pediatric", gender="female", search_mode="fts")` |
| "Emergency doctor" | `search_directory(list_name="doctors", query="emergency", search_mode="fts")` |
| "Find Dr. Smith" | `search_directory(list_name="doctors", query="Dr. Smith", search_mode="exact")` |

## Expected Performance

With Wyckoff's 124 doctor profiles:
- **Query time**: < 50ms for FTS queries (GIN index)
- **Result count**: Configured max_results (default: 5)
- **Relevance**: Results ordered by ts_rank() DESC
- **Accuracy**: Word variations handled via PostgreSQL stemming

## Testing Checklist

- [ ] Word variations work (e.g., "cardio" → "cardiologist")
- [ ] Multi-word queries work (e.g., "plastic surgery")
- [ ] Relevance ranking makes sense (name > tags > entry_data)
- [ ] Combined filters work (FTS + tags + JSONB)
- [ ] Empty query handled gracefully
- [ ] Error handling works (invalid tsquery fallback)
- [ ] Backward compatible (substring mode still works)
- [ ] Performance acceptable (< 100ms)
- [ ] Agent tool integration works end-to-end

