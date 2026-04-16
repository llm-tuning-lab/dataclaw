# Cursor Gaps vs CCHV

## Scope

This note compares Cursor handling in:

- DataClaw: `~/dataclaw`
- Claude Code History Viewer (CCHV): `~/claude-code-history-viewer`

There is no real Cursor data on this machine, so this comparison is based on code only.

## Summary

Based on the current implementations, CCHV appears to preserve more Cursor-specific structure than DataClaw.

The clearest current DataClaw gaps are:

1. It drops user image attachments.
2. It does not preserve `isThought` semantics for assistant thought bubbles.
3. It flattens Cursor bubble content into a smaller normalized schema and loses content-array ordering/interleaving.
4. It does not preserve some Cursor session metadata that CCHV loads from workspace composer data.
5. It may be less robust than CCHV when Cursor JSON contains embedded control characters.

## Detailed Findings

### 1. CCHV keeps user image attachments; DataClaw drops them

CCHV reads `bubble.images` for user bubbles and preserves `data:image/...;base64,...` attachments as image content blocks.

References:

- CCHV user-bubble conversion: `~/claude-code-history-viewer/src-tauri/src/providers/cursor.rs:439-492`
- Image handling in user bubbles: `~/claude-code-history-viewer/src-tauri/src/providers/cursor.rs:452-476`

DataClaw's Cursor parser only exports user `text` and ignores `images`.

References:

- DataClaw user-bubble handling: `~/dataclaw/dataclaw/parsers/cursor.py:251-262`

Practical consequence:

- If Cursor stores user screenshots or pasted image attachments in `bubble.images`, CCHV will preserve them and DataClaw will not.

### 2. CCHV preserves `isThought` as thinking; DataClaw does not

CCHV checks `bubble.isThought` on assistant bubbles and emits a `thinking` content block when present.

References:

- CCHV assistant-bubble conversion: `~/claude-code-history-viewer/src-tauri/src/providers/cursor.rs:494-571`
- `isThought` handling: `~/claude-code-history-viewer/src-tauri/src/providers/cursor.rs:542-553`

DataClaw does not check `isThought`. It only exports assistant thinking when a separate `bubble.thinking.text` field exists.

References:

- DataClaw assistant bubble with tool path: `~/dataclaw/dataclaw/parsers/cursor.py:317-321`
- DataClaw assistant bubble without tool path: `~/dataclaw/dataclaw/parsers/cursor.py:333-347`

Practical consequence:

- A Cursor bubble represented as plain `text` plus `isThought: true` would be preserved by CCHV as thought text, but would become normal assistant `content` in DataClaw.

### 3. CCHV keeps a structured content array; DataClaw flattens it

CCHV converts Cursor bubbles into a structured content array containing items such as:

- `text`
- `image`
- `thinking`
- `tool_use`
- `tool_result`

References:

- CCHV user-bubble content array: `~/claude-code-history-viewer/src-tauri/src/providers/cursor.rs:445-490`
- CCHV assistant-bubble content array: `~/claude-code-history-viewer/src-tauri/src/providers/cursor.rs:500-569`

DataClaw flattens Cursor bubbles into the normalized DataClaw schema:

- user `content`
- assistant `content`
- assistant `thinking`
- assistant `tool_uses`

References:

- DataClaw normalized session schema: `~/dataclaw/dataclaw/parsers/common.py:56-71`
- DataClaw Cursor parser: `~/dataclaw/dataclaw/parsers/cursor.py:251-356`

Practical consequence:

- Even when the same information is mostly present, DataClaw loses original content-array ordering/interleaving.
- For example, an assistant bubble that conceptually contains `tool_use` followed by `tool_result` and then additional text is normalized into `tool_uses[]` plus top-level `content`, not preserved as an ordered content array.

### 4. CCHV keeps more Cursor session metadata than DataClaw exports

CCHV reads workspace-level Cursor composer metadata and keeps fields such as:

- composer `name`
- `createdAt`
- `lastUpdatedAt`
- `unifiedMode`
- `isArchived`
- derived `has_tool_use`
- summary/title

References:

- CCHV session loading from workspace DB: `~/claude-code-history-viewer/src-tauri/src/providers/cursor.rs:116-187`
- Workspace composer metadata loader: `~/claude-code-history-viewer/src-tauri/src/providers/cursor.rs:352-380`

DataClaw exports only the normalized session schema with:

- `session_id`
- `model`
- `git_branch`
- `start_time`
- `end_time`
- `messages`
- `stats`

References:

- DataClaw session schema: `~/dataclaw/dataclaw/parsers/common.py:56-71`

Practical consequence:

- Cursor-specific session title/summary, mode, archived state, and related metadata are not preserved in DataClaw export.

### 5. CCHV may be more robust to malformed Cursor JSON

CCHV sanitizes embedded control characters before parsing Cursor JSON values.

References:

- CCHV Cursor JSON sanitizer: `~/claude-code-history-viewer/src-tauri/src/providers/cursor.rs:383-397`

DataClaw calls `json.loads(...)` directly on Cursor DB values without a similar sanitization pass.

References:

- DataClaw project-index parse path: `~/dataclaw/dataclaw/parsers/cursor.py:85-86,112-113`
- DataClaw session/bubble parse path: `~/dataclaw/dataclaw/parsers/cursor.py:191-192,211-212`

Practical consequence:

- If real Cursor DB rows contain control characters or otherwise slightly malformed JSON, CCHV may still load them while DataClaw may skip them.

## Ambiguous Difference: Tool Input Field Source

CCHV and DataClaw normalize Cursor tool calls from slightly different raw fields.

CCHV uses:

- `toolFormerData.rawArgs`

References:

- `~/claude-code-history-viewer/src-tauri/src/providers/cursor.rs:516-530`

DataClaw uses:

- `toolFormerData.params`
- and a nested `tools[].parameters` unwrapping path

References:

- `~/dataclaw/dataclaw/parsers/cursor.py:272-284`

Without real Cursor data on this machine, this note does not claim that one side is definitively more faithful than the other here. It is simply an implementation difference worth noting.

## Bottom Line

Based on code only, the strongest likely Cursor gaps in DataClaw compared with CCHV are:

- user image attachments
- `isThought` / thought-bubble semantics
- richer ordered content-array structure
- extra session metadata from workspace composer state
- parser robustness for control-character-containing Cursor JSON
