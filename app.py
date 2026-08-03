import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Laptop Picker", page_icon="💻", layout="wide"
)

# Hide Streamlit's default component padding/gaps so the HTML hugs the screen
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        iframe {
            display: block;
            width: 100% !important;
            border: none !important;
        }
    </style>
""", unsafe_allow_html=True)

try:
    with open("laptop_ledger.html", "r", encoding="utf-8") as f:
        html_template = f.read()
    
    df = pd.read_csv("master_laptops.csv")
    data_json = df.to_json(orient="records")

    injection_script = f"""
    <script>
        window.preloadedRows = {data_json};
    </script>
    </body>
    """
    
    final_html = html_template.replace("</body>", injection_script)

    # Render with scrolling enabled
    st.components.v1.html(final_html, height=1200, scrolling=True)

except FileNotFoundError as e:
    st.error(f"⚠️ Missing file: {e}")