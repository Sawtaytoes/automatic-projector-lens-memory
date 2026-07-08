FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/Sawtaytoes/automatic-projector-lens-memory"

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Dependency layer first so source edits don't bust the pip cache.
COPY pyproject.toml README.md ./
COPY lens_memory/ ./lens_memory/
RUN pip install --no-cache-dir .

# Run as a non-root user.
RUN useradd --system --create-home appuser
USER appuser

CMD ["automatic-projector-lens-memory"]
