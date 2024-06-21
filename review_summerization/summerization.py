import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from azure.search.documents.models import QueryAnswerType, QueryCaptionType, QueryType, VectorizedQuery
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import logging

# Configure logging
logging.basicConfig(filename='mix_ranker.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')


class LengthRanker:
    """
    A class to rank reviews based on the length of comments.

    Methods
    -------
    fit(df: pandas.DataFrame) -> pandas.DataFrame
        Ranks the DataFrame based on the length of the comments.
    """

    def __init__(self):
        pass

    def __length_ranker(self, df):
        """
        Private method to rank the DataFrame based on the length of the comments.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing the reviews to be ranked.

        Returns
        -------
        pandas.DataFrame
            DataFrame with length ranks and reciprocal rank frequencies (RRF).
        """
        try:
            df['length'] = df.apply(lambda x: len(x['comments']), axis=1)
            df['length_rank'] = df['length'].rank(method='dense', ascending=False).astype(int)
            df['length_rrf'] = 1 / (60 + df['length_rank'])
            return df
        except Exception as e:
            logging.error(f"Error in __length_ranker: {e}")
            raise

    def fit(self, df):
        """
        Ranks the DataFrame based on the length of the comments.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing the reviews to be ranked.

        Returns
        -------
        pandas.DataFrame
            DataFrame with length ranks and reciprocal rank frequencies (RRF).
        """
        try:
            logging.info("Starting length ranking...")
            df = self.__length_ranker(df)
            self.max_records = df.shape[0]
            logging.info("Length ranking completed.")
            return df
        except Exception as e:
            logging.error(f"Error in fit method: {e}")
            raise


class LexicalRanker:
    """
    A class to rank reviews based on lexical analysis using TF-IDF scores.

    Attributes
    ----------
    keywords_dict : dict
        Dictionary containing keywords for lexical analysis.
    keywords_list : list
        List of keywords for lexical analysis.

    Methods
    -------
    fit(df: pandas.DataFrame) -> (pandas.DataFrame, int)
        Ranks the DataFrame based on lexical analysis.
    """

    def __init__(self, keywords_dict: dict):
        """
        Initializes the LexicalRanker with the provided keywords dictionary.

        Parameters
        ----------
        keywords_dict : dict
            Dictionary containing keywords for lexical analysis.
        """
        self.keywords_dict = keywords_dict
        self.__keyword()

    def __keyword(self):
        """
        Private method to extract unique keywords from the keywords dictionary.
        """
        try:
            keywords_list = set([word for dict_1 in self.keywords_dict.keys() for word in self.keywords_dict[dict_1]['keywords']])
            self.keywords_list = list(keywords_list)
        except Exception as e:
            logging.error(f"Error in __keyword method: {e}")
            raise

    def __calculate_lexical_scores_tfidf(self, df):
        """
        Private method to calculate TF-IDF scores for the reviews.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing the reviews to be ranked.

        Returns
        -------
        pandas.DataFrame
            DataFrame with lexical scores.
        """
        try:
            # Initialize the vectorizer with the keywords as vocabulary
            vectorizer = TfidfVectorizer(vocabulary=self.keywords_list, lowercase=True)

            # Fit and transform the review texts
            tfidf_matrix = vectorizer.fit_transform(df['comments'])

            # Calculate the scores for each review
            scores = tfidf_matrix.sum(axis=1).A1  # .A1 converts it to a 1D array

            # Create a DataFrame with the results
            results = pd.DataFrame({
                'Review_ID': df['id'],
                'Review_Text': df['comments'],
                'Lexical_Score': scores
            })
            
            return results
        except Exception as e:
            logging.error(f"Error in __calculate_lexical_scores_tfidf method: {e}")
            raise

    def fit(self, df):
        """
        Ranks the DataFrame based on lexical analysis using TF-IDF scores.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing the reviews to be ranked.

        Returns
        -------
        (pandas.DataFrame, int)
            DataFrame with lexical ranks and the number of records.
        """
        try:
            logging.info("Starting lexical ranking...")
            lexical_df = self.__calculate_lexical_scores_tfidf(df)
            df = df.merge(lexical_df, how='inner', left_on='id', right_on='Review_ID')
            logging.info(f"Number of lexical records: {df.shape[0]}")
            df['lexical_rank'] = df['Lexical_Score'].rank(method='dense', ascending=False).astype(int)
            df['lexical_rrf'] = 1 / (60 + df['lexical_rank'])
            max_records = df.shape[0]
            logging.info("Lexical ranking completed.")
            return df, max_records
        except Exception as e:
            logging.error(f"Error in fit method: {e}")
            raise



class SemanticRanker:
    
    def __init__(self,azure_index:str,azure_service_endpoint:str,azure_key:str,semantic_query:str,embedding_client,embedding_model_deloyment_name:str):
        self.azure_index=azure_index
        self.azure_service_endpoint=azure_service_endpoint
        self.azure_key=azure_key
        self.semantic_query=semantic_query
        self.embedding_client=embedding_client
        self.embedding_model_deloyment_name=embedding_model_deloyment_name
    
    
    def __semantic_search(self,style_number):
        __azure_search_credential = AzureKeyCredential(self.azure_key)
        search_client = SearchClient(endpoint=self.azure_service_endpoint, index_name=self.azure_index, credential=__azure_search_credential)
        
        ## embedding of query
        print(self.semantic_query)
        vector=self.embedding_client.embeddings.create(input = [self.semantic_query], model=self.embedding_model_deloyment_name).data[0].embedding
        query_vector=VectorizedQuery(vector=vector,fields="text_vector",exhaustive=True)
        
        results=search_client.search(self.semantic_query,
                                     query_type=QueryType.SEMANTIC,
                                     semantic_configuration_name="my-semantic-config",
                                     filter=f"style_number eq '{style_number}'" ,
                                    vector_queries=[query_vector],      
                                     top=self.max_records)
        semantic_list=[doc for doc in results]
        print("Number of Semantic Records :: ",len(semantic_list))
        return pd.DataFrame(semantic_list)
        
    
    def fit(self,style_number,max_records):
        df=self.__semantic_search(style_number)
        if df['@search.reranker_score'].isnull().sum()==0:
            df['semantic_rank'] = df['@search.reranker_score'].rank(method='dense', ascending=False).astype(int)
        else:
            df['semantic_rank'] = df['@search.score'].rank(method='dense', ascending=False).astype(int)
        df['semantic_rrf']=1/(60+df['semantic_rank'])
        return df
    

class MixRanker(LengthRanker, LexicalRanker, SemanticRanker):
    """
    A class to rank reviews based on length, lexical, and semantic analysis.

    Attributes:
    ----------
    keywords_dict : dict
        Dictionary containing keywords for lexical analysis.
    keywords_list : list
        List of keywords for lexical analysis.
    azure_index : str
        Azure search index name.
    azure_service_endpoint : str
        Azure service endpoint URL.
    azure_key : str
        Azure service access key.
    semantic_query : str
        Query for semantic search.
    embedding_client : object
        Client for embedding model.
    embedding_model_deployment_name : str
        Name of the embedding model deployment.
    """

    def __init__(self, keywords: dict, azure_index: str, azure_service_endpoint: str, azure_key: str, embedding_client, embedding_model_deployment_name, semantic_query: str = "find reviews that talk about silhouette, proportion, color, detail, fit and fabric of an apparel or accessories.", keywords_list: list = None):
        self.keywords_dict = keywords
        self.keywords_list = keywords_list
        self.azure_index = azure_index
        self.azure_service_endpoint = azure_service_endpoint
        self.azure_key = azure_key
        self.semantic_query = semantic_query
        self.embedding_client = embedding_client
        self.embedding_model_deployment_name = embedding_model_deployment_name

        LengthRanker.__init__(self)
        LexicalRanker.__init__(self,self.keywords_dict)
        SemanticRanker.__init__(self, self.azure_index, self.azure_service_endpoint, self.azure_key, self.semantic_query, self.embedding_client, self.embedding_model_deployment_name)


    def ranker(self, df, style_num):
        """
        Rank the DataFrame based on length, lexical, and semantic analysis.

        Parameters:
        ----------
        df : pandas.DataFrame
            DataFrame containing the reviews to be ranked.
        style_num : int
            Style number of the product.

        Returns:
        -------
        pandas.DataFrame
            DataFrame with rankings added.
        """
        try:
            logging.info(f"Style Number: {style_num}")
            #"Starting length ranking...
            df = LengthRanker.fit(self, df)
            #Starting lexical ranking...
            df, max_records = LexicalRanker.fit(self, df)
            logging.info(f"Lexical ranking done for style number: {style_num}")

            # Starting semantic ranking...
            semantic_df = SemanticRanker.fit(self, style_num, max_records)
            logging.info(f"Semantic ranking done for style number: {style_num}")

            df = df.merge(semantic_df, left_on="id", right_on="Id", how='inner')[['Id', "style_number", "comments", 'length_rank', 'length_rrf', 'lexical_rank', 'lexical_rrf', 'semantic_rank', 'semantic_rrf']]
            return df

        except Exception as e:
            logging.error(f"Error in ranker method: {e}")
            raise

    def fit(self, df, style_num: int, w1: float = 0.4, w2: float = 0.4, w3: float = 0.2):
        """
        Fit the ranking model and calculate the final ranking.

        Parameters:
        ----------
        df : pandas.DataFrame
            DataFrame containing the reviews to be ranked.
        style_num : int
            Style number of the product.
        w1 : float, optional
            Weight for semantic ranking (default is 0.4).
        w2 : float, optional
            Weight for lexical ranking (default is 0.4).
        w3 : float, optional
            Weight for length ranking (default is 0.2).

        Returns:
        -------
        pandas.DataFrame
            DataFrame with final rankings.
        """
        try:
            if w1 + w2 + w3 != 1:
                logging.error("Weights must sum up to 1.")
                raise ValueError("Weights must sum up to 1.")
            
            logging.info("Starting combined ranking...")
            df = self.ranker(df, style_num)
            df['final_rank'] = w1 * df['semantic_rrf'] + w2 * df['lexical_rrf'] + w3 * df['length_rrf']
            df = df.sort_values("final_rank", ascending=False)
            logging.info(f"Final ranking completed for style number: {style_num}")
            return df
        except Exception as e:
            logging.error(f"Error in fit method: {e}")
            raise