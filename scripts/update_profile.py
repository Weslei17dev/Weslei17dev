#!/usr/bin/env python3
"""Build profile SVGs from public GitHub data; Python standard library only."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.request import Request, urlopen
from profile_motion import animated_banner, animated_snake

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LOGIN = "Weslei17dev"
BG, PANEL, BORDER, INK, MUTED, RED = "#0d1117", "#161b22", "#30363d", "#f0f3f6", "#a5afbc", "#ff4d61"
MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
COLORS = {"HTML": "#ff704d", "JavaScript": "#f1df64", "CSS": "#ae8df0", "Python": "#64a6d8", "PLpgSQL": "#68c5a4", "C": "#c9d1d9"}


def get(url):
    headers = {"User-Agent": "Weslei17dev-profile", "Accept": "application/vnd.github+json" if url.startswith("https://api.github.com/") else "text/html"}
    token = os.getenv("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = "Bearer " + token
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=headers), timeout=30) as response:
                return response.read().decode("utf-8")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells, self.counts, self.target, self.parts = {}, {}, None, []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and attrs.get("data-date"):
            self.cells[attrs["id"]] = {"date": attrs["data-date"], "level": int(attrs["data-level"])}
        if tag == "tool-tip" and attrs.get("for", "").startswith("contribution-day-"):
            self.target, self.parts = attrs["for"], []

    def handle_data(self, data):
        if self.target:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.target:
            value = " ".join(self.parts).strip()
            match = re.match(r"([\d,]+) contributions?\b", value)
            if match:
                self.counts[self.target] = int(match[1].replace(",", ""))
            elif value.startswith("No contributions"):
                self.counts[self.target] = 0
            self.target = None

    def result(self):
        if len(self.cells) < 350 or set(self.cells) != set(self.counts):
            raise ValueError("Calendário público incompleto; os gráficos anteriores serão preservados.")
        return sorted([dict(cell, count=self.counts[key]) for key, cell in self.cells.items()], key=lambda x: x["date"])


def collect():
    repositories, page = [], 1
    while True:
        batch = json.loads(get(f"https://api.github.com/users/{LOGIN}/repos?type=owner&per_page=100&page={page}"))
        if not isinstance(batch, list):
            raise ValueError("Resposta inválida na lista de repositórios")
        repositories.extend(r for r in batch if not r.get("private") and r["owner"]["login"].lower() == LOGIN.lower())
        if len(batch) < 100:
            break
        page += 1
    projects = [r for r in repositories if not r["fork"] and r["name"].lower() != LOGIN.lower()]
    languages = Counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(lambda r: json.loads(get(r["languages_url"])), projects):
            languages.update(result)
    parser = CalendarParser()
    parser.feed(get(f"https://github.com/users/{LOGIN}/contributions"))
    days = parser.result()
    return {"updated": date.today().isoformat(), "repositories": len(repositories), "languages": dict(languages), "days": days}


def text(x, y, content, size=14, color=INK, weight="400", extra=""):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" {extra}>{escape(str(content))}</text>'


def rect(x, y, w, h, fill=PANEL, radius=12, stroke="none"):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def svg(width, height, title, content):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title"><title id="title">{escape(title)}</title><g font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif">{content}</g></svg>\n'


def static_assets():
    ASSETS.joinpath("banner.svg").write_text(animated_banner(), encoding="utf-8")
    ASSETS.joinpath("banner-mobile.svg").write_text(animated_banner(mobile=True), encoding="utf-8")
    for filename, label, width, fill in [("linkedin", "LinkedIn ↗", 133, "#a32b40"), ("github", "Meus projetos ↗", 174, PANEL)]:
        body = rect(1, 1, width - 2, 34, fill, 8, "#63313d" if filename == "linkedin" else BORDER)
        body += text(width / 2, 23, label, 13, INK, "600", 'text-anchor="middle"')
        ASSETS.joinpath(filename + ".svg").write_text(svg(width, 36, label, body), encoding="utf-8")
    rows = [[("HTML", "#ff704d"), ("CSS", "#ae8df0"), ("JavaScript", "#f1df64"), ("Node.js", "#83cc77"), ("Express", "#d2d8e0")], [("PostgreSQL", "#64a6d8"), ("Git", "#ff806d"), ("Power BI", "#f1d253"), ("Power Query", "#70c6a1"), ("DAX", "#a5afea")]]
    body = ""
    for row, items in enumerate(rows):
        for col, (label, color) in enumerate(items):
            x, y = col * 181 + 1, row * 48 + 1
            body += rect(x, y, 174, 40, PANEL, 8, BORDER)
            body += f'<circle cx="{x + 18}" cy="{y + 20}" r="4" fill="{color}"/>'
            body += text(x + 31, y + 25, label, 14, INK, "600")
    ASSETS.joinpath("stack.svg").write_text(svg(900, 90, "Tecnologias utilizadas", body), encoding="utf-8")


def dashboard(data):
    langs = Counter(data["languages"])
    days = data["days"]
    total = sum(d["count"] for d in days)
    active = sum(d["count"] > 0 for d in days)
    stamp = date.fromisoformat(data["updated"]).strftime("%d/%m/%Y")
    body = rect(1, 1, 898, 458, BG, 14, BORDER)
    body += text(26, 33, "CÓDIGO, DADOS E CONSTÂNCIA", 13, MUTED, "650", 'letter-spacing="1.6"')
    body += text(873, 33, "GitHub · " + stamp, 12, MUTED, extra='text-anchor="end"')
    for i, (value, label) in enumerate([(data["repositories"], "repositórios públicos"), (len(langs), "linguagens no código"), (total, "contribuições no período"), (active, "dias com atividade")]):
        x = 24 + i * 219
        body += rect(x, 53, 199, 91, PANEL, 10)
        body += text(x + 16, 95, value, 31, RED if i == 2 else INK, "700")
        body += text(x + 16, 123, label, 12, MUTED)
    body += text(27, 182, "Linguagens dos projetos", 17, INK, "600")
    body += text(27, 203, "Participação por bytes de código", 12, MUTED)
    total_bytes = sum(langs.values())
    top = langs.most_common(6)
    for i, (language, value) in enumerate(top):
        y = 235 + i * 31
        pct = value * 100 / total_bytes if total_bytes else 0
        color = COLORS.get(language, "#ff93a0")
        body += text(27, y, language, 12, INK, "500")
        body += rect(127, y - 9, 228, 7, PANEL, 3)
        body += rect(127, y - 9, round(228 * pct / 100, 2), 7, color, 3)
        body += text(411, y, f"{pct:.1f}%", 12, MUTED, extra='text-anchor="end"')
    body += '<path d="M445 170 V421" stroke="#30363d"/>'
    body += text(471, 182, "Atividade ao longo do tempo", 17, INK, "600")
    body += text(471, 203, "Contribuições por mês · últimos 12 meses", 12, MUTED)
    today = date.fromisoformat(data["updated"])
    months = []
    for i in range(11, -1, -1):
        index = today.year * 12 + today.month - 1 - i
        year, month = divmod(index, 12)
        months.append((year, month + 1))
    values = [sum(d["count"] for d in days if d["date"].startswith(f"{year:04}-{month:02}")) for year, month in months]
    maximum = max(values + [1])
    for fraction in [0, .5, 1]:
        y = 378 - fraction * 129
        body += f'<path d="M475 {y} H870" stroke="#252d38" stroke-dasharray="3 4"/>'
    for i, ((year, month), value) in enumerate(zip(months, values)):
        x, height = 477 + i * 33, max(2, value / maximum * 129)
        body += rect(x, 378 - height, 21, height, RED if value else "#303946", 3)
        if value:
            body += text(x + 10.5, 369 - height, value, 11, INK, "500", 'text-anchor="middle"')
        body += text(x + 10.5, 400, MONTHS[month - 1], 10, MUTED, extra='text-anchor="middle"')
    body += text(475, 432, "Período atual pode estar incompleto.", 11, MUTED)
    if len(langs) > 6:
        body += text(27, 437, f"Exibindo 6 de {len(langs)} linguagens.", 11, MUTED)
    return svg(900, 460, f"{data['repositories']} repositórios públicos, {total} contribuições e {active} dias com atividade. Atualizado em {stamp}.", body)


def calendar(data):
    days = data["days"]
    first = date.fromisoformat(days[0]["date"])
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    body = rect(1, 1, 898, 217, BG, 14, BORDER)
    body += text(26, 33, "Um pouco a cada dia", 17, INK, "600")
    body += text(26, 55, "Calendário exibido no perfil público", 12, MUTED)
    palette = ["#1b222c", "#582333", "#923147", "#cc3b54", RED]
    seen = set()
    for d in days:
        current = date.fromisoformat(d["date"])
        delta = (current - start).days
        x, y = 48 + (delta // 7) * 15, 88 + ((current.weekday() + 1) % 7) * 14
        key = (current.year, current.month)
        if key not in seen and current.day <= 7:
            body += text(x, 79, MONTHS[current.month - 1], 10, MUTED)
            seen.add(key)
        body += f'<rect x="{x}" y="{y}" width="11" height="10" rx="2" fill="{palette[d["level"]]}"><title>{d["date"]}: {d["count"]} contribuições</title></rect>'
    for row, label in [(1, "S"), (3, "Q"), (5, "S")]:
        body += text(27, 97 + row * 14, label, 10, MUTED)
    body += text(657, 202, "Menos", 10, MUTED)
    for i, color in enumerate(palette):
        body += rect(697 + i * 17, 193, 11, 10, color, 2)
    body += text(786, 202, "Mais", 10, MUTED)
    body += text(27, 202, f"{days[0]['date']} — {days[-1]['date']}", 10, MUTED)
    return svg(900, 219, "Calendário real de contribuições do GitHub", body)


def render(data):
    # Generate everything before replacing any asset; failed retrievals preserve the snapshot.
    generated = {"dashboard.svg": dashboard(data), "calendar.svg": calendar(data),
                 "snake.svg": animated_snake(data), "snake-mobile.svg": animated_snake(data, mobile=True)}
    ASSETS.mkdir(parents=True, exist_ok=True)
    static_assets()
    for filename, content in generated.items():
        temporary = ASSETS / (filename + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(ASSETS / filename)
    print(f"Gráficos atualizados: {data['repositories']} repositórios, {sum(d['count'] for d in data['days'])} contribuições.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, help="Render a saved public-data snapshot without network calls")
    args = parser.parse_args()
    try:
        render(json.loads(args.snapshot.read_text(encoding="utf-8")) if args.snapshot else collect())
    except Exception as exc:
        print(f"Não foi possível atualizar o perfil: {exc}", file=sys.stderr)
        sys.exit(1)
