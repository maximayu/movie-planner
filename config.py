# 映画館名と公式上映スケジュールURL
THEATER_URLS = {
    "池袋HUMAXシネマズ": (
        "https://humax-cinema.co.jp/ikebukuro/schedule"
    ),
    "グランドシネマサンシャイン池袋": (
        "https://www.cinemasunshine.co.jp/theater/gdcs/"
    ),
    "新宿ピカデリー": (
        "https://www.smt-cinema.com/sp/site/shinjuku/day.html"
    ),
    "MOVIXさいたま": (
        "https://www.smt-cinema.com/sp/site/saitama/day.html"
    ),
}

ALLOWED_DOMAINS = {
    "humax-cinema.co.jp",
    "www.humax-cinema.co.jp",
    "cinemasunshine.co.jp",
    "www.cinemasunshine.co.jp",
    "smt-cinema.com",
    "www.smt-cinema.com",
}

# SMT系（新宿ピカデリー・MOVIXさいたま等）の
# 日別上映スケジュールHTML取得に必要な劇場コード。
#
# URLの形式：
# https://www.smt-cinema.com/html/site/pc/schedule/
#   {site_code}_{theater_code}_{YYYYMMDD}_schedule_daily_movie_area.html
#
# ここに登録されている劇場だけが自動取得の対象になる。
# 未登録の劇場（MOVIXさいたま等）はDevToolsで調査後、
# 同じ形式で追記する。
SMT_THEATER_CODES = {
    "新宿ピカデリー": {
        "site_code": "s0100",
        "theater_code": "1051",
    },
}