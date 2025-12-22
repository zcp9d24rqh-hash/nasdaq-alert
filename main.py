import yfinance as yf
import telegram
import asyncio
import os

# GitHub Secrets에서 정보를 안전하게 가져오는 설정입니다.
# 직접 토큰 번호를 입력하지 마세요!
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

async def get_data(ticker_symbol):
    """최근 10일 데이터를 가져와서 분석합니다."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="10d")
        
        if hist.empty or len(hist) < 2:
            return None
            
        curr = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        diff = curr - prev
        percent = (diff / prev) * 100
        return {"curr": curr, "diff": diff, "percent": percent}
    except Exception as e:
        print(f"Error fetching {ticker_symbol}: {e}")
        return None

def format_row(name, data, is_rate=False):
    if not data:
        return f"⚠️ {name}: 데이터 오류\n"
    
    emoji = "🔴" if data['diff'] > 0 else "🔵" if data['diff'] < 0 else "⚪"
    mark = "▲" if data['diff'] > 0 else "▼" if data['diff'] < 0 else "-"
    unit = "%" if is_rate else ""
    
    return f"{emoji} {name}: {data['curr']:,.2f}{unit} ({mark}{abs(data['percent']):.2f}%)\n"

async def send_all_in_one_report():
    # 티커 설정
    indices = {"나스닥 100": "^NDX", "S&P 500": "^GSPC"}
    currencies = {"달러/원": "USDKRW=X", "엔/달러": "JPY=X", "달러인덱스": "DX-Y.NYB"}
    rates = {"미 국채 10년물": "^TNX", "VIX 공포지수": "^VIX"}
    commodities = {"WTI 유가": "CL=F", "금(Gold)": "GC=F"}
    crypto = {"비트코인": "BTC-USD"}
    inflation = {"기대 인플레이션": "^T10YIE"}

    msg = "<b>🇺🇸 [데일리 매크로 리포트]</b>\n\n"
    
    # 지수
    msg += "<b>[주요 지수]</b>\n"
    for name, ticker in indices.items():
        msg += format_row(name, await get_data(ticker))
        
    # 환율
    msg += "\n<b>[환율 현황]</b>\n"
    for name, ticker in currencies.items():
        msg += format_row(name, await get_data(ticker))

    # 금리 및 암호화폐
    msg += "\n<b>[금리 및 암호화폐]</b>\n"
    for name, ticker in rates.items():
        msg += format_row(name, await get_data(ticker), is_rate=True)
    for name, ticker in crypto.items():
        msg += format_row(name, await get_data(ticker))

    # 원자재 및 물가
    msg += "\n<b>[원자재 및 물가]</b>\n"
    for name, ticker in commodities.items():
        msg += format_row(name, await get_data(ticker))
    for name, ticker in inflation.items():
        msg += format_row(name, await get_data(ticker), is_rate=True)

    msg += "\n<b>[참고: 최근 CPI 발표치]</b>\n📌 헤드라인 CPI: <b>2.6%</b>\n"

    # 전송
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')

if __name__ == "__main__":
    asyncio.run(send_all_in_one_report())
