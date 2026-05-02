import requests
import pandas as pd
from datetime import datetime, timedelta
import os

USERNAME = "sarowarahmed"
TOKEN = os.getenv("GH_TOKEN")

# ------------------ FETCH DATA ------------------ #
query = """
{
  user(login: "%s") {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
""" % USERNAME

headers = {"Authorization": f"Bearer {TOKEN}"}

response = requests.post(
    "https://api.github.com/graphql",
    json={"query": query},
    headers=headers
)

data = response.json()

weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

days, counts = [], []
for week in weeks:
    for day in week["contributionDays"]:
        days.append(day["date"])
        counts.append(day["contributionCount"])

df = pd.DataFrame({
    "date": pd.to_datetime(days),
    "count": counts
}).sort_values("date")

# Fill missing dates
full_range = pd.date_range(df['date'].min(), df['date'].max())
df = df.tail(30).reset_index(drop=True)
# ------------------ STREAK ------------------ #
today = datetime.utcnow().date()
date_count = dict(zip(df['date'].dt.date, df['count']))

streak = 0
current_day = today
if date_count.get(current_day, 0) == 0:
    current_day -= timedelta(days=1)

while date_count.get(current_day, 0) > 0:
    streak += 1
    current_day -= timedelta(days=1)

# ------------------ MOMENTUM ------------------ #
recent = df['count'].tail(7).mean()
previous = df['count'].tail(14).head(7).mean()

if recent > previous:
    momentum = "📈 Rising"
elif recent < previous:
    momentum = "📉 Falling"
else:
    momentum = "➖ Stable"

# ------------------ GRAPH ------------------ #
df['pred'] = df['count'].rolling(5).mean().fillna(0)

width, height, padding = 800, 300, 40
max_val = max(df['count'].max(), 1)

points, shadow_points, pred_points = [], [], []
offset_x, offset_y = 6, 10

for i, val in enumerate(df['count']):
    x = padding + i * (width - 2*padding) / len(df)
    y = height - padding - (val / max_val) * (height - 2*padding)

    points.append(f"{x},{y}")
    shadow_points.append(f"{x+offset_x},{y+offset_y}")

for i, val in enumerate(df['pred']):
    x = padding + i * (width - 2*padding) / len(df)
    y = height - padding - (val / max_val) * (height - 2*padding)
    pred_points.append(f"{x},{y}")

# Heatmap
heat_blocks = []
block_width = (width - 2*padding) / len(df)

for i, val in enumerate(df['count']):
    x = padding + i * block_width
    intensity = min(val / max_val, 1)
    opacity = 0.1 + (intensity * 0.6)

    heat_blocks.append(
        f'<rect x="{x}" y="{height-padding}" width="{block_width}" height="6" fill="#ff6ec7" opacity="{opacity}" />'
    )

# ------------------ COMMON STYLE ------------------ #
common_style = """
<style>
.title { fill: #c084fc; font-size: 16px; font-weight: 600; }
.label { fill: #9ca3af; font-size: 12px; }
.card { fill: #0d1117; stroke: #1f2937; stroke-width: 1; }
.main { stroke: url(#grad); stroke-width: 3; fill: none; filter: drop-shadow(0 0 6px #7df9ff); }
.shadow { stroke: #ff6ec7; stroke-width: 3; opacity: 0.25; fill: none; filter: blur(4px); }
.pred { stroke: #ffffff; stroke-width: 2; fill: none; stroke-dasharray: 5,5; opacity: 0.4; }
</style>
"""

# ------------------ GRAPH SVG ------------------ #

circles = []

for p in points:
    x, y = p.split(",")
    circles.append(f'<circle cx="{x}" cy="{y}" r="3" fill="white" stroke="#ff6ec7" stroke-width="1"/>')

graph_svg = f"""
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">

<defs>
  <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#7df9ff"/>
    <stop offset="100%" stop-color="#ff6ec7"/>
  </linearGradient>
</defs>

{common_style}

<rect x="5" y="5" width="790" height="290" rx="12" class="card"/>

<text class="title" x="24" y="40">📈 Contribution Trend</text>
<line x1="20" y1="50" x2="780" y2="50" stroke="#1f2937"/>

{''.join(heat_blocks)}

<polyline class="shadow" points="{' '.join(shadow_points)}"/>
<polyline class="main" points="{' '.join(points)}"/>
<polyline class="pred" points="{' '.join(pred_points)}"/>

<!-- 🔥 ADD CIRCLES HERE -->
{''.join(circles)}

<!-- subtle hover illusion -->
<circle cx="{points[-1].split(',')[0]}" cy="{points[-1].split(',')[1]}" r="5" fill="#ff6ec7" opacity="0.8">
  <animate attributeName="r" values="4;7;4" dur="2s" repeatCount="indefinite"/>
</circle>

<text class="label" x="24" y="70">🔥 Streak: {streak} days</text>
<text class="label" x="24" y="90">{momentum}</text>

</svg>
"""

# ------------------ WEEKLY SVG ------------------ #
last_7 = df.tail(7).copy()

# weekday labels
last_7['day'] = last_7['date'].dt.day_name().str[:3]

# force correct order
order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
last_7['day'] = pd.Categorical(last_7['day'], categories=order, ordered=True)

last_7 = last_7.sort_values('day')

bars = []
labels = []

max_val = max(last_7['count'].max(), 1)

for i, (_, row) in enumerate(last_7.iterrows()):
    val = row['count']
    day = row['day']

    x = 40 + i * 100
    bar_height = (val / max_val) * 120
    y = 180 - bar_height

    # highlight today
    is_today = row['date'].date() == datetime.utcnow().date()
    color = "url(#grad)" if not is_today else "#ff6ec7"

    delay = i * 0.15  # stagger timing

    bars.append(f'''
    <rect x="{x}" y="180" width="50" height="0" rx="6" fill="{color}">
      <animate attributeName="height"
               from="0"
               to="{bar_height}"
               dur="0.8s"
               begin="{delay}s"
               fill="freeze" />
      <animate attributeName="y"
               from="180"
               to="{y}"
               dur="0.8s"
               begin="{delay}s"
               fill="freeze" />
    </rect>
    ''')

    <rect x="{x}" y="{y}" width="50" height="6"
          fill="white" opacity="0.15"/>

    <rect x="{x}" y="{y}" width="50" height="{bar_height}" rx="6"
          fill="none" stroke="#ff6ec7" stroke-opacity="0.2"/>
    ''')

    # 🔹 day label (bottom)
    labels.append(
        f'<text x="{x+15}" y="195" fill="#9ca3af" font-size="11">{day}</text>'
    )

    # 🔥 value label (TOP OF BAR)
    if val > 0:
        labels.append(
            f'<text x="{x+15}" y="{y-5}" fill="#aaa" font-size="10">{val}</text>'
        )

weekly_svg = f"""
<svg width="800" height="200" xmlns="http://www.w3.org/2000/svg">

<defs>
  <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#7df9ff"/>
    <stop offset="100%" stop-color="#ff6ec7"/>
  </linearGradient>
</defs>

{common_style}

<rect x="5" y="5" width="790" height="190" rx="12" class="card"/>

<text class="title" x="24" y="40">📊 Weekly Activity</text>

<text x="700" y="40" fill="#666" font-size="10">
Last 7 days
</text>

<line x1="20" y1="50" x2="780" y2="50" stroke="#1f2937"/>

{''.join(bars)}
{''.join(labels)}

</svg>
"""

# ------------------ INSIGHTS SVG ------------------ #
avg = round(df['count'].mean(), 2)
max_day = df['count'].max()

insights_svg = f"""
<svg width="800" height="140" xmlns="http://www.w3.org/2000/svg">

{common_style}

<rect x="5" y="5" width="790" height="130" rx="12" class="card"/>

<text class="title" x="24" y="40">🧠 Dev Insights</text>
<line x1="20" y1="50" x2="780" y2="50" stroke="#1f2937"/>

<text class="label" x="24" y="80">Avg: {avg}</text>
<text class="label" x="400" y="80">Peak: {max_day}</text>

<text class="label" x="24" y="105">Momentum: {momentum}</text>

<text x="650" y="120" fill="#444" font-size="10">Built by Sarowar</text>

</svg>
"""

# ------------------ SAVE FILES ------------------ #
with open("graph.svg", "w") as f:
    f.write(graph_svg)

with open("weekly.svg", "w") as f:
    f.write(weekly_svg)

with open("insights.svg", "w") as f:
    f.write(insights_svg)
