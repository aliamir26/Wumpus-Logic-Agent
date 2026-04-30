# 🧠 Wumpus Logic Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.x-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen?style=for-the-badge)

**A Knowledge-Based Agent that navigates the Wumpus World using Propositional Logic and Resolution Refutation — built from scratch, no SAT solvers.**

[🚀 Live Demo](#deployment) · [📖 Docs](#modules) · [🛠 Run Locally](#run-locally)

</div>

---

## 📸 Screenshots

| Game Board | AI Solving | Game Over Reveal |
|:---:|:---:|:---:|
| ![Screenshot 1](images/screenshot1.png) | ![Screenshot 2](images/screenshot2.png) | ![Screenshot 3](images/screenshot3.png) |

---

## 🎯 What Is This?

The **Wumpus World** is a classic AI problem from Russell & Norvig's *Artificial Intelligence: A Modern Approach*. A cave-exploring agent must navigate a grid containing a deadly Wumpus and bottomless Pits — armed with nothing but its senses and the power of **logical inference**.

This project implements a full **Knowledge-Based Agent (KBA)** that:

- Maintains a **Propositional Logic Knowledge Base (KB)**
- Uses **Resolution Refutation** (a complete inference algorithm) to prove cells are safe *before* moving into them
- Converts percept-based biconditional rules into **Conjunctive Normal Form (CNF)**
- Counts every resolution step performed — making the inference process transparent and educational

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔍 **Real Resolution Refutation** | Implemented from scratch — no external SAT solvers |
| 📐 **CNF Conversion** | Biconditional rules properly expanded into CNF clause sets |
| 🧩 **Living Knowledge Base** | `tell()` and `ask()` interface that grows as the agent explores |
| 🎮 **Manual + AI Modes** | Play yourself or watch the AI agent reason through the grid |
| 📊 **Live Metrics** | Inference steps, clause count, safe cells, visited cells — all real-time |
| 🗺 **Grid Visualization** | Color-coded cells: current, visited, proven-safe, unknown |
| 💥 **Game Over Reveal** | Hidden world (Wumpus, Pits, Gold) revealed on death |
| 📱 **Responsive UI** | Works on desktop and mobile |
| ⚡ **Dark Mode Design** | Professional dark-themed UI built with Tailwind CSS |

---

## 🧠 The Logic (How It Works)

### Propositional Variables

```
P_{r}_{c}    →  Pit at cell (row r, col c)
W_{r}_{c}    →  Wumpus at cell (row r, col c)
B_{r}_{c}    →  Breeze perceived at (r, c)
S_{r}_{c}    →  Stench perceived at (r, c)
V_{r}_{c}    →  Cell (r, c) has been visited
```

### Biconditional Rules (converted to CNF)

```
B_{r}_{c}  ↔  (P_{r-1,c} ∨ P_{r+1,c} ∨ P_{r,c-1} ∨ P_{r,c+1})
S_{r}_{c}  ↔  (W_{r-1,c} ∨ W_{r+1,c} ∨ W_{r,c-1} ∨ W_{r,c+1})
```

### Resolution Refutation

To prove cell (x,y) is safe, the agent asks the KB:

```
KB ⊨ ¬P_{x}_{y}  AND  KB ⊨ ¬W_{x}_{y}
```

This is done by negating the query, adding it to the KB, and attempting to derive the **empty clause (⊥)**. If derived → contradiction → query is **entailed**.

---

## 📁 Project Structure

```
wumpus-logic-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── logic/
│   │   ├── __init__.py
│   │   ├── resolution.py       # CNF conversion + Resolution Refutation algorithm
│   │   ├── knowledge_base.py   # KB class with tell() and ask()
│   │   └── agent.py            # WumpusWorld (env) + WumpusAgent (KBA)
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py              # All REST API endpoints
│   └── templates/
│       └── index.html          # Main frontend (Tailwind + Vanilla JS)
├── static/
│   └── css/
│       └── styles.css          # Custom animations, cell styles, dark theme
├── README.md
├── requirements.txt
├── vercel.json
└── .gitignore
```

### Module Descriptions

| File | Purpose |
|---|---|
| `resolution.py` | Core logic engine. CNF conversion, resolution rule, refutation loop, tautology checks |
| `knowledge_base.py` | KB class. `tell_percepts()` adds facts; `ask_safe()` queries via resolution |
| `agent.py` | `WumpusWorld` generates the hidden grid. `WumpusAgent` navigates using KB |
| `api.py` | REST endpoints: `/new_game`, `/move`, `/ai_step`, `/ai_solve`, `/reveal` |
| `main.py` | FastAPI app setup, static files, templates, CORS middleware |
| `index.html` | Full frontend: grid rendering, percept display, metrics dashboard, game over overlay |
| `styles.css` | Dark theme variables, animated cell states, glassmorphism panels |

---

## 🛠 Run Locally

### Prerequisites

- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/aliamir26/wumpus-logic-agent.git
cd wumpus-logic-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn app.main:app --reload --port 8000

# 5. Open in browser
# → http://localhost:8000
```

---

## 🚀 Deployment on Vercel

Vercel supports Python via Serverless Functions. Here's how to deploy:

### Step 1 — Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2 — Login

```bash
vercel login
```

### Step 3 — Deploy

```bash
cd wumpus-logic-agent
vercel
```

Follow the prompts:
- **Set up and deploy?** → Yes
- **Which scope?** → Your account
- **Link to existing project?** → No (create new)
- **Project name?** → wumpus-logic-agent
- **In which directory is your code?** → ./

### Step 4 — Set Python version (optional)

Create `.python-version` file:
```
3.11
```

### Step 5 — Redeploy for production

```bash
vercel --prod
```

Your app will be live at `https://wumpus-logic-agent-zeta.vercel.app/` 🎉

> **Note:** The in-memory game state resets between serverless function invocations on Vercel. For persistent sessions, add a Redis backend (e.g., Upstash Redis) and store game state there.

---

## 🎮 How to Play

1. **Select grid size** (4×4 Easy → 8×8 Hard)
2. **Set pit density** (5% to 25%)
3. Press **⚡ Start New Game**
4. In **Manual Mode**: Use arrow keys or the D-Pad, or **click adjacent cells** to move
5. In **AI Mode**: Press **▶ AI Step** for one inference step, or **⚡ Auto-Solve** to watch the agent reason through the grid
6. Watch the **inference steps counter** climb as the agent proves cells safe via Resolution Refutation
7. If the agent dies, the **world is revealed** — see exactly where the Wumpus and Pits were hiding

---

## 🔬 Challenges & Learning Outcomes

### Challenge 1: CNF Conversion of Biconditionals

Biconditionals `B ↔ (P₁ ∨ P₂ ∨ … ∨ Pₙ)` must be split into:
- One forward clause: `{¬B, P₁, P₂, …, Pₙ}`
- N backward clauses: `{¬Pᵢ, B}` for each i

Getting this right — especially handling tautologies and duplicates — was the trickiest part.

### Challenge 2: Resolution Loop Termination

The resolution loop can generate exponentially many clauses. A safety cap (2000 clauses) was added to prevent infinite loops while keeping the engine educational and debuggable.

### Challenge 3: Agent Navigation Without Global Knowledge

The agent must decide where to move using only what it has sensed so far. BFS-based pathfinding through proven-safe cells was layered on top of the KB to handle backtracking.

### Learning Outcomes

- Deep understanding of Resolution Refutation as a complete inference procedure
- CNF conversion for compound propositional sentences
- Designing a Knowledge Base with `tell/ask` abstraction
- Building a reactive, KB-driven agent architecture
- FastAPI + Jinja2 + Tailwind for full-stack Python web apps

---

## 🛠 Technologies & Dependencies

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Core language |
| FastAPI | 0.111 | Backend REST API |
| Uvicorn | 0.29 | ASGI server |
| Jinja2 | 3.1.4 | HTML templating |
| Pydantic | 2.7 | Request/response validation |
| Tailwind CSS | CDN | UI styling |
| Vanilla JS | — | Frontend interactivity |

---

## 👨‍💻 Author

**Muhammad Ali**
- Github: [@aliamir26](https://github.com/aliamir26)
- Gmail: maliamir089@gmail.com
- University: FAST-NUCES
- Course: Artificial Intelligence

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">
Built with 🧠 Logic · 🐍 Python · ⚡ FastAPI
</div>
