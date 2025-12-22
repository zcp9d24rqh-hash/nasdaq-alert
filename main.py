Python
import yfinance as yf
import telegram
import asyncio
import os

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

async def get_data(ticker_symbol):
    """데이터 수집 기간을 10일로 늘려 휴장기 영향을 최소화합니다."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        # 휴장일이 긴 연말연시를 대비해 10일치 데이터를 가져옵니다.
        hist = ticker.history(period="10d")
        
        # 데이터가 아예 없거나 부족할 경우 예외 처리
        if hist.empty or len(hist) < 2:
            print(f"⚠️ {ticker_symbol}: 충분한 데이터를 찾을 수 없습니다.")
            return None
            
        curr = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        diff = curr - prev
        percent = (diff / prev) * 100
        return {"curr": curr, "diff": diff, "percent": percent}
    except Exception as e:
        print(f"❌ {ticker_symbol} 데이터 호출 중 에러 발생: {e}")
        return None

def format_row(name, data, is_rate=False):
    if not data:
        # 오류 발생 시 사용자에게 알림
        return f"⚠️ {name}: 데이터 불러오기 실패\n"
    
    emoji = "🔴" if data['diff'] > 0 else "🔵" if data['diff'] < 0 else "⚪"
    mark = "▲" if data['diff'] > 0 else "▼" if data['diff'] < 0 else "-"
    unit = "%" if is_rate else ""
    
    return f"{emoji} {name}: {data['curr']:,.2f}{unit} ({mark}{abs(data['percent']):.2f}%)\n"

async def send_all_in_one_report():
    # 가장 표준적이고 안정적인 티커로 재구성
    indices = {"나스닥 100": "^NDX", "S&P 500": "^GSPC"}
    currencies = {"달러/원": "USDKRW=X", "엔/달러": "JPY=X", "달러인덱스": "DX-Y.NYB"}
    rates = {"미 국채 10년물": "^TNX", "VIX 공포지수": "^VIX"}
    commodities = {"WTI 유가": "CL=F", "금(Gold)": "GC=F"}
    crypto = {"비트코인": "BTC-USD"}
    inflation = {"기대 인플레이션": "^T10YIE"}

    msg = "<b>🇺🇸 [데일리 매크로 리포트]</b>\n\n"
    
    # 헬퍼 함수로 섹션 반복 처리
    sections = [
        ("주요 지수", indices),
        ("환율 현황", currencies),
        ("금리 및 암호화폐", rates, crypto),
        ("원자재 및 물가", commodities, inflation)
    ]

    for section in sections:
        msg += f"<b>[{section[0]}]</b>\n"
        for i in range(1, len(section)):
            for name, ticker in section[i].items():
                is_rate = name in ["미 국채 10년물", "VIX 공포지수", "기대 인플레이션"]
                msg += format_row(name, await get_data(ticker), is_rate)
        msg += "\n"

    msg += "<b>[참고: 최근 CPI 발표치]</b>\n📌 헤드라인 CPI: <b>2.6%</b>\n"

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')

if __name__ == "__main__":
    asyncio.run(send_all_in_one_report())
