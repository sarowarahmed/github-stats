import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

USERNAME = "sarowarahmed"

url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}"
data = requests.get(url).json()

days = []
counts = []

# 🔁 robust parsing
contrib_data = data['contributions']

if isinstance(contrib_data, dict):
    for week in contrib_data.get('weeks', []):
        for day in week.get('contributionDays', []):
            days.append(day['date'])
            counts.append(day['contributionCount'])
else:
    for week in contrib_data:
        for day in week.get('days', []):
            days.append(day['date'])
            counts.append(day['count'])

df = pd.DataFrame({
    "date": pd.to_datetime(days),
    "count": counts
}).sort_values("date")

df = df.tail(60).reset_index(drop=True)

# 📊 STREAK CALCULATION
streak = 0
for val in reversed(df['count']):
    if val > 0:
        streak += 1
    else:
        break

# 📈 SIMPLE ML PREDICTION (moving average)
df['pred'] = df['count'].rolling(5).mean().fillna(0)

# 🎨 SVG GENERATION (CUSTOM — NO MATPLOTLIB)
width = 800
height = 300
padding = 40

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

.dot {{
    fill: #ff6ec7;
}}

@keyframes draw {{
    from {{ stroke-dashoffset: 1000; }}
    to {{ stroke-dashoffset: 0; }}
}}

.line {{
    stroke-dasharray: 1000;
    animation: draw 2s ease-out forwards;
}}
</style>

<rect width="100%" height="100%" fill="#0d1117"/>

<polyline class="glow line" points="{' '.join(points)}"/>
<polyline class="pred" points="{' '.join(pred_points)}"/>

<text x="20" y="30" fill="#c084fc" font-size="16">
🔥 Streak: {streak} days
</text>

<text x="20" y="50" fill="#aaa" font-size="12">
Predicted trend (dashed)
</text>

</svg>
"""

with open("graph.svg", "w") as f:
    f.write(svg)
