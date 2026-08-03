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

    # Notice the double curly braces {{ and }} for JavaScript code blocks,
    # and single curly braces {data_json} for the Python variable injection.
    injection_script = f"""
    <script>
        window.preloadedRows = {data_json};
        
        // Auto-resize iframe height dynamically
        function sendHeight() {{
            const height = document.body.scrollHeight;
            window.parent.postMessage({{isStreamlitMessage: true, type: 'streamlit:setFrameHeight', height: height}}, '*');
        }}
        window.addEventListener('load', sendHeight);
        window.addEventListener('resize', sendHeight);
        setTimeout(sendHeight, 500);
        setTimeout(sendHeight, 1500);
    </script>
    </body>
    """
    
    final_html = html_template.replace("</body>", injection_script)

    st.components.v1.html(final_html, height=800, scrolling=False)

except FileNotFoundError as e:
    st.error(f"⚠️ Missing file: {e}")