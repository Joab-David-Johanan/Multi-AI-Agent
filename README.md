### Multi-Agent Application

### Built using the following techstack:

- langchain
- langgraph
- FastAPI
- Streamlit
- Docker
- SonarQube
- Jenkins
- AWS
    - ECR
    - Fargate
- groq models
- openai models
- tavily search

### Project Structure:

```
AI_agent_app
├── .streamlit
│   └── config.toml
├── assets
│   └── styles.css
├── logs
│   └── log_2026-02-10.log
├── multi_agent_app
│   ├── backend
│   │   ├── __init__.py
│   │   └── api.py
│   ├── common
│   │   ├── __init__.py
│   │   ├── custom_exception.py
│   │   └── logger.py
│   ├── config
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── core
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── frontend
│   │   ├── __init__.py
│   │   └── ui.py
│   ├── __init__.py
│   └── main.py
├── scripts
│   └── generate_tree.sh
├── .env
├── .gitignore
├── AI_agent_app.code-workspace
├── README.md
├── pyproject.toml
└── requirements.txt
```