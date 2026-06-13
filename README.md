# geoChat-v2-core

A lightweight, hard-wired, and dependency-free core engine for geo-intelligence platforms. 🗺️⚙️

---

## 🛡️ Badges

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

---

## 📖 Overview

**geoChat-v2-core** is the minimal, self-contained kernel of a Geo Intelligence platform. It provides the foundational mechanisms—error handling, data models, plugin contracts, service registration, inversion-of-control container, pipeline orchestration, and event management—without any external dependencies. Designed to be embedded into larger systems or used as a standalone component, the core enforces strict decoupling and stability.

---

## 🧠 Core Philosophy

| # | Principle | Description |
|---|-----------|-------------|
| 1 | 🪶 **Small** | Minimal surface area; only essential abstractions. |
| 2 | 🔩 **Hard** | Strong guards against misuse; fail fast, fail loud. |
| 3 | 🪨 **Stable** | Backward-compatible interfaces; semantic versioning. |
| 4 | 🧩 **Independent** | No third-party packages; pure Python stdlib. |
| 5 | 🔒 **Dependency‑free** | Zero runtime dependencies; install and run instantly. |

---

## 🏗️ Architecture Diagram

```
┌──────────────────────────────────────────────┐
│                 geoChat-v2-core               │
│                                               │
│   ┌─────────┐  ┌──────────┐  ┌────────────┐ │
│   │ Errors  │  │  Models  │  │  Contracts  │ │
│   └─────────┘  └──────────┘  └────────────┘ │
│        │             │              │          │
│        ▼             ▼              ▼          │
│   ┌────────────────────────────────────────┐  │
│   │           Registries                   │  │
│   └────────────────────────────────────────┘  │
│        │             │              │          │
│        ▼             ▼              ▼          │
│   ┌─────────┐  ┌──────────┐  ┌────────────┐ │
│   │Container│  │ Pipeline │  │   Events   │ │
│   └─────────┘  └──────────┘  └────────────┘ │
└──────────────────────────────────────────────┘
```

---

## 📦 What's Inside

| Module       | Purpose |
|--------------|---------|
| **Errors**   | Custom exception hierarchy with context enrichment. |
| **Models**   | Base data classes for geo‑entities (Point, Polygon, Feature, etc.). |
| **Contracts** | Abstract interfaces for plugins, services, and pipelines. |
| **Registries** | Thread‑safe registries for plugins and services. |
| **Container** | Simple dependency injection container (no magic, just dict + factory). |
| **Pipeline** | Sequenced execution chain with hooks and error propagation. |
| **Events** | Synchronous event bus for decoupled communication. |

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/geoChat-v2-core.git

# 2. (Optional) Create a virtual environment
python3 -m venv venv && source venv/bin/activate

# 3. Install the core (no dependencies needed)
cd geoChat-v2-core
pip install .
```

Then test it:

```python
from geochat_core import Container, Events
c = Container()
c.register('greeting', lambda: "geoChat core is alive!")
print(c.resolve('greeting')())
```

---

## 📁 Project Structure

```
geoChat-v2-core/
├── geochat_core/
│   ├── __init__.py
│   ├── errors.py
│   ├── models.py
│   ├── contracts.py
│   ├── registries.py
│   ├── container.py
│   ├── pipeline.py
│   └── events.py
├── tests/
│   ├── test_errors.py
│   ├── test_models.py
│   ├── test_contracts.py
│   ├── test_registries.py
│   ├── test_container.py
│   ├── test_pipeline.py
│   └── test_events.py
├── examples/
│   └── basic_usage.py
├── LICENSE
└── README.md
```

---

## 📐 Design Rules

The Core **must not**:

1. Depend on any third‑party package (not even `requests`).
2. Import from `geochat_plugins` or any external module.
3. Use mutable global state (singletons are allowed only via Container).
4. Perform I/O (network, disk) inside core modules.
5. Raise generic `Exception`—always use custom `CoreError` descendants.
6. Assume a specific concurrency model (threading, asyncio, etc.).
7. Leak implementation details into public contracts.
8. Break backward compatibility without a major version bump.

---

## 🔌 Plugin Types

These plugin interfaces are defined in `contracts.py` and can be implemented outside the core:

| Plugin Type      | Interface         | Purpose |
|------------------|-------------------|---------|
| **DataSource**   | `DataSourcePlugin` | Connect to external geodata providers. |
| **Analyzer**     | `AnalyzerPlugin`  | Perform spatial analysis or transformation. |
| **Formatter**    | `FormatterPlugin` | Serialize output (GeoJSON, CSV, etc.). |
| **Validator**    | `ValidatorPlugin` | Validate geo‑features against a schema. |
| **Dispatcher**   | `DispatcherPlugin`| Route events to external message queues. |
| **Cache**        | `CachePlugin`     | Store and retrieve intermediate results. |
| **Hook**         | `HookPlugin`      | Inject custom behavior into pipeline stages. |

---

## 🗺️ Roadmap

1. ✅ Core exception hierarchy and error context
2. ✅ Base geo‑models (Point, LineString, Polygon)
3. ✅ Plugin and service contract definitions
4. ✅ Thread‑safe registries
5. ✅ Simple dependency injection container
6. ✅ Pipeline orchestrator with hooks
7. ✅ Synchronous event bus
8. ⬜ Async pipeline support (optional)
9. ⬜ Comprehensive test suite (>95% coverage)
10. ⬜ Official plugin examples and documentation

---

## ⚖️ License

This project is licensed under the [MIT License](LICENSE).  
You are free to use, modify, and distribute it as long as the original copyright notice is included.