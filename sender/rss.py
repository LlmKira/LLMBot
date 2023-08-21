# -*- coding: utf-8 -*-
# @Time    : 2023/8/21 下午9:56
# @Author  : sudoskys
# @File    : rss.py
# @Software: PyCharm
import json
import socket

import feedparser
import html2text

from middleware.router.schema import router_set

router_set(role="sender", name="rss")


def sha1(string: str):
    import hashlib
    _sha1 = hashlib.sha1()
    _sha1.update(string.encode('utf-8'))
    return _sha1.hexdigest()[:10]


def get_feed(feed_url):
    socket.setdefaulttimeout(15)
    res = feedparser.parse(feed_url)
    try:
        json.dumps(res, indent=4, ensure_ascii=False)
    except Exception as e:
        raise ValueError("Fetch rss feed error")
    entries = res["entries"]
    source = res["feed"]["title"]
    _info = [
        {
            "title": entry["title"],
            "url": entry["link"],
            "id": entry["id"],
            "author": entry["author"],
            "summary": html2text.html2text(entry["summary"]),
        }
        for entry in entries
    ]
    return {
        "title": source,
        "entry": _info
    }


class Rss(object):
    """
    从缓存拉取，没有缓存就初始化，返回最后一条。
    有缓存则比对
    #TODO
    """
    def __init__(self, feed_url):
        # sha1
        self.db_key = f"rss:{sha1(feed_url)}"
        self.feed_url = feed_url

    def fetch(feed_url):
        entries = feedparser.parse(feed_url)["entries"]
        return [
            {
                "title": entry["title"],
                "url": entry["link"].split("#")[0],
                "published": entry["published"].split("T")[0],
            }
            for entry in entries
        ]
