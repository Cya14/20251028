import streamlit as st
import pandas as pd
import altair as alt

# ----------------------------
# 1️⃣ 페이지 기본 설정
# ----------------------------
st.set_page_config(
    page_title="국가별 유형 분석",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 특정 유형이 높은 국가 TOP 10")
st.write("아래에서 분석할 **유형(Type)** 을 선택하세요.")

# ----------------------------
# 2️⃣ 예시 데이터 준비
# ----------------------------
data = {
    "Country": ["Korea", "Japan", "USA", "Germany", "France", "Brazil", "Canada", "India", "China", "UK",
                "Italy", "Spain", "Mexico", "Australia", "Russia"],
    "Type_A": [85, 78, 92, 80, 77, 70, 82, 88, 91, 75, 73, 69, 71, 79, 68],
    "Type_B": [45, 50, 60, 55, 70, 65, 48, 75, 68, 57, 62, 64, 66, 53, 59],
    "Type_C": [30, 40, 38, 45, 33, 28, 35, 50, 49, 29, 27, 31, 32, 36, 37]
}

df = pd.DataFrame(data)

# ----------------------------
# 3️⃣ 사용자 입력 (유형 선택)
# ----------------------------
type_list = [col for col in df.columns if col != "Country"]
selected_type = st.selectbox("유형을 선택하세요:", type_list)

# ----------------------------
# 4️⃣ 상위 10개 국가 필터링
# ----------------------------
top10 = (
    df[["Country", selected_type]]
    .sort_values(by=selected_type, ascending=False)
    .head(10)
)

# ----------------------------
# 5️⃣ Altair 시각화
# ----------------------------
chart = (
    alt.Chart(top10)
    .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8)
    .encode(
        x=alt.X(f"{selected_type}:Q", title=f"{selected_type} 점수"),
        y=alt.Y("Country:N", sort='-x', title="국가"),
        color=alt.Color(f"{selected_type}:Q", scale=alt.Scale(scheme="tealblues")),
        tooltip=["Country", selected_type]
    )
    .properties(
        width=700,
        height=400,
        title=f"🌟 {selected_type} 유형이 높은 국가 TOP 10"
    )
)

# ----------------------------
# 6️⃣ 결과 표시
# ----------------------------
st.altair_chart(chart, use_container_width=True)
st.dataframe(top10, use_container_width=True)
