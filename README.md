
![Python](https://img.shields.io/badge/Python-3.10-blue)
![LangChain](https://img.shields.io/badge/LangChain-LLM%20Framework-purple)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Orchestration-blueviolet)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend%20API-teal)
![Streamlit](https://img.shields.io/badge/Streamlit-App%20Framework-brightgreen)
![MLOps](https://img.shields.io/badge/MLOps-CI%2FCD%20Pipeline-yellow)
![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD-red)
![AWS](https://img.shields.io/badge/AWS-Cloud-orange)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)

Designed and deployed a configurable multi-agent LLM system enabling dynamic behavior selection and tool-based reasoning.

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


## Steps to run the program:

### 1. Create and clone the repository

```bash
git clone https://github.com/Joab-David-Johanan/Multi-AI-Agent
```

### 2. Create a conda environment after opening the repository

```bash
pip install -e .
```

```bash
pip show list
```

### 3. Check all dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file in the root directory and add your LangChain and other API credentials as follows:

```bash
OPENAI_API_KEY = "XXXXXXXXXXXXXXXXXXXXXX"
GROQ_API_KEY = "XXXXXXXXXXXXXXXXXXXXXX"
TAVILY_API_KEY = "XXXXXXXXXXXXXXXXXXXXXX"
LANGCHAIN_API_KEY = "XXXXXXXXXXXXXXXXXXXXXX"

```

```bash
# run the following command to start the Fastapi backend
fastapi dev multi_agent_app\backend\api.py
```

```bash
# Finally run the Streamlit app
streamlit run multi_agent_app\frontend\ui.py
```

## Deployment steps:

### 1. Log-in to AWS console.

### 2. Create IAM user for deployment

      # with specific access
      1. EC2 access: For setting up a virtual server.
      2. ECR access: Elastic container registry to save your docker image in aws.

      # Policy
      1. AmazonEC2ContainerRegistryFullAccess
      2. AmazonEC2FullAccess

      # Description: About the deployment
      1. Build Docker image of the source code.
      2. Push your Docker image to ECR.
      3. Launch your EC2.
      4. Pull your Docker image from ECR to EC2.
      5. Launch your Docker image in EC2.

### 3. Create ECR repo to store/save Docker image

```bash
# Save the URI
454041007932.dkr.ecr.us-east-1.amazonaws.com/multi_agent_app
```

### 4. Create a EC2 instance (Ubuntu)

      # Allow HTTPS and HTTP traffic.
      # Choose 8gb instance (t2.large).
      # Choose 30gb storage.

### 5. Launch the EC2 instance and install Docker in the EC2 instance

1. optional

```bash
sudo apt-get update -y
```

```bash
sudo apt-get upgrade
```

2. required

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
```

```bash
sudo sh get-docker.sh
```

```bash
sudo usermod -aG docker ubuntu
```

```bash
newgrp docker
```

### 6. Configure EC2 instance as a self-hosted runner

      settings-->actions-->runner-->new self hosted runner-->choose os-->then run command one by one

### 7. Setup Github secrets

- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION
- ECR_REPO_NAME
- LANGCHAIN_API_KEY
- TAVILY_API_KEY
- OPENAI_API_KEY

### 8. Ensure conditional integration and deployment with tags

1. Make sure all your changes (including YAML) are committed

```bash
git add .
git commit -m "Initial commit with CI/CD"
```

2. Push your code to GitHub

```bash
git push origin main
```

3. Create a version tag for deployment

```bash
git tag -a v1.0.0 -m "Initial release"
```

4. Push that tag to GitHub (triggers deployment)

```bash
git push origin v1.0.0
```

### 9. Features to include

- Advanced chunking techniques
- Hybrid search strategies
- Query Enhancement techniques
- Multimodal RAG techniques
- Guardrails
- Cache for faster response times
- Custom Javascript frontend with python backend (flask)