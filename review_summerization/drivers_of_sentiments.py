import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
from datetime import datetime
import utility.config as config
from utility.data_source import DataSource
from utility.azure_open_api import AzureOpenApi
from prompts.dos_prompt import dos_prompt_2
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


cosmos_db=DataSource(cosmos_endpoint=HOST,
                        cosmos_key=MASTER_KEY,
                        database_name=DATABASE_ID,
                        container_name=CONTAINER_ID)

azure_ai=AzureOpenApi(api_base=OPENAI_API_BASE,
                      api_key=OPENAI_API_KEY,
                      api_version=OPENAI_API_VERSION,
                      embedding_model_deployment_name=OPENAI_EMBEDDING_MODEL,
                      llm_deployment_name=OPENAI_LLM_MODEL)

class DriverSentiment:

    def __init__(self):
        pass

    def to_dos(self,AZURE_SEARCH_INDEX_NAME,AZURE_SEARCH_SERVICE_ENDPOINT):
        item_list=cosmos_db.read_dos_items()
        for doc in item_list:
            dict1={}
            comments=doc.get("comments")
            prompt_1=dos_prompt_2 + "Review:" + comments
            output=azure_ai.azure_dos_call(prompt_1)
            doc['DOS_flag']=True
            doc['Datetime']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            doc.update(output)
            ## Embedding of doc ref. ID
            vector=azure_ai.generate_embeddings(comments)
            ## push to azure ai search
            dict_1={"Id":str(doc['id']),
                "style_number":str(doc['style_number']),
                "text":comments,
                "headline":doc['headline'],
                "rating":str(doc['rating']),
                "text_vector":vector}

            ## Embedding and upload to the Azure Search
            azure_ai.upload_index(dict_1,AZURE_SEARCH_INDEX_NAME,AZURE_SEARCH_SERVICE_ENDPOINT,azure_search_key=AZURE_SEARCH_INDEX_KEY)
            try:
                # Replace the item in the container
                cosmos_db.container.replace_item(item=doc['id'], body=doc)
                print(f"Updated item with id: {doc['id']}")
            except exceptions.CosmosHttpResponseError as e:
                print(f"Failed to update item with id: {doc['id']}. Error: {str(e)}")

if __name__ == '__main__':
    dos_obj=DriverSentiment()
    dos_obj.to_dos(AZURE_SEARCH_INDEX_NAME,AZURE_SEARCH_SERVICE_ENDPOINT)