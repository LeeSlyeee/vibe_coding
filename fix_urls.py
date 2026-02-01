path = '/home/ubuntu/InsightMind/backend/maum_on/urls.py'
with open(path, 'r') as f:
    content = f.read()

# Fix the broken import line
broken = "from .views import MaumOnViewSet, StatisticsView GetConfigView, GetConfigView,"
fixed = "from .views import MaumOnViewSet, StatisticsView, GetConfigView"

if broken in content:
    content = content.replace(broken, fixed)
else:
    # Try regex or looser search if exact match fails
    # Or just naive replace if slightly different
    pass

# Also look for double imports just in case
content = content.replace("StatisticsView GetConfigView", "StatisticsView, GetConfigView")
content = content.replace(", GetConfigView,", ", GetConfigView")

with open(path, 'w') as f:
    f.write(content)
