# CrewAI Project Setup — Steps Summary

## Environment

- **OS**: Ubuntu 24.04 (dev container)
- **Python**: 3.12.1
- **CrewAI version**: 1.14.4

---

## Step 1: Verify CrewAI Installation

Confirmed that the `crewai` Python package was already installed:

```bash
pip show crewai
# Name: crewai
# Version: 1.14.4
# Location: /home/codespace/.local/lib/python3.12/site-packages
```

However, the `crewai` CLI binary was **not on the PATH**:

```bash
which crewai
# crewai CLI not found
```

---

## Step 2: Fix the Missing CLI Binary

The CLI entry point existed in package metadata but the binary wasn't being placed correctly. Force-reinstalling crewai resolved this:

```bash
pip install --force-reinstall crewai
```

After reinstall, the binary was found at:

```
/home/codespace/.python/current/bin/crewai
```

This directory (`/home/codespace/.python/current/bin`) is already on the system `PATH`, but the shell's command hash cache was stale.

---

## Step 3: Refresh Shell Hash Cache

```bash
hash -r
```

After this, the `crewai` CLI was fully accessible:

```bash
which crewai
# /home/codespace/.python/current/bin/crewai

crewai --version
# crewai, version 1.14.4
```

---

## Step 4: Scaffold the Project Using CrewAI CLI

Ran the CrewAI project creation command from the workspace root:

```bash
cd /workspaces/Simplilearn_Agentic_AI
crewai create crew stock-picker-app
```

The CLI prompted interactively for:

1. **LLM Provider** — chose from a list (openai, anthropic, gemini, groq, ollama, etc.)
2. **Model name** — configured based on the selected provider

The project folder was created as `stock_picker_app/` (hyphens converted to underscores).

---

## Step 5: Verify the Scaffolded Structure

```bash
find stock_picker_app -type f | sort
```

Generated project layout:

```
stock_picker_app/
├── .env                                      ← API keys & environment config
├── .gitignore
├── AGENTS.md                                 ← Agent instructions for AI tools
├── README.md
├── knowledge/
│   └── user_preference.txt                   ← Knowledge base input
├── pyproject.toml                            ← Project metadata & dependencies
└── src/stock_picker_app/
    ├── __init__.py
    ├── crew.py                               ← Crew definition (agents + tasks)
    ├── main.py                               ← Entry point to run the crew
    ├── config/
    │   ├── agents.yaml                       ← Agent role/goal/backstory config
    │   └── tasks.yaml                        ← Task descriptions & outputs
    └── tools/
        ├── __init__.py
        └── custom_tool.py                    ← Placeholder for custom tools
```

---

## Next Steps

1. **Set your API key** in `stock_picker_app/.env`:
   ```
   OPENAI_API_KEY=sk-...
   ```

2. **Define your agents** in `src/stock_picker_app/config/agents.yaml`

3. **Define your tasks** in `src/stock_picker_app/config/tasks.yaml`

4. **Wire them together** in `src/stock_picker_app/crew.py`

5. **Run the crew**:
   ```bash
   cd stock_picker_app
   crewai run
   ```
