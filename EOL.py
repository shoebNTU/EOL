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

st.subheader("Upload an excel file")
temp = st.file_uploader(label='', type=['xlsx'])

if temp: 
    if st.button('Compute EOL',key=456):
        df_input = pd.read_excel(temp)
        df_input['capex'].fillna(0,inplace=True)
        df_input['interest_rate'].fillna(method='ffill',inplace=True)
        df_input['interest_rate'].fillna(0.0)
        df_input['interest_rate'] = df_input['interest_rate']/100.0
        df_input['annuity_factor'] = ((1-(1+df_input.interest_rate)**(-(df_input.index+1)))/df_input.interest_rate)
        df_input.annuity_factor.fillna(df_input.index.to_series()+1,inplace=True)
        opex_PV_cumsum = (df_input.opex/(1+df_input.interest_rate)**(df_input.index+1)).cumsum()
        capex_PV = (df_input.capex/(1+df_input.interest_rate)**(df_input.index+1))
        capex_PV.iloc[0] = df_input.capex.iloc[0]
        capex_PV_cumsum = capex_PV.cumsum()
        df_input['capex_PV'] = capex_PV
        df_input['capex_PV_cumsum'] = capex_PV_cumsum
        df_input['opex_PV'] = (df_input.opex/(1+df_input.interest_rate)**(df_input.index+1))
        df_input['opex_PV_cumsum'] = opex_PV_cumsum
        df_input['opex+capex'] = (capex_PV_cumsum+opex_PV_cumsum)
        df_input['opex_annualized'] = opex_PV_cumsum/df_input.annuity_factor
        df_input['capex_annualized'] = capex_PV_cumsum/df_input.annuity_factor
        try:
            df_input['salvage_PV'] = (df_input.salvage_value/(1+df_input.interest_rate)**(df_input.index+1))
        except:
            df_input['salvage_PV'] = 0.0
            
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
            st.write(df_input.style.format(subset=df_input.columns[df_input.columns.str.contains('pex|annuity|interest|eac',case=False)].tolist(),formatter="{:.2f}"))
            # st.write(df_input)
else:
    st.info("Please upload an excel file in the same format as the shared template")
