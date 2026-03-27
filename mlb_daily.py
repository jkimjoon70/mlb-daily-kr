import os
import json
import urllib.request
import anthropic
from datetime import datetime, timedelta, timezone

# ── API 설정 ──────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

KST = timezone(timedelta(hours=9))

# ── MLB Stats API: 어제 경기 결과 수집 ────────────────────
def fetch_yesterday_games():
    yesterday = (datetime.now(KST) - timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={yesterday}&hydrate=boxscore,linescore"
    try:
        with urllib.request.urlopen(url, timeout=15) as res:
            data = json.loads(res.read())
    except Exception as e:
        print(f"❌ MLB API 오류: {e}")
        return [], yesterday

    games = []
    for date_entry in data.get("dates", []):
        for g in date_entry.get("games", []):
            status = g.get("status", {}).get("abstractGameState", "")
            if status != "Final":
                continue

            teams = g.get("teams", {})
            away = teams.get("away", {})
            home = teams.get("home", {})

            # 팀명 한글 변환
            TEAM_KR = {
                "Yankees": "뉴욕 양키스", "Dodgers": "LA 다저스",
                "Giants": "샌프란시스코 자이언츠", "Mets": "뉴욕 메츠",
                "Braves": "애틀랜타 브레이브스", "Red Sox": "보스턴 레드삭스",
                "Cubs": "시카고 컵스", "Astros": "휴스턴 애스트로스",
                "Phillies": "필라델피아 필리스", "Cardinals": "세인트루이스 카디널스",
                "Padres": "샌디에이고 파드리스", "Mariners": "시애틀 매리너스",
                "Tigers": "디트로이트 타이거스", "Guardians": "클리블랜드 가디언스",
                "Twins": "미네소타 트윈스", "Orioles": "볼티모어 오리올스",
                "Rays": "탬파베이 레이즈", "Rangers": "텍사스 레인저스",
                "Angels": "LA 에인절스", "Athletics": "오클랜드 애슬레틱스",
                "Blue Jays": "토론토 블루제이스", "White Sox": "시카고 화이트삭스",
                "Royals": "캔자스시티 로열스", "Brewers": "밀워키 브루어스",
                "Reds": "신시내티 레즈", "Pirates": "피츠버그 파이리츠",
                "Nationals": "워싱턴 내셔널스", "Marlins": "마이애미 말린스",
                "Rockies": "콜로라도 로키스", "Diamondbacks": "애리조나 다이아몬드백스",
            }

            def kr(name):
                for en, ko in TEAM_KR.items():
                    if en in name:
                        return ko
                return name

            away_name = away.get("team", {}).get("name", "")
            home_name = home.get("team", {}).get("name", "")
            away_score = away.get("score", 0)
            home_score = home.get("score", 0)

            # 박스스코어 주요 선수
            linescore = g.get("linescore", {})
            innings = linescore.get("innings", [])
            inning_scores = [(i.get("away", {}).get("runs", "-"), i.get("home", {}).get("runs", "-")) for i in innings]

            game_info = {
                "away": kr(away_name),
                "home": kr(home_name),
                "away_score": away_score,
                "home_score": home_score,
                "away_abbr": away.get("team", {}).get("abbreviation", ""),
                "home_abbr": home.get("team", {}).get("abbreviation", ""),
                "innings": inning_scores,
                "winner": kr(away_name) if away_score > home_score else kr(home_name),
            }
            games.append(game_info)

    return games, yesterday


# ── 한국 선수 체크 ────────────────────────────────────────
KOREAN_PLAYERS = ["오타니", "이정후", "김하성", "류현진", "고우석", "장현석",
                  "Ohtani", "Lee", "Kim", "Ryu", "Ko", "Chang"]


# ── Claude API: 한국어 리뷰 생성 ──────────────────────────
def generate_review(games, date_str):
    if not games:
        return "오늘은 경기 데이터를 가져오지 못했습니다."

    games_text = ""
    for g in games:
        games_text += f"- {g['away']} {g['away_score']} vs {g['home']} {g['home_score']} (홈팀 승리: {g['winner']})\n"

    prompt = f"""당신은 MLB 전문 한국어 해설가입니다.

아래는 {date_str} MLB 경기 결과입니다:

{games_text}

다음 조건으로 오늘의 MLB 종합 리뷰를 작성해주세요:
- 전체 600~800자
- 오타니 쇼헤이, 이정후, 김하성 등 한국/일본 선수 활약이 있으면 첫 문단에서 강조
- 가장 인상적인 경기 2~3개를 골라 스토리텔링 방식으로 서술
- ERA, OPS 같은 지표는 괄호로 쉬운 설명 추가
- 내일 주목할 경기 또는 선수를 마지막에 한 줄로 예고
- 딱딱하지 않고 팬 친화적인 문체로 작성
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"리뷰 생성 오류: {str(e)}"


# ── 스코어보드 HTML 생성 ──────────────────────────────────
def build_scoreboard_html(games):
    if not games:
        return "<p style='color:#666;text-align:center;padding:40px'>경기 데이터 없음</p>"

    cards = ""
    for g in games:
        away_bold = "font-weight:800;color:#c9a84c;" if g["away_score"] > g["home_score"] else "color:#888;"
        home_bold = "font-weight:800;color:#c9a84c;" if g["home_score"] > g["away_score"] else "color:#888;"
        cards += f"""
        <div class="score-card">
            <div class="team-row">
                <span class="team-name">{g['away']}</span>
                <span class="score" style="{away_bold}">{g['away_score']}</span>
            </div>
            <div class="team-row">
                <span class="team-name">{g['home']}</span>
                <span class="score" style="{home_bold}">{g['home_score']}</span>
            </div>
            <div class="final-label">FINAL</div>
        </div>"""
    return cards


# ── index.html 생성 ───────────────────────────────────────
def build_index_html(games, review, date_str):
    scoreboard = build_scoreboard_html(games)
    game_count = len(games)
    display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y년 %m월 %d일")

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MLB DAILY KR | {display_date} 경기 리뷰</title>
<meta name="description" content="{display_date} MLB 경기 결과 및 한국어 분석 리뷰">
<!-- AdSense -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXX" crossorigin="anonymous"></script>
<style>
  :root {{
    --bg: #080c10;
    --surface: #0d1117;
    --gold: #c9a84c;
    --gold-dim: rgba(201,168,76,0.15);
    --text: #e8e0d0;
    --muted: #6b7280;
    --border: rgba(201,168,76,0.2);
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Segoe UI',system-ui,sans-serif; min-height:100vh; }}

  /* 헤더 */
  header {{ border-bottom:1px solid var(--border); padding:24px 40px; display:flex; align-items:center; justify-content:space-between; }}
  .logo {{ font-size:1.4rem; font-weight:800; letter-spacing:3px; color:var(--gold); }}
  .logo span {{ color:var(--text); font-weight:300; }}
  .date-badge {{ background:var(--gold-dim); border:1px solid var(--border); padding:6px 16px; border-radius:20px; font-size:0.8rem; color:var(--gold); }}

  /* AdSense 상단 */
  .ad-top {{ max-width:900px; margin:24px auto; padding:0 20px; text-align:center; }}

  /* 메인 */
  main {{ max-width:900px; margin:0 auto; padding:32px 20px; }}

  /* 섹션 타이틀 */
  .section-title {{ font-size:0.7rem; letter-spacing:4px; color:var(--gold); text-transform:uppercase; margin-bottom:20px; display:flex; align-items:center; gap:12px; }}
  .section-title::after {{ content:''; flex:1; height:1px; background:var(--border); }}

  /* 스코어보드 그리드 */
  .scoreboard {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:16px; margin-bottom:40px; }}
  .score-card {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:20px; transition:border-color .2s; }}
  .score-card:hover {{ border-color:var(--gold); }}
  .team-row {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }}
  .team-name {{ font-size:0.85rem; color:var(--muted); }}
  .score {{ font-size:1.6rem; font-weight:700; }}
  .final-label {{ font-size:0.65rem; letter-spacing:2px; color:var(--muted); margin-top:8px; text-align:right; }}

  /* AdSense 중간 */
  .ad-mid {{ margin:32px 0; text-align:center; }}

  /* AI 리뷰 */
  .review-box {{ background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:36px; border-left:4px solid var(--gold); margin-bottom:40px; }}
  .review-box h3 {{ color:var(--gold); font-size:0.75rem; letter-spacing:3px; margin-bottom:20px; }}
  .review-text {{ line-height:1.9; color:#c8c0b0; white-space:pre-wrap; font-size:0.95rem; }}

  /* 통계 요약 */
  .stats-row {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:40px; }}
  .stat-card {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:24px; text-align:center; }}
  .stat-num {{ font-size:2rem; font-weight:800; color:var(--gold); }}
  .stat-label {{ font-size:0.75rem; color:var(--muted); margin-top:6px; letter-spacing:1px; }}

  /* AdSense 하단 */
  .ad-bottom {{ margin:32px 0; text-align:center; }}

  /* 푸터 */
  footer {{ border-top:1px solid var(--border); padding:24px 40px; text-align:center; font-size:0.75rem; color:var(--muted); }}
  footer a {{ color:var(--gold); text-decoration:none; }}

  @media(max-width:600px) {{
    header {{ padding:16px 20px; flex-direction:column; gap:12px; }}
    .stats-row {{ grid-template-columns:repeat(3,1fr); }}
    .review-box {{ padding:24px 20px; }}
  }}
</style>
</head>
<body>

<header>
  <div class="logo">MLB<span> DAILY</span> KR</div>
  <div class="date-badge">{display_date}</div>
</header>

<!-- AdSense 상단 -->
<div class="ad-top">
  <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-XXXXXXXXXX" data-ad-slot="1111111111" data-ad-format="auto" data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>

<main>

  <!-- 통계 요약 -->
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-num">{game_count}</div>
      <div class="stat-label">GAMES PLAYED</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{display_date.split('월')[0].split('년')[1].strip()}</div>
      <div class="stat-label">MONTH</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">KR</div>
      <div class="stat-label">LANGUAGE</div>
    </div>
  </div>

  <!-- 스코어보드 -->
  <div class="section-title">경기 결과 스코어보드</div>
  <div class="scoreboard">
    {scoreboard}
  </div>

  <!-- AdSense 중간 -->
  <div class="ad-mid">
    <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-XXXXXXXXXX" data-ad-slot="2222222222" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
  </div>

  <!-- AI 리뷰 -->
  <div class="section-title">AI 경기 분석 리뷰</div>
  <div class="review-box">
    <h3>CLAUDE AI · DAILY ANALYSIS</h3>
    <div class="review-text">{review}</div>
  </div>

  <!-- AdSense 하단 -->
  <div class="ad-bottom">
    <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-XXXXXXXXXX" data-ad-slot="3333333333" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
  </div>

</main>

<footer>
  <p>MLB DAILY KR · 매일 자동 업데이트 · <a href="games/">지난 경기 보기</a></p>
  <p style="margin-top:8px">Powered by MLB Stats API + Claude AI · {display_date}</p>
</footer>

</body>
</html>"""


# ── games/ 아카이브 HTML ──────────────────────────────────
def build_game_archive_html(games, review, date_str):
    """games/YYYYMMDD-report.html 저장용 (index.html과 동일 내용)"""
    return build_index_html(games, review, date_str)


# ── 메인 실행 ─────────────────────────────────────────────
def main():
    print("⚾ MLB DAILY KR 리포트 생성 시작...")

    # 1. 데이터 수집
    games, date_str = fetch_yesterday_games()
    print(f"📅 날짜: {date_str} | 경기 수: {len(games)}")

    # 2. Claude AI 리뷰 생성
    print("🤖 Claude AI 리뷰 생성 중...")
    review = generate_review(games, date_str)

    # 3. index.html 저장
    index_html = build_index_html(games, review, date_str)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("✅ index.html 업데이트 완료")

    # 4. games/ 아카이브 저장
    os.makedirs("games", exist_ok=True)
    file_date = date_str.replace("-", "")
    archive_path = f"games/{file_date}-report.html"
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(build_game_archive_html(games, review, date_str))
    print(f"✅ {archive_path} 아카이브 저장 완료")

    # 5. data/ JSON 저장 (원시 데이터 보관)
    os.makedirs("data", exist_ok=True)
    with open(f"data/{file_date}.json", "w", encoding="utf-8") as f:
        json.dump({"date": date_str, "games": games, "review": review}, f, ensure_ascii=False, indent=2)
    print(f"✅ data/{file_date}.json 저장 완료")

    print("\n🎉 모든 작업 완료!")


if __name__ == "__main__":
    main()
