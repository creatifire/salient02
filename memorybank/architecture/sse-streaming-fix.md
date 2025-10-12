# SSE Streaming: Markdown Formatting Loss

## Problem

Markdown tables and multi-line content were not formatting correctly after streaming completed. Raw markdown appeared instead of formatted HTML.

Example:
```
| Country | Capital ||---------|---------|
```
Instead of a formatted table.

## Root Cause

**SSE Protocol Violation**: Multi-line data in Server-Sent Events must have each line prefixed with `data: `.

### What Was Happening

```python
# WRONG - SSE protocol violation
yield f"event: message\ndata: {event_data}\n\n"

# If event_data contains newlines:
# event: message
# data: Line 1
# Line 2          ← Not recognized as data!
```

The second line `Line 2` was not prefixed with `data:`, so browsers dropped it. Frontend received markdown without newlines, breaking table syntax.

## Investigation Trail

1. **Database check**: LLM response stored correctly with newlines ✅
   ```sql
   '| Country | Capital |\n|---|---|\n| France | Paris |'
   ```

2. **Frontend check**: Received WITHOUT newlines ❌
   ```javascript
   '| Country | Capital ||---|---|| France | Paris |'
   ```

3. **Why tables failed**: `marked.js` requires newlines to parse table syntax. Single-line table markdown is invalid.

## Solution

Fixed `backend/app/api/account_agents.py` line ~738:

```python
# Split multi-line data and prefix each line with 'data: '
if '\n' in event_data:
    data_lines = event_data.split('\n')
    formatted_data = '\n'.join(f"data: {line}" for line in data_lines)
    yield f"event: {event_type}\n{formatted_data}\n\n"
else:
    yield f"event: {event_type}\ndata: {event_data}\n\n"
```

### Correct SSE Output

```
event: message
data: | Country | Capital |
data: |---------|---------|
data: | France  | Paris   |

```

Each line is now properly prefixed, browsers preserve all lines, frontend receives markdown with newlines intact, `marked.js` parses tables correctly.

## Impact

**CRITICAL** - Affects all multi-line content in SSE streaming:
- Markdown tables
- Code blocks with multiple lines
- Multi-paragraph responses
- Any content with `\n` characters

## Files Modified

- `backend/app/api/account_agents.py` - Event generator SSE formatting
- `web/public/widget/chat-widget.js` - Added `gfm: true` to marked.js config
- `web/src/pages/demo/simple-chat.astro` - Added `gfm: true`
- `web/public/htmx-chat.html` - Added `gfm: true`

## Testing

Submit request for markdown table:
```
"in a table list moons of jupiter"
```

**Before fix**: Raw markdown with pipes visible
**After fix**: Properly formatted HTML table

## References

- SSE Spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#server-sent-events
- Key requirement: Multi-line data fields must repeat `data:` prefix
- Related: GitHub Flavored Markdown requires `gfm: true` in marked.js for table support

