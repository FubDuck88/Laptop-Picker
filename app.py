import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Laptop Picker", page_icon="💻", layout="wide"
)

try:
    with open("laptop_ledger.html", "r", encoding="utf-8") as f:
        html_template = f.read()
    
    df = pd.read_csv("master_laptops.csv")
    data_json = df.to_json(orient="records")

    # Only inject the preloaded data variable
    injection_script = f"""
    <script>
        window.preloadedRows = {data_json};
    </script>
    </body>
    """
    
    final_html = html_template.replace("</body>", injection_script)

    # Use a fixed height with scrolling=True so Streamlit handles the scrollbar naturally
    st.components.v1.html(final_html, height=1200, scrolling=True)

except FileNotFoundError as e:
    st.error(f"⚠️ Missing file: {e}")