import streamlit as st
st.set_page_config(page_title="NoBrokerage AI", layout="wide")  

from model import PropertySearchModel  # 👈 Make sure your model class is in model.py
import pandas as pd

# Load model once
@st.cache_resource
def load_model():
    return PropertySearchModel(
        project_csv="data/project.csv",
        address_csv="data/ProjectAddress.csv",
        config_csv="data/ProjectConfiguration.csv",
        variant_csv="data/ProjectConfigurationVariant.csv"
    )

model = load_model()

# UI
# st.set_page_config(page_title="NoBrokerage AI", layout="wide")
st.title("🏠 NoBrokerage Property Search AI")
st.markdown("Type your query like: `3BHK flat in Pune under ₹1.2 Cr`")

# Input
user_query = st.text_input("🔍 Enter your property search query")

if user_query:
    # Run model
    df_results, filters = model.search(user_query)
    summary = model.generate_summary(df_results, filters)

    # Show summary
    st.subheader("📊 Summary")
    st.write(summary)

    # Show cards
    st.subheader("📋 Property Listings")
    if df_results.empty:
        st.warning("No properties found.")
    else:
        df_results = df_results.sort_values(by="projectName", ascending=True).reset_index(drop=True)

        for i, row in df_results.iterrows():
            st.markdown("---")
            st.markdown(f"### #{i+1} — {row['projectName']}")
            city = row.get("city") or row.get("fullAddress") or ""
            locality = row.get("landmark") or row.get("locality") or ""

            # Clean up invalid or missing values
            if not isinstance(city, str) or city.strip().lower() in ["", "nan", "none", "unknown", "not mentioned"]:
                city = "Not mentioned"
            if not isinstance(locality, str) or locality.strip().lower() in ["", "nan", "none", "unknown", "not mentioned"]:
                locality = "Not mentioned"

            # Combine city and locality safely
            if city == "Not mentioned" and locality == "Not mentioned":
                location_display = "Location details coming soon"
            else:
                location_display = f"{city}, {locality}"

            st.markdown(f"📍 **{location_display}**")

            st.markdown(f"🏠 **{row['type']}** | 💰 ₹{row['price']/1e5:.2f} Lakh | 📐 {row['carpetArea']} sq.ft")
           
            status = row.get("status") or ""

            # # Clean missing values
            furnishing = row.get("furnishedType")  # <-- same as model CSV
            if pd.isna(furnishing) or str(furnishing).strip().lower() in ["", "nan", "none", "unknown", "n/a"]:
                furnishing = "Not mentioned"


            st.markdown(f"🔑 Status: `{status}` | 🛋️ `{furnishing}`")
            # st.markdown(f"✨ {row['bathroom']} Bathrooms, {row['balcony']} Balconies")
            # bathroom = row.get("bathroom", "N/A")
            # balcony = row.get("balcony", "N/A")
            # st.markdown(f"✨ {bathroom} Bathrooms, {balcony} Balconies")
            bathroom = row.get("bathrooms")
            balcony = row.get("balcony")

            bathroom = bathroom if pd.notna(bathroom) else "N/A"
            balcony = balcony if pd.notna(balcony) else "N/A"

            st.markdown(f"✨ {bathroom} Bathrooms, {balcony} Balconies")
            # st.markdown(f"[🔗 View Project](/project/{row['slug']})")
            st.markdown("🔗 Project details coming soon")
