import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import os

# ------------------------------------------------------------------------------
# 1. 설정 및 폰트 (한글 깨짐 방지)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="기온 데이터 분석 앱", layout="wide")

# 스트림릿 클라우드/로컬 환경에 따라 한글 폰트 설정
# (Linux 환경인 Streamlit Cloud에서는 NanumGothic을, 로컬에서는 시스템 폰트 시도)
import platform
system_name = platform.system()

if system_name == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif system_name == 'Darwin':  # Mac
    plt.rc('font', family='AppleGothic')
else:  # Linux (Streamlit Cloud 등)
    # 폰트 설치가 안 되어 있을 수 있으므로 나눔폰트 설치 안내가 필요할 수 있음
    # 여기서는 기본적으로 설치된 폰트를 찾거나 fallback 함
    plt.rc('font', family='NanumGothic')

plt.rc('axes', unicode_minus=False)

# ------------------------------------------------------------------------------
# 2. 데이터 로드 함수
# ------------------------------------------------------------------------------
@st.cache_data
def load_data(file):
    # KMA 데이터는 보통 상단에 메타데이터가 7줄 정도 있고, 실제 헤더는 그 아래에 있음
    # 인코딩은 utf-8 또는 cp949
    try:
        df = pd.read_csv(file, encoding='utf-8', header=7)
    except:
        file.seek(0)
        df = pd.read_csv(file, encoding='cp949', header=7)
    
    # 컬럼명 정리 (공백 제거)
    df.columns = [c.strip() for c in df.columns]
    
    # 날짜 컬럼을 datetime으로 변환
    df['날짜'] = pd.to_datetime(df['날짜'])
    
    # 필요한 컬럼만 선택 및 이름 변경 (편의상)
    # 실제 컬럼명: 날짜, 지점, 평균기온(℃), 최저기온(℃), 최고기온(℃)
    rename_dict = {
        '평균기온(℃)': '평균기온',
        '최저기온(℃)': '최저기온',
        '최고기온(℃)': '최고기온'
    }
    df.rename(columns=rename_dict, inplace=True)
    return df

# ------------------------------------------------------------------------------
# 3. 수능 날짜 데이터 (1994~2025)
# ------------------------------------------------------------------------------
# 실제 시험이 치러진 날짜 (연기된 날짜 반영: 2017 포항지진, 2020 코로나)
suneung_dates = {
    1994: '1994-11-23', 1995: '1995-11-22', 1996: '1996-11-13', 1997: '1997-11-19',
    1998: '1998-11-18', 1999: '1999-11-17', 2000: '2000-11-15', 2001: '2001-11-07',
    2002: '2002-11-06', 2003: '2003-11-05', 2004: '2004-11-17', 2005: '2005-11-23',
    2006: '2006-11-16', 2007: '2007-11-15', 2008: '2008-11-13', 2009: '2009-11-12',
    2010: '2010-11-18', 2011: '2011-11-10', 2012: '2012-11-08', 2013: '2013-11-07',
    2014: '2014-11-13', 2015: '2015-11-12', 2016: '2016-11-17', 
    2017: '2017-11-23', # 지진으로 연기
    2018: '2018-11-15', 2019: '2019-11-14', 
    2020: '2020-12-03', # 코로나로 연기
    2021: '2021-11-18', 2022: '2022-11-17', 2023: '2023-11-16', 2024: '2024-11-14',
    2025: '2025-11-13'
}

# ------------------------------------------------------------------------------
# 4. 메인 UI 및 로직
# ------------------------------------------------------------------------------
st.title("📅 기온 데이터 분석 대시보드")

# 사이드바: 파일 업로드
st.sidebar.header("데이터 설정")
uploaded_file = st.sidebar.file_uploader("기상청 데이터 업로드 (CSV)", type=['csv'])

# 기본 파일 설정 (업로드 없으면 로컬 기본 파일 사용)
default_file = 'ta_20260109154427.csv'
data_source = None

if uploaded_file is not None:
    data_source = uploaded_file
elif os.path.exists(default_file):
    data_source = default_file
else:
    st.error("기본 데이터 파일이 없으며 업로드된 파일도 없습니다.")
    st.stop()

# 데이터 로드
df = load_data(data_source)
st.sidebar.success(f"데이터 로드 완료: {len(df):,} 건")

# 탭 구성
tab1, tab2 = st.tabs(["📊 특정 날짜 비교 분석", "🎓 수능일 기온 분석"])

# --- Tab 1: 특정 날짜 비교 ---
with tab1:
    st.header("특정 날짜 기온 비교")
    st.markdown("선택한 날짜가 과거 같은 날짜들에 비해 얼마나 춥거나 더웠는지 비교합니다.")
    
    # 날짜 선택 (기본값: 데이터의 가장 최근 날짜)
    last_date = df['날짜'].max()
    selected_date = st.date_input("날짜를 선택하세요", value=last_date, 
                                  min_value=df['날짜'].min(), max_value=last_date)
    
    # 선택된 날짜의 월, 일 추출
    sel_month = selected_date.month
    sel_day = selected_date.day
    
    # 같은 월/일 데이터 필터링 (과거 데이터)
    # 윤년(2/29) 처리는 2월 29일을 선택했을 때만 2/29끼리 비교하도록 함
    history_df = df[(df['날짜'].dt.month == sel_month) & (df['날짜'].dt.day == sel_day)].copy()
    
    # 선택된 연도의 데이터 찾기
    current_year_data = history_df[history_df['날짜'].dt.year == selected_date.year]
    
    if current_year_data.empty:
        st.warning("선택한 날짜의 데이터가 존재하지 않습니다.")
    else:
        cur_temp = current_year_data.iloc[0]['평균기온']
        cur_min = current_year_data.iloc[0]['최저기온']
        cur_max = current_year_data.iloc[0]['최고기온']
        
        # 과거 평균 계산 (선택된 연도 제외)
        past_df = history_df[history_df['날짜'].dt.year != selected_date.year]
        avg_temp_hist = past_df['평균기온'].mean()
        
        # 비교 텍스트 출력
        diff = cur_temp - avg_temp_hist
        st.metric(
            label=f"{selected_date.strftime('%Y-%m-%d')} 평균기온",
            value=f"{cur_temp} ℃",
            delta=f"{diff:.1f} ℃ (역대 동월동일 평균 대비)"
        )
        
        # 그래프 그리기
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(history_df['평균기온'], kde=True, ax=ax, color='skyblue', label='역대 분포')
        # 선택된 날짜 위치 표시
        ax.axvline(cur_temp, color='red', linestyle='--', linewidth=2, label=f'선택일({selected_date.year})')
        ax.axvline(avg_temp_hist, color='green', linestyle='-', linewidth=2, label='역대 평균')
        
        ax.set_title(f"{sel_month}월 {sel_day}일의 역대 평균기온 분포")
        ax.set_xlabel("평균기온 (℃)")
        ax.legend()
        st.pyplot(fig)
        
        # 순위 정보
        rank = history_df['평균기온'].rank(ascending=False, method='min') # 높은 순
        cur_rank = rank[history_df['날짜'].dt.year == selected_date.year].iloc[0]
        total_count = len(history_df)
        
        st.info(f"선택하신 날은 {total_count}번의 {sel_month}월 {sel_day}일 중 {int(cur_rank)}번째로 더운 날이었습니다. (1위가 가장 더움)")

# --- Tab 2: 수능일 분석 ---
with tab2:
    st.header("1994~2025 수능일 기온 분석")
    
    # 수능 데이터 추출
    suneung_data = []
    
    for year, date_str in suneung_dates.items():
        # 데이터에서 해당 날짜 찾기
        mask = (df['날짜'] == date_str)
        if mask.any():
            row = df[mask].iloc[0]
            suneung_data.append({
                '시험년도': year,
                '날짜': date_str,
                '평균기온': row['평균기온'],
                '최저기온': row['최저기온'],
                '최고기온': row['최고기온']
            })
    
    su_df = pd.DataFrame(suneung_data)
    
    if not su_df.empty:
        # 데이터프레임 표시
        st.dataframe(su_df.style.format("{:.1f}", subset=['평균기온', '최저기온', '최고기온']))
        
        # 1. 시계열 그래프 (최저기온 변화)
        st.subheader("역대 수능일 최저기온 변화 (수능 한파 확인)")
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        
        # 영하인 날은 파란색, 영상은 빨간색 점으로 표시
        colors = ['blue' if x < 0 else 'red' for x in su_df['최저기온']]
        
        ax2.plot(su_df['시험년도'], su_df['최저기온'], color='gray', linestyle='-', alpha=0.5)
        ax2.scatter(su_df['시험년도'], su_df['최저기온'], color=colors, s=50, zorder=5)
        
        # 0도 기준선
        ax2.axhline(0, color='black', linestyle='--', linewidth=1)
        
        for i, txt in enumerate(su_df['최저기온']):
            ax2.annotate(f"{txt}", (su_df['시험년도'].iloc[i], su_df['최저기온'].iloc[i]), 
                         xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8)
            
        ax2.set_title("수능 시험일 최저기온 추이")
        ax2.set_ylabel("최저기온 (℃)")
        ax2.set_xticks(su_df['시험년도'])
        ax2.set_xticklabels(su_df['시험년도'], rotation=45)
        st.pyplot(fig2)
        
        # 2. 통계 요약
        coldest_su = su_df.loc[su_df['최저기온'].idxmin()]
        hottest_su = su_df.loc[su_df['최저기온'].idxmax()]
        
        col1, col2 = st.columns(2)
        with col1:
            st.error(f"🥶 가장 추웠던 수능: {coldest_su['시험년도']}년 ({coldest_su['최저기온']}℃)")
        with col2:
            st.success(f"🥵 가장 따뜻했던 수능: {hottest_su['시험년도']}년 ({hottest_su['최저기온']}℃)")
            
    else:
        st.write("해당 기간의 데이터가 충분하지 않습니다.")
