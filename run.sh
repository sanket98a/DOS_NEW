#!/bin/bash

# Set environment variables
# Export environment variables for Docker Compose
export HOST="${HOST:-default_host}"
export MASTER_KEY="${MASTER_KEY:-default_master_key}"
export DATABASE_ID="${DATABASE_ID:-default_database_id}"
export CONTAINER_ID="${CONTAINER_ID:-default_container_id}"
export OPENAI_API_BASE="${OPENAI_API_BASE:-https://api.openai.com}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-default_openai_api_key}"
export OPENAI_LLM_MODEL="${OPENAI_LLM_MODEL:-default_llm_model}"
export OPENAI_EMBEDDING_MODEL="${OPENAI_EMBEDDING_MODEL:-default_embedding_model}"
export OPENAI_API_VERSION="${OPENAI_API_VERSION:-2023-12-31}"
export AZURE_SEARCH_SERVICE_ENDPOINT="${AZURE_SEARCH_SERVICE_ENDPOINT:-default_search_service_endpoint}"
export AZURE_SEARCH_INDEX_NAME="${AZURE_SEARCH_INDEX_NAME:-default_index_name}"
export AZURE_SEARCH_INDEX_KEY="${AZURE_SEARCH_INDEX_KEY:-default_index_key}"


# Execute docker-compose up command with environment variables
docker-compose up -d
