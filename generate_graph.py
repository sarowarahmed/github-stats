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

shadow_points = []
offset_x = 6
offset_y = 10

for i, val in enumerate(df['count']):
    x = padding + i * (width - 2*padding) / len(df) + offset_x
    y = height - padding - (val / max_val) * (height - 2*padding) + offset_y
    shadow_points.append(f"{x},{y}")

svg = f"""
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">

<defs>
  <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#7df9ff"/>
    <stop offset="100%" stop-color="#ff6ec7"/>
  </linearGradient>

  <linearGradient id="floorGrad" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#ff6ec7" stop-opacity="0.3"/>
    <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
  </linearGradient>

  <filter id="blur">
    <feGaussianBlur stdDeviation="4"/>
  </filter>
</defs>

<style>
.main {{
    stroke: url(#grad);
    stroke-width: 3;
    fill: none;
    filter: drop-shadow(0 0 6px #7df9ff);
}}

.shadow {{
    stroke: #ff6ec7;
    stroke-width: 3;
    opacity: 0.25;
    fill: none;
    filter: url(#blur);
}}

.floor {{
    fill: url(#floorGrad);
}}
</style>

<rect width="100%" height="100%" fill="#0d1117"/>

<!-- 🔥 shadow layer -->
<polyline class="shadow" points="{' '.join(shadow_points)}"/>

<!-- 🔥 main graph -->
<polyline class="main" points="{' '.join(points)}"/>

<!-- 🔥 floor glow -->
<polygon class="floor" points="
{' '.join(points)}
{points[-1].split(',')[0]},{height-padding}
{points[0].split(',')[0]},{height-padding}
"/>

</svg>
"""

with open("graph.svg", "w") as f:
    f.write(svg)
