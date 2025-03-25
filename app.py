import streamlit as st
import pandas as pd
import pdfplumber
import tempfile

def extract_vendor_data(file, vendor_keywords):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 4:
                        continue
                    vendor = str(row[1] or "").strip()
                    currency = str(row[2] or "").strip()
                    amount_raw = str(row[3] or "").strip()

                    if any(v.lower() in vendor.lower() for v in vendor_keywords):
                        try:
                            amount_val = float(amount_raw.replace(",", "").replace(" ", ""))
                            records.append({
                                "Vendor Name": vendor,
                                "Currency": currency,
                                "Amount": amount_val,
                                "Source File": file.name
                            })
                        except ValueError:
                            continue
    return records

st.title("📄 Payment Extractor App")
st.markdown("Upload your PDF payment files and filter by vendor names (e.g., `goldcar`, `hertz`).")

vendor_input = st.text_input("Enter vendor keyword(s), separated by commas", "goldcar")
vendor_keywords = [v.strip() for v in vendor_input.split(",") if v.strip()]

uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files and vendor_keywords:
    all_records = []
    for uploaded_file in uploaded_files:
        all_records.extend(extract_vendor_data(uploaded_file, vendor_keywords))

    if all_records:
        df = pd.DataFrame(all_records)
        summary = df.groupby("Vendor Name").agg({"Amount": "sum", "Currency": "first"}).reset_index()

        st.success(f"✅ Found {len(df)} matching rows")
        st.dataframe(df)

        st.markdown("### 💰 Summary by Vendor")
        st.dataframe(summary)

        # Download Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            with pd.ExcelWriter(tmp.name, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Detailed Payments")
                summary.to_excel(writer, index=False, sheet_name="Summary by Vendor")

            st.download_button(
                label="📥 Download Excel Report",
                data=open(tmp.name, "rb"),
                file_name="payment_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("No matching vendor records found.")
