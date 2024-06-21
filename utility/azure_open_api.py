import os, openai
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import QueryAnswerType, QueryCaptionType, QueryType, VectorizedQuery
from azure.search.documents.indexes.models import ExhaustiveKnnAlgorithmConfiguration, ExhaustiveKnnParameters, SearchIndex, SearchField, SearchFieldDataType, SearchableField, SearchIndex, SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SemanticSearch, VectorSearch, HnswAlgorithmConfiguration, HnswParameters, VectorSearchAlgorithmKind, VectorSearchProfile, VectorSearchAlgorithmMetric
import time
import ast



class AzureOpenApi:
    
    def __init__(self,api_key,api_version,api_base,embedding_model_deployment_name,llm_deployment_name):
        self.api_key=api_key
        self.api_version=api_version
        self.api_base=api_base
        self.embedding_model_deployment_name=embedding_model_deployment_name
        self.llm_deployment_name=llm_deployment_name

        self.client = AzureOpenAI(
              api_key =api_key ,
              api_version = api_version,
              azure_endpoint = api_base)
        
    def load_embedd_clients(self):
        return self.client
        
    
    def generate_embeddings(self,text):
        return self.client.embeddings.create(input = [text], model=self.embedding_model_deployment_name).data[0].embedding
    
    def azure_summerizer_call(self,prompt):

        start=time.time()
        completion = self.client .chat.completions.create(
        model=self.llm_deployment_name,
        temperature=0,
        messages= [ { "role": "assistant",
                "content": "You are an expert in  summarizing product reviews for e-commerce products.",
            },{
                "role": "user",
                "content": prompt
            } ])
        end=time.time()
        latency=end-start
        result = completion.to_dict()['choices'][0]['message']['content']
        print('-----------------------------------------------------------')
        print(result)
        return result
        print('-----------------------------------------------------------')

    def azure_dos_call(self,prompt):
        start=time.time()
        completion = self.client .chat.completions.create(
        model=self.llm_deployment_name,
        temperature=0,
        messages= [ { "role": "assistant",
                "content": "You are an expert in analyzing product reviews for e-commerce products.",
            },{
                "role": "user",
                "content": prompt
            } ])
        end=time.time()
        ## Calculate the inferance time
        latency=end-start
        result = completion.to_dict()['choices'][0]['message']['content']
        print('-----------------------------------------------------------')
        print(result)
        json_review=ast.literal_eval(result[result.index("{"):result.index("}")+1])
        json_review['inferance_time']=latency
        print('-----------------------------------------------------------')
        return json_review

    def create_index(self,admin_client,AZURE_SEARCH_INDEX_NAME):

        fields = [SearchableField(name="Id", 
                                  type=SearchFieldDataType.String,
                                  key=True,
                                  searchable=True,
                                  filterable=True , 
                                  retrievable=True),
                  SearchableField(name="style_number", 
                                  type=SearchFieldDataType.String,
                                  searchable=True,
                                  filterable=True , 
                                  retrievable=True),
                  SearchableField(name="text", 
                                  type=SearchFieldDataType.String,
                                  searchable=True,
                                  filterable=True , 
                                  retrievable=True),
                  SearchableField(name="headline", 
                                  type=SearchFieldDataType.String,
                                  searchable=True,
                                  filterable=True , 
                                  retrievable=True),
                  SearchableField(name="rating", 
                                  type=SearchFieldDataType.String,
                                  searchable=True,
                                  filterable=True , 
                                  retrievable=True),
                  SearchField(name="text_vector", 
                              type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                              searchable=True, 
                              vector_search_dimensions=1536, 
                              vector_search_profile_name="myHnswProfile")]

        vector_search = VectorSearch(algorithms=[HnswAlgorithmConfiguration(name="myHnsw",kind=VectorSearchAlgorithmKind.HNSW,parameters=HnswParameters(m=4,ef_construction=400,ef_search=500,metric=VectorSearchAlgorithmMetric.COSINE)),
                                                 ExhaustiveKnnAlgorithmConfiguration(name="myExhaustiveKnn",kind=VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,parameters=ExhaustiveKnnParameters(metric=VectorSearchAlgorithmMetric.COSINE))],
                                     profiles=[VectorSearchProfile(name="myHnswProfile",algorithm_configuration_name="myHnsw"),VectorSearchProfile(name="myExhaustiveKnnProfile",algorithm_configuration_name="myExhaustiveKnn")])

        semantic_config = SemanticConfiguration(name="my-semantic-config",prioritized_fields=SemanticPrioritizedFields(title_field=SemanticField(field_name="text"),content_fields=[SemanticField(field_name="text")]))
        semantic_search = SemanticSearch(configurations=[semantic_config])
        index = SearchIndex(name=AZURE_SEARCH_INDEX_NAME, fields=fields,vector_search=vector_search, semantic_search=semantic_search)
        result = admin_client.create_or_update_index(index)
        print(f' {result.name} created')

    def upload_index(self,
                    dict_1,
                    AZURE_SEARCH_INDEX_NAME,
                    AZURE_SEARCH_SERVICE_ENDPOINT,
                    azure_search_key):

        azure_search_credential = AzureKeyCredential(azure_search_key)
        admin_client = SearchIndexClient(endpoint=AZURE_SEARCH_SERVICE_ENDPOINT, index_name=AZURE_SEARCH_INDEX_NAME, credential=azure_search_credential)
        search_client = SearchClient(endpoint=AZURE_SEARCH_SERVICE_ENDPOINT, index_name=AZURE_SEARCH_INDEX_NAME, credential=azure_search_credential)
        indexes = admin_client.list_index_names()
        if AZURE_SEARCH_INDEX_NAME not in indexes:
            self.create_index(admin_client,AZURE_SEARCH_INDEX_NAME)
        else:
            print("Azure Ai search index alreday created..")
        
        search_client.upload_documents([dict_1])
        print(f"Upload the Index of Doc ID :: {dict_1['Id']}")