import requests
import pandas as pd
from datetime import datetime, timedelta
import os

USERNAME = "sarowarahmed"
TOKEN = os.getenv("GH_TOKEN")

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

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

response = requests.post(
    "https://api.github.com/graphql",
    json={"query": query},
    headers=headers
)

data = response.json()

# 🔥 Extract real data
weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

days = []
counts = []

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
df = df.set_index('date').reindex(full_range, fill_value=0).rename_axis('date').reset_index()

# 🔥 STREAK (accurate now)
today = datetime.utcnow().date()
date_count = dict(zip(df['date'].dt.date, df['count']))

streak = 0
current_day = today

if date_count.get(current_day, 0) == 0:
    current_day -= timedelta(days=1)

while date_count.get(current_day, 0) > 0:
    streak += 1
    current_day -= timedelta(days=1)

# Prediction
df['pred'] = df['count'].rolling(5).mean().fillna(0)

# SVG
width, height, padding = 800, 300, 40
max_val = max(df['count'].max(), 1)

points = []
pred_points = []

for i, val in enumerate(df['count']):
    x = padding + i * (width - 2*padding) / len(df)
    y = height - padding - (val / max_val) * (height - 2*padding)
    points.append(f"{x},{y}")

for i, val in enumerate(df['pred']):
    x = padding + i * (width - 2*padding) / len(df)
    y = height - padding - (val / max_val) * (height - 2*padding)
    pred_points.append(f"{x},{y}")

svg = f"""
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">

<defs>
  <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#7df9ff"/>
    <stop offset="100%" stop-color="#ff6ec7"/>
  </linearGradient>

  <filter id="glow">
    <feGaussianBlur stdDeviation="3.5" result="coloredBlur"/>
    <feMerge>
      <feMergeNode in="coloredBlur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>

<style>
.line {{
    stroke: url(#grad);
    stroke-width: 3;
    fill: none;
    filter: url(#glow);
    stroke-dasharray: 2000;
    stroke-dashoffset: 2000;
    animation: draw 3s ease-out forwards;
}}

.pred {{
    stroke: #ff6ec7;
    stroke-width: 2;
    fill: none;
    stroke-dasharray: 6,6;
    opacity: 0.7;
}}

.dot {{
    fill: #ff6ec7;
    animation: pulse 2s infinite;
}}

@keyframes draw {{
    to {{ stroke-dashoffset: 0; }}
}}

@keyframes pulse {{
    0% {{ r: 2; opacity: 0.6; }}
    50% {{ r: 5; opacity: 1; }}
    100% {{ r: 2; opacity: 0.6; }}
}}
</style>

<rect width="100%" height="100%" fill="#0d1117"/>

<polyline class="line" points="{' '.join(points)}"/>
<polyline class="pred" points="{' '.join(pred_points)}"/>

{"".join([f'<circle class="dot" cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="2"/>' for p in points[-10:]])}

<text x="20" y="30" fill="#c084fc" font-size="18" font-weight="bold">
🔥 Streak: {streak} days
</text>

</svg>
"""

with open("graph.svg", "w") as f:
    f.write(svg)
