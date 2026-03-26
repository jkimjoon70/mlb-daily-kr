import os
import google.generativeai as genai
from datetime import datetime

# 1. 깃허브 금고(Secrets)에서 API 키 가져오기
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# API 설정 및 모델 로드 (가장 안정적인 1.5 Flash 모델 사용)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_mlb_report():
    # 현재 날짜 설정
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    file_date = today.strftime("%Y%m%d")
    
    # 2. 제미나이에게 오늘 경기 분석 지시 (프롬프트)
    prompt = f"""
    오늘({today_str}) MLB 양키스 vs 자이언츠 개막전 결과를 분석해줘. 
    양키스가 7:0으로 승리했고, 애런 저지의 2점 홈런과 이정후의 1안타 1볼넷 데뷔 소식이 핵심이야.
    이 내용을 바탕으로 준(Jun)의 Obsidian MLB 블로그에 올릴 수 있도록 전문적이고 통찰력 있는 분석 리포트를 한글로 작성해줘.
    """
    
    try:
        response = model.generate_content(prompt)
        insight = response.text
    except Exception as e:
        insight = f"리포트 생성 중 오류가 발생했습니다: {str(e)}"

    # 3. 준 님의 럭셔리 Obsidian MLB 디자인 템플릿 (HTML/CSS)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>OBSIDIAN MLB | {today_str}</title>
        <style>
            body {{ background: #080c10; color: #e8e0d0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px; line-height: 1.8; }}
            .card {{ background: #0d1117; border: 1px solid rgba(201,168,76,0.3); border-radius: 20px; padding: 40px; max-width: 850px; margin: auto; box-shadow: 0 15px 45px rgba(0,0,0,0.6); }}
            .gold {{ color: #c9a84c; }}
            .score-row {{ display: flex; justify-content: space-around; align-items: center; margin: 40px 0; font-size: 3.5rem; font-weight: 800; }}
            .analysis-box {{ background: rgba(255,255,255,0.02); padding: 30px; border-radius: 12px; border-left: 5px solid #c9a84c; white-space: pre-wrap; }}
            .footer {{ text-align: right; font-size: 0.8rem; color: #555; margin-top: 50px; font-style: italic; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2 class="gold">🏆 DAILY GAME INSIGHT</h2>
            <p style="color: #666; margin-bottom: 20px;">{today_str} · MLB Opening Night Report</p>
            
            <div class="score-row">
                <div>NYY <span class="gold">7</span></div>
                <div style="color: #333; font-size: 1.5rem;">VS</div>
                <div>SFG <span style="color: #777;">0</span></div>
            </div>
            
            <div class="analysis-box">
                <h3 class="gold" style="margin-top:0; margin-bottom:15px;">🤖 AI AGENT ANALYSIS</h3>
                {insight}
            </div>
            
            <div class="footer">* Obsidian MLB Integrated Solution | Powered by Gemini AI Agent for Jun</div>
        </div>
    </body>
    </html>
    """

    # 4. 파일 저장 (games 폴더에 자동 저장)
    os.makedirs("games", exist_ok=True)
    file_path = f"games/{file_date}-report.html"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ {file_path} 리포트 생성 성공!")

if __name__ == "__main__":
    generate_mlb_report()
