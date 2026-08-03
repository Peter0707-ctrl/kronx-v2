#!/bin/bash
set -e

echo "[Copetra Ollama] Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

echo "[Copetra Ollama] Waiting for server to be ready..."
sleep 8

echo "[Copetra Ollama] Pulling llama3.2:3b model (this may take a few minutes on first boot)..."
ollama pull llama3.2:3b || echo "[Copetra Ollama] Pull failed or already cached, continuing..."

echo "[Copetra Ollama] Model ready. Server is live on port 11434."
wait $OLLAMA_PID
