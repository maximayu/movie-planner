from datetime import datetime, timedelta

import pandas as pd


def parse_datetime(date_value, time_text):
    parsed_time = datetime.strptime(
        str(time_text).strip(),
        "%H:%M",
    ).time()

    return datetime.combine(
        date_value,
        parsed_time,
    )


def normalize_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def validate_inputs(
    movie1,
    movie2,
    selected_date,
    available_start,
    available_end,
):
    errors = []

    movie1 = movie1.strip()
    movie2 = movie2.strip()

    if not movie1:
        errors.append("作品①を入力してください。")

    if not movie2:
        errors.append("作品②を入力してください。")

    if movie1 and movie2 and movie1 == movie2:
        errors.append(
            "作品①と作品②には別の作品を入力してください。"
        )

    available_start_dt = datetime.combine(
        selected_date,
        available_start,
    )
    available_end_dt = datetime.combine(
        selected_date,
        available_end,
    )

    if available_start_dt >= available_end_dt:
        errors.append(
            "空き時間の終了時刻は、"
            "開始時刻より後にしてください。"
        )

    return errors


def prepare_schedule(
    schedule,
    selected_date,
):
    prepared_rows = []
    row_errors = []

    for index, row in schedule.iterrows():
        title = normalize_text(row.get("作品", ""))
        theater = normalize_text(row.get("映画館", ""))
        start_text = normalize_text(row.get("開始", ""))
        end_text = normalize_text(row.get("終了", ""))
        price = row.get("料金", 0)

        try:
            price_value = int(price)
        except (TypeError, ValueError):
            price_value = -1

        completely_empty = (
            not title
            and not theater
            and not start_text
            and not end_text
            and price_value in (0, -1)
        )

        if completely_empty:
            continue

        if (
            not title
            or not theater
            or not start_text
            or not end_text
        ):
            row_errors.append(
                f"{index + 1}行目：未入力の項目があります。"
            )
            continue

        try:
            start_dt = parse_datetime(
                selected_date,
                start_text,
            )
            end_dt = parse_datetime(
                selected_date,
                end_text,
            )
        except ValueError:
            row_errors.append(
                f"{index + 1}行目："
                "開始・終了は「18:30」の形式で"
                "入力してください。"
            )
            continue

        if start_dt >= end_dt:
            row_errors.append(
                f"{index + 1}行目："
                "終了時刻は開始時刻より後にしてください。"
            )
            continue

        if price_value < 0:
            row_errors.append(
                f"{index + 1}行目：料金を数字で入力してください。"
            )
            continue

        prepared_rows.append(
            {
                "作品": title,
                "映画館": theater,
                "開始": start_dt,
                "終了": end_dt,
                "料金": price_value,
            }
        )

    return prepared_rows, row_errors


def find_plans(
    schedule_rows,
    movie1,
    movie2,
    selected_date,
    available_start,
    available_end,
):
    plans = []

    movie1 = movie1.strip()
    movie2 = movie2.strip()

    available_start_dt = datetime.combine(
        selected_date,
        available_start,
    )
    available_end_dt = datetime.combine(
        selected_date,
        available_end,
    )

    movie1_rows = [
        row
        for row in schedule_rows
        if row["作品"] == movie1
    ]
    movie2_rows = [
        row
        for row in schedule_rows
        if row["作品"] == movie2
    ]

    for movie1_row in movie1_rows:
        for movie2_row in movie2_rows:
            for first, second in (
                (movie1_row, movie2_row),
                (movie2_row, movie1_row),
            ):
                if first["開始"] < available_start_dt:
                    continue

                if second["終了"] > available_end_dt:
                    continue

                if first["終了"] > second["開始"]:
                    continue

                same_theater = (
                    first["映画館"]
                    == second["映画館"]
                )
                required_minutes = (
                    10 if same_theater else 30
                )
                earliest_second_start = (
                    first["終了"]
                    + timedelta(minutes=required_minutes)
                )

                if second["開始"] < earliest_second_start:
                    continue

                gap_minutes = int(
                    (
                        second["開始"]
                        - first["終了"]
                    ).total_seconds()
                    / 60
                )

                plans.append(
                    {
                        "1本目": first,
                        "2本目": second,
                        "合計料金": (
                            first["料金"]
                            + second["料金"]
                        ),
                        "待ち時間": gap_minutes,
                        "必要余裕": required_minutes,
                        "終了時刻": second["終了"],
                        "映画館移動": not same_theater,
                    }
                )

    unique_plans = []
    seen = set()

    for plan in plans:
        key = (
            plan["1本目"]["作品"],
            plan["1本目"]["映画館"],
            plan["1本目"]["開始"],
            plan["2本目"]["作品"],
            plan["2本目"]["映画館"],
            plan["2本目"]["開始"],
        )

        if key in seen:
            continue

        seen.add(key)
        unique_plans.append(plan)

    all_prices_missing = bool(unique_plans) and all(
        plan["合計料金"] == 0
        for plan in unique_plans
    )

    if all_prices_missing:
        return sorted(
            unique_plans,
            key=lambda plan: (
                plan["待ち時間"],
                plan["終了時刻"],
            ),
        )

    return sorted(
        unique_plans,
        key=lambda plan: (
            plan["合計料金"],
            plan["待ち時間"],
            plan["終了時刻"],
        ),
    )
