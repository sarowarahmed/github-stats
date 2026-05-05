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

<!-- TODAY LINE -->
<line x1="{points[-1].split(',')[0]}" 
      y1="60" 
      x2="{points[-1].split(',')[0]}" 
      y2="{height-padding}"
      stroke="#ff6ec7"
      stroke-opacity="0.3"
      stroke-dasharray="4,4"/>

<text x="{points[-1].split(',')[0]}" y="50"
      fill="#ff6ec7" font-size="10" text-anchor="middle">
Today
</text>

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
    color = "url(#grad)" if not is_today else "#00ecbc"

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
    # 🔥 ADD THIS BLOCK
    if is_today:
        bars.append(f'''
    <rect x="{x}" y="{y}" width="50" height="{bar_height}"
          fill="#ff6ec7" opacity="0.08"/>
    ''')

    # 🔥 MAIN BAR (on top)
    bars.append(f'''
    <rect x="{x}" y="180" width="50" height="0" rx="6" fill="{color}">
      <animate attributeName="height" from="0" to="{bar_height}" dur="0.8s" fill="freeze"/>
      <animate attributeName="y" from="180" to="{y}" dur="0.8s" fill="freeze"/>
    </rect>
    ''')

    # keep your light edge + glow after
    bars.append(f'''
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
    <stop offset="0%" stop-color="#20e2d7"/>
    <stop offset="100%" stop-color="#f9fea5"/>
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
# ---------- SPARKLINE DATA ----------
def sparkline(data, width=160, height=30):
    if len(data) == 0:
        return ""

    max_val = max(data) if max(data) != 0 else 1
    points = []

    for i, val in enumerate(data):
        x = i * (width / (len(data)-1)) if len(data) > 1 else 0
        y = height - (val / max_val) * height
        points.append(f"{x},{y}")

    return " ".join(points)

avg = round(df['count'].mean(), 2)
max_day = df['count'].max()
last_14 = df['count'].tail(14).tolist()
spark_avg = sparkline(last_14)
spark_peak = sparkline(df['count'].tail(14).diff().fillna(0).abs().tolist())
spark_consistency = sparkline((df['count'] > 0).astype(int).tail(14).tolist())

weekday_avg = df.groupby(df['date'].dt.dayofweek)['count'].mean().tolist()
spark_bestday = sparkline(weekday_avg)

# ---------- EXTRA METRICS ----------
consistency = round((df['count'] > 0).mean() * 100)
best_day = df.groupby(df['date'].dt.day_name())['count'].mean().idxmax()[:3]

# ---------- SVG ----------
insights_svg = f"""
<svg width="800" height="220" xmlns="http://www.w3.org/2000/svg">

<defs>
  <linearGradient id="cardGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#7df9ff" stop-opacity="0.15"/>
    <stop offset="100%" stop-color="#ff6ec7" stop-opacity="0.15"/>
  </linearGradient>
</defs>

<style>
.title {{ fill: #c084fc; font-size: 16px; font-weight: 600; }}
.label {{ fill: #9ca3af; font-size: 11px; text-anchor: middle; }}
.value {{ fill: #ffffff; font-size: 18px; font-weight: 600; text-anchor: middle; }}
.card {{ fill: #0d1117; stroke: #1f2937; stroke-width: 1; }}
.glass {{ fill: url(#cardGrad); stroke: #7df9ff; stroke-opacity: 0.2; }}
.spark {{ fill: none; stroke: #7df9ff; stroke-width: 1.5; opacity: 0.7; }}
.spark-alt {{ fill: none; stroke: #ff6ec7; stroke-width: 1.5; opacity: 0.6; }}
</style>

<rect x="5" y="5" width="790" height="210" rx="12" class="card"/>

<text class="title" x="24" y="40">🧠 Dev Insights</text>
<circle cx="760" cy="35" r="3" fill="#ff6ec7"/>
<line x1="20" y1="50" x2="780" y2="50" stroke="#1f2937"/>

<!-- ===== ROW 1 ===== -->
<!-- AVG -->
<g transform="translate(40,70)">
  <rect width="200" height="80" rx="10" class="glass"/>
  <text class="label" x="100" y="20">Avg</text>
  <text class="value" x="100" y="45">{avg}</text>
  <polyline class="spark" points="{spark_avg}" transform="translate(20,50)"/>
</g>

<!-- PEAK -->
<g transform="translate(300,70)">
  <rect width="200" height="80" rx="10" class="glass"/>
  <text class="label" x="100" y="20">Peak</text>
  <text class="value" x="100" y="45">{max_day}</text>
  <polyline class="spark-alt" points="{spark_peak}" transform="translate(20,50)"/>
</g>

<!-- MOMENTUM -->
<g transform="translate(560,70)">
  <rect width="200" height="80" rx="10"
        fill="#ff6ec7" fill-opacity="0.15" stroke="#ff6ec7" stroke-opacity="0.3"/>
  <text class="label" x="100" y="20">Momentum</text>
  <text class="value" x="100" y="45">{momentum}</text>
</g>

<!-- ===== ROW 2 ===== -->
<!-- CONSISTENCY -->
<g transform="translate(160,160)">
  <rect width="200" height="60" rx="10" class="glass"/>
  <text class="label" x="100" y="20">Consistency</text>
  <text class="value" x="100" y="40">{consistency}%</text>
  <polyline class="spark" points="{spark_consistency}" transform="translate(20,45) scale(1,0.6)"/>
</g>

<!-- BEST DAY -->
<g transform="translate(440,160)">
  <rect width="200" height="60" rx="10" class="glass"/>
  <text class="label" x="100" y="20">Best Day</text>
  <text class="value" x="100" y="40">{best_day}</text>
  <polyline class="spark-alt" points="{spark_bestday}" transform="translate(20,45) scale(1,0.6)"/>
</g>

<!-- SIGNATURE -->
<text x="720" y="40" fill="#9ca3af" opacity="0.8" font-size="12" text-anchor="end">
Built by Sarowar ⚡
</text>

</svg>
"""

# ------------------ SAVE FILES ------------------ #
with open("graph.svg", "w") as f:
    f.write(graph_svg)

with open("weekly.svg", "w") as f:
    f.write(weekly_svg)

with open("insights.svg", "w") as f:
    f.write(insights_svg)
