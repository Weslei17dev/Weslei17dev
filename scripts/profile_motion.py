"""Animated SVG assets for a GitHub README; no scripts or external resources."""
from datetime import date, timedelta
from html import escape
from math import hypot

BG, INK, MUTED, RED = "#0d1117", "#f0f3f6", "#b2bbc8", "#ff4d61"
PALETTE = ["#1b222c", "#582333", "#923147", "#cc3b54", RED]
MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def svg(width, height, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">'
            f'<title id="title">{escape(title)}</title>'
            '<style>.still{display:none}@media(prefers-reduced-motion:reduce){.motion{display:none}.still{display:inline}}</style>'
            '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif">'
            + body + '</g></svg>\n')


def text(x, y, value, size=14, fill=INK, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>{escape(str(value))}</text>'


def animate(attribute, events, duration):
    events = sorted(dict(events).items())
    values = ";".join(f"{value:.2f}" for _, value in events)
    times = ";".join(f"{time / duration:.8f}" for time, _ in events)
    return (f'<animate attributeName="{attribute}" dur="{duration / 1000:.3f}s" '
            f'values="{values}" keyTimes="{times}" calcMode="discrete" repeatCount="indefinite"/>')


def animated_banner(mobile=False):
    width, height = (480, 290) if mobile else (900, 254)
    left = 26 if mobile else 34
    name_y, focus_y, typing_y = (117, 158, 232) if mobile else (116, 153, 211)
    font_size = 20 if mobile else 16
    typing_x = left + 23
    char_width = font_size * 0.6
    phrases = ["Ideias que viram ferramentas.", "Dados que ajudam a decidir.", "Soluções para facilitar a rotina."]
    durations = [len(phrase) * 100 + 2150 for phrase in phrases]
    total = sum(durations)
    clips, lines, caret = [], [], {0: typing_x + 3, total: typing_x + 3}
    offset = 0
    for index, (phrase, duration) in enumerate(zip(phrases, durations)):
        events = {0: 0, offset: 0, offset + duration: 0, total: 0}
        for length in range(1, len(phrase) + 1):
            events[offset + length * 72] = length * char_width
        delete_start = offset + len(phrase) * 72 + 1800
        for removed in range(1, len(phrase) + 1):
            events[delete_start + removed * 28] = (len(phrase) - removed) * char_width
        for time, value in events.items():
            if offset <= time < offset + duration:
                caret[time] = typing_x + value + 3
        default_width = len(phrase) * char_width if index == 0 else 0
        clips.append(f'<clipPath id="typing-{index}"><rect x="{typing_x}" y="{typing_y - font_size - 3}" '
                     f'width="{default_width}" height="{font_size + 10}">'
                     + animate("width", events.items(), total) + '</rect></clipPath>')
        lines.append(text(typing_x, typing_y, phrase, font_size, MUTED,
                          f'font-family="Courier New,monospace" clip-path="url(#typing-{index})"'))
        offset += duration
    body = ('<defs><linearGradient id="background" x1="0" y1="0" x2="1" y2="1">'
            '<stop stop-color="#29151f"/><stop offset="1" stop-color="#121721"/></linearGradient>'
            '<radialGradient id="aura"><stop stop-color="#e53054" stop-opacity=".16"/>'
            '<stop offset="1" stop-color="#e53054" stop-opacity="0"/></radialGradient>'
            f'<clipPath id="banner-boundary"><rect x="1" y="1" width="{width-2}" height="{height-2}" rx="18"/></clipPath>'
            + "".join(clips) + '</defs>')
    body += f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="18" fill="url(#background)" stroke="#3c2833"/>'
    body += '<g clip-path="url(#banner-boundary)">'
    body += f'<circle class="motion" cx="{width - 30}" cy="15" r="220" fill="url(#aura)">'
    body += '<animateTransform attributeName="transform" type="translate" values="0 0;-100 70;0 0" dur="8s" repeatCount="indefinite"/></circle>'
    for x in range(int(width * .65), width, 24):
        for y in range(20, height, 24):
            body += f'<circle cx="{x}" cy="{y}" r="1" fill="#dd6073" opacity=".24"/>'
    body += '</g>'
    body += f'<rect x="{left}" y="30" width="146" height="28" rx="14" fill="#542235"/>'
    body += text(left + 14, 49, "WESLEI17DEV", 12, "#ffb8c2", 'font-weight="600" letter-spacing="1.5"')
    body += text(left, name_y, "Weslei Campos", 46 if mobile else 48, INK, 'font-weight="700" letter-spacing="-1.3"')
    body += text(left + 1, focus_y, "Desenvolvimento · Dados · Automação", 18 if mobile else 20, "#f3c1ca")
    body += text(left + 1, typing_y, ">", font_size, RED, 'font-family="Courier New,monospace" font-weight="700"')
    body += '<g class="motion">' + "".join(lines)
    body += f'<rect x="{typing_x + 3}" y="{typing_y - font_size + 2}" width="2" height="{font_size}" fill="#ff9aa8">'
    body += animate("x", caret.items(), total)
    body += '<animate attributeName="opacity" values="1;0;1" keyTimes="0;.5;1" calcMode="discrete" dur="1s" repeatCount="indefinite"/>'
    body += '</rect></g><g class="still">' + text(typing_x, typing_y, phrases[0], font_size, MUTED, 'font-family="Courier New,monospace"') + '</g>'
    return svg(width, height, "Weslei Campos — banner com frases animadas sobre desenvolvimento, dados e automação", body)


def animated_snake(data, mobile=False):
    days = data["days"]
    first = date.fromisoformat(days[0]["date"])
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    all_columns = (date.fromisoformat(days[-1]["date"]) - start).days // 7 + 1
    columns = min(26, all_columns) if mobile else all_columns
    first_column = all_columns - columns
    width, height = (480, 219) if mobile else (900, 219)
    left, top, step_x, step_y, cell_w, cell_h = (30, 88, 16, 14, 12, 10) if mobile else (48, 88, 15, 14, 11, 10)
    grid = {}
    for item in days:
        current = date.fromisoformat(item["date"])
        delta = (current - start).days
        x, y = delta // 7 - first_column, (current.weekday() + 1) % 7
        if x >= 0:
            grid[x, y] = item
    route, route_keys = [], []
    for x in range(columns):
        for y in (range(6, -1, -1) if x % 2 else range(7)):
            route.append((left + x * step_x + cell_w / 2, top + y * step_y + cell_h / 2))
            route_keys.append((x, y))
    points = [(left - 70, route[0][1])] + route + [(route[-1][0] + 70, route[-1][1])]
    distance = [0.0]
    for previous, point in zip(points, points[1:]):
        distance.append(distance[-1] + hypot(point[0] - previous[0], point[1] - previous[1]))
    duration = len(route) * .057 + 1.5
    path = "M" + " L".join(f"{x:g} {y:g}" for x, y in points)
    body = (f'<defs><path id="snake-route" d="{path}"/>'
            f'<clipPath id="grid-boundary"><rect x="{left - 12}" y="{top - 10}" '
            f'width="{columns * step_x + 20}" height="110"/></clipPath></defs>'
            f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="14" fill="{BG}" stroke="#30363d"/>')
    body += text(26, 33, "Um pouco a cada dia", 17, INK, 'font-weight="600"')
    body += text(26, 55, "Cobrinha de contribuições · " + ("últimas 26 semanas" if mobile else "último ano"), 12, MUTED)
    month_labels = set()
    for (x, y), item in sorted(grid.items()):
        current = date.fromisoformat(item["date"])
        month = (current.year, current.month)
        if month not in month_labels and current.day <= 7:
            body += text(left + x * step_x, 79, MONTHS[current.month - 1], 10, MUTED)
            month_labels.add(month)
    for x in range(columns):
        for y in range(7):
            item = grid.get((x, y))
            color = PALETTE[item["level"]] if item else PALETTE[0]
            body += (f'<rect x="{left + x * step_x}" y="{top + y * step_y}" width="{cell_w}" '
                     f'height="{cell_h}" rx="2" fill="{color}">')
            if item:
                body += f'<title>{item["date"]}: {item["count"]} contribuições</title>'
            body += '</rect>'
    body += '<g class="motion" clip-path="url(#grid-boundary)">'
    for index, key in enumerate(route_keys):
        if not grid.get(key, {}).get("count"):
            continue
        x, y = key
        eat = distance[index + 1] / distance[-1]
        body += (f'<rect x="{left + x * step_x}" y="{top + y * step_y}" width="{cell_w}" '
                 f'height="{cell_h}" rx="2" fill="{PALETTE[0]}" visibility="hidden">'
                 f'<animate attributeName="visibility" values="hidden;visible;visible" keyTimes="0;{eat:.8f};1" '
                 f'calcMode="discrete" dur="{duration:.3f}s" repeatCount="indefinite"/></rect>')
    segment_delay = step_x / (distance[-1] / duration) * .88
    for index in range(7):
        body += '<g>'
        body += (f'<rect x="{-cell_w / 2:g}" y="{-cell_h / 2:g}" width="{cell_w}" height="{cell_h}" '
                 f'rx="3" fill="{"#ffc0c9" if index == 6 else RED}" opacity="{.52 + index * .08:.2f}"/>')
        if index == 6:
            for sign in (-1, 1):
                body += f'<circle cx="{cell_w * .24:g}" cy="{sign * cell_h * .2:g}" r=".8" fill="#351322"/>'
        body += (f'<animateMotion dur="{duration:.3f}s" begin="{(6-index) * segment_delay:.3f}s" '
                 'repeatCount="indefinite" rotate="auto"><mpath href="#snake-route"/></animateMotion></g>')
    body += '</g>'
    begin = start + timedelta(days=first_column * 7)
    body += text(26, 202, f"{begin.isoformat()} — {days[-1]['date']}", 10, MUTED)
    legend_x = width - 204
    body += text(legend_x, 202, "Menos", 10, MUTED)
    for index, color in enumerate(PALETTE):
        body += f'<rect x="{legend_x + 40 + index * 17}" y="193" width="11" height="10" rx="2" fill="{color}"/>'
    body += text(width - 75, 202, "Mais", 10, MUTED)
    return svg(width, height, "Cobrinha vermelha percorrendo as contribuições públicas de Weslei17dev", body)
