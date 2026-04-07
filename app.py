import streamlit as st
import pandas as pd

# 1. SETUP
st.set_page_config(page_title="TDS Automation Portal", layout="centered")

@st.cache_data
def load_data():
    try:
        # Load the file
        df = pd.read_excel("TDS_Master_Rate_Table_v2.xlsx", sheet_name="Master Rate Table")
        # Clean hidden spaces
        df['Section'] = df['Section'].astype(str).str.strip()
        df['Payee Type'] = df['Payee Type'].astype(str).str.strip()
        df['Effective From'] = pd.to_datetime(df['Effective From'], dayfirst=True)
        df['Effective To'] = pd.to_datetime(df['Effective To'], dayfirst=True)
        return df
    except Exception as e:
        st.error(f"Excel Load Error: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🛡️ TDS Calculation Portal")
    st.info("Prototype v3 - Date & Payee Optimized")

    # 2. INPUTS
    col1, col2 = st.columns(2)
    with col1:
        section = st.selectbox("1. Select Section", options=sorted(df['Section'].unique()))
        amount = st.number_input("2. Transaction Amount (INR)", min_value=0.0)
        pay_date = st.date_input("3. Payment Date")

    with col2:
        pan_status = st.radio("4. PAN Available?", ["Yes", "No"])
        # Only show Payee Types that actually exist for the selected Section
        payee_options = sorted(df[df['Section'] == section]['Payee Type'].unique())
        payee_type = st.selectbox("5. Payee Category", options=payee_options)

    # 3. CALCULATION
    if st.button("Calculate TDS Now"):
        target_date = pd.to_datetime(pay_date)
        
        # Filter logic
        potential_rules = df[(df['Section'] == section) & (df['Payee Type'] == payee_type)]
        
        # Look for the date match
        rule = potential_rules[(potential_rules['Effective From'] <= target_date) & 
                               (potential_rules['Effective To'] >= target_date)]
        
        # Future-Proofing: If date is after March 2025, pick the latest row
        if rule.empty and not potential_rules.empty:
            rule = potential_rules.sort_values(by='Effective From', ascending=False).head(1)
            st.caption("✨ Using latest available rule for this date.")

        if not rule.empty:
            selected = rule.iloc[0]
            base_rate = float(selected['Rate of TDS (%)']) if str(selected['Rate of TDS (%)']) != 'Avg' else 0.0
            
            # Section 206AA
            final_rate = 20.0 if pan_status == "No" else base_rate
            threshold = float(selected['Threshold Amount (Rs)'])
            
            if str(selected['Rate of TDS (%)']) == "Avg":
                st.warning(f"Note: {selected['Notes']}")
            elif amount > threshold:
                tax = (amount * final_rate) / 100
                st.success(f"Deduct TDS: ₹{tax:,.2f}")
                st.metric("Applied Rate", f"{final_rate}%")
            else:
                st.warning(f"Below Threshold (₹{threshold}). No TDS required.")
        else:
            st.error("No matching rule found in Excel.")
