"""
Created on Mon Jun 30 10:20:49 2025
@author: rajvardhan.rawat
"""
import pandas as pd
import numpy as np
import streamlit as st
import datetime
from datetime import datetime
import os
from io import BytesIO
        
# Importing Data and fetching the required columns
TradeJournal = pd.read_excel("Trade Journal Summarized.xlsx", sheet_name = 'TJ')    
TradeJournal = TradeJournal[['Date', 'Structure ','Structure Qty', 'How', 'L/S', 'Price (*100)', 'Why',
       'ALGO', 'Carried/New', 'Scalp OPP', 'Going Ag/Fav', 'Market Theme']]

# Filtering Only Structures
TradeJournal.dropna(subset=['Structure '], inplace = True)

# Fetching latest Date from TJ
latest_date = TradeJournal['Date'].iloc[-1]
latest_date = latest_date.strftime('%Y-%m-%d')

TradeJournal = TradeJournal[TradeJournal['Date'] == latest_date]

# making all structure names of same format and upper case
TradeJournal['Structure '] = TradeJournal['Structure '].astype(str).str.strip().str.upper()

"""d1 = TradeJournal[TradeJournal['Structure '] == 'SO3 Mar26 3M Fly']
d1 = d1[['Date', 'Structure ', 'Structure Qty', 'How', 'L/S',
       'Price (*100)',]]"""

def weighted_average_and_pos_count(dataframe, value, weight, pos):
    dataframe = dataframe[dataframe['L/S'] == pos]
    val = dataframe[value]
    wt = dataframe[weight]
    pos_count = sum(dataframe[weight])
    return pos_count, (val * wt).sum() / wt.sum()

def get_net_pos_price(new_df):
    if new_df['Net Position'] > 0: return new_df['Long wt avg price']
    elif new_df['Net Position'] < 0: return new_df['Short wt avg price']
    else:return 0
    
col_names = ['Structure', 'Long count', 'Long wt avg price', 'Short count', 'Short wt avg price']
new_df = pd.DataFrame(columns=col_names)

list_of_structures = TradeJournal['Structure '].unique()
structures = []; L_count_list = []; L_wt_avg_price_list = []; S_count_list = []; S_wt_avg_price_list = []
main_df = pd.DataFrame()

for i in list_of_structures:
    print(i)
    d = TradeJournal[TradeJournal['Structure '] == i]
    d = d[['Date', 'Structure ', 'Structure Qty', 'L/S', 'Price (*100)']]
    print(d.head())
    print("#######")
    
    main_df = pd.concat([main_df, d], ignore_index=True)
    
    L_count, L_wt_avg_price = weighted_average_and_pos_count(d, "Price (*100)", 'Structure Qty', 'L')
    S_count, S_wt_avg_price = weighted_average_and_pos_count(d, "Price (*100)", 'Structure Qty', 'S')
    
    structures.append(i)
    L_count_list.append(L_count)
    L_wt_avg_price_list.append(L_wt_avg_price)
    S_count_list.append(S_count)
    S_wt_avg_price_list.append(S_wt_avg_price)
    
new_df['Structure'] = structures
new_df['Long count'] = L_count_list
new_df['Long wt avg price'] = L_wt_avg_price_list
new_df['Short count'] = S_count_list
new_df['Short wt avg price'] = S_wt_avg_price_list
new_df['Net Position'] = new_df['Long count'] - new_df['Short count'] 

# Getting net position price
new_df['Net Position wt avg price'] = new_df.apply(get_net_pos_price, axis=1)
print(new_df)

# Sorting
# Define custom sort orders
month_year_order = {'MAR26': 1, 'JUN26': 2, 'SEP26': 3, 'DEC26': 4, 'MAR27': 5, 'JUN27': 6}
fly_order = {'FLY': 0, 'DFLY': 1}  

# Extract month-year and fly/dfly info
new_df['MonthYear'] = new_df['Structure'].str.extract(r'SO3 (\w{3}\d{2})')[0]
new_df['FlyType'] = new_df['Structure'].str.extract(r'(DFLY|FLY)')[0]

# Map to sort keys
new_df['MonthOrder'] = new_df['MonthYear'].map(month_year_order)
new_df['FlyOrder'] = new_df['FlyType'].map(fly_order)

# Sort and clean up
new_df_sorted = new_df.sort_values(by=['MonthOrder', 'FlyOrder']).drop(columns=['MonthYear', 'FlyType', 'MonthOrder', 'FlyOrder'])

#print(new_df_sorted)

# Heat and Settlement Difference Calculation
settlement_price = pd.read_excel("Trade Journal Summarized.xlsx", sheet_name = 'price for DB') 
final_df = pd.merge(new_df_sorted, settlement_price, on = "Structure")
print(final_df)
Tick_value = 17
Tick_size = 0.005
final_df['Heat'] = (final_df['Current Price'] - final_df['Net Position wt avg price']/100)*final_df['Net Position']*(Tick_value/Tick_size)
final_df['Settlement Difference'] = (final_df['Settlement Price'] - final_df['Current Price'])*final_df['Net Position']*(Tick_value/Tick_size)


# Function for Front in DB
def PositionsSummary():
    st.info("""View Your Structures Here""")
    st.write("Date: ", latest_date)
    # Creating RawFillbook
    Journal = TradeJournal.copy()
    
    # Create tabs
    tab1, tab2 = st.tabs(["TradeJournal", "🔍RRW Positions Summary"])
    
    # Tab 1: Show raw data
    with tab1:
        st.header("Trade Journal")
        
        # Add "All" to the top
        dates = sorted(Journal["Date"].unique())
        contracts = sorted(Journal["Structure "].unique())
        dates.insert(0, "All")
        contracts.insert(0, "All")

        col1, col2 = st.columns(2)

        with col1:
            selected_date = st.selectbox("Select Date", dates)
        with col2:
            selected_contract = st.selectbox("Select Contract", contracts)
            
        st.dataframe(Journal, use_container_width=True)
        
         # Apply filters
        df_filtered = Journal.copy()

        if selected_date != "All":
            df_filtered = df_filtered[df_filtered["Date"] == selected_date]

        if selected_contract != "All":
            df_filtered = df_filtered[df_filtered["Structure "] == selected_contract]

        st.success(f"🔍 Showing {len(df_filtered)} rows based on filters.")
        st.dataframe(df_filtered, use_container_width=True)
    
    # Tab 2: Show filtered data
    with tab2:
        st.header("Positions Summary")
        
        st.dataframe(final_df, use_container_width=True)
        
        output = BytesIO()
        final_df.to_excel(output, index=False, engine='xlsxwriter')
        excel_data = output.getvalue()
        
        # Create download button
        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name='exported_data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


