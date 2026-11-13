FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/Sawtaytoes/automatic-projector-lens-memory"

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Dependency layer first, so a source edit does not reinstall every dependency.
# It reads the runtime dependencies and the build backend from pyproject.toml,
# so this layer changes only when pyproject.toml changes.
COPY pyproject.toml ./
RUN python -c "import tomllib; project = tomllib.load(open('pyproject.toml', 'rb')); print('\n'.join(project['project']['dependencies'] + project['build-system']['requires']))" > /tmp/requirements.txt \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Source layer. The dependencies and setuptools are already installed above,
# so this step installs only the package itself and needs no download.
COPY README.md ./
COPY lens_memory/ ./lens_memory/
RUN pip install --no-cache-dir --no-deps --no-build-isolation .

# Run as a non-root user.
RUN useradd --system --create-home appuser
USER appuser

CMD ["automatic-projector-lens-memory"]
