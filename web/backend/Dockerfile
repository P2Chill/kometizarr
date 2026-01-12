FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and fonts
RUN apt-get update && apt-get install -y \
    gcc \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend
COPY web/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project to /app/kometizarr (includes src/, assets/, etc.)
COPY . /app/kometizarr

# Copy backend code to /app/backend (for uvicorn to find backend.main:app)
COPY web/backend /app/backend

# Set Python path to include kometizarr project
ENV PYTHONPATH=/app/kometizarr:$PYTHONPATH

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
