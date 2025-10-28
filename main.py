import streamlit as st
import pandas as pd
import altair as alt
import io

st.set_page_config(page_title="인천공항 이·착륙 비율", layout="centered")
st.title("✈ 인천국제공항 이·착륙 비율 시각화")
st.caption("업로드한 CSV 파일을 기반으로 Altair 시각화를 제공합니다. (별도 설치 불필요)")

uploaded = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])
if not uploaded:
    st.stop()

# 파일 읽기
try:
    df = pd.read_csv(uploaded)
except Exception:
    try:
        df = pd.read_csv(uploaded, encoding="cp949")
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        st.stop()

st.success("파일 불러오기 성공 ✅")
st.dataframe(df.head())

# ---------- 자동 컬럼 인식 ----------
def find_col(cols, keywords):
    for c in cols:
        for k in keywords:
            if k.lower() in c.lower():
                return c
    return None

cols = list(df.columns)

year_col = find_col(cols, ["연도", "년도", "year"])
month_col = find_col(cols, ["월", "month"])
takeoff_col = find_col(cols, ["이륙", "출발", "departure", "takeoff"])
landing_col = find_col(cols, ["착륙", "도착", "arrival", "landing"])
airport_col = find_col(cols, ["공항", "airport"])

missing = [x for x,y in {"연도":year_col, "월":month_col, "이륙":takeoff_col, "착륙":landing_col}.items() if y is None]
if missing:
    st.warning(f"다음 열을 자동으로 찾지 못했습니다: {missing}")
    year_col = st.selectbox("연도 컬럼 선택", cols, index=0 if year_col is None else cols.index(year_col))
    month_col = st.selectbox("월 컬럼 선택", cols, index=0 if month_col is None else cols.index(month_col))
    takeoff_col = st.selectbox("이륙(출발) 컬럼 선택", cols, index=0 if takeoff_col is None else cols.index(takeoff_col))
    landing_col = st.selectbox("착륙(도착) 컬럼 선택", cols, index=0 if landing_col is None else cols.index(landing_col))
    airport_col = st.selectbox("공항 컬럼 선택 (없으면 생략 가능)", [None]+cols)

df = df.rename(columns={
    year_col: "연도",
    month_col: "월",
    takeoff_col: "이륙편수",
    landing_col: "착륙편수",
})
if airport_col:
    df = df.rename(columns={airport_col: "공항"})

# ---------- 인천공항 필터 ----------
if "공항" in df.columns:
    mask = df["공항"].astype(str).str.contains("인천|Incheon", case=False, na=False)
    df = df[mask]
    st.info(f"인천공항 관련 데이터 {len(df)}건 추출 완료")

# ---------- 전처리 ----------
for col in ["연도", "월"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

for col in ["이륙편수", "착륙편수"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

df["총편수"] = df["이륙편수"] + df["착륙편수"]
df["년월"] = df["연도"].astype(str) + "-" + df["월"].astype(str)

# ---------- 시각화 ----------
st.subheader("📊 월별 이·착륙 추이")
trend = (
    alt.Chart(df)
    .transform_fold(["이륙편수","착륙편수"], as_=["구분","편수"])
    .mark_line(point=True)
    .encode(
        x=alt.X("년월:N", sort=None),
        y="편수:Q",
        color="구분:N",
        tooltip=["연도","월","구분","편수"]
    )
    .properties(height=400)
)
st.altair_chart(trend, use_container_width=True)

# ---------- 비율 도넛 ----------
latest_year = int(df["연도"].max())
latest_df = df[df["연도"] == latest_year]
takeoff_sum = latest_df["이륙편수"].sum()
landing_sum = latest_df["착륙편수"].sum()
donut_df = pd.DataFrame({
    "구분":["이륙편수","착륙편수"],
    "편수":[takeoff_sum, landing_sum]
})

st.subheader(f"🍩 {latest_year}년 이·착륙 비율")
donut = (
    alt.Chart(donut_df)
    .mark_arc(innerRadius=60)
    .encode(
        theta="편수:Q",
        color=alt.Color("구분:N", scale=alt.Scale(scheme="set2")),
        tooltip=["구분","편수"]
    )
)
st.altair_chart(donut, use_container_width=True)

# ---------- 월별 막대 ----------
st.subheader(f"📅 {latest_year}년 월별 총편수")
bar = (
    alt.Chart(latest_df)
    .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
    .encode(
        x="월:O",
        y="총편수:Q",
        color=alt.Color("월:O", scale=alt.Scale(scheme="blues")),
        tooltip=["월","총편수"]
    )
    .properties(height=400)
)
st.altair_chart(bar, use_container_width=True)
