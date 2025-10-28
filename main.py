import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="인천공항 이착륙 분석 대시보드", layout="wide")

st.title("✈️ 인천공항 이착륙 분석 대시보드")
st.markdown("CSV 파일을 업로드하면, Flight / Passengers / Cargo의 이착륙 비율과 횟수를 시각화합니다.")

# 🔹 파일 업로드
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # 🔹 정확한 열 확인
    expected_cols = [
        "year", "month",
        "Flight Arrival", "Flight Departure", "Flight Total",
        "Passengers Arrival", "Passengers Departure", "Passengers Total",
        "Cargo Arrival", "Cargo Departure", "Cargo Total"
    ]
    if list(df.columns) != expected_cols:
        st.error(f"❌ CSV 열이 정확히 다음과 같아야 합니다:\n{', '.join(expected_cols)}")
        st.stop()

    # 🔹 year 숫자로 변환
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df[df["year"].notna() & (df["year"] >= 2012)]

    # 🔹 월 문자열 변환
    df["month"] = df["month"].astype(str).str.zfill(2)
    df["year_month"] = df["year"].astype(int).astype(str) + "-" + df["month"]

    # 🔹 숫자 열 쉼표 제거 후 숫자 변환
    num_cols = ["Flight Arrival", "Flight Departure", "Flight Total",
                "Passengers Arrival", "Passengers Departure", "Passengers Total",
                "Cargo Arrival", "Cargo Departure", "Cargo Total"]
    for col in num_cols:
        df[col] = df[col].astype(str).str.replace(",", "").str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 🔹 비율 계산
    df["Flight total_flights"] = df["Flight Arrival"] + df["Flight Departure"]
    df["Flight arrival_ratio"] = df["Flight Arrival"] / df["Flight total_flights"]
    df["Flight departure_ratio"] = df["Flight Departure"] / df["Flight total_flights"]
    df.loc[df["Flight total_flights"] == 0, ["Flight arrival_ratio", "Flight departure_ratio"]] = 0

    df["Passengers total"] = df["Passengers Arrival"] + df["Passengers Departure"]
    df["Passengers arrival_ratio"] = df["Passengers Arrival"] / df["Passengers total"]
    df["Passengers departure_ratio"] = df["Passengers Departure"] / df["Passengers total"]
    df.loc[df["Passengers total"] == 0, ["Passengers arrival_ratio", "Passengers departure_ratio"]] = 0

    df["Cargo total"] = df["Cargo Arrival"] + df["Cargo Departure"]
    df["Cargo arrival_ratio"] = df["Cargo Arrival"] / df["Cargo total"]
    df["Cargo departure_ratio"] = df["Cargo Departure"] / df["Cargo total"]
    df.loc[df["Cargo total"] == 0, ["Cargo arrival_ratio", "Cargo departure_ratio"]] = 0

    # 🔹 CSV 전체 데이터 표 표시
    st.header("📄 CSV 전체 데이터")
    st.dataframe(df)

    # 🔹 기간 선택
    st.sidebar.header("📅 기간 선택")
    year_month_list = df["year_month"].tolist()
    start_period = st.sidebar.selectbox("시작 연-월", year_month_list, index=0)
    end_period = st.sidebar.selectbox("끝 연-월", year_month_list, index=len(year_month_list)-1)

    # 기간 필터링
    df_filtered = df[(df["year_month"] >= start_period) & (df["year_month"] <= end_period)]

    # 🔹 원 그래프: Flight / Passengers / Cargo (선택 기간 마지막 달 기준)
    st.header("🔹 각 카테고리 이착륙 비율 (선택 기간 마지막 달 기준)")
    latest = df_filtered.iloc[-1]  # 마지막 달 데이터

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Flight")
        flight_data = pd.DataFrame({
            'Type': ['Arrival', 'Departure'],
            'Ratio': [latest['Flight arrival_ratio'], latest['Flight departure_ratio']]
        })
        flight_chart = alt.Chart(flight_data).mark_arc().encode(
            theta=alt.Theta(field="Ratio", type="quantitative"),
            color=alt.Color(field="Type", type="nominal"),
            tooltip=["Type", alt.Tooltip("Ratio", format=".2%")]
        )
        st.altair_chart(flight_chart, use_container_width=True)

    with col2:
        st.subheader("Passengers")
        passenger_data = pd.DataFrame({
            'Type': ['Arrival', 'Departure'],
            'Ratio': [latest['Passengers arrival_ratio'], latest['Passengers departure_ratio']]
        })
        passenger_chart = alt.Chart(passenger_data).mark_arc().encode(
            theta=alt.Theta(field="Ratio", type="quantitative"),
            color=alt.Color(field="Type", type="nominal"),
            tooltip=["Type", alt.Tooltip("Ratio", format=".2%")]
        )
        st.altair_chart(passenger_chart, use_container_width=True)

    with col3:
        st.subheader("Cargo")
        cargo_data = pd.DataFrame({
            'Type': ['Arrival', 'Departure'],
            'Ratio': [latest['Cargo arrival_ratio'], latest['Cargo departure_ratio']]
        })
        cargo_chart = alt.Chart(cargo_data).mark_arc().encode(
            theta=alt.Theta(field="Ratio", type="quantitative"),
            color=alt.Color(field="Type", type="nominal"),
            tooltip=["Type", alt.Tooltip("Ratio", format=".2%")]
        )
        st.altair_chart(cargo_chart, use_container_width=True)

else:
    st.info("👆 CSV 파일을 업로드하면 분석이 시작됩니다.")
