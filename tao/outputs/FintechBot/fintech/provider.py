"""Shared validation utilities; market data comes only from SSI."""
import math
import re
from datetime import datetime
from zoneinfo import ZoneInfo
TZ=ZoneInfo('Asia/Ho_Chi_Minh')
SYMBOLS={}
def now():return datetime.now(TZ)
def validate_symbol(value):
    s=value.strip().upper()
    if not re.fullmatch('[A-Z][A-Z0-9]{2,5}',s):
        raise ValueError('Mã cổ phiếu phải có 3–6 chữ/số. Hãy nhập mã bạn muốn xem.')
    return s
def number(x):
    try:
        n=float(str(x).replace(',','').replace('%',''))
        return n if math.isfinite(n) else None
    except (TypeError,ValueError):return None
