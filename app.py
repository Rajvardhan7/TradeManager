"""
Created on Fri Jun 27 15:47:02 2025
@author: rajvardhan.rawat
"""
import pandas as pd
import numpy as np
import streamlit as st
import TradesDash
import PositionsSummary
import PNL
import os 

st.title("Trade Manager")
st.write("Visualize and Manage Trades")

uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        st.session_state.trade_data = pd.read_excel(uploaded_file)
        st.sidebar.success("File uploaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")
        
# Sidebar navigation
st.sidebar.title("📁 Trade Manager")
page = st.sidebar.radio("Select a Page", ["Trades Dashboard", "Positions Summary", "PNL"])

if page == "Trades Dashboard":
    TradesDash.Trades()
    
elif page == "Positions Summary":
    PositionsSummary.PositionsSummary()
    
elif page == "PNL":
    PNL.pnl()
    
    
    