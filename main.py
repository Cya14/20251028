import streamlit as st
import pandas as pd
import altair as alt
import io

# -------------------------------
# 페이지 기본 설정
# -------------------------------
st.set_page_config(page_title="인천공항 이·착륙 분석", layout="centered")
st.title("✈ 인천국제공항 이·착륙 통계 시각화")
st.caption("Altair 기반 자동 분석 (2012년 이후 데이터 기준)")

# -------------------------------
# 파일 업로드
# -------------------------------
uploaded = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])
if not uploaded:
    st.stop()

# CSV 읽기
try:
    df = pd.read_csv(uploaded)
except Exception:
    df = pd.read_csv(uploaded, encoding="cp949")

st.success("✅ 파일 불러오기 완료!")
st.dataframe(df.head())

# -------------------------------
# 컬럼 이름 자동 표준화
# -------------------------------
df.columns = [c.strip().lower() for c in df.columns]

expected_cols = ["year", "month", "flight", "passenger", "cargo", "arrive", "departure", "total"]
missing = [c for c in expected_cols if c not in df.columns]
if missing:
    st.error(f"❌ 다음 필수 컬럼이 누락되어 있습니다: {missing}")
    st.stop()

# -------------------------------
# 데이터 전처리
# -------------------------------
df = df.copy()
for c in ["year", "month"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# 2012년 이후 데이터만
df = df[df["year"] >= 2012].sort_values(["year", "month"])

# 숫자형 컬럼 변환
for c in ["flight", "passenger", "cargo", "arrive", "departure", "total"]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# 연월 문자열
df["년월"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)

# -------------------------------
# 시각화 1: 월별 이·착륙 추이
# -------------------------------
st.subheader("📈 월별 이·착륙 추이")

trend = (
    alt.Chart(df)
    .transform_fold(["arrive", "departure"], as_=["구분", "편수"])
    .mark_line(point=True)
    .encode(
        x=alt.X("년월:N", sort=None, title=None),
        y=alt.Y("편수:Q", title="편수"),
        color=alt.Color("구분:N", title="구분", scale=alt.Scale(scheme="set1")),
        tooltip=["year", "month", "구분", "편수"]
    )
    .properties(height=400, title="월별 이·착륙 추이 (2012년 이후)")
)
st.altair_chart(trend, use_container_width=True)

# -------------------------------
# 시각화 2: 최신 연도 이·착륙 비율 도넛
# -------------------------------
latest_year = int(df["year"].max())
st.subheader(f"🍩 {latest_year}년 이·착륙 비율")

latest = df[df["year"] == latest_year]
sum_arrive = latest["arrive"].sum()
sum_depart = latest["departure"].sum()

donut_df = pd.DataFrame({
    "구분": ["도착(arrive)", "출발(departure)"],
    "편수": [sum_arrive, sum_depart]
})

donut = (
    alt.Chart(donut_df)
    .mark_arc(innerRadius=60)
    .encode(
        theta="편수:Q",
        color=alt.Color("구분:N", scale=alt.Scale(scheme="set2")),
        tooltip=["구분", "편수"]
    )
    .properties(width=400, height=400, title=f"{latest_year}년 이·착륙 비율")
)
st.altair_chart(donut, use_container_width=True)
st.metric(f"{latest_year}년 총편수", f"{(sum_arrive + sum_depart):,}편")

# -------------------------------
# 시각화 3: 월별 총편수 막대 그래프
# -------------------------------
st.subheader(f"📊 {latest_year}년 월별 총편수")

bar = (
    alt.Chart(latest)
    .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
    .encode(
        x=alt.X("month:O", title="월"),
        y=alt.Y("total:Q", title="총편수"),
        color=alt.Color("month:O", scale=alt.Scale(scheme="blues")),
        tooltip=["year", "month", "total"]
    )
    .properties(height=400, title=f"{latest_year}년 월별 총편수")
)
st.altair_chart(bar, use_container_width=True)

# -------------------------------
# 데이터 확인 및 다운로드
# -------------------------------
with st.expander("📂 데이터 확인"):
    st.dataframe(df.tail())

csv_buf = df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "🔽 처리된 데이터 다운로드 (CSV)",
    data=csv_buf,
    file_name="incheon_airport_processed.csv",
    mime="text/csv"
)
