import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. 頁面設定與 UI 比例優化 (支援深淺模式)
# ==========================================
st.set_page_config(page_title="亞馬遜專案數據推演 Dashboard by 歐可", layout="wide")

st.markdown("""
    <style>
    /* 1. 指標數值字型優化，確保 0 不帶點並支援深淺模式 */
    [data-testid="stMetricValue"] {
        font-family: 'Source Sans Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        font-size: 30px !important;
    }
    
    /* 2. 寬度控制：上半段指標 90% */
    [data-testid="stMetric"], .stDivider {
        max-width: 90%;
        margin-left: auto;
        margin-right: auto;
    }

    /* 3. 寬度控制：圖表與表格 80% */
    [data-testid="column"], [data-testid="stTable"], div[style*="background-color"] {
        max-width: 80% !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* 4. 標題靠左對齊樣式 */
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

    # 階段參數連動
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
        target_rev = st.number_input("月營收目標 (USD)", value=30000.0)
    else:
        mkt_size = st.number_input("類目大盤月營收 (USD)", value=1000000.0)
        mkt_share = st.number_input("預期市佔率 (%)", value=1.0, format="%.2f")
        target_rev = mkt_size * (mkt_share / 100)

    price = st.number_input("客單價 Price (USD)", value=30.0)
    cogs = st.number_input("單件成本 (COGS+頭程)", value=0.0)
    
    # --- 確保自動計算區域正確顯示 ---
    amz_fee_rate = st.number_input("亞馬遜抽成率 (%)", value=15.0)
    st.caption(f"💡 單件抽成預覽: **${(price * amz_fee_rate / 100):.2f}**")
    
    ret_rate = st.number_input("預估退貨率 (%)", value=5.0)
    st.caption(f"💡 單件退貨損耗預覽: **${(price * ret_rate / 100):.2f}**")
    
    st.markdown("---")
    st.subheader("📦 庫存與倉儲成本")
    fba_fee = st.number_input("單件 FBA 配送費 (USD)", value=7.0)
    storage_fee_base = st.number_input("淡季單件月倉儲費 (USD)", value=0.31)
    placement_fee = st.number_input("單件入庫配置費 (USD)", value=0.70)
    
    storage_days = st.slider("預估庫存周轉天數", 15, 180, 45, step=5)
    if storage_days <= 60:
        st.success(f"✅ 周轉健康 ({storage_days}天)")
    elif storage_days <= 120:
        st.warning(f"⚠️ 周轉稍慢 ({storage_days}天)")
    else:
        st.error(f"🚨 警告：庫存積壓")

    # 倉儲費加權 (淡季9個月, 旺季3個月3倍)
    avg_storage_fee = (storage_fee_base * 9 + (storage_fee_base * 3 * 3)) / 12
    actual_unit_storage = (avg_storage_fee * (storage_days / 30)) + placement_fee
    st.caption(f"📊 加權後單件持倉成本: **${actual_unit_storage:,.2f}**")

    st.markdown("---")
    st.subheader("📅 年度收益預測")
    calc_period = st.radio("計算範圍", ["整年 (12個月)", "到日曆年底"])
    q4_boost = st.slider("Q4 (10-12月) 營收預期增幅 (%)", 0, 300, 50)

    st.markdown("---")
    st.subheader("📊 流量與廣告參數")
    cpc = st.number_input("預估 CPC (USD)", value=st.session_state.current_cpc)
    ctr = st.number_input("預估 CTR (%)", value=st.session_state.current_ctr)
    cvr = st.number_input("預估 CVR (%)", value=st.session_state.current_cvr)
