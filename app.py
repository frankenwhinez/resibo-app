import streamlit as st
import pandas as pd
import os

# 1. Setup the Title
st.title("📊 Resibo: My Expense Tracker")

# 2. The "Brain" Logic (CSV Storage)
DATA_FILE = "expenses.csv"

# Check if the file exists, if not, create a blank one
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["Date", "Category", "Amount", "Note"])
    df.to_csv(DATA_FILE, index=False)

# 3. Simple Form to Add Data
with st.form("add_expense"):
    date = st.date_input("When?")
    cat = st.selectbox("Category", ["Food", "Transport", "Bills", "Fun"])
    amt = st.number_input("How much?", min_value=0.0)
    note = st.text_input("What for?")
    submit = st.form_submit_button("Save to Brain")

if submit:
    new_data = pd.DataFrame([[date, cat, amt, note]], columns=["Date", "Category", "Amount", "Note"])
    new_data.to_csv(DATA_FILE, mode='a', header=False, index=False)
    st.success("Saved! Refresh the page to see it in the table below.")

# 4. Show the History
st.subheader("History")
history_df = pd.read_csv(DATA_FILE)
st.dataframe(history_df)
