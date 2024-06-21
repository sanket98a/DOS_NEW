import utility.config as config
import pandas as pd
from azure.cosmos import CosmosClient, exceptions
import streamlit as st
from DOS import DOS
from summerizer_run import cosmos_summarizer_db
import os
st.set_page_config(page_title="DOS", page_icon="https://acis.affineanalytics.co.in/assets/images/logo_small.png", layout="wide",
                   initial_sidebar_state="auto", menu_items=None)
############################# Tool Name ###############################################
st.markdown("""
    <div style='text-align: center; margin-top:-50px; margin-bottom: 15px;margin-left: -50px;'>
    <h2 style='font-size: 40px; font-family: Courier New, monospace;
                    letter-spacing: 2px; text-decoration: none;'>
    <img src="https://acis.affineanalytics.co.in/assets/images/logo_small.png" alt="logo" width="70" height="60">
    <span style='background: linear-gradient(45deg, #ed4965, #c05aaf);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            text-shadow: none;'>
                    DOS AND REVIEW SUMMARIZATION
    </span>
    <span style='font-size: 40%;'>
    <sup style='position: relative; top: 5px; color: #ed4965;'>by Affine</sup>
    </span>
    </h2>
    </div>
    """, unsafe_allow_html=True)
####################################################################################
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

def find_distinct_style_num(container):
        
    query = "SELECT DISTINCT c.style_number FROM c"

    # Execute the query
    item_list = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

    print('Found {0} items'.format(item_list.__len__()))
    unqiue_style_num=[i['style_number'] for i in item_list]
    return unqiue_style_num

def read_items(style_num,container):
    query = f"SELECT * FROM c WHERE c.DOS_flag = true AND c.style_number={style_num}"

    # Execute the query
    item_list = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

    print('Found {0} items'.format(item_list.__len__()))
    return item_list

def cosmos_client():
    # Initialize the Cosmos client
    client = CosmosClient(HOST, MASTER_KEY)

    # Get the database and container
    database = client.get_database_client(DATABASE_ID)
    container = database.get_container_client(CONTAINER_ID)
    return container

if "session_client" not in st.session_state:
    st.session_state.session_client = cosmos_client()

if "model_id" not in st.session_state:
    st.session_state.model_id = find_distinct_style_num(st.session_state.session_client)

if "data" not in st.session_state:
    st.session_state.data= ""

if "style_number" not in st.session_state:
    st.session_state.style_number=None


col1, col2 , col3= st.columns([1,1,1],gap="large") 

with col1:
    Style_num=st.selectbox("Select Style Number ::",st.session_state.model_id)
    st.divider()
    summaries_review=cosmos_summarizer_db.get_latest_summarize_review(Style_num)['summaries_review']
    st.write(summaries_review)

   

if st.session_state.data=="" or st.session_state.style_number!=Style_num:
    st.session_state.style_number=Style_num
    data=read_items(Style_num,st.session_state.session_client)
    st.session_state.data=data

if st.session_state.data!="":
    df=pd.DataFrame(st.session_state.data)
    df=df[['id','style_number','headline','rating','comments','brd_dept_desc','Datetime','silhouette','silhouette_mapping','proportion_or_fit','proportion_or_fit_mapping','detail','detail_mapping','color','color_mapping','print_or_pattern','print_or_pattern_mapping','fabric','fabric_mapping','DOS_flag']]
    st.divider()
    st.dataframe(df.drop('id',axis=1))
    dos_obj=DOS()

    with col3:
        fig,cal_df=dos_obj.pyplot_dos(df)
        # Display the plot in Streamlit
        st.plotly_chart(fig)
        st.dataframe(cal_df.set_index("Attribute").T,width=500)
    
    with col2:
            fig,count_df=dos_obj.plot_ratings(df)
            st.plotly_chart(fig)
            st.dataframe(count_df,width=300)

    with col1:
        st.divider()
        selected_col=st.selectbox("Select the Atrribute::",["silhouette_mapping",'proportion_or_fit_mapping','detail_mapping','color_mapping','print_or_pattern_mapping','fabric_mapping'])
        mapping=df[df[selected_col]!="NA"][selected_col].dropna().head(5)
        with st.expander(f"Key Of Phrases :: {selected_col}"):
            for text in mapping:
                st.write(text)

