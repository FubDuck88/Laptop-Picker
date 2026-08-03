import pandas as pd
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="Malaysia Laptop Price Aggregator", page_icon="💻", layout="wide"
)

st.title("💻 Malaysia Laptop Price Aggregator")
st.markdown("Live price and specification tracker for the Malaysian market.")


# 2. Load and Clean Data
@st.cache_data
def load_data():
  try:
    df = pd.read_csv("master_laptops.csv")
    return df
  except FileNotFoundError:
    return pd.DataFrame()


df = load_data()

if df.empty:
  st.error(
      "⚠️ `master_laptops.csv` not found. Make sure your merger script has"
      " generated it in this folder."
  )
else:
  # 3. Sidebar Search / Filters
  st.sidebar.header("Filter Laptops")
  search_query = st.sidebar.text_input("Search Model or CPU", "")

  filtered_df = df.copy()
  if search_query:
    filtered_df = filtered_df[
        filtered_df.astype(str)
        .apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
    ]

  # 4. Metrics & Table Display
  col1, col2 = st.columns(2)
  col1.metric("Total Models Found", len(filtered_df))

  st.dataframe(filtered_df, use_container_width=True, hide_index=True)