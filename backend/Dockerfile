FROM python:3.10-slim-bookworm

LABEL maintainer="https://johnny-coral-dev.vercel.app/"
ENV PYTHONUNBUFFERED=1
ARG DEV=false
ENV DEV=${DEV}

# System-level build deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      poppler-utils \
      qpdf \
      libxml2-dev \
      libxslt1-dev \
      libjpeg-dev \
      zlib1g-dev \
      libffi-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements.dev.txt /tmp/

# 1) Install CPU-only torch wheels from the official PyTorch index  
# 2) Then install everything else from your requirements.txt  
RUN python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install \
      torch torchvision torchaudio \
      --index-url https://download.pytorch.org/whl/cpu && \
    /venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ] ; then \
      /venv/bin/pip install --no-cache-dir -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp/*

# Copy your code, create a non-root user, etc.
COPY ./app /app
RUN adduser --disabled-password --no-create-home django-user \
 && mkdir -p /vol/web/static \
 && chown -R django-user:django-user /vol \
 && chmod -R 755 /vol

ENV PATH="/venv/bin:$PATH"
USER django-user

CMD ["gunicorn", "app.wsgi:application", "--bind", "0.0.0.0:8000"]