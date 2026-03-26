import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. 頁面設定與 UI 比例優化
# ==========================================
st.set_page_config(page_title="亞馬遜專案數據推演 Dashboard by 歐可", layout="wide")

st.markdown("""
    <style>
    /* 指標數值字型優化 */
    [data-testid="stMetricValue"] {
        font-family: 'Source Sans Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        font-size: 30px !important;
    }
    
    /* 寬度控制：上半段指標 90% */
    [data-testid="stMetric"], .stMarkdown, .stDivider {
        max-width: 90%;
        margin-left: auto;
        margin-right: auto;
    }

    /* 寬度控制：圖表與表格 80% */
    [data-testid="column"], [data-testid="stTable"], div[style*="background-color"] {
        max-width: 80% !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* 標題靠左樣式 */
    .left-title {
        text-align: left;
        max-width: 80%;
        margin: 20px auto 10px auto;
        font-weight: bold;
    }

    @media print {
        [data-testid="stSidebar"], header, footer { display: none !important; }
        .main .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
        div[style*="background-color"] { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 初始化動態參數
if 'stage_prev' not in st.session_state:
    st.session_state.stage_prev = "🌱 初期 (Launch)"
    st.session_state.current_ctr, st.session_state.current_cvr = 0.35, 5.0
    st.session_state.current_ad_ratio, st.session_state.current_cpc = 90, 1.2

# ==========================================
# 2. 左側邊欄 (Sidebar)
# ==========================================
with st.sidebar:
    st.header("🎛️ 參數控制台")
    firefighting = st.toggle("🔥 開啟「救火/消極經營」診斷模式", value=False)
    
    stage = st.selectbox("產品所處階段", ["🌱 初期 (Launch)", "🚀 成長期 (Growth)", "🌳 成熟期 (Mature)"], key="stage_select")

    # 階段連動
    if stage != st.session_state.stage_prev:
        if stage == "🌱 初期 (Launch)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.35, 5.0, 90, 1.2
        elif stage == "🚀 成長期 (Growth)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.50, 10.0, 50, 1.0
        elif stage == "🌳 成熟期 (Mature)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.75, 15.0, 30, 0.8
        st.session_state.stage_prev = stage

    st.subheader("1. 營收與目標設定")
    target_mode = st.radio("目標設定方式", ["🎯 直接輸入營收目標", "🍰 市場份額推算", "💰 給定固定預算倒算"])
    
    if target_mode == "💰 給定固定預算倒算":
        fixed_budget = st.number_input("每月固定預算 (USD)", value=1000.0)
        target_rev = 0 
    elif target_mode == "🎯 直接輸入營收目標":
        target_rev
