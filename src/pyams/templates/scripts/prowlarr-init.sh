#!/bin/bash

# --- CONFIGURATION ---
CONFIG_FILE="/config/config.xml"
API_KEY=${API_KEY:-"pyams-secret-key-123"}
PORT=9696

echo "Starting Prowlarr initialization..."

# --- 2. BACKGROUND AUTOMATION ---
(
  echo "Waiting for config.xml to be created..."
  while [ ! -f "$CONFIG_FILE" ]; do sleep 2; done

  echo "Setting API Key in config.xml..."
  if grep -q "<ApiKey>.*</ApiKey>" "$CONFIG_FILE"; then
    sed -i "s|<ApiKey>.*</ApiKey>|<ApiKey>$API_KEY</ApiKey>|" "$CONFIG_FILE"
  else
    # Give it a moment if file was just touched
    sleep 5
    sed -i "s|<ApiKey>.*</ApiKey>|<ApiKey>$API_KEY</ApiKey>|" "$CONFIG_FILE"
  fi

  echo "Waiting for Prowlarr API to become available..."

  # Wait for Prowlarr to be healthy (up to 2 minutes)
  MAX_RETRIES=24
  RETRY_COUNT=0
  until [ "$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/ping")" == "200" ] || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    sleep 5
    RETRY_COUNT=$((RETRY_COUNT + 1))
  done

  if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Error: Prowlarr API did not become available in time."
    exit 1
  fi

  echo "Prowlarr is up! Applying Zero-Config..."

  sleep 5

  # A. Setup FlareSolverr (Indexer Proxy)
  # 1. Create 'fs' tag and extract its ID (robust parsing without jq)
  RESPONSE=$(curl -s -X POST "http://localhost:$PORT/api/v1/tag?apikey=$API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"label": "fs"}')

  sleep 1

  TAG_ID=$(echo "$RESPONSE" | tr -d ' \n\r' | grep -o '"id":[0-9]*' | cut -d: -f2)

  if [ -z "$TAG_ID" ]; then
    echo "Warning: Could not extract Tag ID from response. Falling back to ID 1."
    TAG_ID=1
  fi

  # B. Setup qBittorrent Download Client
  QBIT_HOST=${QBITTORRENT_HOST:-"qbittorrent"}
  curl -s -X POST "http://localhost:$PORT/api/v1/downloadclient?apikey=$API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
            "enable": true,
            "name": "qBittorrent (PYAMS)",
            "implementation": "QBittorrent",
            "configContract": "QBittorrentSettings",
            "protocol": "torrent",
            "priority": 1,
            "categories": [],
            "fields": [
                {"name": "host", "value": "'"$QBIT_HOST"'"},
                {"name": "port", "value": 8081},
                {"name": "useSsl", "value": false},
                {"name": "username", "value": "admin"},
                {"name": "password", "value": "changeme"},
                {"name": "category", "value": "prowlarr"},
                {"name": "initialState", "value": 0},
                {"name": "sequentialOrder", "value": false},
                {"name": "firstAndLast", "value": false},
                {"name": "contentLayout", "value": 0}
            ]
        }'

  sleep 1

  # C. Link Sonarr
  PROWL_HOST=${PROWLARR_HOST:-"prowlarr"}
  if [ -n "$SONARR_API_KEY" ]; then
    curl -s -X POST "http://localhost:$PORT/api/v1/applications?apikey=$API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
                "name": "Sonarr (PYAMS)",
                "implementation": "Sonarr",
                "configContract": "SonarrSettings",
                "syncLevel": "addOnly",
                "fields": [
                    {"name": "prowlarrUrl", "value": "http://'"$PROWL_HOST"':9696"},
                    {"name": "baseUrl", "value": "http://sonarr:8989"},
                    {"name": "apiKey", "value": "'"$SONARR_API_KEY"'"}
                ]
            }'
    sleep 1
  fi

  # D. Link Radarr
  if [ -n "$RADARR_API_KEY" ]; then
    curl -s -X POST "http://localhost:$PORT/api/v1/applications?apikey=$API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
                "name": "Radarr (PYAMS)",
                "implementation": "Radarr",
                "configContract": "RadarrSettings",
                "syncLevel": "addOnly",
                "fields": [
                    {"name": "prowlarrUrl", "value": "http://'"$PROWL_HOST"':9696"},
                    {"name": "baseUrl", "value": "http://radarr:7878"},
                    {"name": "apiKey", "value": "'"$RADARR_API_KEY"'"}
                ]
            }'
    sleep 1
  fi

  # E. Finalize Host Config: Enable Forms Auth + Set admin/changeme
  CURRENT_HOST_CONFIG=$(curl -s "http://localhost:$PORT/api/v1/config/host?apikey=$API_KEY")

  sleep 1

  NEW_HOST_CONFIG=$(echo "$CURRENT_HOST_CONFIG" |
    sed -E 's/"authenticationMethod": *(null|"[^"]*")/"authenticationMethod":"forms"/' |
    sed -E 's/"authenticationRequired": *(null|"[^"]*")/"authenticationRequired":"disabledForLocalAddresses"/' |
    sed -E 's/"username": *(null|"[^"]*")/"username":"admin"/' |
    sed -E 's/"password": *(null|"[^"]*")/"password":"changeme"/' |
    sed -E 's/"passwordConfirmation": *(null|"[^"]*")/"passwordConfirmation":"changeme"/')

  curl -s -X PUT "http://localhost:$PORT/api/v1/config/host/1?apikey=$API_KEY" \
    -H "Content-Type: application/json" \
    -d "$NEW_HOST_CONFIG"

  sleep 1

  # Wait for FlareSolverr to be up (up to 2 minutes)
  RETRY_COUNT=0
  until [ "$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8191")" == "200" ] || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    sleep 5
    RETRY_COUNT=$((RETRY_COUNT + 1))
  done

  echo "Using 'fs' tag with ID: $TAG_ID"
  curl -s -X POST "http://localhost:$PORT/api/v1/indexerproxy?apikey=$API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
            "name": "FlareSolverr (PYAMS)",
            "implementation": "FlareSolverr",
            "configContract": "FlareSolverrSettings",
            "tags": ['"$TAG_ID"'],
            "fields": [
                {"name": "host", "value": "http://flaresolverr:8191"}
            ]
        }'

  echo "Prowlarr Zero-Config Complete!"
) &
