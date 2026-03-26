import os
import google.generativeai as genai
from datetime import datetime

# 1. 깃허브 금고에서 열쇠(API 키) 가져오기
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_mlb_report():
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    file_date = today.strftime("%Y%m%d")
    
    # 2. 제미나이에게 오늘 경기 분석 지시
    prompt = f"오늘({today_str}) MLB 양키스 vs 자이언츠 개막전 결과를 분석해서 저지의 홈런과 이정후의 데뷔 안타 소식을 포함해 Obsidian MLB 블로그용으로 멋지게 요약해줘."
    response = model.generate_content(prompt)
    insight = response.text

    # 3. 준 님의 럭셔리 디자인 템플릿
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>OBSIDIAN MLB | {today_str}</title>
        <style>
            body {{ background: #080c10; color: #e8e0d0; font-family: sans-serif; padding: 40px; }}
            .card {{ background: #0d1117; border: 1px solid rgba(201,168,76,0.4); border-radius: 20px; padding: 40px; max-width: 850px; margin: auto; box-shadow: 0 15px 45px rgba(0,0,0,0.7); }}
            .gold {{ color: #c9a84c; }}
            .score-row {{ display: flex; justify-content: space-around; align-items: center; margin: 40px 0; font-size: 3.5rem; font-weight: 800; }}
            .analysis-box {{ background: rgba(255,255,255,0.02); padding: 25px; border-radius: 12px; border-left: 5px solid #c9a84c; white-space: pre-wrap; line-height: 1.8; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2 class="gold">🏆 DAILY GAME INSIGHT</h2>
            <div class="score-row">
                <div>NYY <span class="gold">7</span></div>
                <div style="color: #333; font-size: 1.5rem;">VS</div>
                <div>SFG <span style="color: #777;">0</span></div>
            </div>
            <div class="analysis-box">
                <h3 class="gold" style="margin-top:0;">🤖 AI AGENT ANALYSIS</h3>
                {insight}
            </div>
            <p style="text-align: right; font-size: 0.8rem; color: #444; margin-top: 50px;">* Powered by Gemini AI Agent for Jun</p>
        </div>
    </body>
    </html>
    """

    # 4. 파일 저장
    os.makedirs("games", exist_ok=True)
    with open(f"games/{file_date}-report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ 리포트 생성 성공!")

if __name__ == "__main__":
    generate_mlb_report()
