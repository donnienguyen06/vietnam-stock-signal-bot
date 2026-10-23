"""PNG daily chart plus independently refreshed latest quote (not intraday candles)."""
import asyncio
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
import math
import os
from threading import Lock

from . import storage
from .provider import now, TZ, validate_symbol
from .strategy import indicators

os.environ.setdefault('MPLCONFIGDIR', str(storage.DATA / '.matplotlib'))
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Rectangle, Patch

_render_lock = Lock()


def is_doji(open_price, high, low, close, volume):
    """Display rule: body <= 10% of nonzero daily range; exclude no-trade bars."""
    return volume > 0 and high > low and abs(close-open_price) <= .1*(high-low)


def timeline_ticks(dates):
    """Session-spaced dates: month boundaries take priority over weekly ticks."""
    parsed = [datetime.fromisoformat(str(value)) for value in dates]
    boundaries = [i for i, day in enumerate(parsed)
                  if i == 0 or (day.year, day.month) != (parsed[i-1].year, parsed[i-1].month)]
    ticks = list(boundaries)
    for i in range(5, len(parsed), 5):
        if all(abs(i-j) >= 4 for j in ticks):
            ticks.append(i)
    labels = []
    for i in sorted(ticks):
        day = parsed[i]
        labels.append(f'Th {day.month}\n{day.year}' if i in boundaries else day.strftime('%d'))
    return sorted(ticks), labels, boundaries


@dataclass
class ChartPhoto:
    symbol: str
    png: bytes
    caption: str


async def create_chart(engine, symbol):
    symbol = validate_symbol(symbol)
    async with engine.symbol_locks.setdefault(symbol, asyncio.Lock()):
        data = await engine.provider.load(symbol)
    quote = None
    # Always request again; do not reuse a cached quote as "realtime".
    try:
        quote = await engine.provider.quote(symbol)
    except (ValueError, KeyError, TypeError):
        pass
    return await asyncio.to_thread(render_chart, symbol, data, quote, now())


def render_chart(symbol, data, quote, requested_at):
    bars = data.get('bars') or []
    if len(bars) < 60:
        raise ValueError('Chưa đủ lịch sử để vẽ chart. Hãy thử lại khi nguồn có đủ dữ liệu.')
    d = indicators(bars).tail(80).reset_index(drop=True)
    warnings = []
    if data.get('cached'):
        warnings.append('Lịch sử từ cache do nguồn lỗi')
    if (requested_at.date() - datetime.fromisoformat(str(d.iloc[-1].date)).date()).days > 4:
        warnings.append('Lịch sử chưa cập nhật phiên gần đây')
    price, quote_time = None, None
    if quote:
        try:
            price = float(quote['price'])
            quote_time = datetime.fromisoformat(quote['timestamp'])
            if not math.isfinite(price) or price <= 0 or quote_time.tzinfo is None:
                raise ValueError('invalid quote')
            if (quote_time - requested_at).total_seconds() > 60:
                raise ValueError('future quote')
        except (ValueError, KeyError, TypeError):
            price, quote_time = None, None
    if price is None:
        quote_label = 'Không lấy được giá mới nhất; chỉ hiển thị lịch sử'
        warnings.append(quote_label)
    else:
        stamp = quote_time.astimezone(TZ).strftime('%d/%m/%Y %H:%M:%S')
        quote_label = f'Giá gần nhất: {price:,.0f} VND  |  Nguồn ghi nhận: {stamp} (VN)'
        if (requested_at - quote_time).total_seconds() > 900:
            warnings.append('Giá gần nhất đã hơn 15 phút; có thể ngoài giờ giao dịch hoặc nguồn trễ')
    history_date = str(d.iloc[-1].date)
    doji = [is_doji(r.open,r.high,r.low,r.close,r.volume) for r in d.itertuples()]
    source = str(data.get('source') or 'SSI FastConnect Data')
    caption = (f'{symbol} • Nến Nhật / Doji • 1D (1 nến = 1 phiên)\n{quote_label}\n'
               f'Giá/EMA điều chỉnh đến {history_date}; khối lượng theo phiên.\n'
               f'Doji màu vàng: thân ≤ 10% biên độ, có giao dịch ({sum(doji)} nến).\n'
               f'Lấy ảnh lúc {requested_at.strftime("%d/%m/%Y %H:%M:%S")} (VN).\n'
               f'Nguồn {source} có thể trễ. Ảnh chụp tại thời điểm gọi /chart; không tự cập nhật.')
    if warnings:
        caption += '\n⚠ ' + '\n'.join(warnings)

    with _render_lock:
        fig = Figure(figsize=(12, 8), dpi=140, facecolor='#0c1017')
        canvas = FigureCanvasAgg(fig)
        grid = fig.add_gridspec(2, 1, height_ratios=[3.4, 1], hspace=.1)
        ax = fig.add_subplot(grid[0]); vol = fig.add_subplot(grid[1], sharex=ax)
        for panel in [ax, vol]:
            panel.set_facecolor('#141b25')
            panel.tick_params(colors='#bdcadc', labelsize=9)
            for spine in panel.spines.values(): spine.set_color('#334052')
            panel.grid(axis='y', color='#334052', alpha=.5, linestyle=':')
        x = list(range(len(d)))
        colors = []
        for i, r in enumerate(d.itertuples()):
            color = '#ffdf66' if doji[i] else '#6ce6b4' if r.close >= r.open else '#ff8f98'
            colors.append(color)
            ax.vlines(i, r.low, r.high, color=color, linewidth=1.1, zorder=3)
            if r.close == r.open:
                ax.hlines(r.close, i-.32, i+.32, color=color, linewidth=1.6, zorder=4)
            else:
                ax.add_patch(Rectangle((i-.32,min(r.open,r.close)), .64, abs(r.close-r.open),
                                       facecolor=color, edgecolor=color, linewidth=.9, zorder=4))
        ax.margins(y=.18)
        ax.plot(x, d.ema20, color='#e9ba70', linewidth=1.2, label='EMA20')
        ax.plot(x, d.ema50, color='#a9afff', linewidth=1.2, label='EMA50')
        level_bars=d.iloc[-21:-1]
        if len(level_bars):
            ax.axhline(level_bars.low.min(),color='#63d9ae',linestyle='--',linewidth=.9,label='Hỗ trợ 20 phiên')
            ax.axhline(level_bars.high.max(),color='#ed9292',linestyle='--',linewidth=.9,label='Kháng cự 20 phiên')
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
        ax.set_ylabel('VND • giá điều chỉnh', color='#bdcadc')
        ax.tick_params(labelbottom=False)
        if price is not None:
            # Separate quote panel: raw live price is not mixed with adjusted history.
            ax.text(.98, .97, f'GIÁ GẦN NHẤT (CHƯA ĐIỀU CHỈNH)\n{price:,.0f} VND',
                    transform=ax.transAxes, ha='right', va='top', fontsize=10,
                    color='#f4dc96', bbox=dict(facecolor='#202a39', edgecolor='#6b6146', pad=8))
        handles, labels = ax.get_legend_handles_labels()
        handles = [Patch(color='#6ce6b4'),Patch(color='#ff8f98'),Patch(color='#ffdf66')] + handles
        labels = ['Tăng','Giảm','Doji'] + labels
        legend = ax.legend(handles, labels, loc='upper left', ncol=3,
                           facecolor='#141b25', edgecolor='#334052', fontsize=9)
        for t in legend.get_texts(): t.set_color('#eaf0f7')
        vol.bar(x, d.volume / 1_000_000, color=colors, width=.7, alpha=.8)
        vol.set_ylabel('Triệu CP', color='#bdcadc')
        ticks, labels, boundaries = timeline_ticks(d.date)
        vol.set_xticks(ticks, labels)
        vol.tick_params(axis='x', length=0, pad=9, labelsize=9)
        for panel in [ax, vol]:
            panel.set_xlim(-1.5, len(d)+1)
            for i in ticks:
                panel.axvline(i, color='#465269' if i in boundaries else '#334052',
                             alpha=.6 if i in boundaries else .35, linewidth=.8, zorder=0)
        for label, tick in zip(vol.get_xticklabels(), ticks):
            if tick in boundaries:
                label.set_color('#eaf0f7'); label.set_fontweight('bold')
        fig.suptitle(f'{symbol}  /  NẾN NHẬT · DOJI', x=.09, ha='left', y=.97,
                     fontsize=20, weight='bold', color='#eaf0f7')
        fig.text(.09, .918, quote_label, fontsize=10, color='#f4dc96')
        fig.text(.97, .966, '1D · 1 NẾN = 1 PHIÊN', ha='right', color='#6ce6b4', fontsize=10,
                 bbox=dict(facecolor='#20362f', edgecolor='#365849', boxstyle='round,pad=.5'))
        start_day = datetime.fromisoformat(str(d.iloc[0].date)).strftime('%d/%m/%Y')
        end_day = datetime.fromisoformat(history_date).strftime('%d/%m/%Y')
        fig.text(.09, .096, f'{start_day}  —  {end_day}  |  {len(d)} phiên', color='#bdcadc', fontsize=9)
        fig.text(.97, .096, 'UTC+7 · Giờ Việt Nam', ha='right', color='#bdcadc', fontsize=9)
        fig.text(.09, .057, f'{source} • {len(d)} phiên đến {history_date} • Chụp {requested_at.strftime("%d/%m/%Y %H:%M:%S")} (VN)',
                 color='#bdcadc', fontsize=9)
        fig.text(.09, .032, warnings[0] if warnings else 'Giá nguồn có thể trễ • Ảnh không tự cập nhật • Không phải chart nến trong phiên',
                 color='#f4b98e', fontsize=9)
        fig.subplots_adjust(left=.09, right=.97, top=.88, bottom=.19)
        buf = BytesIO(); canvas.print_png(buf)
        payload = buf.getvalue()
        fig.clear()
    return ChartPhoto(symbol, payload, caption[:1024])
