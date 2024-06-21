from review_summerization.summerization import MixRanker
from utility.data_source import DataSource
from utility.azure_open_api import AzureOpenApi
import utility.config as config
from prompts.summarize_prompt import summerization_prompt
import azure.cosmos.exceptions as exceptions
from prompts.lexical_data import lexical_list
from datetime import datetime
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

cosmos_dos_db=DataSource(cosmos_endpoint=HOST,
                        cosmos_key=MASTER_KEY,
                        database_name=DATABASE_ID,
                        container_name=CONTAINER_ID)

cosmos_summarizer_db=DataSource(cosmos_endpoint=HOST,
                        cosmos_key=MASTER_KEY,
                        database_name=DATABASE_ID,
                        container_name="summarizer")

azure_ai=AzureOpenApi(api_base=OPENAI_API_BASE,
                      api_key=OPENAI_API_KEY,
                      api_version=OPENAI_API_VERSION,
                      embedding_model_deployment_name=OPENAI_EMBEDDING_MODEL,
                      llm_deployment_name=OPENAI_LLM_MODEL)


rank_ai=MixRanker(keywords=lexical_list,
              azure_index=AZURE_SEARCH_INDEX_NAME,
              embedding_client=azure_ai.client,
              azure_service_endpoint=AZURE_SEARCH_SERVICE_ENDPOINT,
              azure_key=AZURE_SEARCH_INDEX_KEY,
              embedding_model_deployment_name=OPENAI_EMBEDDING_MODEL)


def summarize_review():
    # fina the unqiue style numberin the dataset
    style_nums=cosmos_dos_db.find_distinct_style_num()
    print("Number unqiue styles in Database ::",style_nums)

    ## Review summarization of each unique style level
    for style_num in style_nums:
        ## read the review data from the cosmos database
        df=cosmos_dos_db.read_summerize_items(style_num)
        ## Review summary of each style level (Ranking using custom ranking)
        df_results=rank_ai.fit(df,style_num)

        print("Rank Data Shape ::",df_results.shape)
        ## for review summary of each style level- only Top 20 reviews
        df_head=df_results.head(20)
        ## metadata collection
        review_ids=df_head['Id'].to_list()
        pre_latest_review=cosmos_summarizer_db.get_latest_summarize_review(style_num)['review_id_list']
        if set(pre_latest_review)==set(review_ids):
            print("Updated Review. No Need to Resummarize Again.")
        else:
            ## concat the all review
            reviews='\n\n'.join(df_head['comments'])
            ## add into the prompt
            prompt=summerization_prompt+ reviews
            ## model calling
            summarize_review=azure_ai.azure_summerizer_call(prompt)
            date= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            review_id=cosmos_summarizer_db.get_max_id_number()
            new_review_number = int(review_id) + 1
            review_dict={"id":str(new_review_number),
                        "partition_key":f"SR_{new_review_number}",
                        "style_number":style_num,
                        "review_id_list":review_ids,
                        "summaries_review":summarize_review,
                        "Datetime":date}
            # print(review_dict)
            try:
                cosmos_summarizer_db.container.upsert_item(review_dict)
                # cosmos_summarizer_db.uplaod_data(review_dict)
                print(f"Upserted document with id: {new_review_number}")
            except exceptions.CosmosHttpResponseError as e:
                print(f"Failed to upsert document with id: {new_review_number}. Error: {e}")


if __name__ == "__main__":
    summarize_review()