
import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="AccrueSmart Dashboard", layout="wide")
API = st.secrets.get("API_BASE","http://localhost:8011")

st.title("AccrueSmart — Revenue Recognition Dashboard")

tab1, tab2, tab3 = st.tabs(["Single Contract", "Contracts Repository", "Consolidated"])

with tab1:
    st.subheader("Allocate, Schedule, Disclose, and Post")
    colA, colB = st.columns(2)
    with colA:
        contract_id = st.text_input("Contract ID", "C-EX-STREAM")
        customer = st.text_input("Customer", "StreamCo")
        price = st.number_input("Transaction Price", 0.0, step=100.0, value=1200.0)
        commission = st.checkbox("Include Commission?", True)
        if commission:
            total_comm = st.number_input("Total Commission", 0.0, step=10.0, value=120.0)
            benefit_months = st.number_input("Benefit Months", 1, step=1, value=36)
            expedient = st.checkbox("≤1 year expedient (expense now)", False)
        vc = st.checkbox("Variable Consideration? (Returns/Loyalty)", True)
        returns_rate=0.0; loyalty_pct=0.0; loyalty_months=12; loyalty_breakage=0.0
        if vc:
            returns_rate = st.slider("Expected Returns Rate (on point-in-time POs)", 0.0, 0.9, 0.1, step=0.05)
            loyalty_pct = st.slider("Loyalty Allocation % of TP", 0.0, 0.5, 0.1, step=0.01)
            loyalty_months = st.number_input("Loyalty Recognition Months", 1, step=1, value=12)
            loyalty_breakage = st.slider("Loyalty Breakage Rate", 0.0, 0.9, 0.2, step=0.05)
    with colB:
        st.markdown("**Performance Obligations**")
        po_rows = st.session_state.get("po_rows",[
            {"po_id":"PO-1","description":"Device","ssp":900.0,"method":"point_in_time","start_date":"2025-01-01","end_date":""},
            {"po_id":"PO-2","description":"Support 36mo","ssp":300.0,"method":"straight_line","start_date":"2025-01-01","end_date":"2027-12-01"}
        ])
        edited = st.data_editor(pd.DataFrame(po_rows), num_rows="dynamic", use_container_width=True)
        st.session_state["po_rows"]=edited.to_dict(orient="records")

    if st.button("Allocate & Schedule"):
        payload = {
            "contract_id": contract_id, "customer": customer, "transaction_price": price,
            "pos": st.session_state["po_rows"],
            "commission": ({"total_commission":total_comm, "benefit_months":int(benefit_months), "practical_expedient_1yr":bool(expedient)} if commission else None),
            "variable": ({"returns_rate":returns_rate, "loyalty_pct":loyalty_pct, "loyalty_months":int(loyalty_months), "loyalty_breakage_rate":loyalty_breakage} if vc else None)
        }
        r = requests.post(f"{API}/contracts/allocate", json=payload); r.raise_for_status()
        data = r.json()
        st.success("Allocation complete")
        st.dataframe(pd.DataFrame(data["allocated"]))
        for poid, sched in data["schedules"].items():
            st.markdown(f"**Schedule — {poid}**")
            st.dataframe(pd.DataFrame(list(sched.items()), columns=["Period","Revenue"]).set_index("Period"))
        if data.get("commission_schedule"):
            st.markdown("**Commission Amortization**")
            st.dataframe(pd.DataFrame(list(data["commission_schedule"].items()), columns=["Period","Expense"]).set_index("Period"))
        if data.get("adjustments"):
            st.markdown("**Variable Consideration / Loyalty Adjustments**")
            st.json(data["adjustments"])

        if st.button("Save Contract"):
            s = requests.post(f"{API}/contracts/save", json=payload); s.raise_for_status()
            st.info("Saved to repository")

        if st.button("Generate Disclosure (PDF)"):
            r = requests.post(f"{API}/reports/disclosure", json=payload); r.raise_for_status()
            st.write("PDF written on backend:", r.json()["pdf_path"])

        if st.button("Post Journals"):
            r = requests.post(f"{API}/post/journal", json=payload); r.raise_for_status()
            st.write("Journal CSV:", r.json()["journal_csv"])

with tab2:
    st.subheader("Contracts Repository")
    r = requests.get(f"{API}/contracts/list")
    if r.ok and r.json():
        df = pd.DataFrame(r.json())
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No contracts saved yet. Use the Single Contract tab to save one.")

with tab3:
    st.subheader("Consolidated Disclosures")
    r = requests.get(f"{API}/contracts/list")
    ids = [c["contract_id"] for c in r.json()] if r.ok else []
    selected = st.multiselect("Contracts", ids, default=ids)
    if st.button("Generate Consolidated CSV"):
        r = requests.post(f"{API}/reports/disclosure/consolidated", json=selected); r.raise_for_status()
        out = r.json()
        st.success("Consolidated CSV generated on backend")
        st.write("CSV Path:", out["csv_path"])
        if out.get("notes"):
            st.markdown("**Notes (Variable Consideration & Loyalty by contract)**")
            st.json(out["notes"])
