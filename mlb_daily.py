name: MLB Daily Review Bot

on:
  schedule:
    - cron: "0 11 * * *"  # 매일 한국 시간 20:00 실행
  workflow_dispatch:      # 수동 실행 버튼 활성화

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install google-generativeai
      - name: Run bot
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python mlb_daily.py
      - name: Commit and Push
        run: |
          git config --global user.name "AI-Agent"
          git config --global user.email "agent@mlb-daily.kr"
          git add .
          git commit -m "Auto-update MLB review: $(date +%Y-%m-%d)" || echo "No changes"
          git push
