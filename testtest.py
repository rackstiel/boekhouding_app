import streamlit as st

try:
    import gspread
    st.success("✅ gspread is succesvol geïmporteerd!")
except ImportError:
    st.error("❌ Fout: gspread kon niet worden geïmporteerd.")
