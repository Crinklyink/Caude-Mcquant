import json, sys
sys.path.insert(0,'.')
from yf import get, crumb
import urllib.parse
for s in ["most_shorted_stocks","day_gainers","most_actives","small_cap_gainers","growth_technology_stocks","aggressive_small_caps"]:
    try:
        u=f"https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?count=50&scrIds={s}&crumb={urllib.parse.quote(crumb)}"
        r=json.loads(get(u))["finance"]["result"][0]
        q=r.get("quotes",[])
        print(s,len(q),[x["symbol"] for x in q][:50])
    except Exception as e:
        print(s,"ERR",e)
