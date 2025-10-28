# app.py
import streamlit as st
import pandas as pd
import altair as alt
import io

st.set_page_config(page_title="인천공항 이·착륙 통계", layout="centered")
st.title("✈️ 인천국제공항 이·착륙 통계 자동 시각화")
st.caption("업로드하신 데이터에서 자동으로 분석합니다. (Altair 사용)")

# -----------------------
# 도움말: 설치 관련
# -----------------------
st.info(
    "참고: 스트림릿 클라우드에서 .xlsx 파일을 읽으려면 `openpyxl`이 필요합니다. "
    "추가 라이브러리 설치 없이 사용하려면 업로드 전에 Excel 파일을 CSV로 저장하신 뒤 업로드해주세요.\n\n"
    "원하시면 requirements.txt 에 `openpyxl` 한 줄 추가하는 예시도 알려드릴게요."
)

# -----------------------
# 파일 업로드
# -----------------------
uploaded = st.file_uploader("엑셀(.xlsx) 또는 CSV(.csv) 파일을 업로드하세요. (권장: CSV)", type=["xlsx", "csv"])

# also allow automatic local path (developer message said file uploaded to /mnt/data)
LOCAL_AUTO_PATH = "/mnt/data/By_TimeSeries_202001_202509.xlsx"
use_local = False
try:
    # show option to try reading local file if exists
    import os
    if os.path.exists(LOCAL_AUTO_PATH):
        if st.checkbox("서버에 업로드된 예시 파일을 사용합니다 (/mnt/data/By_TimeSeries_202001_202509.xlsx)", value=False):
            use_local = True
except Exception:
    pass

if uploaded is None and not use_local:
    st.stop()

# -----------------------
# 유틸: 유사 컬럼명 매핑
# -----------------------
def find_best_columns(df_cols):
    cols = [c.lower().strip() for c in df_cols]
    mapping = {}
    # possible names
    year_keys = ["연도", "년도", "year", "yr"]
    month_keys = ["월", "month", "mon", "m"]
    takeoff_keys = ["이륙편수", "이륙", "departure", "departures", "takeoff", "takeoffs", "출발편", "출발"]
    landing_keys = ["착륙편수", "착륙", "arrival", "arrivals", "landing", "landings", "도착편", "도착"]
    airport_keys = ["공항", "airport", "airport_name", "공항명", "공항 이름", "공항명(국문)"]

    def pick(keys):
        for k in keys:
            if k in cols:
                return df_cols[cols.index(k)]
        # try contains
        for i, c in enumerate(cols):
            for k in keys:
                if k in c:
                    return df_cols[i]
        return None

    mapping['year'] = pick(year_keys)
    mapping['month'] = pick(month_keys)
    mapping['takeoff'] = pick(takeoff_keys)
    mapping['landing'] = pick(landing_keys)
    mapping['airport'] = pick(airport_keys)
    return mapping

# -----------------------
# 데이터 로드
# -----------------------
def load_dataframe_from_uploaded(uploaded_file):
    name = uploaded_file.name
    raw = uploaded_file.read()
    # if csv
    if name.lower().endswith(".csv"):
        try:
            df = pd.read_csv(io.BytesIO(raw))
            return df, None
        except Exception as e:
            return None, f"CSV 읽기 오류: {e}"
    # if xlsx
    else:
        try:
            # Try reading with pandas (may raise missing dependency)
            df = pd.read_excel(io.BytesIO(raw))
            return df, None
        except Exception as e:
            return None, str(e)

def load_dataframe_from_path(path):
    try:
        if path.lower().endswith(".csv"):
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)
        return df, None
    except Exception as e:
        return None, str(e)

if use_local:
    df, err = load_dataframe_from_path(LOCAL_AUTO_PATH)
else:
    df, err = load_dataframe_from_uploaded(uploaded)

if df is None:
    st.error("파일을 읽는 중 오류가 발생했습니다.")
    st.write("오류 메시지:")
    st.code(err)
    st.warning(
        "해결 방법:\n\n"
        "1) 업로드 파일을 Excel(.xlsx)에서 CSV(.csv)로 저장한 뒤 다시 업로드\n"
        "2) Streamlit Cloud에 배포할 때 `requirements.txt`에 아래 한 줄 추가:\n\n"
        "   openpyxl\n\n"
        "   => 그러면 .xlsx 읽기가 정상 동작합니다."
    )
    st.stop()

st.success("파일을 정상적으로 불러왔습니다. (첫 5행 미리보기)")
st.dataframe(df.head())

# -----------------------
# 전처리: 컬럼 자동 매핑
# -----------------------
mapping = find_best_columns(df.columns.tolist())
missing = [k for k,v in mapping.items() if (k in ['year','month','takeoff','landing'] and v is None)]
if missing:
    st.warning(f"파일에 다음 필수 열이 없거나 자동으로 찾지 못했습니다: {missing}\n"
               "열 이름을 수동으로 지정해 주세요.")
    col1, col2, col3, col4, col5 = st.columns(5)
    year_col = col1.selectbox("연도 컬럼", options=[None]+list(df.columns), index=0)
    month_col = col2.selectbox("월 컬럼", options=[None]+list(df.columns), index=0)
    takeoff_col = col3.selectbox("이륙(출발) 컬럼", options=[None]+list(df.columns), index=0)
    landing_col = col4.selectbox("착륙(도착) 컬럼", options=[None]+list(df.columns), index=0)
    airport_col = col5.selectbox("공항(선택, 없으면 인천 필터 불가)", options=[None]+list(df.columns), index=0)
    # override mapping if user selected
    if year_col:
        mapping['year'] = year_col
    if month_col:
        mapping['month'] = month_col
    if takeoff_col:
        mapping['takeoff'] = takeoff_col
    if landing_col:
        mapping['landing'] = landing_col
    if airport_col:
        mapping['airport'] = airport_col

# final check
essential = ['year','month','takeoff','landing']
for e in essential:
    if mapping.get(e) is None:
        st.error(f"필수 열 `{e}` 을(를) 아직 지정하지 않았습니다. 앱을 종료합니다.")
        st.stop()

# rename for convenience
df = df.rename(columns={
    mapping['year']: "연도",
    mapping['month']: "월",
    mapping['takeoff']: "이륙편수",
    mapping['landing']: "착륙편수",
    **({mapping['airport']: "공항"} if mapping.get('airport') else {})
})

# If month or year are floats, cast to int
try:
    df['연도'] = df['연도'].astype(int)
except Exception:
    pass
try:
    df['월'] = df['월'].astype(int)
except Exception:
    pass

# Filter for Incheon if airport column exists
if '공항' in df.columns:
    # try to detect 인천 rows
    mask = df['공항'].astype(str).str.contains("인천|Incheon", case=False, na=False)
    if mask.sum() == 0:
        st.warning("업로드된 데이터에 '인천' 관련 공항 행이 발견되지 않았습니다. 전체 데이터로 시각화합니다.")
        df_incheon = df.copy()
    else:
        df_incheon = df[mask].copy()
else:
    df_incheon = df.copy()

# Ensure numeric
for c in ["이륙편수", "착륙편수"]:
    df_incheon[c] = pd.to_numeric(df_incheon[c], errors='coerce').fillna(0).astype(int)

df_incheon["총편수"] = df_incheon["이륙편수"] + df_incheon["착륙편수"]
df_incheon["년월"] = df_incheon["연도"].astype(str) + "년 " + df_incheon["월"].astype(str) + "월"

# Sort by 연도,월
df_incheon = df_incheon.sort_values(["연도","월"])

# -----------------------
# 시각화: 추이, 도넛, 막대
# -----------------------
st.subheader("1) 월별 이·착륙 추이")
trend = (
    alt.Chart(df_incheon)
    .transform_fold(["이륙편수","착륙편수"], as_=["구분","편수"])
    .mark_line(point=True)
    .encode(
        x=alt.X("년월:N", sort=None, title=None),
        y=alt.Y("편수:Q", title="편수"),
        color=alt.Color("구분:N", scale=alt.Scale(scheme="tableau10")),
        tooltip=["연도","월","구분","편수"]
    )
    .properties(height=420, title="월별 이·착륙 편수 추이")
)
st.altair_chart(trend, use_container_width=True)

# latest year donut
latest_year = int(df_incheon["연도"].max())
st.subheader(f"2) {latest_year}년 누적 이·착륙 비율")
latest_df = df_incheon[df_incheon["연도"] == latest_year]
takeoff_sum = int(latest_df["이륙편수"].sum())
landing_sum = int(latest_df["착륙편수"].sum())
donut_df = pd.DataFrame({"구분":["이륙편수","착륙편수"], "편수":[takeoff_sum, landing_sum]})
donut = (
    alt.Chart(donut_df)
    .mark_arc(innerRadius=60, outerRadius=120)
    .encode(
        theta="편수:Q",
        color=alt.Color("구분:N", scale=alt.Scale(scheme="set2")),
        tooltip=["구분","편수"]
    )
    .properties(width=420, height=420, title=f"{latest_year}년 누적 이·착륙 비율")
)
st.altair_chart(donut, use_container_width=True)
st.metric(f"{latest_year}년 총편수", f"{(takeoff_sum + landing_sum):,}편")

st.subheader(f"3) {latest_year}년 월별 총편수")
bar = (
    alt.Chart(latest_df)
    .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
    .encode(
        x=alt.X("월:O", title="월"),
        y=alt.Y("총편수:Q", title="총편수"),
        tooltip=["연도","월","총편수"],
        color=alt.Color("월:O", scale=alt.Scale(scheme="blues"))
    )
    .properties(height=420, title=f"{latest_year}년 월별 총편수")
)
st.altair_chart(bar, use_container_width=True)

# 데이터 테이블
with st.expander("원본 데이터 (인천 필터 적용 후)"):
    st.dataframe(df_incheon.style.format({"이륙편수":"{:,}","착륙편수":"{:,}","총편수":"{:,}"}))

# 다운로드: csv로 저장해서 제공
csv_buf = df_incheon.to_csv(index=False).encode('utf-8-sig')
st.download_button("🔽 인천 데이터 CSV로 다운로드", data=csv_buf, file_name="incheon_airport_summary.csv", mime="text/csv")
