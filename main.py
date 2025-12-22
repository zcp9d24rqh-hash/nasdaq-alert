import yfinance as yf
import telegram
import asyncio
import os

# GitHub Secrets에서 정보를 안전하게 가져옵니다.
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

async def get_data(ticker_symbol):
    """최근 10일 데이터를 가져와서 분석합니다."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        # 한국 지수의 경우 데이터 지연이 있을 수 있어 10일치 데이터를 넉넉히 가져옵니다.
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
    
    # 상승/하락에 따른 이모지와 기호 설정
    emoji = "🔴" if data['diff'] > 0 else "🔵" if data['diff'] < 0 else "⚪"
    mark = "▲" if data['diff'] > 0 else "▼" if data['diff'] < 0 else "-"
    unit = "%" if is_rate else ""
    
    return f"{emoji} {name}: {data['curr']:,.2f}{unit} ({mark}{abs(data['percent']):.2f}%)\n"

async def send_all_in_one_report():
    # 1. 지수 설정 (코스닥 제외, 코스피 포함)
    indices = {
        "나스닥 100": "^NDX", 
        "S&P 500": "^GSPC",
        "코스피": "^KS11"
    }
    
    # 2. 환율 설정 (엔/원, 유로/원 포함)
    currencies = {
        "달러/원": "USDKRW=X", 
        "엔/원": "JPYKRW=X", 
        "유로/원": "EURKRW=X", 
        "달러인덱스": "DX-Y.NYB"
    }
    
    # 3. 채권 및 변동성
    rates = {"미 국채 10년물": "^TNX", "VIX 공포지수": "^VIX"}
    
    # 4. 원자재 및 암호화폐
    commodities = {"WTI 유가": "CL=F", "금(Gold)": "GC=F"}
    crypto = {"비트코인": "BTC-USD"}

    msg = "<b>📊 [데일리 매크로 리포트]</b>\n\n"
    
    # 지수 섹션
    msg += "<b>[주요 지수]</b>\n"
    for name, ticker
