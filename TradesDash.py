"""
Created on Mon Jun 30 10:12:55 2025
@author: rajvardhan.rawat
"""

import pandas as pd
import numpy as np
import streamlit as st
import os 

def Trades():
    st.info("""View Your Trades Here""")

    # Creating RawFillbook
    raw_fillbook = pd.read_excel("fillbook1.xlsx")
    raw_fillbook = raw_fillbook[['Date', 'Time', 'Exchange', 'Contract', 'B/S', 
                                 'FillQty', 'Price', 'P/F']]
    
    # Excluding OUTS
    filtered_fillbook = raw_fillbook[raw_fillbook['Contract'].str.len()>10]
    
    
    # Create long tabs
    tab1, tab2 = st.tabs(["📄 Raw Fillbook", "🔍 Filtered Fillbook"])
    
    # Tab 1: Show raw data
    with tab1:
        st.header("📄 Raw Fillbook")
        st.dataframe(raw_fillbook, use_container_width=True)
    
    # Tab 2: Show filtered data
    with tab2:
        st.header("🔍 Filtered Fillbook (Contract name > 5 characters)")
        
        # Add "All" to the top
        dates = sorted(filtered_fillbook["Date"].unique())
        contracts = sorted(filtered_fillbook["Contract"].unique())
        dates.insert(0, "All")
        contracts.insert(0, "All")

        col1, col2 = st.columns(2)

        with col1:
            selected_date = st.selectbox("Select Date", dates)
        with col2:
            selected_contract = st.selectbox("Select Contract", contracts)
        
        st.dataframe(filtered_fillbook, use_container_width=True)
        
         # Apply filters
        df_filtered = filtered_fillbook.copy()

        if selected_date != "All":
            df_filtered = df_filtered[df_filtered["Date"] == selected_date]

        if selected_contract != "All":
            df_filtered = df_filtered[df_filtered["Contract"] == selected_contract]

        st.success(f"🔍 Showing {len(df_filtered)} rows based on filters.")
        st.dataframe(df_filtered, use_container_width=True)
        
       
        
 