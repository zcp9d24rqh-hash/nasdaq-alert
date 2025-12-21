import yfinance as yf
import telegram
import asyncio
import os

# 1. 설정 (환경변수 또는 직접 입력)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

async def send_nasdaq_report():
    # 1. API로부터 나스닥 100 지수 데이터 수신
    ticker = yf.Ticker("^NDX")
    info = ticker.fast_info
    
    current_price = info['last_price']         # 현재가
    prev_close = info['previous_close']        # 전일 종가
    
    change = current_price - prev_close        # 변동 절대값
    change_percent = (change / prev_close) * 100 # 변동 백분율
    
    # 2. 상승/하락에 따른 색상 이모지 및 스타일 설정
    if change > 0:
        status_emoji = "🔴"  # 상승 시 빨간색
        mark = "▲"
    elif change < 0:
        status_emoji = "🔵"  # 하락 시 파란색
        mark = "▼"
    else:
        status_emoji = "⚪"  # 보합 시 회색
        mark = "-"

    # 3. HTML 형식 메시지 조립 (<b> 태그는 글자를 굵게 만듭니다)
    msg = (
        f"📊 <b>나스닥 100 마감 리포트</b>\n\n"
        f"현재 지수: <b>{current_price:,.2f}</b>\n"
        f"등락 상황: {status_emoji} {mark} {abs(change):.2f} (<b>{change_percent:+.2f}%</b>)"
    )

    # 4. 텔레그램 발송 (parse_mode='HTML' 설정 필수)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')

if __name__ == "__main__":
    asyncio.run(send_nasdaq_report())
