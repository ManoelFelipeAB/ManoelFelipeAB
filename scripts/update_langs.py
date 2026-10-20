"""Gera assets/langs.svg: card "Most Used Languages" com cores vivas próprias.

Uso:
  python scripts/update_langs.py            -> busca os dados na API do GitHub (precisa de GITHUB_TOKEN)
  python scripts/update_langs.py --seed     -> usa os percentuais fixos abaixo (sem rede)
"""
import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

USER = "ManoelFelipeAB"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "langs.svg")
HIDE = {"Jupyter Notebook"}
TOP_N = 8

# Cores vivas na ordem do ranking
PALETTE = ["#2F6BFF",  # azul escuro
           "#A3FF12",  # verde-lima
           "#FF8C1A",  # laranja
           "#00E5FF",  # azul ciano
           "#FFD43B",  # amarelo
           "#A5D8FF",  # azul bebê
           "#FF4D9D",  # rosa
           "#A78BFA"]  # lilás

_RAW = {"Python": 28.25, "Java": 27.36, "HTML": 13.48, "Haskell": 8.50,
        "C#": 7.58, "C++": 7.22, "Clojure": 5.04, "TypeScript": 2.57}
SEED = {k: v * 100 / sum(_RAW.values()) for k, v in _RAW.items()}

BG, TITLE, TEXT = "#0D1117", "#A3FF12", "#F0F6FC"


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={"Accept": "application/vnd.github+json",
                 "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                 "User-Agent": USER},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch():
    totals, page = {}, 1
    while True:
        repos = api(f"users/{USER}/repos?per_page=100&type=owner&page={page}")
        if not repos:
            break
        for repo in repos:
            if repo["fork"] or repo["name"].lower() == USER.lower():
                continue
            for lang, size in api(f"repos/{USER}/{repo['name']}/languages").items():
                if lang not in HIDE:
                    totals[lang] = totals.get(lang, 0) + size
        page += 1
    top = sorted(totals.items(), key=lambda kv: -kv[1])[:TOP_N]
    total = sum(v for _, v in top) or 1
    return {k: v * 100 / total for k, v in top}


def render(data):
    langs = list(data.items())
    w, pad = 300, 25
    bar_y, bar_w, bar_h = 55, w - 2 * pad, 8
    rows = (len(langs) + 1) // 2
    h = 85 + rows * 25
    font = "font-family=\"'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif\""

    segs, x = [], pad
    for i, (_, pct) in enumerate(langs):
        seg_w = bar_w * pct / 100
        segs.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{seg_w + 0.5:.2f}" height="{bar_h}" fill="{PALETTE[i]}"/>')
        x += seg_w

    legend = []
    for i, (name, pct) in enumerate(langs):
        col, row = i // rows, i % rows
        lx, ly = pad + col * 150, 90 + row * 25
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{PALETTE[i]}"/>'
            f'<text x="{lx + 15}" y="{ly}" {font} font-size="11" fill="{TEXT}">{escape(name)} {pct:.2f}%</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Most Used Languages">
  <rect width="{w}" height="{h}" rx="10" fill="{BG}"/>
  <text x="{pad}" y="35" {font} font-size="18" font-weight="600" fill="{TITLE}">Most Used Languages</text>
  <clipPath id="bar"><rect x="{pad}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="4"/></clipPath>
  <g clip-path="url(#bar)">{''.join(segs)}</g>
  {''.join(legend)}
</svg>
'''


if __name__ == "__main__":
    data = SEED if "--seed" in sys.argv else fetch()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(data))
    print(", ".join(f"{k} {v:.2f}%" for k, v in data.items()))
