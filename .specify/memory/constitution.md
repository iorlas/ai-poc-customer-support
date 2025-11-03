<!--
SYNC IMPACT REPORT
==================
Version Change: 2.0.0 → 2.1.0
Change Type: MINOR (New coding standards section added)
Date: 2025-11-04

Modified Principles:
- None (existing principles unchanged)

Added Sections:
- New Principle VI: Coding Standards & Pragmatism
  - No docstrings required for POC
  - Minimal __init__.py files
  - Idiomatic Python only
  - All imports at top of file
  - Divide and conquer architecture (components + orchestrator)
  - Happy path first, fail fast philosophy

Removed Sections:
- None

Modified Sections:
- None

Templates Requiring Updates:
- ✅ .specify/templates/plan-template.md (No structural changes needed)
- ✅ .specify/templates/spec-template.md (No changes needed)
- ✅ .specify/templates/tasks-template.md (No changes needed)

Follow-up TODOs:
- None (all changes applied)
-->

# Customer Support Bot Constitution

**Project Scope**: Proof of Concept (POC) - Rapid iteration without formal testing, CI/CD, or deployment processes.

## Core Principles

### I. Pipeline-First Architecture

Every feature MUST integrate into the Dagster pipeline architecture. All data processing follows the bronze → silver → gold medallion pattern:

- **Bronze Layer**: Raw data extraction (HTML, YouTube, RSS feeds)
- **Silver Layer**: Cleaned and transformed content (LLM processing, summarization)
- **Gold Layer**: Aggregated, business-ready data (serving via FastAPI/Streamlit)

Assets MUST be independently materializable. Inter-asset dependencies MUST be explicitly declared via Dagster asset dependencies.

**Rationale**: Ensures data lineage traceability, enables incremental processing, and supports MLflow experiment tracking even in POC phase.

### II. Code Quality Gates (NON-NEGOTIABLE)

Pre-commit hooks and `make check` MUST pass before any commit:

1. `ruff format` - Enforce consistent formatting
2. `ruff check --fix` - Auto-fix linting issues
3. `ty check` - Validate type safety

Manual interventions for non-auto-fixable issues MUST be resolved before commit.

**Testing Policy for POC**: Tests are NOT required. This is a proof-of-concept focused on rapid iteration and exploration, not production readiness.

**Rationale**: Maintains code quality and prevents obvious bugs without the overhead of comprehensive test suites. Quality gates catch syntax errors, type issues, and style violations automatically.

### III. Type Safety & Validation

Python 3.12+ type hints SHOULD be used for public function signatures. Pydantic MUST be used for:

- Configuration management (environment variables, settings)
- Data validation (API requests, LLM responses)
- Schema enforcement (entity models)

The `ty` type checker MUST report zero errors on core type safety rules (see pyproject.toml). Warnings are acceptable and MAY be deferred for POC iteration speed.

**Rationale**: Catches bugs at development time and provides inline documentation. Type hints are relaxed to "SHOULD" for POC flexibility, but Pydantic validation remains mandatory for external data.

### IV. Observability & Experiment Tracking

All LLM calls SHOULD be tracked via MLflow when experimenting with prompts or models:

- **Experiments**: Track prompts, model versions, parameters
- **Runs**: Log inputs, outputs, metrics, artifacts
- **Models**: Version promising approaches

Structured logging via `structlog` SHOULD be used for debugging. Log levels:
- INFO: Pipeline stage completions, asset materializations
- WARNING: Fallback behaviors, retries
- ERROR: Failures requiring attention

**Rationale**: Enables learning from experiments and debugging issues. Requirements relaxed to "SHOULD" to allow rapid iteration without mandatory tracking overhead.

### V. Dependency Management & Reproducibility

Dependencies MUST be managed via `uv`:

- `pyproject.toml` is the single source of truth
- `uv sync` ensures reproducible environments
- Lock files SHOULD be committed (but may be regenerated frequently in POC)

External services MUST support environment-based configuration:
- OpenAI-compatible APIs (OpenRouter, local deployments)
- MLflow tracking URIs (optional in POC)
- Dagster home directories

**Rationale**: Eliminates "works on my machine" issues even in POC phase. Consistent dependency management enables smooth transition to production later.

### VI. Coding Standards & Pragmatism

Code MUST follow these pragmatic standards optimized for POC velocity:

**Documentation**:
- NO docstrings required at POC stage
- Code should be self-explanatory through clear naming
- Comments only for non-obvious business logic or workarounds

**Module Structure**:
- AVOID creating `__init__.py` files unless genuinely beneficial (namespace packages, re-exports)
- Flat module structure preferred over deep hierarchies
- Import directly from modules, not via `__init__.py` indirection

**Import Policy**:
- ALL imports MUST be at the top of the file
- NO inline imports (except for circular dependency workarounds - ask first)
- Standard library → third-party → local imports (ruff enforces this)

**Code Idioms**:
- MUST use idiomatic Python approaches (list comprehensions, context managers, decorators)
- If diverging from Python idioms is necessary, ASK for approval first
- Examples: Use `with open()`, not manual file.close(); use `@property`, not getters

**Architecture Pattern**:
- "Divide and conquer": Components with concentrated logic + orchestrator
- NOT enterprise scale - avoid over-abstraction, factories, complex inheritance
- Example: `extract_html()` + `process_content()` + `pipeline_orchestrator()`

**Error Handling Philosophy**:
- Happy path FIRST - implement the main flow without defensive programming
- Fail fast, fail often - let errors surface during POC experimentation
- ONLY handle errors you've actually encountered or know will occur
- If unsure whether error handling is needed, ASK rather than over-engineer

**Rationale**: Maximizes POC velocity by eliminating documentation overhead, simplifying structure, and focusing on learning through failures rather than preventing hypothetical issues.

## Quality Standards

### Code Quality Gates (Mandatory)

`make check` runs these quality checks:

1. **Format check**: `ruff format` ensures consistent code style
2. **Lint check**: `ruff check` catches common errors and enforces best practices
3. **Type check**: `ty check` validates type annotations and catches type errors

All checks MUST pass before committing code.

**Pre-commit Hook**: Automatically runs quality gates on every commit attempt. Failed checks BLOCK the commit.

### Performance Expectations (Advisory, Not Enforced)

Dagster assets SHOULD aim for reasonable performance:

- HTML extraction: < 10s per page
- LLM summarization: < 60s per content item
- Full pipeline run: Complete within reasonable development iteration time

Performance issues that block development MUST be addressed. Minor slowdowns MAY be deferred.

## Development Workflow

### Feature Development Process (POC-Simplified)

1. **Specification** (Optional): Use `/speckit.specify` for complex features requiring clarity
2. **Planning** (Optional): Use `/speckit.plan` for multi-step features
3. **Implementation**: Iterate rapidly, commit frequently with `make check` passing
4. **Validation**: Manual testing via Streamlit UI or Dagster materialization
5. **Learning**: Document insights, promising approaches, and dead ends

**Philosophy**: Bias toward action. Skip formal specs/plans for simple experiments. Document learnings, not comprehensive design docs.

### Commit Conventions

Follow conventional commits format:

- `feat:` - New features or capabilities
- `fix:` - Bug fixes
- `docs:` - Documentation updates
- `refactor:` - Code improvements without behavior changes
- `experiment:` - Experimental features or approaches being explored
- `chore:` - Dependency updates, tooling changes

**Commit Frequency**: Commit early and often. Every working increment SHOULD be committed.

## Governance

### Amendment Process

Constitution amendments REQUIRE:

1. Documented rationale for the change
2. Version bump following semantic versioning:
   - **MAJOR**: Backward-incompatible principle changes or removals
   - **MINOR**: New principles or materially expanded guidance
   - **PATCH**: Clarifications, wording fixes, non-semantic refinements
3. Update to Sync Impact Report (HTML comment at top of this file)

Template propagation SHOULD be done but MAY be deferred if blocking rapid iteration.

### Compliance Reviews (POC-Simplified)

Feature development SHOULD consider:

- Does this fit the pipeline architecture?
- Did `make check` pass?
- Is this approach worth documenting for future reference?

Formal constitution checks and complexity justifications are OPTIONAL for POC work.

### Agent Guidance

For runtime development guidance specific to Claude Code, refer to `/Users/iorlas/Projects/my/pocs/customer_support/CLAUDE.md`.

Generic principles in this constitution apply to all development agents and team members, adapted for POC scope.

**Version**: 2.1.0 | **Ratified**: 2025-11-04 | **Last Amended**: 2025-11-04
