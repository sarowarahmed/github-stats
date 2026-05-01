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
<style>
.glow {{
    stroke: #7df9ff;
    stroke-width: 2;
    fill: none;
    filter: drop-shadow(0 0 6px #7df9ff);
}}

.pred {{
    stroke: #ff6ec7;
    stroke-width: 2;
    fill: none;
    stroke-dasharray: 5,5;
}}

.line {{
    stroke-dasharray: 1000;
    animation: draw 2s ease-out forwards;
}}

@keyframes draw {{
    from {{ stroke-dashoffset: 1000; }}
    to {{ stroke-dashoffset: 0; }}
}}
</style>

<rect width="100%" height="100%" fill="#0d1117"/>

<polyline class="glow line" points="{' '.join(points)}"/>
<polyline class="pred" points="{' '.join(pred_points)}"/>

<text x="20" y="30" fill="#c084fc" font-size="16">
🔥 Streak: {streak} days
</text>

</svg>
"""

with open("graph.svg", "w") as f:
    f.write(svg)
