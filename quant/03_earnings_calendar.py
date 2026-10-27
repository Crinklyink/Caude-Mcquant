import json, urllib.request, datetime as dt, time
def day(d):
    req = urllib.request.Request(f"https://api.nasdaq.com/api/calendar/earnings?date={d}", headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=25).read())["data"]["rows"] or []
out = {}
d = dt.date(2026,10,12)
while d <= dt.date(2026,11,9):
    if d.weekday() < 5:
        try:
            rows = day(d.isoformat())
            out[d.isoformat()] = rows
            print(d, len(rows))
        except Exception as e:
            print(d, "ERR", e)
        time.sleep(0.4)
    d += dt.timedelta(days=1)
json.dump(out, open("earnings.json","w"))
