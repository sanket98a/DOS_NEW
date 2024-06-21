from review_summerization.drivers_of_sentiments import DriverSentiment
import os

HOST=os.getenv("host")
MASTER_KEY=os.getenv("master_key")
DATABASE_ID=os.getenv("database_id")
CONTAINER_ID=os.getenv("container_id")
OPENAI_API_BASE=os.getenv("openai_api_base")
OPENAI_API_KEY=os.getenv("openai_api_key")
OPENAI_LLM_MODEL=os.getenv("openai_llm_model")
OPENAI_EMBEDDING_MODEL=os.getenv("openai_embedding_model")
OPENAI_API_VERSION=os.getenv("openai_api_version")
AZURE_SEARCH_SERVICE_ENDPOINT=os.getenv("azure_search_service_endpoint")
AZURE_SEARCH_INDEX_NAME=os.getenv("azure_search_index_name")
AZURE_SEARCH_INDEX_KEY=os.getenv("azure_search_index_key")

if __name__ == '__main__':
    dos_obj=DriverSentiment()
    dos_obj.to_dos(AZURE_SEARCH_INDEX_NAME,AZURE_SEARCH_SERVICE_ENDPOINT)