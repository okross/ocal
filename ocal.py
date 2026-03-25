import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. 頁面設定
# ==========================================
st.set_page_config(page_title="歐可跨境計算器 (Okross Calculator)", layout="wide")

# 初始化動態參數
if 'stage_prev' not in st.session_state:
    st.session_state.stage_prev = "🌱 初期 (Launch)"
    st.session_state.current_ctr, st.session_state.current_cvr = 0.35, 5.0
    st.session_state.current_ad_ratio, st.session_state.current_cpc = 90, 1.2

# ==========================================
# 2. 左側邊欄 (Sidebar)
# ==========================================
with st.sidebar:
    st.header("🎛️ 專案參數控制台")
    stage = st.selectbox("產品所處階段", ["🌱 初期 (Launch)", "🚀 成長期 (Growth)", "🌳 成熟期 (Mature)"], key="stage_select")

    if stage != st.session_state.stage_prev:
        if stage == "🌱 初期 (Launch)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.35, 5.0, 90, 1.2
        elif stage == "🚀 成長期 (Growth)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.50, 10.0, 50, 1.0
        elif stage == "🌳 成熟期 (Mature)":
            st.session_state.current_ctr, st.session_state.current_cvr, st.session_state.current_ad_ratio, st.session_state.current_cpc = 0.75, 15.0, 30, 0.8
        st.session_state.stage_prev = stage

    target_rev = st.number_input("月營收目標 (USD)", value=30000, step=1000)
    price = st.number_input("客單價 Price (USD)", value=30.0)
    cogs = st.number_input("單件成本 (COGS+頭程)", value=0.0)
    
    st.markdown("---")
    cpc = st.number_input("預估 CPC (USD)", value=st.session_state.current_cpc, step=0.1)
    ctr = st.number_input("預估 CTR (%)", value=st.session_state.current_ctr, step=0.05)
    cvr = st.number_input("預估 CVR (%)", value=st.session_state.current_cvr, step=0.5)
    ad_ratio = st.slider("廣告單佔比 (%)", 0, 100, st.session_state.current_ad_ratio)
    ppc_ratio = st.slider("站內 PPC 佔預算比 (%)", 0, 100, 70)

# ==========================================
# 3. 運算邏輯
# ==========================================
total_units = target_rev / price if price > 0 else 0
ad_units = total_units * (ad_ratio / 100)
req_clicks = ad_units / (cvr / 100) if cvr > 0 else 0
req_imps = req_clicks / (ctr / 100) if ctr > 0 else 0

ppc_spend = req_clicks * cpc
total_budget = ppc_spend / (ppc_ratio / 100) if ppc_ratio > 0 else 0
mkt_spend = total_budget - ppc_spend
tacos = (total_budget / target_rev * 100) if target_rev > 0 else 0

# ==========================================
# 4. 主畫面 Dashboard
# ==========================================
st.title("📊 歐可跨境計算器 (Okross Calculator)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("目標營收", f"${target_rev:,.0f}")
c2.metric("日均銷量", f"{total_units/30:,.1f} 件")
c3.metric("總行銷預算", f"${total_budget:,.0f}")
c4.metric("預估 TACOS", f"{tacos:.1f}%")

st.divider()

col_l, col_r = st.columns(2)

with col_l:
    st.write("### 🛒 流量漏斗 (預估廣告路徑)")
    # 使用 Funnel 圖，但固定顯示寬度，並客製化 Text
    fig_f = go.Figure(go.Funnel(
        y = ["曝光量", "點擊數", "廣告訂單"],
        x = [100, 70, 40], # 固定視覺形狀
        text = [
            f"{req_imps:,.0f}",
            f"{req_clicks:,.1f} ({ctr}%)",
            f"{ad_units:,.1f} ({cvr}%)"
        ],
        textinfo = "text+label",
        hoverinfo = "none",
        marker = {"color": ["#E5ECF6", "#94B4DE", "#1F77B4"]}
    ))
    fig_f.update_layout(showlegend=False, font=dict(size=18), height=450)
    st.plotly_chart(fig_f, use_container_width=True)

with col_r:
    st.write("### 🍰 預算配置比例")
    fig_p = px.pie(
        names=["站內 PPC", "站外/促銷"], 
        values=[ppc_spend, mkt_spend], 
        hole=0.4,
        color_discrete_sequence=['#FF9900', '#146EB4']
    )
    fig_p.update_traces(textinfo='percent+label', textfont_size=20)
    fig_p.update_layout(font=dict(size=16), height=450)
    st.plotly_chart(fig_p, use_container_width=True)

# 損益試算表
st.write("### 💵 專案 P&L 損益試算 (月度)")
f_ref, f_fba, f_st, f_ret = target_rev*0.15, total_units*7.0, total_units*1.5, target_rev*0.05
net_profit = target_rev - (total_units*cogs + f_ref + f_fba + f_st + f_ret + total_budget)

pl_df = pd.DataFrame({
    "項目": ["總營收", "產品成本", "平台抽成(15%)", "FBA費用", "倉儲分倉", "退貨耗損(5%)", "行銷總預算"],
    "金額": [target_rev, -(total_units*cogs), -f_ref, -f_fba, -f_st, -f_ret, -total_budget]
})
pl_df["佔比"] = (abs(pl_df["金額"]) / target_rev * 100).map("{:.1f}%".format)
st.table(pl_df)

# 優化後的底部淨利顯示 (深藍色背景，白色大字)
st.markdown(f"""
<div style='background-color: #1F77B4; padding: 25px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
    <h1 style='margin:0; font-size: 36px; color: white;'>✨ 預估專案淨利: ${net_profit:,.2f}</h1>
    <h3 style='margin:10px 0 0 0; color: #D1E8FF;'>獲利率 (Net Margin): {(net_profit/target_rev*100):.1f}%</h3>
</div>
""", unsafe_allow_html=True)
