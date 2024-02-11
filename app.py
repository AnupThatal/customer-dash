import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from shiny import App, render, ui


def data_collection():
    odata_urls = [
        'https://survey.kuklpid.gov.np/v1/projects/7/forms/kukl_customer_survey_01.svc',
        'https://survey.kuklpid.gov.np/v1/projects/7/forms/kukl_customer_survey.svc',
        'https://survey.kuklpid.gov.np/v1/projects/15/forms/kukl_customer_survey_01.svc',
        'https://survey.kuklpid.gov.np/v1/projects/9/forms/kukl_customer_survey_01.svc',
        'https://survey.kuklpid.gov.np/v1/projects/6/forms/kukl_customer_survey_01.svc',
        'https://survey.kuklpid.gov.np/v1/projects/2/forms/kukl_customer_survey_01.svc',
        'https://survey.kuklpid.gov.np/v1/projects/2/forms/kukl_customer_survey.svc',
        'https://survey.kuklpid.gov.np/v1/projects/16/forms/kukl_customer_survey_01.svc'

    ]
    params = {
        '$select':'unique_form_id,b10_sub_dmi,gb12_skip/gc01_skp1/gc20/c20,gb12_skip/gc01_skp1/gc20/c22,__system/submitterName,__system/reviewState,b02,unit_owners,gb12_skip/gc01_skp2/d08'
    }
    submission_entity_set = 'Submissions'
    username = 'anupthatal2@gmail.com'
    password = 'Super@8848'
    session = requests.Session()
    session.auth = (username, password)
    
    all_dfs = []  # List to store DataFrames from each URL
    for odata_url in odata_urls:
        submission_url = f"{odata_url}/{submission_entity_set}"
        response = session.get(submission_url, params=params)

        # Parse the JSON response
        data = response.json()

        if 'value' in data:
            df = pd.DataFrame(data['value'])
            all_dfs.append(df)
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df['gb12_skip-gc01_skp1-gc20-c20'] = final_df['gb12_skip'].apply(lambda x: x.get('gc01_skp1', {}).get('gc20', {}).get('c20'))
    final_df['gb12_skip-gc01_skp1-gc20-c22'] = final_df['gb12_skip'].apply(lambda x: x.get('gc01_skp1', {}).get('gc20', {}).get('c22'))
    final_df['SubmitterName'] = final_df['__system'].apply(lambda x: x['submitterName'] if 'submitterName' in x else None).str.upper()
    final_df['ReviewState'] = final_df['__system'].apply(lambda x: x['reviewState'] if 'reviewState' in x else None)
    final_df['b02-Longitude'] = final_df['b02'].apply(lambda x: x['coordinates'][0] if (x and 'coordinates' in x) else None)
    final_df['b02-Latitude'] = final_df['b02'].apply(lambda x: x['coordinates'][1] if (x and 'coordinates' in x) else None)
    final_df['gb12_skip-gc01_skp2-d08'] = final_df['gb12_skip'].apply(lambda x: x.get('gc01_skp2', {}).get('d08'))

    return final_df
    

df = data_collection()

df_hhc=pd.read_csv('HHC_Data.csv')

df.dropna(subset=['b10_sub_dmi'], inplace=True)

c1_list = df['b10_sub_dmi'].unique().astype(int).tolist()
c3_list = df['SubmitterName'].unique().tolist()
df['b10_sub_dmi']=df['b10_sub_dmi'].astype(int)


def data_cleaning_hhc(x):
    df_hhc.rename(columns={'sDMA ': 'SDMA'}, inplace=True)
    df_hhc['SDMA'] = df_hhc['SDMA'].str.replace(r'(\d+\.\d+\.\d+).*', r'\1').str.replace('.', '').astype(int)
    df_hhc['SDMA wise HHC'] = df_hhc['SDMA wise HHC'].str.replace(',', '').astype(int)
    return df_hhc

df_hhc1=data_cleaning_hhc(x=df_hhc)

app_ui = ui.page_fluid(
       
    ui.panel_title(ui.div({"style":"text-align:center;font-size:20px;"},
                   'Welcome to Survey dashboard')),
    ui.layout_sidebar(
        ui.panel_sidebar(
            # {"style": "background-color: rgba(0, 128, 255, 0.1)"},
            ui.input_select('sub_dma','Which Sub dma you wanna forecast',choices=c1_list,selected=153),
            # ui.input_select('sub_dma','Which Sub dma you wanna forecast',choices=c3),
            ui.input_select('Enumertor','Select enumertor Name',choices=c3_list),
            ui.input_text('customer','Customer number or Connection number'),
            ui.download_button("downloadData", "Download"),

            width=2
            ),
            
        ui.panel_main(
            ui.div({"style":"display: flex;flex-direction:row;gap:2rem;justify-content:space-evenly;"}, 
            ui.div( {"style":"font-weight:bold;text-align:center;"},
              ui.markdown(
                """
                ***Survey report***
                """
            ),   

            ui.dataframe.output_data_frame('survey_details'),
            ),
            ),
            ui.div({"style":"display: flex;flex-direction:row;gap:2rem;justify-content:space-evenly;"}, 
            ui.div( {"style":"font-weight:bold;text-align:center;"},
            ui.markdown(
                """
                ***Total***
                """
            ),                       
            ui.dataframe.output_data_frame('data_summary'),

            ),

              ui.div( {"style":"font-weight:bold;text-align:center;"},
            ui.markdown(
                """
                ***Customer details***
                """
            ),                       
            ui.dataframe.output_data_frame('customer1'),

            ),
                       ),

            ui.output_plot('data_details1'),
            ui.dataframe.output_data_frame('data_details2'),

            # ),
            ui.div({"style": "display: flex;flex-direction:row;gap:2rem;justify-content:space-evenly;"}, 
            ui.output_plot('mypie',width='170%',height='400px'),

            ui.output_plot('data_table',width='170%',height='500px'),

            ),
            ui.div({"style": "display: flex;flex-direction:row;gap:2rem;justify-content:space-evenly;"}, 

            ui.output_plot('myplot',width='100%',height='650px'),

            ),

            ui.output_plot('dma_measuring'),
            ),
),
)


def server(input,output, session):
    @output
    @render.plot
    def myplot():
        sub_dma = input.sub_dma() or '153'  # Use a default value if sub_dma is empty
        filtered_df = df[df['b10_sub_dmi'] == int(sub_dma)]

        agg_df = filtered_df.groupby(['SubmitterName', 'ReviewState'])['unique_form_id'].count().unstack(fill_value=0)
        ax = agg_df.plot(kind='bar', stacked=False, rot=10, color=None)  # Remove the color parameter

        ax.set_xlabel('SubmitterName')
        ax.set_ylabel('Total Count')
        ax.set_title('Counts by Submitter Name and Review State')

        for p in ax.patches:
            ax.annotate(f'{p.get_height():.0f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='center', fontsize=12, color='black', xytext=(0, 5),
                        textcoords='offset points')

        return ax.figure

        
    @output
    @render.plot
    def mypie():
        x=input.sub_dma()
        filtered_df = df[df['b10_sub_dmi'] == int(x)]
        unique_submitters = filtered_df.shape[0]
        y2 = df_hhc1[df_hhc1['SDMA'] == int(x)]
        y2.loc[:, 'SDMA wise HHC'] = y2['SDMA wise HHC']

        # y2['SDMA wise HHC']=y2['SDMA wise HHC']
        data={'Remarks':['collected','remaining'],'SDMA wise Collection':[unique_submitters,int(y2['SDMA wise HHC'].iloc[0])
        -int(unique_submitters)]}
        df1=pd.DataFrame(data)
        return df1.plot.pie(y='SDMA wise Collection', labels=df1['Remarks'], autopct='%1.1f%%', startangle=140, legend=False)
    
    @output
    @render.data_frame
    def data_summary():
        x=input.sub_dma()
        filtered_df=df[df['b10_sub_dmi']==int(x)]
        Total=filtered_df['b10_sub_dmi'].count()
        TD=df_hhc1[df_hhc1['SDMA'] == int(x)]
        r=TD['SDMA wise HHC']-Total
        df_summary = pd.DataFrame({'Total': [Total], 'DMA Total':TD['SDMA wise HHC'], 'Remaining': r})
        return df_summary
    
    @output
    @render.data_frame
    def survey_details():
        collected_value = df.shape[0]
        total_value = df_hhc1['SDMA wise HHC'].sum()
        approved_count = df[df['ReviewState'] == 'approved'].shape[0]
        rejected_count = df[(df['ReviewState'].isin(['rejected', 'hasIssues']))].shape[0]
        needs_to_check_count = df['ReviewState'].isna().sum()
        remaining = total_value - collected_value

        df_total = pd.DataFrame({
            'Total': [total_value],
            'Collected': [collected_value],
            'Approved': [approved_count],
            'Rejected/hasIssues': [rejected_count],
            'Needs to check': [needs_to_check_count],
            'Remaining': [remaining]
        })

        return df_total


    @output
    @render.plot
    def data_details1():
        x=input.Enumertor()
        filtered_df=df[df['SubmitterName']==str(x)]
        # filtered_df.groupby('b10_sub_dmi')['unique_form_id'].count().reset_index()
        # heatmap = sns.heatmap(filtered_df.corr(), vmin=-1, vmax=1, annot=True)
        pivot_table = filtered_df.pivot_table(index='SubmitterName', columns='b10_sub_dmi',aggfunc='size',fill_value=0)
        pivot_table_sorted = pivot_table.sort_index(axis=1, ascending=False)
        return sns.heatmap(pivot_table_sorted, annot=True, cmap='coolwarm', fmt='d', linewidths=.5)
    
    @output
    @render.data_frame
    def data_details2():
        x=input.Enumertor()
        filtered_df=df[df['SubmitterName']==str(x)]
        filtered_df['ReviewState'] = filtered_df['ReviewState'].fillna('needs to check')

        # Calculate counts
        counts = filtered_df['ReviewState'].value_counts()
        
        # Initialize a DataFrame
        df_final = pd.DataFrame(counts).reset_index()
        df_final.columns = ['Review State', 'Count']
        
        return df_final

 
    @output
    @render.plot 
    def data_table():
        x=input.sub_dma()
        filtered_df=df[df['b10_sub_dmi']==int(x)]
        filtered_df.loc[:, 'ReviewState'] = filtered_df['ReviewState'].fillna('needs to check')
        # filtered_df['ReviewState'] = filtered_df['ReviewState'].fillna('needs to check')
        counts = filtered_df.groupby('ReviewState')['b10_sub_dmi'].count()
        custom_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        fig, ax = plt.subplots(figsize=(8, 4))
        counts.plot(kind='bar', color=custom_colors, legend=True, ax=ax)
        ax.set_xlabel('Review State')
        ax.set_ylabel('Collect')
        ax.set_title('Counts by Review State')
        for i, v in enumerate(counts):
            ax.text(i, v + 1, str(v), ha='center', va='bottom')
        return fig
    
    @output
    @render.plot
    def dma_measuring():
        data_collected=df.groupby('b10_sub_dmi')['unique_form_id'].count().reset_index()
        # df_hhc1.groupby('SDMA')['SDMA wise HHC'].reset_index()
        hhc=df_hhc1[['SDMA','SDMA wise HHC']]

        result = pd.merge(data_collected,hhc,left_on='b10_sub_dmi',right_on='SDMA', how='inner')

        result['diff']=result['SDMA wise HHC']-result['unique_form_id']
        # print(result)

        sorted_df = result.sort_values(by='diff', ascending=False)
        
        sorted_df=sorted_df[sorted_df['diff']>0]
        dot_size = sorted_df['diff'] * 100
        scatter_plot=sns.scatterplot(x='SDMA', y='diff', size='diff', data=sorted_df, sizes=(10, 400))
        for i, txt in enumerate(sorted_df['SDMA']):
            plt.annotate(txt, (sorted_df['SDMA'].iloc[i], sorted_df['diff'].iloc[i]), fontsize=8, ha='center')
        plt.xlabel('SDMA')
        plt.ylabel('diff')
        plt.title('Scatterplot of SDMA vs. diff')
        return scatter_plot
    
    @output
    @render.data_frame
    def customer1():
        x=input.customer()

        df.rename(columns={'b10_dmi':'DMA'},inplace=True)

        df_c=df[df['gb12_skip-gc01_skp1-gc20-c20'] == str(x)]

        # if df_c.empty:
        #     df_c = df[df['gb12_skip-gc01_skp1-gc20-c22'] == str(x)]
        #     df_c.rename(columns={
        #     'unique_form_id': 'ID',
        #     'b10_sub_dmi': 'Sub DMA',
        #     'gb12_skip-gc01_skp1-gc22':'Connection no',
        #     'unit_owners': 'Unit Owners',
        #     'SubmitterName': 'Enumerator'}, inplace=True)

        #     return df_c[['ID','Sub DMA','Unit Owners','Enumerator']]
        if df_c.empty:
            df_c = df[df['gb12_skip-gc01_skp2-d08'] == str(x)]
            df_c.rename(columns={
            'unique_form_id': 'ID',
            'b10_sub_dmi': 'Sub DMA',
            'gb12_skip-gc01_skp1-gc22':'Connection no',
            'unit_owners': 'Unit Owners',
            'SubmitterName': 'Enumerator',
            'gb12_skip-gc01_skp2-d08':"Meter id"}, inplace=True)
            return df_c[['ID','Sub DMA','Unit Owners','Meter id']]


        else:
            df_c.rename(columns={
            'unique_form_id': 'ID',
            'b10_sub_dmi': 'Sub DMA',
            'gb12_skip-gc01_skp1-gc22': 'Customer no',
            'unit_owners': 'Unit Owners',
            'SubmitterName': 'Enumerator'}, inplace=True)
            
            return df_c[['ID','Sub DMA','Unit Owners','Enumerator']]
    
    @session.download(filename="data.csv")
    async def downloadData():
        x = input.sub_dma()
        filtered_df = df[df['b10_sub_dmi'] == int(x)]  # Apply the filter based on sub_dma

        if filtered_df.empty:
            yield "No data matching the filter criteria."
        else:
            csv_content = filtered_df.to_csv(index=False)
            yield csv_content
app = App(app_ui, server)
# end=time.time()
# diff=end-start
# print(diff)
