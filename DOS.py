import pandas as pd
import numpy as np
import os
from openai import AzureOpenAI
import time
import ast
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go


class DOS():

    def __init__(self):
        pass
    

    def to_dos(self,df,file_name,prompt,progress_bar):
        ## Temp step
        df=df.rename({"style number":"style_number"},axis=1)
        output_list=[]
        for review in df.iterrows():
            try:
                review_text=review[1]["comments"]
                # prompt_1=prompt.format(review=review_text)
                prompt_1=prompt + "Review:" + review_text
                output=self.azure_gpt_v(prompt_1)
                output['final_response']['style_number']=review[1]["style_number"]
                output['final_response']['headline']=review[1]["headline"]
                output['final_response']['rating']=review[1]["rating"]
                output['final_response']['comments']=review[1]["comments"]
                output['final_response']['brd_dept_desc']=review[1]["brd_dept_desc"]
                output['final_response']['dos_flag']=1
                output_list.append(output['final_response'])
                # Calculate the progress percentage
                progress_percentage = review[0]/df.shape[0] 
                progress_bar.progress(progress_percentage)
            except:
                pass

        dos_df=pd.DataFrame(output_list)
        dos_df=dos_df[['style_number','headline','rating','comments','brd_dept_desc','silhouette','silhouette_mapping','proportion_or_fit','proportion_or_fit_mapping','detail','detail_mapping','color','color_mapping','print_or_pattern',"print_or_pattern_mapping","fabric","fabric_mapping"]]
        dos_df['Rating Flag']=dos_df.apply(lambda x:"High Rated" if x['rating']>=3 else "Low Rated",axis=1)
        dos_df.to_csv(file_name,index=False)
        return dos_df
    
    def stack_plot(self,df):
        """"""
        filter_df=df[['silhouette','proportion_or_fit','detail','color','print_or_pattern','fabric']]
        transformed_data = filter_df.melt(var_name='Attribute', value_name='Sentiment')
        transformed_data=transformed_data.loc[transformed_data['Sentiment']!=0]
        grouped_counts_1=transformed_data.groupby(['Attribute','Sentiment'])['Sentiment'].count().reset_index(name="count")
        # Pivot the DataFrame
        pivot_df = grouped_counts_1.pivot(index='Attribute', columns='Sentiment', values='count')
        pivot_df_percentage = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100
        cal_df=pivot_df.reset_index().fillna(0).rename({-1:"Negative",1:"Postive"},axis=1)
        cal_df['Total']=cal_df['Negative']+cal_df['Postive']
        cal_df['Positive %']=(cal_df['Postive']/cal_df['Total'])*100
        cal_df['Negative %']=(cal_df['Negative']/cal_df['Total'])*100
        cal_df.set_index("Attribute")
        ## PLOT
        fig, ax = plt.subplots(figsize=(10, 6))
        pivot_df_percentage.plot(kind='bar', stacked=True, figsize=(10, 6),ax=ax)
        # Add text annotations
        for p in ax.patches:
            width, height = p.get_width(), p.get_height()
            x, y = p.get_xy()
            ax.text(x + width / 2, y + height / 2, f'{int(height)}%', ha='center', va='center')

        plt.title('Stacked Column Chart of Sentiment Counts by Attribute')
        plt.xlabel('Attribute')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.legend(title='Sentiment', bbox_to_anchor=(1.05, 1), loc='upper left')
        return fig,cal_df
    
    def pyplot_dos(self,df):
        filter_df=df[['silhouette','proportion_or_fit','detail','color','print_or_pattern','fabric']]
        transformed_data = filter_df.melt(var_name='Attribute', value_name='Sentiment')
        transformed_data=transformed_data.loc[transformed_data['Sentiment']!=0]
        grouped_counts_1=transformed_data.groupby(['Attribute','Sentiment'])['Sentiment'].count().reset_index(name="count")
        # Pivot the DataFrame
        pivot_df = grouped_counts_1.pivot(index='Attribute', columns='Sentiment', values='count')
        cal_df=pivot_df.reset_index().fillna(0).rename({-1:"Negative",1:"Postive"},axis=1)
        cal_df['Total']=cal_df['Negative']+cal_df['Postive']
        cal_df['Positive %']=(cal_df['Postive']/cal_df['Total'])*100
        cal_df['Negative %']=(cal_df['Negative']/cal_df['Total'])*100
        cal_df.set_index("Attribute")
        # Calculate percentages
        pivot_df_percentage = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100
        # Plot stacked bar chart with percentages and values
        fig = go.Figure()

        for col in pivot_df_percentage.columns:
            if col==1:
                color = 'green'
            else:
                color = 'red'

            fig.add_trace(go.Bar(
                x=pivot_df_percentage.index,
                y=pivot_df_percentage[col],
                name=str(col),
                text=[val for val in pivot_df[col]],#[f"{val:.2f}%" for val in pivot_df_percentage[col]],  # Display percentage values
                textposition='auto',
                hoverinfo='x+name+text',
                marker_color=color,
            ))

        fig.update_layout(
            barmode='stack',
            title='Attribute Level Distribution',
            xaxis=dict(title='Attribute'),
            yaxis=dict(title='Percentage'),
            legend=dict(title='Sentiment'),
            width=500,
            height=400
        )
        return fig,cal_df
    
    def plot_ratings(self,df):
        df['Rating Flag']=df.apply(lambda x:"High Rated" if x['rating']>=3 else "Low Rated",axis=1)
        count_df = df['Rating Flag'].value_counts().reset_index()
        count_df.columns = ['Rating Flag', 'Count']
        print(count_df)
        # Plot stacked bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=count_df['Rating Flag'],
            y=count_df['Count'],
            text=count_df['Count'],
            textposition='auto',
            marker_color=['green',"red"],
        ))

        fig.update_layout(
            barmode='stack',
            title='Rating Level Distribution',
            xaxis=dict(title='Rating'),
            yaxis=dict(title='Count'),
            legend=dict(title='Rating Flag'),
            width=200,
            height=400
        )
        return fig,count_df.set_index("Rating Flag")