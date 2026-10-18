# The API image: gunicorn serving Django with the static files collected in. One image does all three
# processes on a server — the web process, the Celery worker and beat — each with its own command (docs/deploy.md).
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Requirements first: the layer is cached until they change, so a code-only build skips the install.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Collected at build time, not at boot: the files are the same on every server, and whitenoise serves them
# from gunicorn. The build needs no real settings, so it uses the development ones.
RUN python manage.py collectstatic --noinput

# Nothing here needs root.
RUN useradd --create-home --uid 10001 rackline && chown -R rackline:rackline /app
USER rackline

# What this image is, for the Console's Server screen: the deploy workflow passes the commit and the time it built
# it. Last, so a new commit rebuilds only this layer. A service's own environment variables would win over these.
ARG APP_VERSION=dev
ARG DEPLOYED_AT=
ENV APP_VERSION=$APP_VERSION DEPLOYED_AT=$DEPLOYED_AT

EXPOSE 8000
# Asks the API the same question the load balancer asks (apps/core/views.HealthView).
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD ["python", "-c", \
  "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health/', timeout=4).status == 200 else 1)"]
# Logs go to stdout, where App Runner and ECS pick them up. Migrations are not run here: a deploy runs them once
# (docs/deploy.md), not in every container that starts.
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", \
     "--access-logfile", "-", "--error-logfile", "-"]
