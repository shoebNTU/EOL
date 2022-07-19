import pandas as pd
import streamlit as st
import plotly.express as px
import io

st.set_option('deprecation.showfileUploaderEncoding', False)

with open('favicon.png', 'rb') as f:
    favicon = io.BytesIO(f.read())

st.set_page_config(page_title='EOL',
                   page_icon=favicon, 
                   layout='wide', 
                   initial_sidebar_state='expanded')

st.header('Economic Optimal Life')

# st.sidebar.title("Upload an excel file")
# temp = st.sidebar.file_uploader(label='', type=['xlsx'])

with st.expander('What is Economic Optimal Life (EOL)?',expanded=False):
    st.markdown("""
    Any asset will have the following cost components: 
    - Capital recovery cost (average first cost), computed from the first cost (purchase price) of the machine. 
    - Average operating and maintenance cost (O & M cost)
    - Total cost which is the sum of capital recovery cost (average first cost) and average maintenance cost.  
    A typical shape of each of the above costs with respect to life of the machine is shown in below Figure.
    """)

    st.image('./eol_colour.JPG',caption='Figure: Chart showing economic life',width=400)

    st.markdown("""From above Figure, it is clear that the capital recovery cost (average first cost) goes on decreasing with the life of the machine and the average operating and maintenance cost goes on increasing with the life of the machine. From the beginning, the total cost continues to decrease up to a particular life and then it starts increasing. The point where the total cost is _**minimum**_ is called the _**economic optimal life**_ of the machine. """)

with st.expander('How to use this app?',expanded=False):
    template_df = pd.read_excel('./EOL_template.xlsx')
    for col in template_df.columns:
        template_df[col] = template_df[col].astype(str)
        template_df[col] = template_df[col].str.replace('nan','')
        
    str_columns = str(template_df.columns.tolist())
    for i in """.'[]".""":
        str_columns = str_columns.replace(i,'')

    st.info(f"Please upload an excel file containing the following columns - **{str_columns}**. See an example template below - ")
    st.table(template_df)

st.subheader(f"Upload an excel file")
st.info(f"Please upload an excel file in the same format as the shared template (i.e. with columns - **{str_columns}**)  \n Please ensure the column names match the ones mentioned here.")
temp = st.file_uploader(label='', type=['xlsx'])

if temp: 
    df_input = pd.read_excel(temp)
    df_input.columns= df_input.columns.str.strip().str.lower()
    df_input['capex'].fillna(0.0,inplace=True)
    df_input['opex'].fillna(0.0,inplace=True)
    df_input['interest_rate'].fillna(method='ffill',inplace=True)
    df_input['interest_rate'].fillna(0.0)
    ccc1,_ = st.columns([1,4])
    with ccc1:
        interest = st.number_input(label='Please enter interest rate',min_value=0.0,max_value=100.0,step=0.01,value=df_input['interest_rate'][0])
    
    df_input['interest_rate'] = interest
    if st.button('Compute EOL',key=456):
        df_input['annuity_factor'] = ((1-(1+df_input.interest_rate*0.01)**(-(df_input.index+1)))/(df_input.interest_rate*0.01))
        df_input.annuity_factor.fillna(df_input.index.to_series()+1,inplace=True)
        opex_PV_cumsum = (df_input.opex/(1+df_input.interest_rate*0.01)**(df_input.index+1)).cumsum()
        capex_PV = (df_input.capex/(1+df_input.interest_rate*0.01)**(df_input.index))
        # capex_PV.iloc[0] = df_input.capex.iloc[0]
        capex_PV_cumsum = capex_PV.cumsum()
        df_input['capex_PV'] = capex_PV
        df_input['capex_PV_cumsum'] = capex_PV_cumsum
        df_input['opex_PV'] = (df_input.opex/(1+df_input.interest_rate*0.01)**(df_input.index+1))
        df_input['opex_PV_cumsum'] = opex_PV_cumsum
        df_input['opex+capex'] = (capex_PV_cumsum+opex_PV_cumsum)
        df_input['opex_annualized'] = opex_PV_cumsum/df_input.annuity_factor
        df_input['capex_annualized'] = capex_PV_cumsum/df_input.annuity_factor
        if 'salvage_value' not in df_input.columns.tolist():            
            df_input['salvage_value'] = 0.0     
        df_input.salvage_value.fillna(0.0,inplace=True)
        df_input['salvage_PV'] = (df_input.salvage_value/(1+df_input.interest_rate*0.01)**(df_input.index+1))
 

        df_input['EAC'] = ((capex_PV_cumsum+opex_PV_cumsum- df_input['salvage_PV'])/df_input.annuity_factor)  #+         

        fig=px.line(df_input,x=df_input.year,y=[df_input.opex,df_input.opex_annualized,df_input.capex,df_input.capex_annualized,df_input.EAC],markers=True)
        fig.update_yaxes(title='$')
        fig.add_vline(x=df_input['year'][df_input['EAC'].argmin()], line_width=3, line_dash="dash", line_color="olive",annotation_text='EOL')
        fig.add_annotation(                 x=0.5,
                                                y=1.1,
                                                showarrow=False,
                                                text=f"EOL is at year - {df_input['year'][df_input['EAC'].argmin()]}",
                                                textangle=0,
                                                xanchor='left',
                                                xref="paper",
                                                yref="paper")
        fig.update_layout(
            title="EOL",    
            legend_title="Costs",
            font=dict(
                family="Courier New, monospace",
                size=16,
                color="RebeccaPurple"
            ))
        st.plotly_chart (fig, use_container_width=True)

        with st.expander('Show calculation table',expanded=False):  
            @st.cache
            def convert_df(df):
                # IMPORTANT: Cache the conversion to prevent computation on every rerun
                return df.to_csv().encode('utf-8')
            csv = convert_df(df_input)

            st.download_button(
                label="Download calculation table as CSV",
                data=csv,
                file_name='output.csv',
                mime='text/csv',
            )         
            st.write(df_input.style.format(subset=df_input.columns[df_input.columns.str.contains('pex|annuity|interest|eac|salvage',case=False)].tolist(),formatter="{:.2f}"))

           

           
