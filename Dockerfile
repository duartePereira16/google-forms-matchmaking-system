FROM python:3.10-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install dependencies using uv for lightning-fast builds
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy project files
COPY . .

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]