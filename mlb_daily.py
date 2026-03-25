"""
MLB 매일 경기 결과 수집 스크립트
- MLB Stats API (무료, 인증 불필요)
- 경기 스코어, 선발투수, 홈런/주요타자 기록
- 한국어 팀명 자동 변환
- JSON + HTML 동시 저장
"""

import urllib.request
import json
import os
from datetime import datetime, timezone

# ─────────────────────────────────────────
# 한국어 팀명 매핑
# ─────────────────────────────────────────
TEAM_KR = {
    "Arizona Diamondbacks": "애리조나 다이아몬드백스",
    "Atlanta Braves": "애틀랜타 브레이브스",
    "Baltimore Orioles": "볼티모어 오리올스",
    "Boston Red Sox": "보스턴 레드삭스",
    "Chicago Cubs": "시카고 컵스",
    "Chicago White Sox": "시카고 화이트삭스",
    "Cincinnati Reds": "신시내티 레즈",
    "Cleveland Guardians": "클리블랜드 가디언스",
    "Colorado Rockies": "콜로라도 로키스",
    "Detroit Tigers": "디트로이트 타이거스",
    "Houston Astros": "휴스턴 애스트로스",
    "Kansas City Royals": "캔자스시티 로열스",
    "Los Angeles Angels": "로스앤젤레스 에인절스",
    "Los Angeles Dodgers": "로스앤젤레스 다저스",
    "Miami Marlins": "마이애미 말린스",
    "Milwaukee Brewers": "밀워키 브루어스",
    "Minnesota Twins": "미네소타 트윈스",
    "New York Mets": "뉴욕 메츠",
    "New York Yankees": "뉴욕 양키스",
    "Oakland Athletics": "오클랜드 애슬레틱스",
    "Philadelphia Phillies": "필라델피아 필리스",
    "Pittsburgh Pirates": "피츠버그 파이리츠",
    "San Diego Padres": "샌디에이고 파드리스",
    "San Francisco Giants": "샌프란시스코 자이언츠",
    "Seattle Mariners": "시애틀 매리너스",
    "St. Louis Cardinals": "세인트루이스 카디널스",
    "Tampa Bay Rays": "탬파베이 레이스",
    "Texas Rangers": "텍사스 레인저스",
    "Toronto Blue Jays": "토론토 블루제이스",
    "Washington Nationals": "워싱턴 내셔널스",
    "Athletics": "오클랜드 애슬레틱스",
}

def kr(name):
    return TEAM_KR.get(name, name)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "mlb-daily-kr/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def get_games(date_str):
    """날짜별 경기 목록 가져오기 (YYYY-MM-DD)"""
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=linescore,probablePitcher,boxscore"
    data = fetch(url)
    games = []
    for date in data.get("dates", []):
        for g in date.get("games", []):
            games.append(parse_game(g))
    return games

def parse_game(g):
    status = g.get("status", {}).get("detailedState", "")
    away = g["teams"]["away"]
    home = g["teams"]["home"]
    away_name = away["team"]["name"]
    home_name = home["team"]["name"]

    # 스코어
    away_score = away.get("score", "-")
    home_score = home.get("score", "-")

    # 선발투수
    away_pitcher = away.get("probablePitcher", {}).get("fullName", "미정")
    home_pitcher = home.get("probablePitcher", {}).get("fullName", "미정")

    # 홈런 & 주요타자 (boxscore에서 추출)
    homers = []
    top_batters = []
    boxscore = g.get("boxscore", {})
    for side in ["away", "home"]:
        players = boxscore.get("teams", {}).get(side, {}).get("players", {})
        team_name = away_name if side == "away" else home_name
        for pid, p in players.items():
            stats = p.get("stats", {}).get("batting", {})
            hr = stats.get("homeRuns", 0)
            hits = stats.get("hits", 0)
            rbi = stats.get("rbi", 0)
            name = p.get("person", {}).get("fullName", "")
            if hr and hr > 0:
                homers.append(f"{name} ({kr(team_name)}) {hr}HR")
            if hits and hits >= 2:
                top_batters.append(f"{name} ({kr(team_name)}) {hits}안타 {rbi}타점")

    return {
        "status": status,
        "away": kr(away_name),
        "home": kr(home_name),
        "away_en": away_name,
        "home_en": home_name,
        "away_score": away_score,
        "home_score": home_score,
        "away_pitcher": away_pitcher,
        "home_pitcher": home_pitcher,
        "homers": homers,
        "top_batters": top_batters[:5],
        "game_pk": g.get("gamePk"),
    }

def save_json(games, date_str):
    path = f"data/{date_str}.json"
    os.makedirs("data", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"date": date_str, "games": games}, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON 저장: {path}")
    return path

def save_html(games, date_str):
    os.makedirs("data", exist_ok=True)

    finished = [g for g in games if "Final" in g["status"] or "완료" in g["status"]]
    scheduled = [g for g in games if g not in finished]

    cards = ""
    for g in games:
        is_final = "Final" in g["status"]
        score_block = f"""
        <div class="score-row">
          <span class="team">{g['away']}</span>
          <span class="score {'winner' if is_final and g['away_score'] > g['home_score'] else ''}">{g['away_score']}</span>
          <span class="vs">:</span>
          <span class="score {'winner' if is_final and g['home_score'] > g['away_score'] else ''}">{g['home_score']}</span>
          <span class="team">{g['home']}</span>
        </div>
        """ if is_final else f"""
        <div class="score-row">
          <span class="team">{g['away']}</span>
          <span class="vs-badge">VS</span>
          <span class="team">{g['home']}</span>
        </div>
        """

        homers_html = ""
        if g["homers"]:
            homers_html = f"<div class='detail'><b>💣 홈런:</b> {' / '.join(g['homers'])}</div>"

        batters_html = ""
        if g["top_batters"]:
            batters_html = f"<div class='detail'><b>🔥 주요타자:</b> {' / '.join(g['top_batters'])}</div>"

        status_badge = f"<span class='badge {'final' if is_final else 'scheduled'}'>{g['status']}</span>"

        cards += f"""
        <div class="card">
          {status_badge}
          {score_block}
          <div class="pitchers">
            ⚾ 선발: {g['away_pitcher']} vs {g['home_pitcher']}
          </div>
          {homers_html}
          {batters_html}
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MLB 경기 결과 | {date_str}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #0d1117; color: #e6edf3; padding: 20px; }}
  h1 {{ text-align: center; font-size: 1.6rem; margin-bottom: 6px; color: #58a6ff; }}
  .subtitle {{ text-align: center; color: #8b949e; margin-bottom: 24px; font-size: 0.9rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; max-width: 1100px; margin: 0 auto; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 18px; }}
  .badge {{ display: inline-block; font-size: 0.75rem; padding: 2px 10px; border-radius: 20px; margin-bottom: 10px; }}
  .badge.final {{ background: #1f6feb; color: #fff; }}
  .badge.scheduled {{ background: #21262d; color: #8b949e; }}
  .score-row {{ display: flex; align-items: center; justify-content: space-between; margin: 8px 0; }}
  .team {{ font-size: 0.95rem; font-weight: 600; flex: 1; }}
  .score {{ font-size: 1.8rem; font-weight: 700; width: 40px; text-align: center; color: #8b949e; }}
  .score.winner {{ color: #3fb950; }}
  .vs {{ color: #8b949e; font-size: 1.2rem; margin: 0 8px; }}
  .vs-badge {{ background: #21262d; color: #58a6ff; font-weight: 700; padding: 4px 12px; border-radius: 6px; }}
  .pitchers {{ font-size: 0.82rem; color: #8b949e; margin: 8px 0 6px; }}
  .detail {{ font-size: 0.82rem; color: #e6edf3; margin-top: 6px; line-height: 1.5; }}
</style>
</head>
<body>
<h1>⚾ MLB 경기 결과</h1>
<p class="subtitle">{date_str} | 총 {len(games)}경기 | 완료 {len(finished)}경기</p>
<div class="grid">
{cards}
</div>
</body>
</html>"""

    path = f"data/{date_str}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML 저장: {path}")
    return path

def main():
    # 오늘 날짜 (미국 동부 기준으로 하루 전 경기 확인하려면 timedelta 조정)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"📅 날짜: {today}")

    games = get_games(today)
    if not games:
        print("❌ 오늘 경기 없음")
        return

    print(f"🎮 총 {len(games)}경기 발견")
    save_json(games, today)
    save_html(games, today)

    # 콘솔 미리보기
    print("\n─── 경기 결과 미리보기 ───")
    for g in games:
        if "Final" in g["status"]:
            print(f"✅ {g['away']} {g['away_score']} : {g['home_score']} {g['home']}")
        else:
            print(f"🕐 {g['away']} vs {g['home']} ({g['status']})")

if __name__ == "__main__":
    main()
