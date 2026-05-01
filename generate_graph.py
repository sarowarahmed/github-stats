import requests
import pandas as pd
import matplotlib.pyplot as plt

USERNAME = "sarowarahmed"

url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}"
data = requests.get(url).json()

days = []
counts = []

for week in data['contributions']:
    for day in week['days']:
        days.append(day['date'])
        counts.append(day['count'])

df = pd.DataFrame({
    "date": pd.to_datetime(days),
    "count": counts
})

# Last 30 days only
df = df.sort_values("date").tail(30)
df['day'] = range(1, len(df)+1)

# Style
plt.style.use("dark_background")

plt.figure(figsize=(14,5))
plt.plot(
    df['day'], df['count'],
    color="#7df9ff",
    linewidth=2,
    marker='o',
    markerfacecolor="#ff6ec7"
)

plt.fill_between(df['day'], df['count'], alpha=0.15)

plt.title(f"{USERNAME}'s Contribution Graph", color="#c084fc", fontsize=16)
plt.xlabel("Days")
plt.ylabel("Contributions")

plt.grid(color="#444", linestyle='--', linewidth=0.5)

plt.savefig("graph.svg", format="svg", bbox_inches="tight")
