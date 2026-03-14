# DataClaw — AGENTS.md

**Generated:** 2026-03-14  
**Project:** DataClaw — Export coding agent conversations to Hugging Face  
**Stack:** Python 3.10+ / pytest / ruff / mypy  
**Status:** Active (v0.3.2)

---

## OVERVIEW

DataClaw is a CLI tool that exports conversation history from Claude Code, Codex, Gemini CLI, OpenCode, and OpenClaw to Hugging Face as structured JSONL datasets. It handles multi-source discovery, PII redaction, secret detection, and attestation-gated publishing.

**Core Features:**
- Multi-source session discovery (Claude, Codex, Gemini, OpenCode, OpenClaw, Kimi, custom)
- Automated secret detection (API keys, tokens, private keys, entropy analysis)
- PII redaction (usernames, emails, custom strings)
- Attestation-gated publishing (requires explicit user confirmation)
- Hugging Face Hub integration (push/pull datasets)
- JSON output with metadata (token counts, model info, timestamps)

---

## STRUCTURE

```
dataclaw/
  pyproject.toml                    # Package config (ruff, mypy, pytest)
  Makefile                          # Dev targets: test, lint, format, type-check, coverage
  README.md                         # User guide + examples
  AGENTS.md                         # This file (developer guide)
  LICENSE                           # MIT
  
  dataclaw/
    __init__.py                     # Version + public API
    cli.py                          # Main CLI entry point (argparse)
    parser.py                       # Multi-source session discovery + parsing
    config.py                       # Config file management (YAML)
    anonymizer.py                   # Username/path anonymization
    secrets.py                      # Secret detection + redaction (regex + entropy)
  
  scripts/
    export_kaidol_conversations.py  # KAIdol-specific export helper
  
  tests/
    conftest.py                     # pytest fixtures
    test_cli.py                     # CLI argument parsing + flow tests
    test_parser.py                  # Session discovery + parsing tests
    test_config.py                  # Config load/save tests
    test_anonymizer.py              # Anonymization tests
    test_secrets.py                 # Secret detection + redaction tests
  
  .github/workflows/
    test.yml                        # CI: lint + type-check + test matrix (3.10-3.13)
    publish.yml                     # CD: publish to PyPI on release
```

---

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add CLI command | `dataclaw/cli.py` | argparse subcommands: status, prep, list, config, confirm, export |
| Add data source | `dataclaw/parser.py` | CLAUDE_DIR, CODEX_DIR, GEMINI_DIR, OPENCODE_DIR, OPENCLAW_DIR, KIMI_DIR, CUSTOM_DIR |
| Add secret pattern | `dataclaw/secrets.py` | Regex patterns + entropy analysis for detection |
| Add redaction rule | `dataclaw/anonymizer.py` | Username hashing, path anonymization |
| Config schema | `dataclaw/config.py` | DataClawConfig dataclass, load/save YAML |
| Test CLI flow | `tests/test_cli.py` | Stage transitions, attestation validation |
| Test parsing | `tests/test_parser.py` | Session discovery, conversation reconstruction |

---

## KEY MODULES

### cli.py (Main Entry Point)

**Subcommands:**
- `status` — Show current stage (1-4: auth → configure → review → done)
- `prep` — Discover projects, check HF auth
- `list` — List all projects with exclusion status
- `config` — Show/update config (repo, source, excludes, redactions)
- `confirm` — Scan PII, verify attestations, unlock pushing
- `export` — Export locally or push to HF (gated by confirm)
- `update-skill` — Install/update Claude Code skill

**Output Format:**
- `prep`, `config`, `status`, `confirm` → pure JSON
- `export` → human-readable text + `---DATACLAW_JSON---` + JSON block
- Always parse JSON and follow `next_steps`

**Key Fields in JSON:**
- `stage` / `stage_number` / `total_stages` — workflow position
- `next_steps` — ordered list of actions
- `next_command` — single most important command (null if user input needed)

### parser.py (Multi-Source Discovery)

**Supported Sources:**
- `claude` — Claude Code sessions (~/.claude/projects/)
- `codex` — Codex sessions (~/.codex/sessions/)
- `gemini` — Gemini CLI sessions (~/.gemini/)
- `opencode` — OpenCode sessions (~/.opencode/)
- `openclaw` — OpenClaw sessions (~/.openclaw/)
- `kimi` — Kimi CLI sessions (~/.kimi/)
- `custom` — Custom JSONL files (user-provided)

**Key Functions:**
- `discover_projects(source)` — Find all projects for a source
- `parse_project_sessions(project_path, source)` — Extract conversations
- `Session` dataclass — Holds messages, metadata, token counts

### secrets.py (Detection + Redaction)

**Detection Methods:**
1. **Regex patterns** — JWT, API keys (Anthropic, OpenAI, HF, GitHub, AWS), DB passwords, private keys, Discord webhooks
2. **Entropy analysis** — Long high-entropy strings in quotes (potential secrets)
3. **Email detection** — Personal email addresses

**Redaction:**
- `redact_text(text, config)` — Apply all redaction rules
- `redact_session(session, config)` — Redact messages + tool calls
- Custom strings + usernames from config

### config.py (Configuration)

**DataClawConfig:**
- `repo` — HF repo (user/dataset-name)
- `source` — Scope (claude|codex|gemini|opencode|openclaw|all)
- `excluded_projects` — Projects to skip
- `redact_strings` — Custom strings to redact
- `redact_usernames` — Usernames to anonymize
- `confirmed_projects` — User has reviewed project list

**File Location:** `~/.dataclaw/config.yaml`

### anonymizer.py (PII Anonymization)

**Anonymization:**
- Username hashing (stable hash for consistency)
- Path anonymization (strip to project-relative)
- Email redaction

---

## CONVENTIONS

**Line length:** 120 chars (ruff)  
**Target Python:** 3.10+  
**Lint rules:** E, W, F, I, B, C4, UP (E501 ignored)  
**Type checking:** mypy with `warn_return_any`, `warn_unused_configs`  
**Testing:** pytest, `tests/` directory, 100% coverage target  
**Package layout:** Flat (`dataclaw/` at root, not `src/`)  

**Naming:**
- CLI commands: lowercase, hyphenated (e.g., `--no-push`, `--full-name`)
- Functions: snake_case
- Classes: PascalCase
- Constants: UPPER_SNAKE_CASE

**JSON Output:**
- Always include `stage`, `stage_number`, `total_stages`
- Always include `next_steps` (list of strings)
- Always include `next_command` (string or null)
- Use ISO 8601 timestamps

---

## ANTI-PATTERNS

- Do NOT use `# type: ignore` or `cast()` — fix the type error properly
- Do NOT add runtime dependencies without updating `pyproject.toml`
- Do NOT skip PII audit — automated redaction is not foolproof
- Do NOT publish without explicit user confirmation (gated by `dataclaw confirm`)
- Do NOT run bare `huggingface-cli login` — always use `--token`
- Do NOT assume `--exclude`, `--redact`, `--redact-usernames` overwrite — they APPEND
- Do NOT skip source selection — must be explicitly set before export

---

## COMMANDS

```bash
# Run all tests
make test

# Lint + type check
make check

# Format code
make format

# Coverage report
make coverage

# Clean build artifacts
make clean

# Install in development mode
pip install -e ".[dev]"

# Run specific test
pytest tests/test_cli.py -v

# Run with coverage
pytest tests/ --cov=dataclaw --cov-report=html
```

---

## DEVELOPMENT WORKFLOW

### Adding a New Data Source

1. **Add source constant** in `parser.py`:
   ```python
   MY_SOURCE = "my_source"
   MY_DIR = Path.home() / ".my_source"
   ```

2. **Implement discovery** in `parser.py`:
   ```python
   def discover_projects_my_source() -> list[str]:
       # Return list of project names
   ```

3. **Implement parsing** in `parser.py`:
   ```python
   def parse_my_source_sessions(project_path: Path) -> list[Session]:
       # Return list of Session objects
   ```

4. **Update `discover_projects()`** to handle new source

5. **Add tests** in `tests/test_parser.py`

6. **Update CLI help** in `cli.py`

### Adding a New Secret Pattern

1. **Add regex pattern** in `secrets.py`:
   ```python
   PATTERNS = {
       "my_secret": re.compile(r"pattern_here"),
   }
   ```

2. **Add test cases** in `tests/test_secrets.py`

3. **Document** in README.md

### Adding a New CLI Command

1. **Add subparser** in `cli.py`:
   ```python
   subparsers.add_parser("my_command", help="...")
   ```

2. **Implement handler** in `cli.py`:
   ```python
   def handle_my_command(args) -> dict[str, Any]:
       # Return JSON output
   ```

3. **Add tests** in `tests/test_cli.py`

4. **Update AGENTS.md** (this file)

---

## TESTING

**Test Coverage:** 100% target  
**Test Framework:** pytest  
**Fixtures:** `conftest.py` provides temp directories, mock configs

**Run Tests:**
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_cli.py -v

# Specific test
pytest tests/test_cli.py::test_status_stage_1 -v

# With coverage
pytest tests/ --cov=dataclaw --cov-report=term-missing
```

**Test Organization:**
- `test_cli.py` — CLI argument parsing, stage transitions, JSON output
- `test_parser.py` — Session discovery, conversation reconstruction
- `test_config.py` — Config load/save, validation
- `test_anonymizer.py` — Username hashing, path anonymization
- `test_secrets.py` — Secret detection, redaction

---

## CI/CD

**GitHub Actions:**
- `test.yml` — Lint + type-check + test matrix (Python 3.10-3.13)
- `publish.yml` — Publish to PyPI on release

**Triggers:**
- `test.yml` — Push to main, pull requests
- `publish.yml` — Release tags (v*)

---

## NOTES

- **Version:** Managed in `dataclaw/__init__.py` and `pyproject.toml`
- **Dependencies:** Minimal (huggingface_hub only)
- **Dev dependencies:** pytest, mypy, ruff
- **License:** MIT
- **Repository:** https://github.com/banodoco/dataclaw
- **PyPI:** https://pypi.org/project/dataclaw/

---

## GOTCHAS

1. **Config file location** — `~/.dataclaw/config.yaml` (not in project root)
2. **Source selection is required** — Must explicitly set before export
3. **Attestations are gated** — `dataclaw confirm` must pass before `dataclaw export --publish-attestation`
4. **PII audit is critical** — Automated redaction misses things; manual review required
5. **Large exports take time** — 500+ sessions may take 1-3 minutes
6. **HF token handling** — Always use `--token` flag, never interactive login

---

**Last Updated:** 2026-03-14  
**Maintainer:** Banodoco  
**Status:** Active Development
