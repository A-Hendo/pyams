#!/bin/bash

# --- CONFIGURATION ---
CONFIG_FILE="/config/config/config.yaml"
API_KEY=${BAZARR_API_KEY:-"pyams-bazarr-secret-123"}

echo "Starting Bazarr initialization..."

# --- 2. BACKGROUND AUTOMATION ---
(
  echo "Waiting for config.yaml to be created at $CONFIG_FILE..."
  # Wait up to 1 minute for Bazarr to generate the initial config
  MAX_WAIT=30
  COUNT=0
  while [ ! -f "$CONFIG_FILE" ] && [ $COUNT -lt $MAX_WAIT ]; do 
    sleep 2
    COUNT=$((COUNT + 1))
  done

  if [ ! -f "$CONFIG_FILE" ]; then
    echo "Config file not found after waiting. Creating directory and basic structure..."
    mkdir -p "$(dirname "$CONFIG_FILE")"
    # We'll let Bazarr create it if it hasn't yet, but if we are here, something is slow.
    # We skip direct modification if it doesn't exist to avoid corrupting a half-written file.
    exit 0
  fi

  echo "Applying direct configuration to $CONFIG_FILE..."

  # 1. Update Bazarr's own API Key
  sed -i "/^auth:/,/^[a-z]/ s|apikey:.*|apikey: $API_KEY|" "$CONFIG_FILE"

  # 2. Update Sonarr Settings
  if [ -n "$SONARR_API_KEY" ]; then
    sed -i "/^sonarr:/,/^[a-z]/ s|apikey:.*|apikey: $SONARR_API_KEY|" "$CONFIG_FILE"
    sed -i "/^sonarr:/,/^[a-z]/ s|ip:.*|ip: sonarr|" "$CONFIG_FILE"
  fi

  # 3. Update Radarr Settings
  if [ -n "$RADARR_API_KEY" ]; then
    sed -i "/^radarr:/,/^[a-z]/ s|apikey:.*|apikey: $RADARR_API_KEY|" "$CONFIG_FILE"
    sed -i "/^radarr:/,/^[a-z]/ s|ip:.*|ip: radarr|" "$CONFIG_FILE"
  fi

  # 4. Ensure Sonarr/Radarr are enabled in general settings
  sed -i "/^general:/,/^[a-z]/ s|use_sonarr:.*|use_sonarr: true|" "$CONFIG_FILE"
  sed -i "/^general:/,/^[a-z]/ s|use_radarr:.*|use_radarr: true|" "$CONFIG_FILE"

  echo "Bazarr Zero-Config (Direct File) Complete!"
) &
