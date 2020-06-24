from datetime import datetime, timedelta
import math

x = datetime(2020,6,11,18,20,34)
y = datetime.now() - x
print(y)
y = int(y.total_seconds())
print(y)
hours = math.floor(y/3600)
y -= hours*3600
mins = math.floor(y/60)
y -= mins*60

z = f"{hours}h{mins}m ago"
