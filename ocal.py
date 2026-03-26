import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. 頁面設定與自定義 CSS (徹底鎖定樣式)
# ==========================================
st.set_page_config(page_title="亞馬遜專案數據推演 Dashboard by 歐可", layout="wide")

st.markdown("""
    <style>
    /* 全域字體鎖定：使用標準無襯線字體，確保 0 不帶點 */
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    }

    /* 自定義指標卡片樣式 */
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .metric-label {
        font-size: 14px;
        color: #586069;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #1f2328;
    }

    /* 表格寬度優化 (80%) */
    [data-testid="stTable"] {
        max-width: 80% !important;
        margin: auto !important;
    }

    /* 確保所有容器居中 */
    .block-container {
        max-width: 90% !important;
        margin: auto;
    }

    @media print {
        [data-testid="stSidebar"], header, footer { display: none !important; }
        div[style*="background-color"] { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------
# 輔助函式：產生自定義指標卡片
# ------------------------------------------
def custom_metric(label, value):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
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

    if stage != st.session_state.stage_prev:
        if stage == "🌱 初期 (Launch)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.35, 5.0, 90, 1.2
        elif stage == "🚀 成長期 (Growth)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.50, 10.0, 50, 1.0
        elif stage == "🌳 成熟期 (Mature)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.75, 15.0, 30, 0.8
        st.session_state.stage_prev = stage

    target_mode = st.radio("設定方式", ["🎯 直接輸入營收目標", "🍰 市場份額推算", "💰 給定固定預算倒算"])
    
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
    amz_fee_rate = st.number_input("亞馬遜抽成率 (%)", value=15.0)
    st.caption(f"💡 單件抽成: **${(price * amz_fee_rate / 100):.2f}**")
    
    st.markdown("---")
    cpc = st.number_input("預估 CPC (USD)", value=st.session_state.current_cpc)
    ctr = st.number_input("預估 CTR (%)", value=st.session_state.current_ctr)
    cvr = st.number_input("預估 CVR (%)", value=st.session_state.current_cvr)
    
    actual_cvr = cvr * 0.7 if firefighting else cvr
    ad_ratio = st.slider("廣告單佔比 (%)", 0, 100, 95 if firefighting else st.session_state.current_ad_ratio)
    ppc_ratio = st.slider("站內 PPC 佔總預算比 (%)", 0, 100, 70)

# ==========================================
# 3. 運算邏輯
# ==========================================
if target_mode == "💰 給定固定預算倒算":
    ppc_part = fixed_budget * (ppc_ratio / 100)
    clicks = ppc_part / cpc if cpc > 0 else 0
    ad_units = clicks * (actual_cvr / 100)
    total_units = ad_units / (ad_ratio / 100) if ad_ratio > 0 else ad_units
    target_rev = total_units * price
    total_budget = fixed_budget
else:
    total_units = target_rev / price if price > 0 else 0
    ad_units = total_units * (ad_ratio / 100)
    req_clicks = ad_units / (actual_cvr / 100) if actual_cvr > 0 else 0
    ppc_spend = req_clicks * cpc
    total_budget = ppc_spend / (ppc_ratio / 100) if ppc_ratio > 0 else 0

ad_rev = ad_units * price
org_rev = target_rev - ad_rev
tacos = (total_budget / target_rev * 100) if target_rev > 0 else 0

# ==========================================
# 4. 主畫面 Dashboard
# ==========================================
st.title("📊 亞馬遜專案數據推演 Dashboard by 歐可")
st.write("")

# 第一層：指標 (使用自定義 HTML，解決字體與顏色問題)
c1, c2, c3, c4 = st.columns(4)
with c1: custom_metric("目標總營收", f"${target_rev:,.2f}")
with c2: custom_metric("營收結構 (Ad / Org)", f"${ad_rev:,.0f} / ${org_rev:,.0f}")
with c3: custom_metric("總行銷預算", f"${total_budget:,.2f}")
with c4: custom_metric("預估 TACOS", f"{tacos:.2f}%")

st.divider()

# 第二層：核心假設 (使用自定義 HTML)
st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>⚙️ 核心經營假設 (Core Assumptions)</h3>", unsafe_allow_html=True)
a1, a2, a3, a4, a5 = st.columns(5)
with a1: custom_metric("客單價", f"${price:.2f}")
with a2: custom_metric("預估 CPC", f"${cpc:.2f}")
with a3: custom_metric("預估 CTR", f"{ctr}%")
with a4: custom_metric("實際 CVR", f"{actual_cvr:.2f}%")
with a5: custom_metric("廣告佔比", f"{ad_ratio}%")

if firefighting:
    st.error(f"⚠️ 偵測到店鋪權重流失：實際轉化率已從 {cvr}% 衰減至 {actual_cvr:.2f}% (-30%)")

st.divider()

# 第三層：圖表 (80% 寬度)
col_l, col_r = st.columns(2)
with col_l:
    st.write("### 🛒 流量漏斗 (預估廣告路徑)")
    f_clicks = (ad_units / (actual_cvr / 100)) if actual_cvr > 0 else 0
    f_imps = (f_clicks / (ctr / 100)) if ctr > 0 else 0
    fig_f = go.Figure(go.Funnel(
        y = ["曝光量", "點擊數", "廣告訂單"],
        x = [100, 75, 50], 
        text = [f"{f_imps:,.0f}", f"{f_clicks:,.1f}", f"{ad_units:,.1f}"],
        textinfo = "text+label",
        marker = {"color": ["#FADBD8" if firefighting else "#E5ECF6", "#E74C3C" if firefighting else "#94B4DE", "#1F77B4"]}
    ))
    fig_f.update_layout(showlegend=False, font=dict(size=18, color="white"), height=400, margin=dict(t=20, b=20))
    st.plotly_chart(fig_f, use_container_width=True)

with col_r:
    st.write("### 🍰 營收結構佔比")
    fig_p = px.pie(names=["廣告營收", "自然營收"], values=[ad_rev, org_rev], hole=0.4, 
                   color_discrete_sequence=['#E74C3C', '#2ECC71'] if firefighting else ['#1F77B4', '#2ECC71'])
    fig_p.update_traces(textinfo='percent+label', textfont_size=20)
    fig_p.update_layout(font=dict(size=16), height=400, margin=dict(t=20, b=20))
    st.plotly_chart(fig_p, use_container_width=True)

# 第四層：損益表 (80% 寬度)
st.markdown("<h3 style='text-align: center; margin-top: 30px; margin-bottom: 20px;'>💵 專案 P&L 損益試算 (月度)</h3>", unsafe_allow_html=True)
f_ref, f_fba, f_st, f_ret = round(target_rev*(amz_fee_rate/100), 2), round(total_units*7.0, 2), round(total_units*1.5, 2), round(target_rev*0.05, 2)
total_cogs = round(total_units * cogs, 2)
net_p = round(target_rev - (total_cogs + f_ref + f_fba + f_st + f_ret + total_budget), 2)

pl_df = pd.DataFrame({
    "項目": ["總營收", "產品成本", f"平台抽成({amz_fee_rate}%)", "FBA費用", "倉儲分倉", "退貨耗損(5%)", "站內廣告(PPC)", "站外行銷(Marketing)"],
    "金額": [target_rev, -total_cogs, -f_ref, -f_fba, -f_st, -f_ret, -(total_budget * ppc_ratio/100), -(total_budget * (1-ppc_ratio/100))]
})
pl_df["佔比"] = (abs(pl_df["金額"]) / target_rev * 100).map("{:.2f}%".format)
st.table(pl_df.style.format({"金額": "{:,.2f}"}))

# 底部淨利看板
st.markdown(f"""
<div style='background-color: {"#C0392B" if net_p < 0 else "#1F77B4"}; padding: 30px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.2); max-width: 80%; margin: 30px auto;'>
    <h1 style='margin:0; font-size: 42px; color: white; font-family: Arial, sans-serif;'>✨ 預估專案淨利: ${net_p:,.2f}</h1>
    <h3 style='margin:10px 0 0 0; color: #D1E8FF; font-family: Arial, sans-serif;'>獲利率 (Net Margin): {(net_p/target_rev*100 if target_rev > 0 else 0):.2f}%</h3>
</div>
""", unsafe_allow_html=True)
