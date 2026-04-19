import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "MS Gothic"

st.set_page_config(page_title="積立シミュレーター", layout="wide")

# タイトル
st.title("📈 積立投資シミュレーター")
st.write("複数の積立ルール（積立額・年利）に基づいて将来の資産額を計算します。")

# -----------------------------
# 入力エリア
# -----------------------------
st.sidebar.header("入力パラメータ")

start_age = st.sidebar.number_input("現在の年齢", 0, 120, 51)
years = st.sidebar.slider("積立期間（年）", 1, 40, 14)
n = years * 12  # 月数

initial_principal_man = st.sidebar.number_input("スタート時点の元本（万円）", 0, 100000, 0)
initial_principal = initial_principal_man * 10000  # 円に変換

# --- ルール① ---
st.sidebar.subheader("積立ルール①")
rule1_start = st.sidebar.number_input("開始年齢①", 0, 120, 51)
rule1_end   = st.sidebar.number_input("終了年齢①", 0, 120, 65)
rule1_monthly = st.sidebar.number_input("毎月の積立額①", 0, 500000, 30000)
rule1_rate    = st.sidebar.number_input("年利①（％）", 0.0, 20.0, 5.0)

# --- ルール② ---
st.sidebar.subheader("積立ルール②")
rule2_start = st.sidebar.number_input("開始年齢②", 0, 120, 65)
rule2_end   = st.sidebar.number_input("終了年齢②", 0, 120, 70)
rule2_monthly = st.sidebar.number_input("毎月の積立額②", 0, 500000, 10000)
rule2_rate    = st.sidebar.number_input("年利②（％）", 0.0, 20.0, 2.0)

# ルールまとめ
rules = [
    {"start": rule1_start, "end": rule1_end, "monthly": rule1_monthly, "rate": rule1_rate},
    {"start": rule2_start, "end": rule2_end, "monthly": rule2_monthly, "rate": rule2_rate},
]

# -----------------------------
# 年齢ごとの積立額・年利を取得
# -----------------------------
def get_params_by_age(age, rules):
    for r in rules:
        if r["start"] <= age < r["end"]:
            return r["monthly"], r["rate"]
    return 0, 0  # 該当なし → 積立なし

# -----------------------------
# 月ごとの積立額・利率リストを作成
# -----------------------------
monthly_list = []
rate_list = []
age_list = []

for i in range(n):
    current_age = start_age + i/12
    m, r_year = get_params_by_age(current_age, rules)
    monthly_list.append(m)
    rate_list.append(r_year / 100 / 12)  # 月利
    age_list.append(current_age)

# -----------------------------
# 元本（累積）
# -----------------------------
principal = initial_principal + np.cumsum(monthly_list)

# -----------------------------
# 資産額（複利）
# -----------------------------
values = []
v = initial_principal
for i in range(n):
    v = v * (1 + rate_list[i]) + monthly_list[i]
    values.append(v)

# -----------------------------
# DataFrame
# -----------------------------
df = pd.DataFrame({
    "月": np.arange(1, n + 1),
    "年齢": age_list,
    "元本": principal,
    "資産額": values,
    "運用益": values - principal
})

# -----------------------------
# 結果表示
# -----------------------------
st.subheader("📊 結果")

final_value = values[-1]
final_principal = principal[-1]
final_profit = final_value - final_principal

col1, col2, col3 = st.columns(3)
col1.metric("最終資産額", f"{final_value:,.0f} 円")
col2.metric("元本", f"{final_principal:,.0f} 円")
col3.metric("運用益", f"{final_profit:,.0f} 円")

# -----------------
# イベント情報
# -----------------
events = {
    57: "高校入学",
    60: "大学入学",
    65: "退職",
    69: "固定ローン〆切"
}
df["イベント"] = df["年齢"].map(events).fillna("")

# -----------------------------
# 年単位のデータに変換
# -----------------------------
df_year = df.iloc[11::12].copy()  # 12ヶ月ごと（年末のデータ）
df_year["年齢"] = df_year["年齢"].astype(int)  # 年齢を整数に
df_year["イベント"] = df_year["年齢"].map(events).fillna("")
df_year.reset_index(drop=True, inplace=True)

# -----------------------------
# 万円単位に変換して見やすくする
# -----------------------------
df_year["元本"] = df_year["元本"] / 10000
df_year["資産額"] = df_year["資産額"] / 10000
df_year["運用益"] = df_year["運用益"] / 10000


# -----------------------------
# グラフ表示
# -----------------------------
st.subheader("📈 資産推移グラフ")

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df["年齢"], df["資産額"] / 10000, label="資産額（万円）", color="blue")
ax.plot(df["年齢"], df["元本"] / 10000, label="元本（万円）", color="green")
ax.fill_between(df["年齢"], df["元本"] / 10000, df["資産額"] / 10000,
                color="orange", alpha=0.3)

ax.set_xlabel("年齢")
ax.set_ylabel("金額（万円）")
ax.legend()
ax.grid(True, linestyle="--", alpha=0.6)

# X軸を整数年齢に
unique_ages = np.arange(int(df["年齢"].min()), int(df["年齢"].max()) + 1)
ax.set_xticks(unique_ages)

# ★ イベント表示（まずは「縦線＋上ラベル」だけ）
y_top = ax.get_ylim()[1]
for age_mark, label in events.items():
    ax.axvline(x=age_mark, color="red", linestyle="--", alpha=0.7)
    ax.text(
        age_mark,
        y_top,
        f"▼ {label}",
        color="red",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )

st.pyplot(fig)

# -----------------
# イベント行を色付け
# -----------------
def highlight_event(row):
    if row["年齢"] in events.keys():
        return ["background-color: #ffe5e5"] * len(row)
    return [""] * len(row)

for age_mark, label in events.items():
    # 縦線
    ax.axvline(x=age_mark, color="red", linestyle="--", alpha=0.7)

    # 年齢が一致する行を取得
    row = df[df["年齢"].astype(int) == age_mark]

    if not row.empty:
        asset = row["資産額"].values[0] / 10000  # 万円に変換

        # ★ 吹き出し（イベント名＋資産額）
        ax.text(
            age_mark,
            asset,
            f"{label}\n{asset:,.0f} 万円",
            ha="left",
            va="bottom",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="#ffe5e5", ec="red")
        )


# -----------------------------
# データ表示
# -----------------------------
st.subheader("📘 年ごとのデータ")
#st.dataframe(df_year.style.apply(highlight_event, axis=1))
st.dataframe(
    df_year.style
        .format({
            "元本": "{:,.0f}",
            "資産額": "{:,.0f}",
            "運用益": "{:,.0f}"
        })
        .apply(highlight_event, axis=1)
)
