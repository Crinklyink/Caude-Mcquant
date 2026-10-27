import json, sys, urllib.request, http.cookiejar, urllib.parse, time
UA = {"User-Agent": "Mozilla/5.0"}
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = list(UA.items())
def get(url):
    return op.open(url, timeout=25).read().decode()
try: get("https://fc.yahoo.com")
except Exception: pass
crumb = get("https://query1.finance.yahoo.com/v1/test/getcrumb")
def chart(sym, rng="2y", interval="1d", events=""):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval={interval}" + (f"&events={events}" if events else "")
    return json.loads(get(u))["chart"]["result"][0]
def options(sym, date=None):
    u = f"https://query2.finance.yahoo.com/v7/finance/options/{sym}?crumb={urllib.parse.quote(crumb)}" + (f"&date={date}" if date else "")
    return json.loads(get(u))["optionChain"]["result"][0]
if __name__ == "__main__":
    o = options("SPY")
    print(o["expirationDates"][:12], o["quote"].get("regularMarketPrice"))
