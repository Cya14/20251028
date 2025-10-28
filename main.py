import streamlit as st
import pandas as pd
import altair as alt

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="인천공항 이착륙 통계", layout="centered")
st.title("✈️ 인천국제공항 이·착륙 통계 대시보드")
st.caption("엑셀 데이터를 업로드하면 자동으로 시각화됩니다 (Altair 기반).")

# -----------------------------
# 엑셀 파일 업로드
# -----------------------------
uploaded_file = st.file_uploader("📂 인천공항 이착륙 통계 엑셀 파일을 업로드하세요 (.xlsx)", type=["xlsx"])

if uploaded_file is None:
    st.info("예시 형식: 연도, 월, 이륙편수, 착륙편수 컬럼이 포함된 Excel 파일을 업로드해주세요.")
    st.stop()

# -----------------------------
# 데이터 불러오기
# -----------------------------
try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"파일을 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# -----------------------------
# 컬럼 확인 및 전처리
# -----------------------------
required_cols = {"연도", "월", "이륙편수", "착륙편수"}
if not required_cols.issubset(df.columns):
    st.error(f"파일에 {required_cols} 컬럼이 모두 포함되어야 합니다.")
    st.stop()

df = df.copy()
df["총편수"] = df["이륙편수"] + df["착륙편수"]
df["년월"] = df["연도"].astype(str) + "년 " + df["월"].astype(str) + "월"

# -----------------------------
# 그래프 1️⃣ : 월별 이착륙 추이
# -----------------------------
st.subheader("📈 월별 이·착륙 추이")

trend_chart = (
    alt.Chart(df)
    .transform_fold(["이륙편수", "착륙편수"], as_=["구분", "편수"])
    .mark_line(point=True)
    .encode(
        x=alt.X("년월:N", sort=None, title=None),
        y=alt.Y("편수:Q", title="편수"),
        color=alt.Color("구분:N", scale=alt.Scale(scheme="tableau10")),
        tooltip=["연도", "월", "구분", "편수"]
    )
    .properties(height=400, title="인천공항 월별 이착륙 추이")
)

st.altair_chart(trend_chart, use_container_width=True)

# -----------------------------
# 그래프 2️⃣ : 최근 연도 도넛 차트
# -----------------------------
latest_year = df["연도"].max()
latest_data = df[df["연도"] == latest_year]

st.subheader(f"🟢 {latest_year}년 이·착륙 비율")

donut_df = pd.DataFrame({
    "구분": ["이륙편수", "착륙편수"],
    "편수": [latest_data["이륙편수"].sum(), latest_data["착륙편수"].sum()]
})

donut_chart = (
    alt.Chart(donut_df)
    .mark_arc(innerRadius=60, outerRadius=120)
    .encode(
        theta="편수:Q",
        color=alt.Color("구분:N", scale=alt.Scale(scheme="set2")),
        tooltip=["구분", "편수"]
    )
    .properties(width=400, height=400, title=f"{latest_year}년 이·착륙 비율")
)

st.altair_chart(donut_chart, use_container_width=True)

st.metric(
    f"{latest_year}년 총편수",
    f"{(donut_df['편수'].sum()):,}편"
)

# -----------------------------
# 그래프 3️⃣ : 월별 총편수 막대그래프
# -----------------------------
st.subheader(f"📊 {latest_year}년 월별 총편수 추이")

bar_chart = (
    alt.Chart(latest_data)
    .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
    .encode(
        x=alt.X("월:O", title="월"),
        y=alt.Y("총편수:Q", title="총편수"),
        color=alt.Color("월:O", scale=alt.Scale(scheme="blues")),
        tooltip=["연도", "월", "총편수"]
    )
    .properties(height=400, title=f"{latest_year}년 월별 총편수 변화")
)

st.altair_chart(bar_chart, use_container_width=True)

# -----------------------------
# 데이터 표
# -----------------------------
with st.expander("📄 원본 데이터 보기"):
    st.dataframe(df.style.format({"이륙편수": "{:,}", "착륙편수": "{:,}", "총편수": "{:,}"}))
