from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st

from config import THEATER_URLS
from planner import (
    find_plans,
    prepare_schedule,
    validate_inputs,
)
from scraper import (
    extract_humax_schedule_for_date,
    fetch_theater_page,
)


st.set_page_config(
    page_title="Movie Planner",
    page_icon="🎬",
    layout="wide",
)

EMPTY_SCHEDULE = pd.DataFrame(
    {
        "作品": ["", "", "", ""],
        "映画館": ["", "", "", ""],
        "開始": ["", "", "", ""],
        "終了": ["", "", "", ""],
        "料金": [0, 0, 0, 0],
    }
)

if "schedule_df" not in st.session_state:
    st.session_state.schedule_df = (
        EMPTY_SCHEDULE.copy()
    )

# st.data_editorに固定keyを渡すと、次回以降のrerunで
# 新しく渡したdata引数よりsession_state[key]の値が
# 優先されてしまい、再検索しても表示が更新されない。
# そのため、新しいデータをセットするたびにこの番号を
# インクリメントし、keyを変えてウィジェットを作り直す。
if "schedule_editor_version" not in st.session_state:
    st.session_state.schedule_editor_version = 0


def show_plans(plans: list[dict]) -> None:
    st.header("⑥ 検索結果")

    if not plans:
        st.warning(
            "条件に合うハシゴプランが"
            "見つかりませんでした。"
        )
        return

    st.success(
        f"{len(plans)}件のプランが"
        "見つかりました。"
    )

    if all(
        plan["合計料金"] == 0
        for plan in plans
    ):
        st.info(
            "料金未入力のため、"
            "待ち時間が短い順に表示しています。"
        )

    for rank, plan in enumerate(
        plans,
        start=1,
    ):
        first = plan["1本目"]
        second = plan["2本目"]

        if rank == 1:
            result_title = "🥇 おすすめ候補"
        elif rank == 2:
            result_title = "🥈 第2候補"
        elif rank == 3:
            result_title = "🥉 第3候補"
        else:
            result_title = f"候補 {rank}"

        with st.container(border=True):
            st.subheader(result_title)

            price_col, wait_col, end_col = st.columns(3)

            price_col.metric(
                "合計料金",
                (
                    f"{plan['合計料金']:,}円"
                    if plan["合計料金"]
                    else "未入力"
                ),
            )
            wait_col.metric(
                "待ち時間",
                f"{plan['待ち時間']}分",
            )
            end_col.metric(
                "終了時刻",
                plan["終了時刻"].strftime(
                    "%H:%M"
                ),
            )

            st.markdown(
                f"""
### 1本目
**{first['開始'].strftime('%H:%M')}〜{first['終了'].strftime('%H:%M')}**  
🎬 {first['作品']}  
📍 {first['映画館']}

### 2本目
**{second['開始'].strftime('%H:%M')}〜{second['終了'].strftime('%H:%M')}**  
🎬 {second['作品']}  
📍 {second['映画館']}
"""
            )


st.title("🎬 Movie Planner")
st.write(
    "観たい2作品と空き時間を入力すると、"
    "公式上映情報からハシゴ候補を検索します。"
)


st.header("① 観たい作品")

movie1 = st.text_input(
    "作品①",
    placeholder="例：ちいかわ",
)

movie2 = st.text_input(
    "作品②",
    placeholder="例：クレヨンしんちゃん",
)


st.header("② 空き時間")

date_col, start_col, end_col = st.columns(3)

with date_col:
    selected_date = st.date_input("日付")

with start_col:
    available_start = st.time_input(
        "開始時刻",
        value=datetime.strptime(
            "14:00",
            "%H:%M",
        ).time(),
        step=timedelta(minutes=5),
    )

with end_col:
    available_end = st.time_input(
        "終了時刻",
        value=datetime.strptime(
            "23:30",
            "%H:%M",
        ).time(),
        step=timedelta(minutes=5),
    )


st.header("③ 対象映画館")

selected_theaters = st.multiselect(
    "上映情報を調べる映画館を選んでください",
    options=list(THEATER_URLS.keys()),
    default=["池袋HUMAXシネマズ"],
)

search_button = st.button(
    "🚀 上映情報を取得してプラン検索",
    type="primary",
    width="stretch",
)

search_ready = False

if search_button:
    input_errors = validate_inputs(
        movie1,
        movie2,
        selected_date,
        available_start,
        available_end,
    )

    if input_errors:
        for error in input_errors:
            st.error(error)

    elif not selected_theaters:
        st.warning(
            "映画館を1館以上選んでください。"
        )

    else:
        unsupported = [
            theater
            for theater in selected_theaters
            if theater != "池袋HUMAXシネマズ"
        ]

        if unsupported:
            st.info(
                "現在の自動取得対応は"
                "池袋HUMAXシネマズです。"
            )

        auto_rows = []

        if (
            "池袋HUMAXシネマズ"
            in selected_theaters
        ):
            with st.spinner(
                "上映情報を取得しています..."
            ):
                try:
                    page = fetch_theater_page(
                        THEATER_URLS[
                            "池袋HUMAXシネマズ"
                        ]
                    )

                    auto_rows = (
                        extract_humax_schedule_for_date(
                            page["html"],
                            [movie1, movie2],
                            selected_date,
                        )
                    )

                except (
                    requests.RequestException,
                    ValueError,
                ) as error:
                    st.error(
                        "上映情報の取得に失敗しました。"
                    )
                    st.caption(str(error))

        if auto_rows:
            editor_rows = [
                {
                    "作品": row["作品"],
                    "映画館": row["映画館"],
                    "開始": row["開始"],
                    "終了": row["終了"],
                    "料金": row["料金"],
                }
                for row in auto_rows
            ]

            st.session_state.schedule_df = (
                pd.DataFrame(editor_rows)
            )
            # 新しいデータで表を作り直させるためkeyを更新する
            st.session_state.schedule_editor_version += 1
            search_ready = True

            st.success(
                f"{selected_date:%Y/%m/%d}の上映回を"
                f"{len(editor_rows)}件取得しました。"
            )

        elif (
            "池袋HUMAXシネマズ"
            in selected_theaters
        ):
            st.warning(
                "選択日の上映回を取得できませんでした。"
                "作品名を短めにして再検索してください。"
            )


st.header("④ 上映回一覧")

edited_schedule = st.data_editor(
    st.session_state.schedule_df,
    num_rows="dynamic",
    width="stretch",
    hide_index=True,
    key=(
        "schedule_editor_"
        f"{st.session_state.schedule_editor_version}"
    ),
    column_config={
        "作品": st.column_config.TextColumn(
            "作品",
            required=True,
        ),
        "映画館": st.column_config.TextColumn(
            "映画館",
            required=True,
        ),
        "開始": st.column_config.TextColumn(
            "開始",
            required=True,
        ),
        "終了": st.column_config.TextColumn(
            "終了",
            required=True,
        ),
        "料金": st.column_config.NumberColumn(
            "料金",
            min_value=0,
            step=100,
            format="%d円",
            required=True,
        ),
    },
)

st.session_state.schedule_df = (
    edited_schedule.copy()
)


st.header("⑤ 検索")

manual_search_button = st.button(
    "🔍 修正した上映回で再検索",
    width="stretch",
)

if search_ready or manual_search_button:
    input_errors = validate_inputs(
        movie1,
        movie2,
        selected_date,
        available_start,
        available_end,
    )

    if input_errors:
        for error in input_errors:
            st.error(error)

    else:
        schedule_rows, schedule_errors = (
            prepare_schedule(
                edited_schedule,
                selected_date,
            )
        )

        if schedule_errors:
            for error in schedule_errors:
                st.error(error)

        elif not schedule_rows:
            st.warning(
                "上映回がありません。"
            )

        else:
            plans = find_plans(
                schedule_rows,
                movie1,
                movie2,
                selected_date,
                available_start,
                available_end,
            )

            show_plans(plans)