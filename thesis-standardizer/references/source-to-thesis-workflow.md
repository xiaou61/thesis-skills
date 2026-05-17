# Source To Thesis

Use this when the user gives code, repo, database, API, screenshots, or test reports and wants thesis content.

## Goal

Turn implementation evidence into thesis facts before writing prose.

## Default Flow

1. Run:

```powershell
python .\scripts\build_project_evidence.py . --out .\paper-context\evidence
```

2. Read:

- `project-evidence.json`
- `code-structure.md`
- `tech-stack.md`
- `api-list.md`
- `database-schema.md`
- `test-results.md`

3. Confirm important claims against source code or user material.
4. Write facts into:

- `thesis-ai-spec.yaml`
- `figure-registry.yaml`

5. Draft chapters only after facts are stable.

## Draft Order

For system papers, write in this order:

1. related technology
2. requirement analysis
3. overall design
4. database / API / module design
5. detailed implementation
6. testing
7. introduction and conclusion last

## Stop Conditions

Do not draft final prose if any of these are missing:

- school template or standard profile
- code evidence for claimed modules
- schema/API evidence for database or interface claims
- screenshots/run evidence for UI claims
- test evidence for tested/stable/effective claims

Return a missing-material list instead.

## Figures

Update `figure-registry.yaml` before drawing:

- architecture
- module diagram
- business flow
- ER diagram
- sequence diagram
- screenshots

Do not create diagrams that cannot be traced to code or evidence.
