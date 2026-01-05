import yfinance as yf
import telegram
import asyncio
import os

# GitHub Secrets 설정
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

async def get_data(ticker_symbol):
    """최근 데이터를 가져와서 분석합니다."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        # 휴장일을 고려해 7일치 데이터를 가져옵니다.
        hist = ticker.history(period="7d")
        
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
    # '나스닥 100(^NDX)'을 '나스닥 종합지수(^IXIC)'로 변경했습니다.
    indices = {
        "나스닥 종합": "^IXIC", 
        "S&P 500": "^GSPC",
        "코스피": "^KS11"
    }
    
    currencies = {
        "달러/원": "USDKRW=X", 
        "달러인덱스": "DX-Y.NYB"
    }
    
    rates = {"미 국채 10년물": "^TNX", "VIX 공포지수": "^VIX"}
    commodities = {"WTI 유가": "CL=F", "금(Gold)": "GC=F"}
    crypto = {"비트코인": "BTC-USD"}

    msg = "<b>📊 [데일리 매크로 리포트]</b>\n\n"
    
    # 각 섹션별 데이터 처리
    sections = [
        ("주요 지수", indices, False),
        ("환율 현황", currencies, False),
        ("채권 및 암호화폐", {**rates, **crypto}, True), # 금리/비트코인 혼합
        ("원자재 현황", commodities, False)
    ]

    for section_name, items, is_rate in sections:
        msg += f"<b>[{section_name}]</b>\n"
        for name, ticker in items.items():
            # 비트코인이나 지수는 퍼센트 단위가 아니므로 개별 처리 가능하지만 
            # 편의상 기존 format_row 로직을 유지합니다.
            msg += format_row(name, await get_data(ticker), is_rate if "국채" in name else False)
        msg += "\n"

    # 참고 지표 (필요시 수동 업데이트)
    msg += "<b>[참고: 주요 경제 지표]</b>\n"
    msg += "🏦 미국 기준금리: <b>4.50 ~ 4.75%</b>\n"
    msg += "🏦 한국 기준금리: <b>3.00%</b>\n"

    # 전송
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')

if __name__ == "__main__":
    asyncio.run(send_all_in_one_report())
