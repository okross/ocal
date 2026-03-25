import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. 頁面與基本設定
# ==========================================
st.set_page_config(page_title="歐可跨境計算器 (Okross Calculator)", layout="wide")

# 初始化動態參數 (Session State)
if 'init' not in st.session_state:
    st.session_state.ctr = 0.35
    st.session_state.cvr = 5.0
    st.session_state.ad_ratio = 90
    st.session_state.init = True

# 切換產品階段的 Callback 函數
def update_stage_defaults():
    stage = st.session_state.stage_select
    if stage == "🌱 初期 (Launch)":
        st.session_state.ctr = 0.35
        st.session_state.cvr = 5.0
        st.session_state.ad_ratio = 90
    elif stage == "🚀 成長期 (Growth)":
        st.session_state.ctr = 0.50
        st.session_state.cvr = 10.0
        st.session_state.ad_ratio = 50
    elif stage == "🌳 成熟期 (Mature)":
        st.session_state.ctr = 0.75
        st.session_state.cvr = 15.0
        st.session_state.ad_ratio = 30

# ==========================================
# 2. 左側邊欄 (Sidebar) - 控制台
# ==========================================
with st.sidebar:
    st.header("🎛️ 專案參數控制台")
    
    st.subheader("1. 賣家與目標設定")
    stage = st.selectbox(
        "產品所處階段", 
        ["🌱 初期 (Launch)", "🚀 成長期 (Growth)", "🌳 成熟期 (Mature)"],
        key="stage_select",
        on_change=update_stage_defaults
    )
    
    target_mode = st.radio("目標推算模式", ["🎯 直接輸入營收目標", "🍰 頂層市場份額推算 (Top-down)"])
    
    if target_mode == "🎯 直接輸入營收目標":
        target_revenue = st.number_input("月營收目標 (USD)", value=30000, step=1000)
    else:
        market_size = st.number_input("類目大盤月營收 (USD)", value=1000000, step=10000)
        market_share = st.number_input("預期拿下市佔率 (%)", value=1.0, step=0.1)
        target_revenue = market_size * (market_share / 100)
        st.info(f"💡 換算月營收目標：${target_revenue:,.2f}")

    st.subheader("2. 產品基礎數據")
    price = st.number_input("客單價 Price (USD)", value=30.0, step=1.0)
    cogs = st.number_input("單件成本 COGS + 頭程 (USD) [選填]", value=0.0, step=0.5)
    
    st.subheader("3. 平台雜費與抽成")
    amazon_fee_pct = st.number_input("亞馬遜抽成 (%)", value=15.0, step=1.0)
    fba_fee = st.number_input("單件 FBA 配送費 (USD)", value=7.0, step=0.5)
    storage_fee = st.number_input("單件分倉與倉儲費估算 (USD)", value=1.5, step=0.1)
    return_rate = st.number_input("預估退貨率 (%)", value=5.0, step=1.0)
    
    st.subheader("4. 流量與廣告假設")
    cpc = st.number_input("預估 CPC (USD)", value=1.0, step=0.1)
    
    # 讀取 Session state 的動態預設值
    ctr = st.number_input("預估 CTR (%)", value=st.session_state.ctr, key="ctr_input")
    cvr = st.number_input("預估 CVR (%)", value=st.session_state.cvr, key="cvr_input")
    ad_ratio = st.slider("廣告單佔比 (%)", min_value=0, max_value=100, value=st.session_state.ad_ratio, key="ad_ratio_input")
    
    st.subheader("5. 預算配置比例")
    ppc_ratio = st.slider("站內廣告 (PPC) 佔總預算比例 (%)", min_value=0, max_value=100, value=70)
    marketing_ratio = 100 - ppc_ratio
    st.caption(f"*剩餘 {marketing_ratio}% 將分配給站外/促銷行銷*")

# ==========================================
# 3. 核心運算邏輯 (漏斗推算)
# ==========================================
# 基礎目標銷量
total_units = target_revenue / price if price > 0 else 0
daily_units = total_units / 30

# 廣告漏斗推算
ad_units = total_units * (ad_ratio / 100)
required_clicks = ad_units / (cvr / 100) if cvr > 0 else 0
required_impressions = required_clicks / (ctr / 100) if ctr > 0 else 0

# 預算計算
ppc_spend = required_clicks * cpc
total_budget = ppc_spend / (ppc_ratio / 100) if ppc_ratio > 0 else 0
marketing_spend = total_budget - ppc_spend

# ACOS / TACOS
acos = (ppc_spend / (ad_units * price)) * 100 if ad_units > 0 else 0
tacos = (total_budget / target_revenue) * 100 if target_revenue > 0 else 0

# ==========================================
# 4. 主畫面 Dashboard 渲染
# ==========================================
st.title("📊 亞馬遜專案數據推演 Dashboard")
if cogs == 0:
    st.warning("💡 **溫馨提示：** 目前尚未填寫左側的「單件成本 COGS」，下方財務報表的「預估專案淨利」目前僅代表扣除廣告與平台費用的「毛利 (Gross Margin)」。建議補齊以獲得最精準的試算結果！")

# 區塊 1: 大數據指標
st.markdown("### 🏆 核心預期效益 (30天)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("總營收目標", f"${target_revenue:,.0f}")
col2.metric("日均銷量目標", f"{daily_units:,.1f} 件")
col3.metric("總行銷預算", f"${total_budget:,.0f}")
col4.metric("預估 TACOS", f"{tacos:.1f}%")

st.divider()

# 區塊 2 & 3: 圖表區 (並排)
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("### 🛒 流量漏斗拆解")
    # Plotly 漏斗圖
    funnel_data = dict(
        number=[required_impressions, required_clicks, ad_units],
        stage=["曝光量 (Impressions)", "點擊數 (Clicks)", "廣告訂單 (Ad Orders)"]
    )
    fig_funnel = px.funnel(funnel_data, x='number', y='stage')
    fig_funnel.update_layout(margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_funnel, use_container_width=True)

with col_chart2:
    st.markdown("### 🍰 預算配置建議")
    # Plotly 圓餅圖
    pie_data = pd.DataFrame({
        "預算類別": ["站內廣告 (PPC/DSP)", "站外/促銷 (KOL/Coupon)"],
        "金額": [ppc_spend, marketing_spend]
    })
    fig_pie = px.pie(pie_data, values='金額', names='預算類別', hole=0.4, 
                     color_discrete_sequence=['#ff9900', '#146eb4'])
    fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# 區塊 4: 財務 P&L 損益表
st.markdown("### 💵 專案 P&L 損益表 (Unit Economics)")

# 計算各項總金額與單件分攤
amazon_fee_total = target_revenue * (amazon_fee_pct / 100)
fba_fee_total = total_units * fba_fee
storage_fee_total = total_units * storage_fee
return_cost_total = target_revenue * (return_rate / 100)
cogs_total = total_units * cogs

net_profit_total = target_revenue - (cogs_total + amazon_fee_total + fba_fee_total + storage_fee_total + return_cost_total + total_budget)

# 建立表格 Dataframe
pl_data = {
    "財務項目": [
        "💰 總銷售額 (Total Revenue)",
        "➖ 產品總成本 (COGS + 頭程)",
        "➖ 亞馬遜抽成 (Referral Fee)",
        "➖ FBA 配送費 (Fulfillment Fee)",
        "➖ 分倉與倉儲費 (3-4個月預估)",
        "➖ 退貨耗損 (Return Cost)",
        "➖ 站內廣告花費 (PPC Ad Spend)",
        "➖ 站外/行銷花費 (Marketing)"
    ],
    "總金額 (USD)": [
        target_revenue, -cogs_total, -amazon_fee_total, -fba_fee_total, 
        -storage_fee_total, -return_cost_total, -ppc_spend, -marketing_spend
    ],
    "單件分攤 (USD)": [
        price, -cogs, -(price * (amazon_fee_pct/100)), -fba_fee, 
        -storage_fee, -(price * (return_rate/100)), -(ppc_spend/total_units if total_units else 0), -(marketing_spend/total_units if total_units else 0)
    ]
}

df_pl = pd.DataFrame(pl_data)
# 計算佔比
df_pl["佔營收比例 (%)"] = (abs(df_pl["總金額 (USD)"]) / target_revenue * 100).round(1)

# 顯示表格 (使用 Streamlit 的 dataframe 視覺化)
st.dataframe(
    df_pl.style.format({
        "總金額 (USD)": "${:,.2f}",
        "單件分攤 (USD)": "${:,.2f}",
        "佔營收比例 (%)": "{:.1f}%"
    }), 
    use_container_width=True, 
    hide_index=True
)

# 最終淨利大字報
st.markdown(f"""
<div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;'>
    <h2 style='margin:0; color: #1f77b4;'>✨ 預估專案淨利 (Net Profit): ${net_profit_total:,.2f}</h2>
    <p style='margin:0; font-size: 18px;'>整體獲利率 (Margin): <strong>{(net_profit_total/target_revenue*100):.1f}%</strong></p>
</div>
""", unsafe_allow_html=True)