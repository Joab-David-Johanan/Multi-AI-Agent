# Parent image
FROM python:3.10-slim

# Essential environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Work directory inside the docker container
WORKDIR /multi_agent_app

# Installing system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copying ur all contents from local to app
COPY . .

# Run pyproject.toml
RUN pip install --no-cache-dir -e .

# Used PORTS
EXPOSE 8000
EXPOSE 8501

# Run the app 
CMD ["python", "multi_agent_app/main.py"]