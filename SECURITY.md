# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main`  | ✅ Yes     |

Only the current `main` branch receives security fixes.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report security issues privately by emailing **coding.projects.1642@proton.me**.

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations (optional)

You will receive an acknowledgment within 72 hours. We aim to release a fix within 14 days of a confirmed report, depending on severity and complexity.

## Scope

DagExecutor is the DAG-based workflow executor for bounded AI task orchestration. The primary security surface is:

- **Arbitrary command execution** via bash/script nodes in the DAG
- **Path traversal** via workspace or artifact path construction
- **Variable injection** — untrusted variable values reaching agent or script prompts
- **Gate bypass** — anything that advances a gate node without explicit approval
- **Log injection** via untrusted task content written to structured logs

## Out of Scope

- Vulnerabilities in upstream AI providers or Claude Code
- Issues requiring physical access to the host machine
- Denial-of-service via normal task load (rate limiting is a configuration concern)
