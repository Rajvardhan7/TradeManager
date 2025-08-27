# -*- coding: utf-8 -*-
"""
Created on Mon Jun 30 10:24:24 2025

@author: rajvardhan.rawat
"""
import pandas as pd
import numpy as np
import streamlit as st
from collections import deque
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

# Filtering Required columns
TradeJournal_filtered = TradeJournal[['Structure ','Structure Qty', 'L/S', 'Price (*100)']]

# Importing this sheet for Current Prices
mapper = pd.read_excel("Trade Journal Summarized.xlsx", sheet_name = 'mapper')

# Mapping current prices 
TradeJournal_filtered = pd.merge(TradeJournal_filtered, mapper[['Journal name', 'Current Price']],
    left_on='Structure ', right_on = 'Journal name', how = 'left')


TradeJournal_filtered['Price'] = TradeJournal_filtered['Price (*100)']/100

TradeJournal_filtered['BPS'] = abs(TradeJournal_filtered['Current Price']
                                   -TradeJournal_filtered['Price'])*100

TradeJournal_filtered['Ticks'] = TradeJournal_filtered['BPS']*2 # As 2 bps = 1 tick

TradeJournal_filtered['Profit/Loss'] = 'No Change'
for i in range(TradeJournal_filtered.shape[0]):
   if TradeJournal_filtered.at[i, 'L/S'] == 'S':
        if TradeJournal_filtered.at[i, 'Current Price'] < TradeJournal_filtered.at[i, 'Price']:
            TradeJournal_filtered.at[i, 'Profit/Loss'] = 'Profit'
        else:
            TradeJournal_filtered.at[i, 'Profit/Loss'] = 'Loss'
   elif TradeJournal_filtered.at[i, 'L/S'] == 'L':
        if TradeJournal_filtered.at[i, 'Current Price'] > TradeJournal_filtered.at[i, 'Price']:
            TradeJournal_filtered.at[i, 'Profit/Loss'] = 'Profit'
        else:
            TradeJournal_filtered.at[i, 'Profit/Loss'] = 'Loss'
            
Tick_value = 16.5 # In Dollars
TradeJournal_filtered['PNL'] = 0
TradeJournal_filtered['PNL/Lot'] = 0
for i in range(TradeJournal_filtered.shape[0]):
   if TradeJournal_filtered.at[i, 'Profit/Loss'] == 'Profit':
        TradeJournal_filtered.at[i, 'PNL'] =  TradeJournal_filtered.at[i, 'Ticks']*TradeJournal_filtered.at[i, 'Structure Qty']*Tick_value
        TradeJournal_filtered.at[i, 'PNL/Lot'] =  TradeJournal_filtered.at[i, 'Ticks']*Tick_value
   if TradeJournal_filtered.at[i, 'Profit/Loss'] == 'Loss':
        TradeJournal_filtered.at[i, 'PNL'] =  TradeJournal_filtered.at[i, 'Ticks']*TradeJournal_filtered.at[i, 'Structure Qty']*Tick_value*(-1)
        TradeJournal_filtered.at[i, 'PNL/Lot'] =  TradeJournal_filtered.at[i, 'Ticks']*Tick_value*(-1)
   if TradeJournal_filtered.at[i, 'Profit/Loss'] == 'No Change':
        TradeJournal_filtered.at[i, 'PNL'] =  0
        TradeJournal_filtered.at[i, 'PNL/Lot'] =  0
        
# TOTAL PNL ##

# Booked Plus Open Positions PNL:
Total_pnl = TradeJournal_filtered.groupby('Structure ', as_index=False)['PNL'].sum()
Total_pnl = Total_pnl.sort_values('PNL', ascending=False)

# Creating a DF to store calculated metrics
col_names = ['Structure', 'Total pnl', 'Booked pnl', 'Non Booked pnl', 'Open Positions Count', 'Open Positions Side', 'Open Positions']
pnl_df = pd.DataFrame(columns=col_names)

list_of_structures = TradeJournal['Structure '].unique()

for i in list_of_structures:
    print(i)
    structure_name = i
    d = TradeJournal_filtered[TradeJournal_filtered['Structure '] == structure_name]
    
    # BOOKED PNL ##
    
    # Step 1: Expand rows based on qty
    df_expanded = d.loc[d.index.repeat(d['Structure Qty'])].copy()
    df_expanded['Structure Qty'] = 1
    df_expanded.reset_index(drop=True, inplace=True)
    
    #if i == 'SO3 C MAR26 3 DFLY': print(df_expanded[['Structure ','Structure Qty', 'L/S', 'Price (*100)']])
        
    long_queue = deque()
    short_queue = deque()
    
    # Step 2: Iterate and populate queues
    for _, row in df_expanded.iterrows():
        row_dict = {"L/S": row["L/S"], "Price": round(row["Price"],4), "PNL/Lot": round(row["PNL/Lot"],2)}
        if row["L/S"] == "L":
            long_queue.append(row_dict)
        elif row["L/S"] == "S":
            short_queue.append(row_dict)
    
    # Step 3: Closing postions and adding pnls
    Net_pos_LS = "Zero"
    if len(long_queue) < len(short_queue): Net_pos_LS = "Short"
    if len(long_queue) > len(short_queue): Net_pos_LS = "Long"
    
    Net_pos_number = abs(len(long_queue) - len(short_queue))
    
    first_n_long_pnlperlot = [item["PNL/Lot"] for item in list(long_queue)[:min(len(short_queue), len(long_queue))]]
    first_n_short_pnlperlot = [item["PNL/Lot"] for item in list(short_queue)[:min(len(short_queue), len(long_queue))]]
    Booked_pnl = sum(first_n_short_pnlperlot) + sum(first_n_long_pnlperlot)
    
    # NON-BOOKED PNL ##
    Non_Booked_pnl = 0
    if Net_pos_LS == "Short": 
        non_booked_pnls = [ item["PNL/Lot"] for item in list(short_queue)[-Net_pos_number:] ]
        Non_Booked_pnl = sum(non_booked_pnls)
        Remaining_positions = [ item for item in list(short_queue)[-Net_pos_number:] ]
    if Net_pos_LS == "Long": 
        non_booked_pnls = [ item["PNL/Lot"] for item in list(long_queue)[-Net_pos_number:] ]
        Non_Booked_pnl = sum(non_booked_pnls)
        Remaining_positions = [ item for item in list(long_queue)[-Net_pos_number:] ]
    
    
    metrics_list = [structure_name, Total_pnl[Total_pnl['Structure '] == structure_name]['PNL'].iloc[0], Booked_pnl, Non_Booked_pnl, 
                    Net_pos_number, Net_pos_LS, pd.DataFrame(Remaining_positions)]
    
    pnl_df.loc[len(pnl_df)] = metrics_list



# Sorting
# Define custom sort orders

def Sorter(df):
    month_year_order = {'MAR26': 1, 'JUN26': 2, 'SEP26': 3, 'DEC26': 4, 'MAR27': 5, 'JUN27': 6}
    fly_order = {'FLY': 0, 'DFLY': 1}  
    
    # Extract month-year and fly/dfly info
    df['MonthYear'] = df['Structure'].str.extract(r'SO3 (\w{3}\d{2})')[0]
    df['FlyType'] = df['Structure'].str.extract(r'(DFLY|FLY)')[0]
    
    # Map to sort keys
    df['MonthOrder'] = df['MonthYear'].map(month_year_order)
    df['FlyOrder'] = df['FlyType'].map(fly_order)
    
    # Sort and clean up
    df_sorted = df.sort_values(by=['MonthOrder', 'FlyOrder']).drop(columns=
                    ['MonthYear', 'FlyType', 'MonthOrder', 'FlyOrder'])
    return df_sorted
        
# Sort and clean up
pnl_df_sorted = Sorter(pnl_df)


# Lots Distribution
distribution_df = pd.DataFrame(columns = ['Structure', 'Distribution DF', 'Distribution','Average Price', 'Open Pos Count', 'Open Pos Side'])
for i in range(pnl_df_sorted.shape[0]):
    d = pnl_df_sorted.at[i, 'Open Positions']
    Structure_name = pnl_df_sorted.at[i, 'Structure']
    
    if pnl_df_sorted.at[i, 'Open Positions Side'] == "Short":  pos_count = (-1)*pnl_df_sorted.at[i, 'Open Positions Count']
    else:  pos_count = pnl_df_sorted.at[i, 'Open Positions Count']
    pos_side = pnl_df_sorted.at[i, 'Open Positions Side']
   
    Lots_count = d['Price'].value_counts().reset_index()
    avg_price = round(d['Price'].mean(),4)
    formated_result = " | ".join(f"{row['count']} Lots @ {row['Price']}" for _, row in Lots_count.iterrows())
    if pos_count == 0: avg_price = 0; formated_result = 0
    
    result_list = [Structure_name, Lots_count, formated_result, avg_price, pos_count, pos_side]
    distribution_df.loc[len(distribution_df)] = result_list
    distribution_df = Sorter(distribution_df)
    


def pnl():
    st.info("""Analyze your pnl here""")
    st.write("pnl metrics as on Date: ", latest_date)
    st.write("Total PNL", round(Total_pnl['PNL'].sum(), 1))
    st.write("Total Booked PNL", round(pnl_df_sorted['Booked pnl'].sum(), 1))
    st.write("Total Non Booked PNL", round(pnl_df_sorted['Non Booked pnl'].sum(), 1))
    
    min_Booked_pnl_row = pnl_df_sorted.loc[pnl_df_sorted["Booked pnl"].idxmin()]
    st.write("Structure with max Booked Loss:", min_Booked_pnl_row["Structure"], min_Booked_pnl_row["Booked pnl"])
    max_Booked_pnl_row = pnl_df_sorted.loc[pnl_df_sorted["Non Booked pnl"].idxmin()]
    st.write("Structure with max Non-Booked Loss:", max_Booked_pnl_row["Structure"], max_Booked_pnl_row["Non Booked pnl"])
    
    # Creating RawFillbook
    Journal = TradeJournal.copy()
    
    # Create tabs
    tab1, tab2 = st.tabs([ "SO3 PNL Metrics", "Open Positions Distribution"])
    
    # Tab 1: Show raw data
    with tab1:
        st.header("PNL Metrics")
        
        st.dataframe(pnl_df_sorted, use_container_width=True)
        
        output_1 = BytesIO()
        pnl_df_sorted.to_excel(output_1, index=False, engine='xlsxwriter')
        excel_data_1 = output_1.getvalue()
        
        # Create download button
        st.download_button(
            label="Download Excel",
            data=excel_data_1,
            file_name='exported_data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key = "download_tab1")
        
    
    # Tab 2: Show filtered data
    with tab2:
        st.header("Open Positions and Average Price of Open lots")
        
        st.dataframe(distribution_df, use_container_width=True)
        
        output_2 = BytesIO()
        distribution_df.to_excel(output_2, index=False, engine='xlsxwriter')
        excel_data_2 = output_2.getvalue()
        
        # Create download button
        st.download_button(
            label="Download Excel",
            data=excel_data_2,
            file_name='exported_data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key = "download_tab2")

        


