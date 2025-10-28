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

    # 🔹 숫자 열 변환
    num_cols = ["Flight Arrival", "Flight Departure", "Flight Total",
                "Passengers Arrival", "Passengers Departure", "Passengers Total",
                "Cargo Arrival", "Cargo Departure", "Cargo Total"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.strip(), errors="coerce").fillna(0)

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

    # 🔹 CSV 전체 데이터 표
    st.header("📄 CSV 전체 데이터")
    st.dataframe(df)

    # 🔹 기간 선택
    st.sidebar.header("📅 기간 선택")
    year_month_list = df["year_month"].tolist()
    start_period = st.sidebar.selectbox("시작 연-월", year_month_list, index=0)
    end_period = st.sidebar.selectbox("끝 연-월", year_month_list, index=len(year_month_list)-1)

    # 기간 필터링
    df_filtered = df[(df["year_month"] >= start_period) & (df["year_month"] <= end_period)]

    # 🔹 Line chart (기존)
    st.header("🔹 이착륙 비율 / 횟수 비교")
    st.sidebar.header("⚙️ 그래프 설정")
    category = st.sidebar.selectbox("데이터 종류", ["Flight", "Passengers", "Cargo"])
    view_mode = st.sidebar.selectbox("표시할 데이터", ["이착륙 비율", "이착륙 횟수"])

    if category == "Flight":
        if view_mode == "이착륙 비율":
            chart_data = df_filtered[["year_month", "Flight arrival_ratio", "Flight departure_ratio"]].melt(
                "year_month", var_name="Type", value_name="Ratio")
            y_field = "Ratio"
            y_title = "비율"
            color_scheme = "set2"
        else:
            chart_data = df_filtered[["year_month", "Flight Arrival", "Flight Departure"]].melt(
                "year_month", var_name="Type", value_name="Count")
            y_field = "Count"
            y_title = "횟수"
            color_scheme = "category10"
    elif category == "Passengers":
        if view_mode == "이착륙 비율":
            chart_data = df_filtered[["year_month", "Passengers arrival_ratio", "Passengers departure_ratio"]].melt(
                "year_month", var_name="Type", value_name="Ratio")
            y_field = "Ratio"
            y_title = "비율"
            color_scheme = "set2"
        else:
            chart_data = df_filtered[["year_month", "Passengers Arrival", "Passengers Departure"]].melt(
                "year_month", var_name="Type", value_name="Count")
            y_field = "Count"
            y_title = "횟수"
            color_scheme = "category10"
    else:  # Cargo
        if view_mode == "이착륙 비율":
            chart_data = df_filtered[["year_month", "Cargo arrival_ratio", "Cargo departure_ratio"]].melt(
                "year_month", var_name="Type", value_name="Ratio")
            y_field = "Ratio"
            y_title = "비율"
            color_scheme = "set2"
        else:
            chart_data = df_filtered[["year_month", "Cargo Arrival", "Cargo Departure"]].melt(
                "year_month", var_name="Type", value_name="Count")
            y_field = "Count"
            y_title = "횟수"
            color_scheme = "category10"

    line_chart = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("year_month:N", title="연-월", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y(f"{y_field}:Q", title=y_title),
            color=alt.Color("Type:N", title="구분", scale=alt.Scale(scheme=color_scheme)),
            tooltip=["year_month", "Type", y_field]
        )
        .properties(width=900, height=450)
        .interactive()
    )
    st.altair_chart(line_chart, use_container_width=True)

    # 🔹 마지막 달 기준 원 그래프
    st.header("🔹 마지막 달 기준 원 그래프 (이착륙 비율)")
    latest = df_filtered.iloc[-1]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Flight")
        flight_data = pd.DataFrame({
            'Type': ['Arrival', 'Departure'],
            'Ratio': [latest['Flight arrival_ratio'], latest['Flight departure_ratio']]
        })
        st.altair_chart(
            alt.Chart(flight_data).mark_arc().encode(
                theta=alt.Theta(field="Ratio", type="quantitative"),
                color=alt.Color(field="Type", type="nominal"),
                tooltip=["Type", alt.Tooltip("Ratio", format=".2%")]
            ),
            use_container_width=True
        )

    with col2:
        st.subheader("Passengers")
        passenger_data = pd.DataFrame({
            'Type': ['Arrival', 'Departure'],
            'Ratio': [latest['Passengers arrival_ratio'], latest['Passengers departure_ratio']]
        })
        st.altair_chart(
            alt.Chart(passenger_data).mark_arc().encode(
                theta=alt.Theta(field="Ratio", type="quantitative"),
                color=alt.Color(field="Type", type="nominal"),
                tooltip=["Type", alt.Tooltip("Ratio", format=".2%")]
            ),
            use_container_width=True
        )

    with col3:
        st.subheader("Cargo")
        cargo_data = pd.DataFrame({
            'Type': ['Arrival', 'Departure'],
            'Ratio': [latest['Cargo arrival_ratio'], latest['Cargo departure_ratio']]
        })
        st.altair_chart(
            alt.Chart(cargo_data).mark_arc().encode(
                theta=alt.Theta(field="Ratio", type="quantitative"),
                color=alt.Color(field="Type", type="nominal"),
                tooltip=["Type", alt.Tooltip("Ratio", format=".2%")]
            ),
            use_container_width=True
        )

    # 🔹 선택 기간 평균 기준 원 그래프
    st.header("🔹 선택 기간 전체 월 평균 기준 원 그래프 (이착륙 비율)")

    # Flight 평균
    flight_avg = df_filtered[["Flight arrival_ratio", "Flight departure_ratio"]].mean()
    flight_avg_data = pd.DataFrame({
        'Type': ['Arrival', 'Departure'],
        'Ratio': [flight_avg['Flight arrival_ratio'], flight_avg['Flight departure_ratio']]
    })
    st.subheader("Flight")
    st.altair_chart(
        alt.Chart(flight_avg_data).mark_arc().encode(
            theta=alt.Theta(field="Ratio", type="quantitative"),
            color=alt.Color(field="Type", type="nominal"),
            tooltip=["Type", alt.Tooltip("Ratio", format=".2%")]
        ),
        use_container_width=True
    )

    # Passengers 평균
    passenger_avg = df_filtered[["Passengers arrival_ratio", "Passengers departure_ratio"]].mean()
    passenger_avg_data = pd.DataFrame({
        'Type': ['Arrival', 'Departure'],
        'Ratio': [passenger_avg['Passengers arrival_ratio'], passenger_avg['Passengers departure_ratio']]
    })
    st.subheader("Passengers")
    st.altair_chart(
        alt.Chart(passenger_avg_data).mark_arc().encode(
            theta=alt.Theta(field="Ratio", type="quantitative"),
            color=alt.Color(field="Type", type="nominal"),
            tooltip=["Type", alt.Tooltip("Ratio", format=".2%")]
        ),
        use_container_width=True
    )

    # Cargo 평균
    cargo_avg = df_filtered[["Cargo arrival_ratio", "Cargo departure_ratio"]].mean()
    cargo_avg_data = pd.DataFrame({
        'Type': ['Arrival', 'Departure'],
        'Ratio': [cargo_avg['Cargo arrival_ratio'], cargo_avg['Cargo departure_ratio']]
    })
    st.subheader("Cargo")
    st.altair_chart(
        alt.Chart(cargo_avg_data).mark_arc().encode(
            theta=alt.Theta(field="Ratio", type="quantitative"),
            color=alt.Color(field="Type", type="nominal"),
            tooltip=["Type", alt.Tooltip("Ratio", format=".2%")]
        ),
        use_container_width=True
    )

else:
    st.info("👆 CSV 파일을 업로드하면 분석이 시작됩니다.")
