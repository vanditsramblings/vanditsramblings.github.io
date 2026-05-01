#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "Starting local development server..."
npm run dev
