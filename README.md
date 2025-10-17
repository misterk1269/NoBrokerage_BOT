# 🏠 NoBrokerage AI - Natural Language Property Search

NoBrokerage AI is a Streamlit-based web application that allows users to search real estate properties across India using **natural language queries**. The system intelligently parses queries like `"3BHK flat in Pune under ₹1.2 Cr"` and returns relevant property listings from CSV datasets.

---

## Live Demo

Try the app online here: [NoBrokerage AI - Live](https://misterk1269-nobrokerage-bot-app-6taze2.streamlit.app/)  

GitHub repository: [NoBrokerage BOT](https://github.com/misterk1269/NoBrokerage_BOT)

---

## Features

- **Natural Language Search**  
  Users can type queries in plain English to filter properties based on:
  - BHK (1BHK, 2BHK, etc.)
  - Budget (₹Lakhs / ₹Crores)
  - City or locality
  - Status (Ready to move / Under construction)
  - Property type (Apartment, Villa, Plot)
  - Furnishing type (Furnished, Semi-Furnished, Unfurnished)

- **Smart Filtering & Ranking**  
  - Filters properties using BHK, price, city, and furnishing.
  - Prioritizes ready-to-move properties in search results.
  - Sorts properties by relevance and price.

- **Property Cards**  
  Each property listing shows:
  - Project name
  - City and locality
  - BHK type
  - Price (formatted in ₹Lakh/₹Crore)
  - Carpet area
  - Status & furnishing
  - Amenities (Lift, Balcony, Bathroom, Security, Parking)

- **Summary Generation**  
  Provides a concise summary of search results, including count, price range, and key highlights.

---

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/misterk1269/NoBrokerage_BOT.git
   cd NoBrokerage_BOT
   
2. Install dependencies
   pip install -r requirements.txt
   
3. Run the Streamlit app
   streamlit run app.py

