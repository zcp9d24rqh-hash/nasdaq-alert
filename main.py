import yfinance as yf
import telegram
import asyncio
import os

# GitHub Secrets에서 정보 가져오기
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

async def get_data(ticker_symbol):
    """티커를 입력받아 현재가, 전일종가, 등락율을 반환합니다."""
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="2d")
    if len(hist) < 2: return None
    
    curr = hist['Close'].iloc[-1]
    prev = hist['Close'].iloc[-2]
    diff = curr - prev
    percent = (diff / prev) * 100
    return {"curr": curr, "diff": diff, "percent": percent}

def format_row(name, data, is_rate=False):
    """지표별 한 줄 메시지를 생성합니다."""
    if not data: return f"{name}: 데이터 오류\n"
    
    # 주식/환율/원자재는 상승시 빨간색, 하락시 파란색 (관례 기준)
    # 단, 금리나 공포지수는 상황에 따라 해석이 다르나 동일 규칙 적용
    emoji = "🔴" if data['diff'] > 0 else "🔵" if data['diff'] < 0 else "⚪"
    mark = "▲" if data['diff'] > 0 else "▼" if data['diff'] < 0 else "-"
    
    unit = "%" if is_rate else "" # 금리는 뒤에 % 표시
    return f"{emoji} {name}: {data['curr']:,.2f}{unit} ({mark}{abs(data['percent']):.2f}%)\n"

async def send_all_in_one_report():
    # 1. 수집할 지표 설정 (이름: 티커)
    indices = {"나스닥 100": "^NDX", "S&P 500": "^GSPC"}
    currencies = {"달러/원": "USDKRW=X", "엔/달러": "JPY=X", "달러인덱스": "DX-Y.NYB"}
    rates = {"미 국채 10년물": "^TNX", "VIX 공포지수": "^VIX"}
    commodities = {"WTI 유가": "CL=F", "금(Gold)": "GC=F"}

    # 2. 데이터 수집
    msg = "<b>🇺🇸 [데일리 매크로 리포트]</b>\n\n"
    
    msg += "<b>[주요 지수]</b>\n"
    for name, ticker in indices.items():
        msg += format_row(name, await get_data(ticker))
        
    msg += "\n<b>[환율 현황]</b>\n"
    for name, ticker in currencies.items():
        msg += format_row(name, await get_data(ticker))

    msg += "\n<b>[금리 및 변동성]</b>\n"
    for name, ticker in rates.items():
        msg += format_row(name, await get_data(ticker), is_rate=True)

    msg += "\n<b>[원자재]</b>\n"
    for name, ticker in commodities.items():
        msg += format_row(name, await get_data(ticker))

    # 3. 텔레그램 전송
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')

if __name__ == "__main__":
    asyncio.run(send_all_in_one_report())
