import streamlit as st

# -----------------------------
# タイトル
# -----------------------------
st.title("🎬 Movie Planner")

st.write("映画ハシゴ検索へようこそ！")

st.divider()

# -----------------------------
# 観たい作品
# -----------------------------
st.header("🎥 観たい作品")

movie1 = st.text_input(
    "作品①",
    placeholder="例：ヌーヴェルヴァーグ"
)

movie2 = st.text_input(
    "作品②",
    placeholder="例：大統領のケーキ"
)

st.divider()

# -----------------------------
# 空き時間
# -----------------------------
st.header("📅 空き時間")

date = st.date_input("日付")

start_time = st.time_input(
    "開始時刻"
)

end_time = st.time_input(
    "終了時刻"
)

# -----------------------------
# 検索ボタン
# -----------------------------
if st.button("🔍 プランを検索"):

    st.success("検索ボタンが押されました！")

    st.write("作品①：", movie1)
    st.write("作品②：", movie2)

    st.write("日付：", date)
    st.write("開始：", start_time)
    st.write("終了：", end_time)
