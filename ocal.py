import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. 頁面設定與 CSS
# ==========================================
st.set_page_config(page_title="亞馬遜專案數據推演 Dashboard by 歐可", layout="wide")

st.markdown("""
    <style>
    .stTable { font-size: 20px !important; }
    div[data-testid="stMetricValue"] { font-size: 32px !important; }
    [dt-testid="stMetric"], .stMarkdown, .stDivider { max-width: 90%; margin: auto; }
    [data-testid="column"] { max-width: 80%; margin: auto; }
    [data-testid="stTable"], div[style*="background-color"] { max-width: 70% !important; margin: auto !important; }
    @media print {
        [data-testid="stSidebar"], header, footer { display: none !important; }
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
    
    # 新增：救火模式開關
    firefighting = st.toggle("🔥 開啟「救火/消極經營」診斷模式", value=False)
    if firefighting:
        st.warning("⚠️ 已開啟救火模式：系統將引入權重懲罰係數，模擬店鋪萎縮現況。")

    stage = st.selectbox("產品所處階段", ["🌱 初期 (Launch)", "🚀 成長期 (Growth)", "🌳 成熟期 (Mature)"], key="stage_select")

    # 階段連動 (救火模式下強制壓低指標)
    if stage != st.session_state.stage_prev:
        if stage == "🌱 初期 (Launch)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.35, 5.0, 90, 1.2
        elif stage == "🚀 成長期 (Growth)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.50, 10.0, 50, 1.0
        elif stage == "🌳 成熟期 (Mature)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.75, 15.0, 30, 0.8
        st.session_state.stage_prev = stage

    # 營收設定
    target_mode = st.radio("設定方式", ["🎯 直接輸入營收目標", "🍰 市場份額推算", "💰 給定固定預算倒算"])
    
    # 邏輯計算
    if target_mode == "💰 給定固定預算倒算":
        fixed_budget = st.number_input("每月固定預算 (USD)", value=1000.0)
        # 暫時設定一個預算導向的目標，後面運算會覆蓋
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
    
    # 救火模式對 CVR 的懲罰
    actual_cvr = cvr * 0.7 if firefighting else cvr
    
    ad_ratio = st.slider("廣告單佔比 (%)", 0, 100, 95 if firefighting else st.session_state.current_ad_ratio)
    ppc_ratio = st.slider("站內 PPC 佔總預算比 (%)", 0, 100, 70)

# ==========================================
# 3. 核心運算邏輯
# ==========================================
if target_mode == "💰 給定固定預算倒算":
    # 預算倒推模式
    ppc_part = fixed_budget * (ppc_ratio / 100)
    clicks = ppc_part / cpc if cpc > 0 else 0
    ad_units = clicks * (actual_cvr / 100)
    total_units = ad_units / (ad_ratio / 100) if ad_ratio > 0 else ad_units
    target_rev = total_units * price
    total_budget = fixed_budget
else:
    # 目標反推模式
    total_units = target_rev / price if price > 0 else 0
    ad_units = total_units * (ad_ratio / 100)
    req_clicks = ad_units / (actual_cvr / 100) if actual_cvr > 0 else 0
    ppc_spend = req_clicks * cpc
    total_budget = ppc_spend / (ppc_ratio / 100) if ppc_ratio > 0 else 0

# 營收 Breakdown
ad_rev = ad_units * price
org_rev = target_rev - ad_rev
tacos = (total_budget / target_rev * 100) if target_rev > 0 else 0

# ==========================================
# 4. 主畫面 Dashboard
# ==========================================
st.title("📊 亞馬遜專案數據推演 Dashboard by 歐可")
st.write("")

# 第一層：指標 (新增營收 Breakdown)
c1, c2, c3, c4 = st.columns(4)
c1.metric("目標總營收", f"${target_rev:,.2f}")
c2.metric("廣告營收 / 自然營收", f"${ad_rev:,.0f} / ${org_rev:,.0f}")
c3.metric("總行銷預算", f"${total_budget:,.2f}")
c4.metric("預估 TACOS", f"{tacos:.2f}%")

st.divider()

# 第二層：核心假設 (救火模式下會顯示懲罰後的 CVR)
st.markdown("<h3 style='text-align: center;'>⚙️ 核心經營假設 (Core Assumptions)</h3>", unsafe_allow_html=True)
a1, a2, a3, a4, a5 = st.columns(5)
a1.metric("客單價", f"${price:.2f}")
a2.metric("預估 CPC", f"${cpc:.2f}")
a3.metric("預估 CTR", f"{ctr}%")
a4.metric("實際 CVR", f"{actual_cvr:.2f}%", delta="-30% (權重懲罰)" if firefighting else None, delta_color="inverse")
a5.metric("廣告訂單佔比", f"{ad_ratio}%")

st.divider()

# 第三層：圖表 (80% 寬度)
col_l, col_r = st.columns(2)
with col_l:
    st.write("### 🛒 流量漏斗 (預估廣告路徑)")
    # 計算漏斗數據
    final_clicks = (ad_units / (actual_cvr / 100)) if actual_cvr > 0 else 0
    final_imps = (final_clicks / (ctr / 100)) if ctr > 0 else 0
    fig_f = go.Figure(go.Funnel(
        y = ["曝光量", "點擊數", "廣告訂單"],
        x = [100, 75, 50], 
        text = [f"{final_imps:,.0f}", f"{final_clicks:,.1f}", f"{ad_units:,.1f}"],
        textinfo = "text+label",
        marker = {"color": ["#FADBD8" if firefighting else "#E5ECF6", "#E74C3C" if firefighting else "#94B4DE", "#C0392B" if firefighting else "#1F77B4"]}
    ))
    fig_f.update_layout(showlegend=False, font=dict(size=18, color="white"), height=400)
    st.plotly_chart(fig_f, use_container_width=True)

with col_r:
    st.write("### 🍰 營收結構佔比")
    fig_p = px.pie(names=["廣告營收", "自然營收"], values=[ad_rev, org_rev], hole=0.4, color_discrete_sequence=['#E74C3C', '#2ECC71'] if firefighting else ['#1F77B4', '#2ECC71'])
    fig_p.update_traces(textinfo='percent+label', textfont_size=20)
    fig_p.update_layout(font=dict(size=16), height=400)
    st.plotly_chart(fig_p, use_container_width=True)

# 第四層：損益表
st.markdown("<h3 style='text-align: center;'>💵 專案 P&L 損益試算</h3>", unsafe_allow_html=True)
f_ref = round(target_rev*(amz_fee_rate/100), 2)
f_fba = round(total_units*7.0, 2)
f_st = round(total_units*1.5, 2)
f_ret = round(target_rev*0.05, 2)
total_cogs = round(total_units * cogs, 2)
# 分開 PPC 與行銷預算
ppc_s = total_budget * (ppc_ratio / 100)
mkt_s = total_budget - ppc_s
net_p = round(target_rev - (total_cogs + f_ref + f_fba + f_st + f_ret + total_budget), 2)

pl_df = pd.DataFrame({
    "項目": ["總營收", "產品成本", f"平台抽成({amz_fee_rate}%)", "FBA費用", "倉儲分倉", "退貨耗損(5%)", "站內廣告(PPC)", "站外行銷(Marketing)"],
    "金額": [target_rev, -total_cogs, -f_ref, -f_fba, -f_st, -f_ret, -ppc_s, -mkt_s]
})
pl_df["佔比"] = (abs(pl_df["金額"]) / target_rev * 100).map("{:.2f}%".format)
st.table(pl_df.style.format({"金額": "{:,.2f}"}))

# 底部淨利看板
st.markdown(f"""
<div style='background-color: {"#C0392B" if net_p < 0 else "#1F77B4"}; padding: 30px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.2);'>
    <h1 style='margin:0; font-size: 42px; color: white;'>✨ 預估專案淨利: ${net_p:,.2f}</h1>
    <h3 style='margin:10px 0 0 0; color: #D1E8FF;'>獲利率 (Net Margin): {(net_p/target_rev*100 if target_rev > 0 else 0):.2f}%</h3>
</div>
""", unsafe_allow_html=True)
