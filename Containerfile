FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY pluxee_mcp_server.py /app/

# Runtime envs expected:
# - PLUXEE_TOKEN (required)
# - PLUXEE_BASE_URL (optional)
# - PLUXEE_APPLICATION_ID (optional)
# - MCP_TRANSPORT (stdio|sse) default stdio

ENTRYPOINT ["python", "-u", "/app/pluxee_mcp_server.py"] 