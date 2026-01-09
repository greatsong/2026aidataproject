import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os

# 페이지 설정
st.set_page_config(
    page_title="서울 기온 분석기",
    page_icon="🌡️",
    layout="wide"
)

# 수능 시험 날짜 (1994년~2025년)
SUNEUNG_DATES = {
    1994: "1993-11-16",  # 1994학년도 (1993년 11월 시행)
    1995: "1994-11-23",
    1996: "1995-11-22",
    1997: "1996-11-13",
    1998: "1997-11-19",
    1999: "1998-11-18",
    2000: "1999-11-17",
    2001: "2000-11-15",
    2002: "2001-11-07",
    2003: "2002-11-06",
    2004: "2003-11-05",
    2005: "2004-11-17",
    2006: "2005-11-23",
    2007: "2006-11-16",
    2008: "2007-11-15",
    2009: "2008-11-13",
    2010: "2009-11-12",
    2011: "2010-11-18",
    2012: "2011-11-10",
    2013: "2012-11-08",
    2014: "2013-11-07",
    2015: "2014-11-13",
    2016: "2015-11-12",
    2017: "2016-11-17",
    2018: "2017-11-23",  # 포항 지진으로 1주일 연기
    2019: "2018-11-15",
    2020: "2019-11-14",
    2021: "2020-12-03",  # 코로나로 2주 연기
    2022: "2021-11-18",
    2023: "2022-11-17",
    2024: "2023-11-16",
    2025: "2024-11-14",
    2026: "2025-11-13",
}


@st.cache_data
def load_data(file_path=None, uploaded_file=None):
    """데이터 로드 함수"""
    try:
        if uploaded_file is not None:
            # 업로드된 파일 처리
            df = pd.read_csv(uploaded_file, encoding='euc-kr', skiprows=7, header=None)
        else:
            # 기본 데이터 파일 로드
            df = pd.read_csv(file_path, encoding='euc-kr', skiprows=7, header=None)
        
        # 컬럼명 설정
        df.columns = ['날짜', '지점', '평균기온', '최저기온', '최고기온']
        
        # 날짜 앞의 탭 문자 제거 및 날짜 변환
        df['날짜'] = df['날짜'].str.strip()
        df['날짜'] = pd.to_datetime(df['날짜'], format='%Y-%m-%d', errors='coerce')
        
        # 결측치 제거
        df = df.dropna(subset=['날짜'])
        
        # 기온 데이터 숫자 변환
        for col in ['평균기온', '최저기온', '최고기온']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 월, 일 컬럼 추가
        df['월'] = df['날짜'].dt.month
        df['일'] = df['날짜'].dt.day
        df['년'] = df['날짜'].dt.year
        df['월일'] = df['날짜'].dt.strftime('%m-%d')
        
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return None


def get_historical_stats(df, month, day):
    """특정 월/일의 역사적 통계 계산"""
    same_day_data = df[(df['월'] == month) & (df['일'] == day)]
    
    if len(same_day_data) == 0:
        return None
    
    stats = {
        '평균기온_평균': same_day_data['평균기온'].mean(),
        '평균기온_std': same_day_data['평균기온'].std(),
        '평균기온_최고': same_day_data['평균기온'].max(),
        '평균기온_최저': same_day_data['평균기온'].min(),
        '최저기온_평균': same_day_data['최저기온'].mean(),
        '최저기온_최고': same_day_data['최저기온'].max(),
        '최저기온_최저': same_day_data['최저기온'].min(),
        '최고기온_평균': same_day_data['최고기온'].mean(),
        '최고기온_최고': same_day_data['최고기온'].max(),
        '최고기온_최저': same_day_data['최고기온'].min(),
        '데이터_수': len(same_day_data),
        '연도_범위': f"{same_day_data['년'].min()}~{same_day_data['년'].max()}",
        'history': same_day_data.sort_values('년')
    }
    return stats


def calculate_percentile(df, month, day, temp_value, temp_type='평균기온'):
    """특정 기온이 역사적으로 몇 퍼센타일인지 계산"""
    same_day_data = df[(df['월'] == month) & (df['일'] == day)]
    if len(same_day_data) == 0:
        return None
    
    temps = same_day_data[temp_type].dropna()
    percentile = (temps < temp_value).sum() / len(temps) * 100
    return percentile


def get_temperature_description(percentile):
    """퍼센타일에 따른 설명 반환"""
    if percentile <= 5:
        return "🥶 역대급 추위!", "blue"
    elif percentile <= 15:
        return "❄️ 매우 추움", "lightblue"
    elif percentile <= 30:
        return "🌨️ 다소 추움", "cyan"
    elif percentile <= 70:
        return "🌤️ 평년 수준", "gray"
    elif percentile <= 85:
        return "☀️ 다소 따뜻함", "orange"
    elif percentile <= 95:
        return "🔥 매우 따뜻함", "orangered"
    else:
        return "🌋 역대급 더위!", "red"


def main():
    st.title("🌡️ 서울 기온 분석기")
    st.markdown("### 역사적 기온 데이터로 오늘 날씨가 얼마나 특별한지 알아보세요!")
    
    # 사이드바 - 데이터 업로드
    st.sidebar.header("📂 데이터 설정")
    
    uploaded_file = st.sidebar.file_uploader(
        "새 데이터 업로드 (선택사항)",
        type=['csv'],
        help="기상청 형식의 CSV 파일을 업로드하세요. 업로드하지 않으면 기본 데이터를 사용합니다."
    )
    
    # 데이터 로드
    default_path = os.path.join(os.path.dirname(__file__), 'ta_20260109154427.csv')
    
    if uploaded_file is not None:
        df = load_data(uploaded_file=uploaded_file)
        st.sidebar.success("✅ 업로드된 데이터 사용 중")
    else:
        df = load_data(file_path=default_path)
        st.sidebar.info("📊 기본 데이터 사용 중")
    
    if df is None or len(df) == 0:
        st.error("데이터를 로드할 수 없습니다.")
        return
    
    # 데이터 정보 표시
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**데이터 기간:** {df['날짜'].min().strftime('%Y-%m-%d')} ~ {df['날짜'].max().strftime('%Y-%m-%d')}")
    st.sidebar.markdown(f"**총 데이터 수:** {len(df):,}일")
    
    # 메인 탭
    tab1, tab2, tab3 = st.tabs(["📊 날짜별 분석", "🎓 수능날 기온 분석", "📈 전체 데이터 탐색"])
    
    # ============ TAB 1: 날짜별 분석 ============
    with tab1:
        st.header("📊 특정 날짜 기온 분석")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # 날짜 선택
            max_date = df['날짜'].max().date()
            min_date = df['날짜'].min().date()
            
            selected_date = st.date_input(
                "분석할 날짜 선택",
                value=max_date,
                min_value=min_date,
                max_value=max_date
            )
            
            # 선택한 날짜의 데이터 가져오기
            selected_data = df[df['날짜'].dt.date == selected_date]
            
            if len(selected_data) == 0:
                st.warning("선택한 날짜의 데이터가 없습니다.")
            else:
                row = selected_data.iloc[0]
                month, day = selected_date.month, selected_date.day
                
                st.markdown("### 📌 선택 날짜 기온")
                st.metric("평균기온", f"{row['평균기온']:.1f}°C")
                st.metric("최저기온", f"{row['최저기온']:.1f}°C")
                st.metric("최고기온", f"{row['최고기온']:.1f}°C")
        
        with col2:
            if len(selected_data) > 0:
                row = selected_data.iloc[0]
                month, day = selected_date.month, selected_date.day
                
                # 역사적 통계 계산
                stats = get_historical_stats(df, month, day)
                
                if stats:
                    # 퍼센타일 계산
                    avg_pct = calculate_percentile(df, month, day, row['평균기온'], '평균기온')
                    min_pct = calculate_percentile(df, month, day, row['최저기온'], '최저기온')
                    max_pct = calculate_percentile(df, month, day, row['최고기온'], '최고기온')
                    
                    st.markdown(f"### 📈 {month}월 {day}일 역사 비교 ({stats['연도_범위']}, {stats['데이터_수']}년)")
                    
                    # 결과 표시
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        desc, color = get_temperature_description(avg_pct)
                        diff = row['평균기온'] - stats['평균기온_평균']
                        st.markdown(f"**평균기온**")
                        st.markdown(f"역사 평균: **{stats['평균기온_평균']:.1f}°C**")
                        st.markdown(f"차이: **{diff:+.1f}°C**")
                        st.markdown(f"순위: 하위 **{avg_pct:.1f}%**")
                        st.markdown(f"{desc}")
                    
                    with col_b:
                        desc, color = get_temperature_description(min_pct)
                        diff = row['최저기온'] - stats['최저기온_평균']
                        st.markdown(f"**최저기온**")
                        st.markdown(f"역사 평균: **{stats['최저기온_평균']:.1f}°C**")
                        st.markdown(f"차이: **{diff:+.1f}°C**")
                        st.markdown(f"순위: 하위 **{min_pct:.1f}%**")
                        st.markdown(f"{desc}")
                    
                    with col_c:
                        desc, color = get_temperature_description(max_pct)
                        diff = row['최고기온'] - stats['최고기온_평균']
                        st.markdown(f"**최고기온**")
                        st.markdown(f"역사 평균: **{stats['최고기온_평균']:.1f}°C**")
                        st.markdown(f"차이: **{diff:+.1f}°C**")
                        st.markdown(f"순위: 하위 **{max_pct:.1f}%**")
                        st.markdown(f"{desc}")
                    
                    # 역사적 분포 차트
                    st.markdown("---")
                    st.markdown("### 📊 역사적 기온 분포")
                    
                    history = stats['history']
                    
                    fig = go.Figure()
                    
                    # 평균기온 히스토리
                    fig.add_trace(go.Scatter(
                        x=history['년'],
                        y=history['평균기온'],
                        mode='lines+markers',
                        name='평균기온',
                        line=dict(color='green'),
                        marker=dict(size=4)
                    ))
                    
                    # 최저기온
                    fig.add_trace(go.Scatter(
                        x=history['년'],
                        y=history['최저기온'],
                        mode='lines+markers',
                        name='최저기온',
                        line=dict(color='blue'),
                        marker=dict(size=4)
                    ))
                    
                    # 최고기온
                    fig.add_trace(go.Scatter(
                        x=history['년'],
                        y=history['최고기온'],
                        mode='lines+markers',
                        name='최고기온',
                        line=dict(color='red'),
                        marker=dict(size=4)
                    ))
                    
                    # 선택 연도 강조
                    selected_year = selected_date.year
                    fig.add_vline(x=selected_year, line_dash="dash", line_color="purple", 
                                  annotation_text=f"{selected_year}년", annotation_position="top")
                    
                    fig.update_layout(
                        title=f"{month}월 {day}일 기온 변화 추이",
                        xaxis_title="연도",
                        yaxis_title="기온 (°C)",
                        hovermode='x unified',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 히스토그램
                    st.markdown("### 📊 기온 분포 히스토그램")
                    
                    fig2 = go.Figure()
                    fig2.add_trace(go.Histogram(
                        x=history['평균기온'],
                        name='평균기온 분포',
                        opacity=0.7,
                        marker_color='green'
                    ))
                    
                    # 현재 값 표시
                    fig2.add_vline(x=row['평균기온'], line_dash="dash", line_color="red",
                                   annotation_text=f"선택일: {row['평균기온']:.1f}°C", 
                                   annotation_position="top")
                    
                    fig2.update_layout(
                        title=f"{month}월 {day}일 평균기온 분포",
                        xaxis_title="평균기온 (°C)",
                        yaxis_title="빈도",
                        height=300
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
    
    # ============ TAB 2: 수능날 분석 ============
    with tab2:
        st.header("🎓 수능 시험일 기온 분석 (1994~2025)")
        st.markdown("대학수학능력시험은 매년 11월에 치러지며, 수능 한파는 수험생들의 관심사입니다.")
        
        # 수능일 데이터 추출
        suneung_data = []
        for year, date_str in SUNEUNG_DATES.items():
            date = pd.to_datetime(date_str)
            day_data = df[df['날짜'] == date]
            if len(day_data) > 0:
                row = day_data.iloc[0]
                month, day = date.month, date.day
                
                # 해당 날짜의 역사적 통계
                stats = get_historical_stats(df, month, day)
                avg_pct = calculate_percentile(df, month, day, row['평균기온'], '평균기온') if stats else None
                
                suneung_data.append({
                    '학년도': f"{year}학년도",
                    '시험일': date_str,
                    '평균기온': row['평균기온'],
                    '최저기온': row['최저기온'],
                    '최고기온': row['최고기온'],
                    '역사평균': stats['평균기온_평균'] if stats else None,
                    '편차': row['평균기온'] - stats['평균기온_평균'] if stats else None,
                    '퍼센타일': avg_pct,
                    '연도': year
                })
        
        suneung_df = pd.DataFrame(suneung_data)
        
        if len(suneung_df) > 0:
            # 요약 통계
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                coldest = suneung_df.loc[suneung_df['평균기온'].idxmin()]
                st.metric("🥶 가장 추웠던 수능", 
                         f"{coldest['평균기온']:.1f}°C",
                         f"{coldest['학년도']}")
            
            with col2:
                warmest = suneung_df.loc[suneung_df['평균기온'].idxmax()]
                st.metric("🔥 가장 따뜻했던 수능",
                         f"{warmest['평균기온']:.1f}°C",
                         f"{warmest['학년도']}")
            
            with col3:
                avg_temp = suneung_df['평균기온'].mean()
                st.metric("📊 수능일 평균기온", f"{avg_temp:.1f}°C")
            
            with col4:
                cold_count = len(suneung_df[suneung_df['퍼센타일'] <= 30])
                st.metric("❄️ 평년보다 추운 수능", f"{cold_count}회 / {len(suneung_df)}회")
            
            st.markdown("---")
            
            # 수능일 기온 차트
            st.markdown("### 📈 수능일 기온 변화 추이")
            
            fig = go.Figure()
            
            # 평균기온 라인
            fig.add_trace(go.Scatter(
                x=suneung_df['연도'],
                y=suneung_df['평균기온'],
                mode='lines+markers',
                name='평균기온',
                line=dict(color='green', width=2),
                marker=dict(size=8)
            ))
            
            # 최저/최고 범위
            fig.add_trace(go.Scatter(
                x=suneung_df['연도'],
                y=suneung_df['최저기온'],
                mode='lines',
                name='최저기온',
                line=dict(color='blue', dash='dash'),
            ))
            
            fig.add_trace(go.Scatter(
                x=suneung_df['연도'],
                y=suneung_df['최고기온'],
                mode='lines',
                name='최고기온',
                line=dict(color='red', dash='dash'),
            ))
            
            # 0도 선
            fig.add_hline(y=0, line_dash="dot", line_color="gray", annotation_text="0°C")
            
            # 평균 기온 선
            fig.add_hline(y=avg_temp, line_dash="dot", line_color="green", 
                         annotation_text=f"수능일 평균 {avg_temp:.1f}°C")
            
            fig.update_layout(
                xaxis_title="학년도 (시험 연도)",
                yaxis_title="기온 (°C)",
                hovermode='x unified',
                height=450
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 평년 대비 편차 차트
            st.markdown("### 📊 수능일 기온 - 평년 대비 편차")
            
            fig2 = go.Figure()
            
            colors = ['blue' if x < 0 else 'red' for x in suneung_df['편차']]
            
            fig2.add_trace(go.Bar(
                x=suneung_df['연도'],
                y=suneung_df['편차'],
                marker_color=colors,
                name='평년 대비 편차',
                text=[f"{x:+.1f}°C" for x in suneung_df['편차']],
                textposition='outside'
            ))
            
            fig2.add_hline(y=0, line_color="black")
            
            fig2.update_layout(
                xaxis_title="학년도",
                yaxis_title="평년 대비 편차 (°C)",
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # 상세 데이터 테이블
            st.markdown("### 📋 수능일 기온 상세 데이터")
            
            display_df = suneung_df[['학년도', '시험일', '평균기온', '최저기온', '최고기온', '역사평균', '편차', '퍼센타일']].copy()
            display_df.columns = ['학년도', '시험일', '평균기온(°C)', '최저기온(°C)', '최고기온(°C)', '평년평균(°C)', '편차(°C)', '하위 %']
            
            # 포맷팅
            for col in ['평균기온(°C)', '최저기온(°C)', '최고기온(°C)', '평년평균(°C)', '편차(°C)', '하위 %']:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # 특별 분석
            st.markdown("---")
            st.markdown("### 🔍 수능 한파 분석")
            
            cold_suneungs = suneung_df[suneung_df['퍼센타일'] <= 20].sort_values('퍼센타일')
            
            if len(cold_suneungs) > 0:
                st.markdown("**역대 가장 추웠던 수능일 TOP 5** (해당 날짜 기준 하위 20% 이하)")
                for _, row in cold_suneungs.head(5).iterrows():
                    desc, _ = get_temperature_description(row['퍼센타일'])
                    st.markdown(f"- **{row['학년도']}** ({row['시험일']}): 평균 {row['평균기온']:.1f}°C, "
                               f"최저 {row['최저기온']:.1f}°C — {desc} (하위 {row['퍼센타일']:.1f}%)")
            
            warm_suneungs = suneung_df[suneung_df['퍼센타일'] >= 80].sort_values('퍼센타일', ascending=False)
            
            if len(warm_suneungs) > 0:
                st.markdown("**역대 가장 따뜻했던 수능일 TOP 5** (해당 날짜 기준 상위 20% 이상)")
                for _, row in warm_suneungs.head(5).iterrows():
                    desc, _ = get_temperature_description(row['퍼센타일'])
                    st.markdown(f"- **{row['학년도']}** ({row['시험일']}): 평균 {row['평균기온']:.1f}°C, "
                               f"최저 {row['최저기온']:.1f}°C — {desc} (하위 {row['퍼센타일']:.1f}%)")
    
    # ============ TAB 3: 전체 데이터 탐색 ============
    with tab3:
        st.header("📈 전체 데이터 탐색")
        
        # 연도 범위 선택
        year_range = st.slider(
            "연도 범위 선택",
            min_value=int(df['년'].min()),
            max_value=int(df['년'].max()),
            value=(1970, int(df['년'].max()))
        )
        
        filtered_df = df[(df['년'] >= year_range[0]) & (df['년'] <= year_range[1])]
        
        # 연평균 기온 추이
        st.markdown("### 🌡️ 연평균 기온 변화 추이")
        
        yearly_avg = filtered_df.groupby('년').agg({
            '평균기온': 'mean',
            '최저기온': 'mean',
            '최고기온': 'mean'
        }).reset_index()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=yearly_avg['년'],
            y=yearly_avg['평균기온'],
            mode='lines+markers',
            name='연평균기온',
            line=dict(color='green', width=2)
        ))
        
        # 추세선 추가
        z = np.polyfit(yearly_avg['년'], yearly_avg['평균기온'], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=yearly_avg['년'],
            y=p(yearly_avg['년']),
            mode='lines',
            name='추세선',
            line=dict(color='red', dash='dash')
        ))
        
        trend_per_decade = z[0] * 10
        
        fig.update_layout(
            title=f"서울 연평균 기온 변화 (10년당 {trend_per_decade:+.2f}°C)",
            xaxis_title="연도",
            yaxis_title="평균기온 (°C)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 월별 평균 기온
        st.markdown("### 📅 월별 평균 기온")
        
        monthly_avg = filtered_df.groupby('월').agg({
            '평균기온': 'mean',
            '최저기온': 'mean',
            '최고기온': 'mean'
        }).reset_index()
        
        fig2 = go.Figure()
        
        fig2.add_trace(go.Bar(
            x=monthly_avg['월'],
            y=monthly_avg['평균기온'],
            name='평균기온',
            marker_color='green'
        ))
        
        fig2.add_trace(go.Scatter(
            x=monthly_avg['월'],
            y=monthly_avg['최저기온'],
            mode='lines+markers',
            name='최저기온 평균',
            line=dict(color='blue')
        ))
        
        fig2.add_trace(go.Scatter(
            x=monthly_avg['월'],
            y=monthly_avg['최고기온'],
            mode='lines+markers',
            name='최고기온 평균',
            line=dict(color='red')
        ))
        
        fig2.update_layout(
            xaxis_title="월",
            yaxis_title="기온 (°C)",
            xaxis=dict(tickmode='linear', dtick=1),
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # 극단값 기록
        st.markdown("### 🏆 역대 기록")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🥶 역대 가장 추운 날 TOP 10**")
            coldest_days = filtered_df.nsmallest(10, '평균기온')[['날짜', '평균기온', '최저기온', '최고기온']]
            coldest_days['날짜'] = coldest_days['날짜'].dt.strftime('%Y-%m-%d')
            st.dataframe(coldest_days, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**🔥 역대 가장 더운 날 TOP 10**")
            hottest_days = filtered_df.nlargest(10, '평균기온')[['날짜', '평균기온', '최저기온', '최고기온']]
            hottest_days['날짜'] = hottest_days['날짜'].dt.strftime('%Y-%m-%d')
            st.dataframe(hottest_days, use_container_width=True, hide_index=True)
    
    # 푸터
    st.markdown("---")
    st.markdown("💡 **Tip**: 사이드바에서 새로운 CSV 파일을 업로드하여 다른 지역 데이터를 분석할 수 있습니다.")
    st.caption("데이터 출처: 기상청 | 개발: Claude AI")


# numpy 임포트 추가 (추세선용)
import numpy as np

if __name__ == "__main__":
    main()
