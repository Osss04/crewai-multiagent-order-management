# CrewAI Multi-Agent Order Management System

This project implements a **multi-agent AI system** for restaurant order management using **CrewAI** and **Large Language Models (LLMs)**. The system autonomously handles user orders expressed in natural language, validates them, and persists them into a database, following a modular and production-oriented architecture.

The project is designed as a **portfolio-ready example of agentic AI**, showcasing agent orchestration, LLM integration, and clean Python engineering practices.

---

## 🧠 System Architecture

The system follows a **multi-agent architecture** where each agent has a well-defined role and responsibility. Agents collaborate through structured tasks coordinated by a **Crew**, enabling separation of concerns and scalable workflows.

### High-level flow:
1. User submits an order via a Streamlit interface.
2. The order is processed by a set of specialized agents.
3. Agents communicate and reason using an LLM (Grok via LiteLLM).
4. Validated orders are stored in a database.
5. The system returns a structured confirmation or error response.

---

## 🤖 Agents and Roles

The system is composed of the following agents:

### 🧾 Order Intake Agent
- Interprets the user’s natural language input.
- Extracts structured order information (items, quantities, special requests).
- Handles ambiguous or incomplete requests via LLM reasoning.

### ✅ Order Validation Agent
- Validates business rules (menu availability, quantities, constraints).
- Ensures consistency and correctness of the order.
- Requests clarification if validation fails.

### 💾 Persistence Agent
- Handles database interactions.
- Stores validated orders in a relational database.
- Ensures transactional integrity and error handling.

Each agent is implemented as a **CrewAI Agent**, with its own:
- Role description
- Goal
- Backstory
- Tools (when applicable)

---

## 🧩 Tasks and Crew Orchestration

Tasks define **what needs to be done**, while agents define **who does it**.

Typical tasks include:
- Parsing and structuring the raw order.
- Validating order constraints.
- Persisting the order into the database.
- Generating a final response for the user.

These tasks are orchestrated by a **Crew**, which:
- Controls execution order.
- Manages shared context between agents.
- Enables collaborative reasoning across agents.

This design allows easy extension (e.g. adding a payment agent or recommendation agent).

---

## 🧠 LLM Integration (LiteLLM + Grok)

The system integrates **Grok** as the underlying LLM via **LiteLLM**, providing:
- A unified API interface for LLM calls.
- Easy model swapping if needed.
- Centralized configuration via environment variables.

LLM calls are used for:
- Natural language understanding.
- Reasoning and validation logic.
- Generating structured outputs from free-form input.

All LLM access is secured using environment variables and **never hardcoded**.


---

## 🚀 Installation & Setup

### 1. Create virtual environment
```bash
py -3.11 -m venv .venv
```

### 2. Activate virtual environment
```bash
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the project root and set your Groq API key:
```bash
GROQ_API_KEY="your_api_key_here"
```

### 5. Run the Streamlit application
```bash
streamlit run .\streamlit_app.py
```