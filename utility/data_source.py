import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
from azure.cosmos import CosmosClient, exceptions
import pandas as pd

class DataSource():
    
    def __init__(self,cosmos_endpoint,cosmos_key,database_name,container_name):
        self.cosmos_endpoint=cosmos_endpoint
        self.cosmos_key=cosmos_key
        self.database_name=database_name
        self.container_name=container_name
        
        # Initialize the Cosmos client
        client = CosmosClient(self.cosmos_endpoint, self.cosmos_key)
        # Get the database and container
        database = client.get_database_client(self.database_name)
        self.container = database.get_container_client(self.container_name)
    
    def find_distinct_style_num(self):
        
        query = "SELECT DISTINCT c.style_number FROM c"

        # Execute the query
        item_list = list(self.container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        print('Found {0} items'.format(item_list.__len__()))
        unqiue_style_num=[i['style_number'] for i in item_list]
        return unqiue_style_num
    
    def read_summerize_items(self,style_number):
            query = f"SELECT c.id, c.comments FROM c WHERE c.style_number={style_number}"
            # Execute the query
            item_list = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))

            print('Found {0} items'.format(item_list.__len__()))
            df=pd.DataFrame(item_list)
            print(f"Style Number :{style_number}  :: Size :{df.shape[0]}")
            return df

    def read_dos_items(self):
     
        query = "SELECT * FROM c WHERE c.DOS_flag = false"

        # Execute the query
        item_list = list(self.container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        print('Found {0} items'.format(item_list.__len__()))

        return item_list

    def get_max_id_number(self):
        # Query to get the maximum style_number in the container
        #  query = "SELECT VALUE MAX(c.id) FROM c"
        query="SELECT TOP 1 c.id FROM c ORDER BY c.datetime_field DESC"
        items = list(self.container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        # If there are no items, return 0 as the starting point
        if len(items) == 0 or items[0] is None:
            return 0
        return items[0]['id']

    def get_latest_summarize_review(self,style_number):

        query=f"SELECT TOP 1 c.review_id_list, c.summaries_review FROM c WHERE c.style_number={style_number} ORDER BY c.datetime_field DESC"
        items = list(self.container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        # If there are no items, return 0 as the starting point
        if len(items) == 0 or items[0] is None:
            return 0
        return items[0]


    def uplaod_data(self,document:dict):
        review_id=document["review_id"]
        try:
            self.container.upsert_item(document)
            print(f"Upserted document with id: {review_id}")
        except exceptions.CosmosHttpResponseError as e:
            print(f"Failed to upsert document with id: {review_id}. Error: {e}")