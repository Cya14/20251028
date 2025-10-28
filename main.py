import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="인천공항 이착륙 비율 대시보드", layout="wide")

st.title("✈️ 인천공항 이착륙 비율 시각화")
st.markdown("CSV 파일을 업로드하면, 인천공항의 연도별 이착륙 비율을 시각적으로 보여줍니다.")

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

    # 🔹 year를 숫자로 변환 (변환 불가 시 NaN 처리)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df[df["year"].notna() & (df["year"] >= 2012)]

    # 🔹 월을 문자열로 변환
    df["month"] = df["month"].astype(str).str.zfill(2)
    df["year_month"] = df["year"].astype(int).astype(str) + "-" + df["month"]

    # 🔹 Flight 이착륙 비율 계산
    df["Flight total_flights"] = df["Flight Arrival"] + df["Flight Departure"]
    df["Flight arrival_ratio"] = df["Flight Arrival"] / df["Flight total_flights"]
    df["Flight departure_ratio"] = df["Flight Departure"] / df["Flight total_flights"]

    # 🔹 시각화 선택 옵션
    st.sidebar.header("⚙️ 그래프 설정")
    view_mode = st.sidebar.selectbox("표시할 데이터", ["Flight 이착륙 비율", "Flight 이착륙 횟수"])

    # 🔹 데이터 선택
    if view_mode == "Flight 이착륙 비율":
        chart_data = df[["year_month", "Flight arrival_ratio", "Flight departure_ratio"]].melt(
            "year_month", var_name="Type", value_name="Ratio"
        )
        y_title = "비율"
        color_scheme = "set2"
    else:
        chart_data = df[["year_month", "Flight Arrival", "Flight Departure"]].melt(
            "year_month", var_name="Type", value_name="Count"
        )
        y_title = "횟수"
        color_scheme = "category10"

    # 🔹 Altair 그래프 생성
    chart = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("year_month:N", title="연-월", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("value:Q", title=y_title),
            color=alt.Color("Type:N", title="구분", scale=alt.Scale(scheme=color_scheme)),
            tooltip=["year_month", "Type", "value"]
        )
        .properties(width=900, height=450)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)

    # 🔹 데이터 미리보기
    with st.expander("📄 데이터 미리보기"):
        st.dataframe(df.head())

else:
    st.info("👆 CSV 파일을 업로드하면 분석이 시작됩니다.")
