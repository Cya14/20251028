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

    # 🔹 원 그래프: Flight / Passengers / Cargo (마지막 달 기준)
    st.header("🔹 각 카테고리 이착륙 비율 (마지막 달 기준)")

    latest = df.iloc[-1]  # 마지막 행 사용

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
            tooltip=["Type", "Ratio"]
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
            tooltip=["Type", "Ratio"]
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
            tooltip=["Type", "Ratio"]
        )
        st.altair_chart(cargo_chart, use_container_width=True)

    # 🔹 이착륙 비율 + 횟수 비교 (라인 + 바)
    st.header("🔹 이착륙 비율 vs 횟수 비교 (Flight 예시)")
    chart_data_ratio = df[["year_month", "Flight arrival_ratio", "Flight departure_ratio"]].melt(
        "year_month", var_name="Type", value_name="Ratio")
    chart_data_count = df[["year_month", "Flight Arrival", "Flight Departure"]].melt(
        "year_month", var_name="Type", value_name="Count")

    # Line: 비율
    line = alt.Chart(chart_data_ratio).mark_line(point=True, color='blue').encode(
        x='year_month:N',
        y='Ratio:Q',
        color='Type:N',
        tooltip=['year_month', 'Type', 'Ratio']
    )

    # Bar: 횟수
    bar = alt.Chart(chart_data_count).mark_bar(opacity=0.4).encode(
        x='year_month:N',
        y='Count:Q',
        color='Type:N',
        tooltip=['year_month', 'Type', 'Count']
    )

    st.altair_chart((bar + line).interactive(), use_container_width=True)

else:
    st.info("👆 CSV 파일을 업로드하면 분석이 시작됩니다.")
