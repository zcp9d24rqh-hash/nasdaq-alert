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
    # 1. 주요 지수 (나스닥 100 -> 나스닥 종합 수정 완료)
    indices = {
        "나스닥 종합": "^IXIC", 
        "S&P 500": "^GSPC",
        "코스피": "^KS11"
    }
    
    # 2. 환율 현황 (엔/원, 유로/원 누락 확인 및 복구 완료)
    currencies = {
        "달러/원": "USDKRW=X", 
        "엔/원": "JPYKRW=X",
        "유로/원": "EURKRW=X",
        "달러인덱스": "DX-Y.NYB"
    }
    
    # 3. 채권, 암호화폐, 원자재
    rates = {"미 국채 10년물": "^TNX", "VIX 공포지수": "^VIX"}
    commodities = {"WTI 유가": "CL=F", "금(Gold)": "GC=F"}
    crypto = {"비트코인": "BTC-USD"}

    msg = "<b>📊 [데일리 매크로 리포트]</b>\n\n"
    
    # [주요 지수] 섹션
    msg += "<b>[주요 지수]</b>\n"
    for name, ticker in indices.items():
        msg += format_row(name, await get_data(ticker))
        
    # [환율 현황] 섹션
    msg += "\n<b>[환율 현황]</b>\n"
    for name, ticker in currencies.items():
        msg += format_row(name, await get_data(ticker))

    # [채권 및 암호화폐] 섹션
    msg += "\n<b>[채권 및 암호화폐]</b>\n"
    for name, ticker in rates.items():
        msg += format_row(name, await get_data(ticker), is_rate=True)
    for name, ticker in crypto.items():
        msg += format_row(name, await get_data(ticker))

    # [원자재 현황] 섹션
    msg += "\n<b>[원자재 현황]</b>\n"
    for name, ticker in commodities.items():
        msg += format_row(name, await get_data(ticker))

    # [참고: 주요 경제 지표] 섹션 (미국 CPI 포함 확인)
    msg += "\n<b>[참고: 주요 경제 지표]</b>\n"
    msg += "🏦 미국 기준금리: <b>4.50 ~ 4.75%</b>\n"
    msg += "🏦 한국 기준금리: <b>3.00%</b>\n"
    msg += "📌 미국 CPI(최근): <b>2.7%</b>\n"

    # 전송 로직
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("에러: 텔레그램 토큰 또는 채팅 ID 설정이 누락되었습니다.")
        return

    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
        print("✅ 데일리 리포트 전송 성공!")
    except Exception as e:
        print(f"❌ 텔레그램 전송 중 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(send_all_in_one_report())
