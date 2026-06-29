#!/usr/bin/env bash
# POC ReadAid — OCR webcam via glm-ocr (Ollama local)
# Sert la page sur http://localhost:8000 (getUserMedia exige un contexte sécurisé)
set -e
cd "$(dirname "$0")"

PORT=8000

# 1) Vérifie qu'Ollama tourne
if ! curl -s "http://localhost:11434/api/tags" >/dev/null 2>&1; then
  echo "⚠️  Ollama ne répond pas sur :11434. Lance-le d'abord :  ollama serve"
  echo "    (et vérifie le modèle :  ollama list | grep glm-ocr)"
fi

# 2) Autorise le navigateur à appeler Ollama (CORS) — utile si l'appel échoue
#    Si tu vois 'Connexion à Ollama impossible', relance Ollama ainsi :
#      OLLAMA_ORIGINS='*' ollama serve

echo "▶  POC dispo sur :  http://localhost:$PORT"
echo "   (Ctrl+C pour arrêter)"
( sleep 1 && open "http://localhost:$PORT" ) &
python3 -m http.server "$PORT"
