#!/bin/bash

# --- CONFIGURATION ---
PORT=8096
JELLYFIN_URL="http://localhost:$PORT"
AUTH_HEADER='X-Emby-Authorization: MediaBrowser Client="Pyams", Device="Server", DeviceId="pyams-init-script", Version="1.0.0"'

echo -e "\nStarting Jellyfin initialization...\n"

# --- BACKGROUND AUTOMATION ---
(
  echo -e "\nWaiting for Jellyfin API to become available...\n"

  # Wait for Jellyfin to be healthy (up to 5 minutes)
  MAX_RETRIES=60
  RETRY_COUNT=0
  until [ "$(curl -s -o /dev/null -w "%{http_code}" "$JELLYFIN_URL/System/Ping")" == "200" ] || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    sleep 5
    RETRY_COUNT=$((RETRY_COUNT + 1))
  done

  if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "\nError: Jellyfin API did not become available in time.\n"
    exit 1
  fi

  echo -e "\nJellyfin is up! Applying Startup Configuration...\n"

  sleep 5

  # 1. Trigger initialization and ensure a user exists in the database
  # This prevents "Sequence contains no elements" errors in subsequent calls
  echo -e "\nInitializing user database...\n"
  curl -s -X GET "$JELLYFIN_URL/Startup/User" -H "$AUTH_HEADER"

  sleep 1

  # 2. Set Startup Configuration
  # POST /Startup/Configuration
  echo -e "\nSetting server configuration...\n"
  curl -s -X POST "$JELLYFIN_URL/Startup/Configuration" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{"ServerName":"Jellyfin","UICulture":"en-GB","MetadataCountryCode":"GB","PreferredMetadataLanguage":"en"}'

  sleep 1

  # 3. Create/Update the Admin User
  # POST /Startup/User
  echo -e "\nCreating admin user...\n"
  curl -s -X POST "$JELLYFIN_URL/Startup/User" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{"Name":"admin","Password":"changeme"}'

  sleep 1

  # 4. Add Movies Library
  echo -e "\nAdding Movies library...\n"
  curl -s -X POST "$JELLYFIN_URL/Library/VirtualFolders?name=Movies&collectionType=movies&refreshLibrary=true" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{
      "LibraryOptions": {
        "EnableRealtimeMonitor": true,
        "SaveLocalMetadata": true,
        "PathInfos": [
          { "Path": "/data/movies" }
        ]
      }
    }'

  sleep 1

  # 5. Add TV Shows Library
  echo -e "\nAdding TV Shows library...\n"
  curl -s -X POST "$JELLYFIN_URL/Library/VirtualFolders?name=TV%20Shows&collectionType=tvshows&refreshLibrary=true" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{
      "LibraryOptions": {
        "EnableRealtimeMonitor": true,
        "SaveLocalMetadata": true,
        "PathInfos": [
          { "Path": "/data/tvshows" }
        ]
      }
    }'

  sleep 1

  # 6. Complete Startup Wizard
  echo -e "\nCompleting startup wizard...\n"
  curl -s -X POST "$JELLYFIN_URL/Startup/Complete" \
    -H "$AUTH_HEADER" \
    -d "{}"

  sleep 1

  echo -e "\nJellyfin Startup Configuration Complete!\n"
) &
