ARG BUILD_FROM
FROM ${BUILD_FROM}

# Which repo/ref to install. Override these build args to pin a tag/commit.
ARG VN_REPO=https://github.com/jscarrott/Vinted-Notifications
ARG VN_REF=main

# git is needed to fetch the app; the add-on build context only contains this
# folder, so the application code is cloned at build time.
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN git clone --depth 1 --branch "${VN_REF}" "${VN_REPO}" /app \
 && pip install --no-cache-dir -r requirements.txt

# Persist the database and logs on the add-on's /data mount
ENV VN_DATA_DIR=/data \
    VN_LOG_DIR=/data/logs \
    PYTHONUNBUFFERED=1

LABEL \
  io.hass.name="Vinted Notifications" \
  io.hass.type="addon"

CMD ["python", "vinted_notifications.py"]
