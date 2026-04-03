#!/bin/bash

# --- CONFIGURATION ---
CONFIG_FILE="/config/config.xml"
API_KEY=${API_KEY:-"pyams-secret-key-123"}
PORT=8989

echo "Starting Sonarr initialization..."

# --- 2. BACKGROUND AUTOMATION ---
(
  echo "Waiting for config.xml to be created..."
  while [ ! -f "$CONFIG_FILE" ]; do sleep 2; done

  echo "Setting API Key in config.xml..."
  if grep -q "<ApiKey>.*</ApiKey>" "$CONFIG_FILE"; then
    sed -i "s|<ApiKey>.*</ApiKey>|<ApiKey>$API_KEY</ApiKey>|" "$CONFIG_FILE"
  else
    # If the file is just being created, it might not have the tag yet if it's empty
    # or it might have just the root tag. Sonarr usually populates it.
    # But let's be safe and wait a bit more if it's missing.
    sleep 5
    sed -i "s|<ApiKey>.*</ApiKey>|<ApiKey>$API_KEY</ApiKey>|" "$CONFIG_FILE"
  fi

  echo "Waiting for Sonarr API to become available..."

  # Wait for Sonarr to be healthy (up to 2 minutes)
  MAX_RETRIES=24
  RETRY_COUNT=0
  until [ "$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/ping")" == "200" ] || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    sleep 5
    RETRY_COUNT=$((RETRY_COUNT + 1))
  done

  if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Error: Sonarr API did not become available in time."
    exit 1
  fi

  echo "Sonarr is up! Applying Zero-Config..."

  sleep 5

  # A. Setup Root Folder (/data/tv)
  curl -s -X POST "http://localhost:$PORT/api/v3/rootfolder?apikey=$API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"path": "/data/tvshows"}'

  sleep 1

  # B. Setup qBittorrent Download Client
  QBIT_HOST=${QBITTORRENT_HOST:-"qbittorrent"}
  curl -s -X POST "http://localhost:$PORT/api/v3/downloadclient?apikey=$API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
            "enable": true,
            "name": "qBittorrent (PYAMS)",
            "implementation": "Qbittorrent",
            "configContract": "QbittorrentSettings",
            "fields": [
                {"name": "host", "value": "'"$QBIT_HOST"'"},
                {"name": "port", "value": 8081},
                {"name": "username", "value": "admin"},
                {"name": "password", "value": "changeme"}
            ]
        }'

  sleep 1

  # C. Finalize Host Config: Enable Forms Auth + Set admin/changeme
  # We fetch current config to preserve other settings
  CURRENT_HOST_CONFIG=$(curl -s "http://localhost:$PORT/api/v3/config/host?apikey=$API_KEY")

  sleep 1

  # Replace values carefully, handling both string values and nulls
  NEW_HOST_CONFIG=$(echo "$CURRENT_HOST_CONFIG" |
    sed -E 's/"authenticationMethod": *(null|"[^"]*")/"authenticationMethod":"forms"/' |
    sed -E 's/"authenticationRequired": *(null|"[^"]*")/"authenticationRequired":"disabledForLocalAddresses"/' |
    sed -E 's/"username": *(null|"[^"]*")/"username":"admin"/' |
    sed -E 's/"password": *(null|"[^"]*")/"password":"changeme"/' |
    sed -E 's/"passwordConfirmation": *(null|"[^"]*")/"passwordConfirmation":"changeme"/')

  curl -s -X PUT "http://localhost:$PORT/api/v3/config/host/1?apikey=$API_KEY" \
    -H "Content-Type: application/json" \
    -d "$NEW_HOST_CONFIG"

  sleep 1

  echo "Sonarr Zero-Config Complete!"
) &
