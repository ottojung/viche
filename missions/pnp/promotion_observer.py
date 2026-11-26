"""Separate read-only allocator observation of competition, not a promoter."""
import json
import time
from . import competition, desk, state
from .lbcert import promotion

def observe():
    auth=promotion.enabled()
    if not auth or desk.retry_until()>time.time():return
    now=time.time()
    try:old=json.loads(promotion.observation_path().read_text())
    except (OSError,ValueError,TypeError):old={}
    at=old.get("at",0)
    if type(at) in (int,float) and 0<=now-at<20:return
    ids=list(dict.fromkeys(g for g,_ in promotion.pending(auth)))
    if not ids:return
    order=old.get("probed",{})
    if not isinstance(order,dict):order={}
    order={g:t for g,t in order.items() if g in ids and type(t) in (int,float)}
    ids=sorted(ids,key=lambda g:order.get(g,0))[:competition.MAX_BATCH]
    counts=competition.observe(ids)
    if promotion.enabled()==auth:
        order.update({g:now for g in ids})
        state.atomic_write(str(promotion.observation_path()),json.dumps({"at":now,"counts":counts,"probed":order}))
