"""Deterministic explanations and conditional price scenarios, not forecasts."""
import math

def analysis(s):
    c,e20,e50=s['close'],s['ema20'],s['ema50']
    trend='Tăng' if c>e20>e50 else 'Giảm' if c<e20<e50 else 'Chưa đồng thuận'
    rsi=s['rsi'];rv=s['rvol']
    momentum='Quá mua' if rsi>=70 else 'Quá bán' if rsi<=30 else 'Nghiêng tăng' if rsi>50 else 'Nghiêng giảm'
    volume='Bùng nổ' if rv>=1.5 else 'Trên trung bình' if rv>=1 else 'Dưới trung bình'
    plan=None
    atr=s['atr']
    if s['action']=='BUY' and not (s.get('cached') or s.get('stale')) and math.isfinite(atr) and 0<2*atr<c:
        # A conservative hypothetical entry at the upper end of the band.
        low=c;high=c+.25*atr;stop=c-2*atr;risk=high-stop
        plan=dict(entry_low=round(low,2),entry_high=round(high,2),stop=round(stop,2),
            target1=round(high+2*risk,2),target2=round(high+3*risk,2),rr1=2,rr2=3,
            resistance_in_path=high<s['resistance']<high+2*risk)
    return dict(trend=trend,momentum=momentum,volume=volume,plan=plan)

def describe(s):
    a=analysis(s);p=a['plan'];money=lambda v:f'{v:,.0f}'
    label={'BUY':'MUA • có tín hiệu mới','SELL':'BÁN • cảnh báo vị thế đang giữ','HOLD':'CHỜ • chưa có tín hiệu mới'}[s['action']]
    lines=[f"{s['symbol']} | {label}",f"Phiên {s['date']} • TA theo nến ngày",
        f"Đóng cửa {money(s['close'])} đ ({s.get('change_pct',0):+.2f}%)",
        '',f"Xu hướng: {a['trend']} | EMA20 {money(s['ema20'])} / EMA50 {money(s['ema50'])}",
        f"Động lượng: RSI14 {s['rsi']:.1f} • {a['momentum']}",
        f"Dòng tiền: RVOL {s['rvol']:.2f}x • {a['volume']}",
        '', 'CĂN CỨ TÍN HIỆU',*['• '+r for r in s['reasons']],
        '',f"Hỗ trợ 20 phiên: {money(s['support'])} đ",
        f"Kháng cự 20 phiên: {money(s['resistance'])} đ",f"ATR14: {money(s['atr'])} đ"]
    if p:
        lines+=['','KỊCH BẢN THAM KHẢO CHO PHIÊN SAU',
            f"Vùng giá xét mua: {money(p['entry_low'])}–{money(p['entry_high'])} đ",
            f"Mốc vô hiệu kịch bản (2 ATR): {money(p['stop'])} đ",
            f"Mục tiêu 1: {money(p['target1'])} đ • 2R",
            f"Mục tiêu 2: {money(p['target2'])} đ • 3R",
            'R tính từ đầu trên vùng mua tới mốc vô hiệu, chưa tính phí/trượt giá.',
            'Nếu giá mở cửa ngoài vùng mua: không áp dụng kế hoạch này. Các mục tiêu là giả định, không phải dự báo.']
        if p['resistance_in_path']:lines+=['⚠ Có kháng cự trước mục tiêu 1; cần xác nhận vượt cản.']
    elif s['action']=='SELL':lines+=['','Ưu tiên đánh giá giảm/thoát vị thế đang giữ; không phải lệnh bán khống.']
    else:lines+=['','Chưa có kế hoạch mua mới hợp lệ. Chờ bộ điều kiện EMA giao cắt + RSI + khối lượng xác nhận.']
    if s.get('cached') or s.get('stale'):lines+=['⚠ Dữ liệu cache/cũ: chỉ tham khảo, không dùng làm tín hiệu mới.']
    lines+=['',f"Nguồn: {s.get('source','SSI FastConnect Data')} • lấy lúc {s['fetched_at']}",
        'BCTC: chưa đủ dữ liệu SSI để kết luận định giá.' if s.get('value_status')=='MISSING' else 'Kết luận trên dùng chiến lược kỹ thuật.',
        'Mô hình học tập; kiểm tra thanh khoản và giá thực tế trước quyết định. Không tự đặt lệnh.']
    return '\n'.join(lines)
