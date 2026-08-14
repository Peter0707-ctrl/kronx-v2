# Phase 3.1 — Production Operations, Observability, Recovery & Lifecycle Control Engine

## 1. Overview
The Operations Subsystem (`backend/operations/`) provides an enterprise-grade operational control, observability, recovery, and diagnostics layer around the core Kron-X AI security architecture.

It enforces zero-trust authority invariants, deterministic state machines, bounded metrics, structured event correlation, multi-tenant isolation, atomic backup/recovery, and fail-closed readiness evaluations.

---

## 2. Architecture & Subsystems

```
backend/operations/
├── __init__.py           # Unified exports
├── schemas.py            # Strict Pydantic models & enums
├── errors.py             # Standardized operational error codes
├── lifecycle.py          # SystemLifecycleManager (state transitions & draining)
├── health.py             # OperationsHealthEngine (subsystem & store health)
├── readiness.py          # OperationsReadinessEngine (fail-closed scoring)
├── metrics.py            # MetricsEngine (cardinally bounded aggregation)
├── events.py             # OperationalEventManager (structured events)
├── correlation.py       # Correlation ID & request propagation
├── diagnostics.py        # DiagnosticEngine (safe non-destructive checks)
├── integrity.py          # StoreIntegrityManager (SHA-256 hash & syntax)
├── backup.py             # BackupEngine (atomic JSON store backups)
├── recovery.py           # RecoveryEngine (hash-verified atomic restoration)
├── jobs.py               # JobLifecycleManager (cooperative job control)
├── incidents.py          # IncidentEngine (incident tracking & security triggers)
├── retention.py          # RetentionEngine (bounded pruning & cleanup)
├── configuration.py      # ConfigurationValidator (secret-safe validation)
├── store.py              # OperationsStore (thread-safe JSON persistence)
├── audit.py              # Structured [operations_audit] logging
└── orchestrator.py       # Central operations coordinator
```

---

## 3. Core Operational Rules & Security Invariants

1. **AI is Never the Authority**: Models cannot restore backups, transition lifecycle states, disable security controls, or elevate caller roles.
2. **Zero Shell Execution**: No `subprocess`, `os.system`, `eval`, `exec`, or `shell=True` anywhere in the operations layer.
3. **Multi-Tenant Scoping**: All metrics, events, jobs, incidents, and dashboard data are strictly partitioned by authenticated `tenant_id`.
4. **Secret Protection**: All credentials, tokens (`Bearer`, `sk-...`, `AKIA...`), and passwords are automatically redacted in audit logs, diagnostics, and event metadata.
5. **Fail-Closed Readiness**: If any critical subsystem or store integrity check fails, readiness is immediately set to `BLOCKED`.
6. **Bounded Cardinalities**: Metric names, labels, and storage limits are strictly bounded to prevent unbounded memory growth or denial of service.

---

## 4. API Endpoints Reference

| Method | Endpoint | Access Level | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/operations/status` | User / Operator | Retrieves current lifecycle status |
| `GET` | `/api/operations/lifecycle` | User / Operator | Alias for lifecycle status |
| `POST` | `/api/operations/lifecycle/drain` | Operator / Admin | Transitions system into `DRAINING` mode |
| `POST` | `/api/operations/lifecycle/recover` | Operator / Admin | Recovers system state back to `READY` |
| `GET` | `/api/operations/metrics` | User / Operator | Bounded operational metrics summary |
| `GET` | `/api/operations/events` | User / Operator | Structured operational events |
| `POST` | `/api/operations/diagnostics/run` | Operator / Admin | Runs non-destructive system diagnostics |
| `GET` | `/api/operations/diagnostics/{id}` | Operator / Admin | Retrieves diagnostic report |
| `GET` | `/api/operations/jobs` | User / Operator | Lists tenant-scoped jobs |
| `GET` | `/api/operations/jobs/{id}` | User / Operator | Retrieves specific job |
| `POST` | `/api/operations/jobs/{id}/cancel`| User / Operator | Cooperatively cancels ongoing job |
| `GET` | `/api/operations/incidents` | User / Operator | Lists operational incidents |
| `GET` | `/api/operations/incidents/{id}` | User / Operator | Retrieves specific incident |
| `POST` | `/api/operations/incidents/{id}/resolve`| Operator / Admin | Resolves an incident |
| `GET` | `/api/operations/backups` | Operator / Admin | Lists stored backup records |
| `POST` | `/api/operations/backups/create` | Operator / Admin | Creates atomic SHA-256 verified backup |
| `POST` | `/api/operations/recovery/restore` | Operator / Admin | Restores store from verified backup |
| `GET` | `/api/operations/configuration/status`| User / Operator | Safe configuration verification summary |
| `GET` | `/api/operations/dashboard` | User / Operator | Aggregated operational dashboard data |

---

## 5. State Machines

### Lifecycle State Machine
$$\text{STARTING} \longrightarrow \text{READY} \rightleftharpoons \text{DEGRADED} \longrightarrow \text{DRAINING} \longrightarrow \text{STOPPING} \longrightarrow \text{STOPPED}$$
$$(\text{Any State} \longrightarrow \text{FAILED} \longrightarrow \text{READY})$$

### Job Lifecycle State Machine
$$\text{QUEUED} \longrightarrow \text{RUNNING} \longrightarrow \text{COMPLETED} \ / \ \text{FAILED} \ / \ \text{CANCELLED}$$
