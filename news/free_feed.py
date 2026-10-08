import email.utils
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

SOURCES={
    "全球財經": [
        ("CNBC Markets","https://www.cnbc.com/id/10000664/device/rss/rss.html"),
        ("Federal Reserve","https://www.federalreserve.gov/feeds/press_all.xml"),
    ],
    "台股": [
        ("Google News 台股","https://news.google.com/rss/search?q=%E5%8F%B0%E8%82%A1%20OR%20%E5%8F%B0%E7%A9%8D%E9%9B%BB&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"),
    ],
    "美股": [
        ("Google News 美股","https://news.google.com/rss/search?q=US%20stocks%20OR%20Federal%20Reserve&hl=en-US&gl=US&ceid=US:en"),
    ],
    "加密貨幣": [
        ("CoinDesk","https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ],
}

def _text(node, names):
    for name in names:
        found=node.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""

def _date(value):
    if not value:
        return None
    try:
        return email.utils.parsedate_to_datetime(value).astimezone(timezone.utc)
    except (TypeError,ValueError,OverflowError):
        try:
            return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
        except ValueError:
            return None

def parse_feed(content,source,category):
    root=ET.fromstring(content)
    nodes=root.findall(".//item")
    if not nodes:
        nodes=root.findall(".//{http://www.w3.org/2005/Atom}entry")
    output=[]
    for node in nodes:
        title=html.unescape(re.sub("<[^>]+>","",_text(node,["title","{http://www.w3.org/2005/Atom}title"])))
        url=_text(node,["link"])
        if not url:
            for link in node.findall("{http://www.w3.org/2005/Atom}link"):
                if link.attrib.get("href"):
                    url=link.attrib["href"]; break
        published=_date(_text(node,["pubDate","{http://www.w3.org/2005/Atom}updated","{http://www.w3.org/2005/Atom}published"]))
        if title and url.startswith(("https://","http://")):
            output.append({"title":title,"url":url,"source":source,"category":category,"published":published})
    return output

def fetch_news(category="全部",limit=60):
    feeds=[(cat,name,url) for cat,items in SOURCES.items() for name,url in items if category in ("全部",cat)]
    items=[]; errors=[]
    for cat,name,url in feeds:
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 PRBM-NewsReader/0.9"})
            with urllib.request.urlopen(req,timeout=8) as response:
                body=response.read(1_500_000)
            items.extend(parse_feed(body,name,cat))
        except Exception:
            errors.append(name+" 暫時無法讀取")
    unique={}
    for item in items:
        key=re.sub(r"\W+","",item["title"].casefold())
        if key not in unique or (item["published"] or datetime.min.replace(tzinfo=timezone.utc))>(unique[key]["published"] or datetime.min.replace(tzinfo=timezone.utc)):
            unique[key]=item
    ordered=sorted(unique.values(),key=lambda x:x["published"] or datetime.min.replace(tzinfo=timezone.utc),reverse=True)
    return ordered[:limit],errors
