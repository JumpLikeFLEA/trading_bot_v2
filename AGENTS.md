## 📌 Project Overview

This repository contains a modular trading bot MVP.

Architecture is strictly layered:

Strategy → Signal → Risk → Order → Broker → Execution

Primary goal:
- Clean, extensible system
- One strategy = one file
- Easy to add new strategies and brokers
- Safe for real trading (with risk controls)

MVP scope:
- Single broker: Trading 212
- Basic strategies
- Simple risk management
- Local execution (desktop environment)

---

## 🧠 Core Principles

- Keep everything **simple and explicit**
- Do NOT overengineer
- Do NOT introduce frameworks unless explicitly requested
- Prefer readability over abstraction
- Each module must have **one clear responsibility**

---

## 🏗️ Architecture Rules (STRICT)

### 1. Strategy Layer
- Strategies MUST:
  - Inherit from `Strategy` base class
  - Implement `on_data(data)`
  - Return a `Signal`

- Strategies MUST NOT:
  - Call broker methods
  - Place orders
  - Access external APIs
  - Modify global state

---

### 2. Signal → Execution Flow

ALWAYS follow this pipeline:

Strategy → Signal → RiskManager → Order → Broker

NEVER bypass this flow.

---

### 3. Broker Layer
- Only broker adapters may:
  - Communicate with external APIs
  - Place orders
  - Fetch balances or positions

- Broker must implement:
  - `get_balance()`
  - `get_positions()`
  - `place_order(order)`

---

### 4. Risk Layer
- Converts `Signal` → `Order`
- Applies:
  - Position sizing
  - Basic safety checks

- Must NOT:
  - Call external APIs
  - Contain strategy logic

---

### 5. Engine Layer
- Orchestrates the system
- Responsibilities:
  - Fetch data
  - Run strategies
  - Pass signals to risk manager
  - Send orders to broker
  - Record metrics

- Must NOT:
  - Contain trading logic
  - Modify strategy behavior

---

### 6. Data Flow Constraints

- Data flows **top-down only**
- No circular dependencies
- No hidden side effects

---

## 📂 Project Structure Rules

- `core/` → interfaces and engine (no external dependencies)
- `strategies/` → one file per strategy
- `adapters/` → broker integrations only
- `services/` → supporting utilities (data, metrics, storage)
- `ui/` → visualization only (no trading logic)

---

## 🧩 Strategy Rules

- One strategy = one file
- File must contain exactly one class
- Class name must match file name (PascalCase)

Example:
- `rsi_strategy.py` → `RSIStrategy`

- Strategies must:
  - Be stateless OR explicitly manage state locally
  - Use only provided `data`

---

## 🔐 Security Rules

- API keys must NEVER be hardcoded
- Load secrets from local storage only
- Do NOT log secrets
- Do NOT expose credentials in output

---

## 🧪 Testing & Safety

- Default mode = safe / simulated
- Do NOT assume real trading unless explicitly enabled
- Avoid large position sizes in examples

---

## 🚫 Forbidden Actions

Agents MUST NOT:

- Introduce new architecture patterns
- Modify existing interfaces without instruction
- Add hidden dependencies between modules
- Mix responsibilities across layers
- Call broker from strategy
- Add async/multithreading unless requested
- Add external libraries without approval

---

## ✅ Allowed Improvements

Agents MAY:

- Improve readability
- Add type hints
- Add docstrings
- Add small helper functions (within the same module)
- Refactor ONLY if behavior remains unchanged

---

## 📤 Output Rules (CRITICAL)

When generating code:

- Output ONLY the requested file
- Do NOT include explanations
- Do NOT modify other files
- Follow existing structure exactly

---

## 🎯 Guiding Principle

When in doubt:

→ Choose the simplest solution that respects the architecture
