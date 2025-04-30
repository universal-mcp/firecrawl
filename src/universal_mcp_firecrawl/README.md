
# Universal Mcp Firecrawl MCP Server

An MCP Server for the Universal Mcp Firecrawl API.

## 📋 Prerequisites

Before you begin, ensure you have met the following requirements:
* Python 3.11+ (Recommended)
* [uv](https://github.com/astral-sh/uv) installed globally (`pip install uv`)

## 🛠️ Setup Instructions

Follow these steps to get the development environment up and running:

### 1. Sync Project Dependencies
Navigate to the project root directory (where `pyproject.toml` is located).
```bash
uv sync
```
This command uses `uv` to install all dependencies listed in `pyproject.toml` into a virtual environment (`.venv`) located in the project root.

### 2. Activate the Virtual Environment
Activating the virtual environment ensures that you are using the project's specific dependencies and Python interpreter.
- On **Linux/macOS**:
```bash
source .venv/bin/activate
```
- On **Windows**:
```bash
.venv\\Scripts\\activate
```

### 3. Start the MCP Inspector
Use the MCP CLI to start the application in development mode.
```bash
mcp dev src/universal_mcp_firecrawl/mcp.py
```
The MCP inspector should now be running. Check the console output for the exact address and port.

## 🔌 Supported Integrations

- AgentR
- API Key (Coming Soon)
- OAuth (Coming Soon)

## 🛠️ Tool List

This is automatically generated from OpenAPI schema for the Universal Mcp Firecrawl API.


| Tool | Description |
|------|-------------|
| `scrape_url` | Scrapes a single URL using Firecrawl and returns the extracted data. |
| `search` | Performs a web search using Firecrawl's search capability. |
| `start_crawl` | Starts a crawl job for a given URL using Firecrawl. Returns the job ID immediately. |
| `check_crawl_status` | Checks the status of a previously initiated Firecrawl crawl job. |
| `cancel_crawl` | Cancels a currently running Firecrawl crawl job. |
| `start_batch_scrape` | Starts a batch scrape job for multiple URLs using Firecrawl. |
| `check_batch_scrape_status` | Checks the status of a previously initiated Firecrawl batch scrape job. |
| `start_extract` | Starts an extraction job for one or more URLs using Firecrawl. |
| `check_extract_status` | Checks the status of a previously initiated Firecrawl extraction job. |

## 📁 Project Structure

The generated project has a standard layout:
```
.
├── src/                  # Source code directory
│   └── universal_mcp_firecrawl/
│       ├── __init__.py
│       └── mcp.py        # Server is launched here
│       └── app.py        # Application tools are defined here
├── tests/                # Directory for project tests
├── .env                  # Environment variables (for local development)
├── pyproject.toml        # Project dependencies managed by uv
├── README.md             # This file
```

## 📝 License

This project is licensed under the MIT License.

---

_This project was generated using **MCP CLI** — Happy coding! 🚀_
