import json, sys, urllib.parse, urllib.request
sys.path.insert(0,'.')
import yf
def screen(offset=0,size=250):
    q={"offset":offset,"size":size,"sortField":"intradaymarketcap","sortType":"DESC","quoteType":"EQUITY","topOperator":"AND",
       "query":{"operator":"AND","operands":[
         {"operator":"eq","operands":["region","us"]},
         {"operator":"or","operands":[{"operator":"EQ","operands":["exchange","NMS"]},{"operator":"EQ","operands":["exchange","NYQ"]}]},
         {"operator":"gt","operands":["intradaymarketcap",1000000000]},
         {"operator":"gt","operands":["intradayprice",5]},
         {"operator":"gt","operands":["avgdailyvol3m",500000]}]},
       "userId":"","userIdType":"guid"}
    u="https://query1.finance.yahoo.com/v1/finance/screener?crumb="+urllib.parse.quote(yf.crumb)+"&lang=en-US&region=US&formatted=false&corsDomain=finance.yahoo.com"
    req=urllib.request.Request(u,data=json.dumps(q).encode(),headers={"User-Agent":"Mozilla/5.0","Content-Type":"application/json"})
    return json.loads(yf.op.open(req,timeout=30).read())["finance"]["result"][0]
r=screen(0,250)
print(r["total"],len(r["quotes"]))
print(r["quotes"][0].keys())
allq=[]
off=0
while off<r["total"] and off<3500:
    rr=screen(off,250)
    allq+=rr["quotes"]
    off+=250
print(len(allq))
json.dump(allq,open("univ_all.json","w"))
