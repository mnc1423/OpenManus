# OpenManus (Fork)

A customized fork of [FoundationAgents/OpenManus](https://github.com/FoundationAgents/OpenManus) — an open-source framework for building general AI agents.

This fork adds a **Streamlit web frontend**, **RAG (Retrieval-Augmented Generation) tool**, **interactive todo/planning review**, and other quality-of-life improvements on top of the original OpenManus project.

---

## What's New in This Fork

| Feature | Description |
|---|---|
| **Streamlit Frontend** | A multi-page web UI with input, plan review, live execution, and results phases. Includes an agent execution graph visualization. |
| **RAG Tool** | A Retrieval-Augmented Generation pipeline that searches the web (or uses local documents), ranks results, and generates cited answers via the LLM. |
| **Interactive Todo / Plan Review** | The planning flow now presents generated steps to the user for review and modification before execution begins. |
| **Daytona Made Optional** | The Daytona sandbox integration is now opt-in, so the agent runs without a Daytona environment configured. |
| **Baidu Search Removed** | Baidu removed from the active search engine registry. Remaining engines: Google, Bing, DuckDuckGo. |
| **Dependency Fixes** | Resolved package version conflicts introduced by the above additions. |

---

## Installation

### Prerequisites

- Python 3.12+
- [conda](https://docs.conda.io/) or [uv](https://github.com/astral-sh/uv)

### Using conda

```bash
conda create -n open_manus python=3.12
conda activate open_manus
git clone https://github.com/mnc1423/OpenManus.git
cd OpenManus
pip install -r requirements.txt
```

### Using uv (Recommended)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/mnc1423/OpenManus.git
cd OpenManus
uv venv --python 3.12
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate   # On Windows
uv pip install -r requirements.txt
```

### Browser Automation (Optional)

```bash
playwright install
```

---

## Configuration

1. Copy the example config:

```bash
cp config/config.example.toml config/config.toml
```

2. Edit `config/config.toml` with your API key and preferred model:

```toml
[llm]
model = "claude-3-7-sonnet-20250219"
base_url = "https://api.anthropic.com/v1/"
api_key = "YOUR_API_KEY"
max_tokens = 8192
temperature = 0.0
```

Supported providers include **Anthropic**, **OpenAI**, **Azure OpenAI**, **AWS Bedrock**, **Ollama**, and **Jiekou.AI**. See `config/config.example.toml` for full examples.

---

## Usage

### CLI Mode

```bash
python main.py
```

You can specify the flow type:

```bash
python main.py --flow planning   # Interactive planning with todo review
python main.py --flow agent      # Direct agent execution
```

### Streamlit Web UI

Launch the web frontend:

```bash
# Linux / macOS
./run_streamlit.sh

# Windows
run_streamlit.bat
```

The Streamlit app provides four phases:
1. **Input** — Enter your prompt
2. **Review** — Inspect and edit the generated plan
3. **Executing** — Watch the agent run with a live execution graph
4. **Done** — View results

### MCP Tool Version

```bash
python run_mcp.py
```

### Multi-Agent Flow

```bash
python run_flow.py
```

To enable the Data Analysis agent, set in `config/config.toml`:

```toml
[runflow]
use_data_analysis_agent = true
```

---

## Project Structure

```
OpenManus/
├── main.py                  # CLI entry point
├── run_flow.py              # Multi-agent flow runner
├── run_mcp.py               # MCP tool version
├── run_streamlit.bat/.sh    # Streamlit launcher scripts
├── app/
│   ├── agent/               # Agent implementations
│   ├── flow/                # Flow orchestration (planning, etc.)
│   ├── frontend/streamlit/  # Streamlit web UI
│   ├── tool/                # Tools available to agents
│   │   ├── rag_tool.py      # RAG pipeline (new)
│   │   ├── web_search.py    # Web search tool
│   │   ├── search/          # Search engine backends
│   │   ├── browser_use_tool.py
│   │   └── ...
│   ├── config.py            # Configuration loading
│   └── prompt/              # Prompt templates
├── config/                  # Configuration files
├── tests/                   # Test suite
└── workspace/               # Agent workspace output
```

---

## Roadmap / TODO

- [ ] **Session persistence** — Save and resume agent sessions so users can pick up where they left off
- [ ] **RAG with local file support** — Allow the RAG tool to index local files (PDF, markdown, code) instead of only web search results
- [ ] **Streamlit auth & multi-user support** — Add basic authentication so the frontend can be safely exposed beyond localhost
- [ ] **Execution history dashboard** — Store past runs and let users browse/search previous agent outputs in the Streamlit UI
- [ ] **Streaming output in frontend** — Show real-time token-by-token LLM responses in the Streamlit execution phase
- [ ] **Cost tracking** — Display token usage and estimated API cost per run
- [ ] **Configurable tool selection** — Let users enable/disable specific tools (browser, RAG, search, etc.) per session from the UI
- [ ] **Docker Compose setup** — One-command deployment with Docker Compose bundling the app, browser automation, and optional sandbox
- [ ] **Test coverage** — Expand unit and integration tests, especially for the RAG tool and Streamlit frontend
- [ ] **Sync with upstream** — Periodically merge updates from FoundationAgents/OpenManus

---

## Original Project

This is a fork of **[FoundationAgents/OpenManus](https://github.com/FoundationAgents/OpenManus)** — an open-source framework for building general AI agents, created by the [MetaGPT](https://github.com/geekan/MetaGPT) team.

Original authors: Xinbin Liang, Jinyu Xiang, Zhaoyang Yu, Jiayi Zhang, Sirui Hong, and others.

> See also: [OpenManus-RL](https://github.com/OpenManus/OpenManus-RL) — reinforcement learning-based tuning for LLM agents.

---

## License

[MIT](LICENSE)
