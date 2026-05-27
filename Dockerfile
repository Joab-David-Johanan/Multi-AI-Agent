# Parent image
FROM python:3.11-slim

# Essential environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Work directory inside the docker container
WORKDIR /multi_agent_app

# Installing system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies before copying app code so Docker can cache this layer.
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.5.1+cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copying ur all contents from local to app
COPY . .

# Install the local package without reinstalling dependencies.
RUN pip install --no-cache-dir --no-deps -e .

# Used PORTS
EXPOSE 8000
EXPOSE 8501

# Run the backend by default. Docker Compose can override this per service.
CMD ["uvicorn", "multi_agent_app.backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
