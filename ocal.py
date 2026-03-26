import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. 頁面設定與 Printer Friendly CSS
# ==========================================
st.set_page_config(page_title="亞馬遜專案數據推演 Dashboard by 歐可", layout="wide")

st.markdown("""
    <style>
    /* 全域字體與表格優化 */
    .stTable { font-size: 20px !important; }
    div[data-testid="stMetricValue"] { font-size: 32px !important; }
    
    /* 限制表格寬度並置中 */
    [data-testid="stTable"] {
        max-width: 70%;
        margin-left: auto;
        margin-right: auto;
    }

    /* 針對列印與截圖的優化 */
    @media print {
        [data-testid="stSidebar"], header, footer, .stButton, .stTooltipIcon, [data-testid="stNotification"] {
            display: none !important;
        }
        .main .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
        div[style*="background-color"] { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        [data-testid="stTable"] { max-width: 90%; } /* 列印時稍微放大一點 */
    }
    </style>
    """, unsafe_allow_html=True)

# 初始化動態參數 (延用先前的邏輯)
if 'stage_prev' not in st.session_state:
    st.session_state.stage_prev = "🌱 初期 (Launch)"
    st.session_state.current_ctr, st.session_state.current_cvr = 0.35, 5.0
    st.session_state.current_ad_ratio, st.session_state.current_cpc = 90, 1.2

# ==========================================
# 2. 左側邊欄 (Sidebar)
# ==========================================
with st.sidebar:
    st.header("🎛️ 參數控制台")
    stage = st.selectbox("產品所處階段", ["🌱 初期 (Launch)", "🚀 成長期 (Growth)", "🌳 成熟期 (Mature)"], key="stage_select")

    if stage != st.session_state.stage_prev:
        if stage == "🌱 初期 (Launch)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.35, 5.0, 90, 1.2
        elif stage == "🚀 成長期 (Growth)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.50, 10.0, 50, 1.0
        elif stage == "🌳 成熟期 (Mature)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.75, 15.0, 30, 0.8
        st.session_state.stage_prev = stage

    st.subheader("1. 營收目標設定")
    target_mode = st.radio("設定方式", ["🎯 直接輸入營收目標", "🍰 頂層市場份額推算"])
    if target_mode == "🎯 直接輸入營收目標":
        target_rev = st.number_input("月營收目標 (USD)", value=30000.0, step=1000.0)
    else:
        mkt_size = st.number_input("類目大盤月營收 (USD)", value=1000000.0)
        mkt_share = st.number_input("預期市佔率 (%)", value=1.0, step=0.1, format="%.2f")
        target_rev = mkt_size * (mkt_share / 100)

    st.subheader("2. 核心成本與雜費")
    price = st.number_input("客單價 Price (USD)", value=30.0)
    cogs = st.number_input("單件成本 (COGS+頭程)", value=0.0)
    amz_fee_rate = st.number_input("亞馬遜抽成率 (%)", value=15.0, step=1.0)
    ret_rate = st.number_input("預估退貨率 (%)", value=5.0, step=1.0)
    fba_fee = st.number_input("單件 FBA 配送費 (USD)", value=7.0)
    storage_fee = st.number_input("單件倉儲分倉費 (USD)", value=1.5)
    
    st.markdown("---")
    st.subheader("3. 流量與廣告參數")
    cpc = st.number_input("預估 CPC (USD)", value=st.session_state.current_cpc, step=0.1)
    ctr = st.number_input("預估 CTR (%)", value=st.session_state.current_ctr, step=0.05)
    cvr = st.number_input("預估 CVR (%)", value=st.session_state.current_cvr, step=0.5)
    ad_ratio = st.slider("廣告單佔比 (%)", 0, 100, st.session_state.current_ad_ratio)
    ppc_ratio = st.slider("站內 PPC 佔總預算比 (%)", 0, 100, 70)

# ==========================================
# 3. 運算邏輯
# ==========================================
total_units = round(target_rev / price, 2) if price > 0 else 0
ad_units = round(total_units * (ad_ratio / 100), 2)
req_clicks = round(ad_units / (cvr / 100), 2) if cvr > 0 else 0
req_imps = round(req_clicks / (ctr / 100), 2) if ctr > 0 else 0
ppc_spend = round(req_clicks * cpc, 2)
total_budget = round(ppc_spend / (ppc_ratio / 100), 2) if ppc_ratio > 0 else 0
mkt_spend = round(total_budget - ppc_spend, 2)
tacos = round((total_budget / target_rev * 100), 2) if target_rev > 0 else 0

# ==========================================
# 4. 主畫面 Dashboard
# ==========================================
st.title("📊 亞馬遜專案數據推演 Dashboard by 歐可")

# 第一層：指標
c1, c2, c3, c4 = st.columns(4)
c1.metric("目標營收", f"${target_rev:,.2f}")
c2.metric("日均銷量", f"{total_units/30:,.2f} 件")
c3.metric("總行銷預算", f"${total_budget:,.2f}")
c4.metric("預估 TACOS", f"{tacos:.2f}%")

st.divider()

# 第二層：核心假設
st.write("### ⚙️ 核心經營假設 (Core Assumptions)")
a1, a2, a3, a4, a5 = st.columns(5)
a1.metric("客單價", f"${price:.2f}", delta="Price", delta_color="off")
a2.metric("預估 CPC", f"${cpc:.2f}", delta="CPC", delta_color="off")
a3.metric("預估 CTR", f"{ctr}%", delta="CTR", delta_color="off")
a4.metric("預估 CVR", f"{cvr}%", delta="CVR", delta_color="off")
a5.metric("廣告佔比", f"{ad_ratio}%", delta="Ad Ratio", delta_color="off")

st.divider()

# 第三層：圖表
col_l, col_r = st.columns(2)
with col_l:
    st.write("### 🛒 流量漏斗 (預估廣告路徑)")
    fig_f = go.Figure(go.Funnel(
        y = ["曝光量", "點擊數", "廣告訂單"],
        x = [100, 75, 50], 
        text = [f"{req_imps:,.0f}", f"{req_clicks:,.2f} ({ctr}%)", f"{ad_units:,.2f} ({cvr}%)"],
        textinfo = "text+label",
        marker = {"color": ["#E5ECF6", "#94B4DE", "#1F77B4"]}
    ))
    fig_f.update_layout(showlegend=False, font=dict(size=18, color="white"), height=400)
    st.plotly_chart(fig_f, use_container_width=True)

with col_r:
    st.write("### 🍰 預算配置比例")
    fig_p = px.pie(names=["站內 PPC", "站外/行銷"], values=[ppc_spend, mkt_spend], hole=0.4, color_discrete_sequence=['#FF9900', '#146EB4'])
    fig_p.update_traces(textinfo='percent+label', textfont_size=20)
    fig_p.update_layout(font=dict(size=16), height=400)
    st.plotly_chart(fig_p, use_container_width=True)

# 第四層：損益表 (置中縮小寬度)
st.markdown("<h3 style='text-align: center;'>💵 專案 P&L 損益試算 (月度)</h3>", unsafe_allow_html=True)
f_ref = round(target_rev*(amz_fee_rate/100), 2)
f_fba = round(total_units*fba_fee, 2)
f_st = round(total_units*storage_fee, 2)
f_ret = round(target_rev*(ret_rate/100), 2)
total_cogs = round(total_units * cogs, 2)
net_profit = round(target_rev - (total_cogs + f_ref + f_fba + f_st + f_ret + ppc_spend + mkt_spend), 2)

pl_df = pd.DataFrame({
    "項目": ["總營收", "產品成本", f"平台抽成({amz_fee_rate}%)", "FBA費用", "倉儲分倉", f"退貨耗損({ret_rate}%)", "站內廣告(PPC)", "站外行銷(Marketing)"],
    "金額": [target_rev, -total_cogs, -f_ref, -f_fba, -f_st, -f_ret, -ppc_spend, -mkt_spend]
})
pl_df["佔比"] = (abs(pl_df["金額"]) / target_rev * 100).map("{:.2f}%".format)

# 使用 table 渲染以獲得穩定的 Printer-friendly 效果
st.table(pl_df.style.format({"金額": "{:,.2f}"}))

# 底部淨利看板
st.markdown(f"""
<div style='background-color: #1F77B4; padding: 30px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.2); max-width: 70%; margin: 20px auto;'>
    <h1 style='margin:0; font-size: 42px; color: white;'>✨ 預估專案淨利: ${net_profit:,.2f}</h1>
    <h3 style='margin:10px 0 0 0; color: #D1E8FF;'>獲利率 (Net Margin): {(net_profit/target_rev*100 if target_rev > 0 else 0):.2f}%</h3>
</div>
""", unsafe_allow_html=True)
