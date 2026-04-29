"""
主力资金因子规则 (MainFlowRule)
================================

设计目标：解决"涨停诱多陷阱"（如 600654 4/13 涨停吸筹后 8 日派发 -7.6 亿）。

数据源：东方财富免费 fflow 接口（无需 token）
  https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get

包含三个子因子：
  A1. MainNetFlow_5D   ：近 5 日主力（超大单+大单）累计净额（万元）
  A2. MainContinuity   ：近 10 日主力净流入天数 / 10
  A3. LimitUpFollowThrough ：检查最近一次涨停后 1-5 日主力跟进度
                             (= 涨停后 5 日主力净额 / 涨停日主力净额)

判定逻辑（一票否决 OR 通过）：
  * 5 日净流出 > flow_out_veto（默认 5000 万）→ 否决
  * 涨停后跟进度 < follow_veto（默认 -0.3）→ 否决（典型派发型涨停）
  * 否则按主力净流入和连续性给出通过

为减少接口压力，模块级 LRU 缓存（同一交易日内同代码只取一次）。
"""
from __future__ import annotations

import json
import random
import re
import time
import urllib.request
from datetime import datetime
from functools import lru_cache

import pandas as pd

from rules.base import BaseRule


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def _to_secid(code: str) -> str:
    """6 位股票代码 -> 东财 secid 格式"""
    code = str(code).zfill(6)
    if code.startswith(('60', '68', '5', '11', '13')):
        return f"1.{code}"
    return f"0.{code}"


_JSONP_RE = re.compile(r"^[^(]*\((.*)\)\s*;?\s*$", re.S)


@lru_cache(maxsize=4096)
def _fetch_fflow_raw(secid: str, day_key: str) -> tuple:
    """
    拉取东财日资金流向 (近若干日)。
    使用 JSONP 回调（cb=...）以避免服务器侧反爬限流。
    返回元组：每条 (date, main, small, mid, big, super) 单位：元
    """
    base = (
        "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
        f"?secid={secid}"
        "&fields1=f1,f2,f3,f7"
        "&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65"
        "&klt=101&lmt=15"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Referer": "https://data.eastmoney.com/",
        "Accept": "*/*",
    }
    for attempt in range(3):
        try:
            cb = f"jQuery{random.randint(10**14, 10**15)}_{int(time.time()*1000)}"
            url = f"{base}&cb={cb}&_={int(time.time()*1000)}"
            req = urllib.request.Request(url, headers=headers)
            raw = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "ignore")
            m = _JSONP_RE.match(raw.strip())
            payload = m.group(1) if m else raw
            data = json.loads(payload)
            klines = (data.get("data") or {}).get("klines") or []
            out = []
            for ln in klines:
                a = ln.split(",")
                if len(a) < 6:
                    continue
                try:
                    out.append((
                        a[0],
                        float(a[1]),  # main net
                        float(a[2]),  # small net
                        float(a[3]),  # mid net
                        float(a[4]),  # big net
                        float(a[5]),  # super net
                    ))
                except ValueError:
                    continue
            if out:
                return tuple(out)
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.5 * (attempt + 1))
    return tuple()


def fetch_money_flow(code: str) -> pd.DataFrame:
    """对外暴露的接口：返回近 30 日资金流向 DataFrame（万元）"""
    secid = _to_secid(code)
    day_key = datetime.now().strftime("%Y%m%d")
    rows = _fetch_fflow_raw(secid, day_key)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["date", "main", "small", "mid", "big", "super"])
    # 元 -> 万元
    for col in ("main", "small", "mid", "big", "super"):
        df[col] = df[col] / 1e4
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


# ---------------------------------------------------------------------------
# 规则类
# ---------------------------------------------------------------------------
class MainFlowRule(BaseRule):
    """主力资金过滤规则

    Args:
        flow_out_veto (float):  5 日累计净流出阈值（万元，正数；超过即一票否决）
        follow_veto   (float):  涨停后 5 日跟进度阈值（< 此值即否决）
        require_net_in (bool):  是否要求 5 日主力净流入为正才算通过
        min_continuity (float): 最低连续性（10 日中净流入天数比例），默认 0.4
        limit_up_threshold (float): 涨停判定阈值，默认 0.095
        net_in_pass_wan (float): 5 日主力净流入达到此值（万元）则强通过
    """

    name = "主力资金"

    def __init__(
        self,
        flow_out_veto: float = 5000.0,
        follow_veto: float = -0.3,
        require_net_in: bool = False,
        min_continuity: float = 0.4,
        limit_up_threshold: float = 0.095,
        net_in_pass_wan: float = 2000.0,
    ):
        self.flow_out_veto = flow_out_veto
        self.follow_veto = follow_veto
        self.require_net_in = require_net_in
        self.min_continuity = min_continuity
        self.limit_up_threshold = limit_up_threshold
        self.net_in_pass_wan = net_in_pass_wan

    # 兼容 BaseRule(daily_df, weekly_df) 签名 + 通过 **kwargs 接收 code
    def evaluate(self, daily_df: pd.DataFrame, weekly_df=None, **kwargs) -> dict:
        code = kwargs.get("code")
        if not code:
            return {"passed": False, "detail": {"reason": "未传入股票代码"}}

        flow = fetch_money_flow(code)
        if flow.empty or len(flow) < 5:
            # 接口不可用时降级：不应一票否决整只股票
            return {
                "passed": True,
                "detail": {
                    "reason": "资金流接口暂不可用，跳过该过滤",
                    "degraded": True,
                },
            }

        # ── A1: 5 日主力净额 ──
        main_5d = float(flow.tail(5)["main"].sum())

        # ── A2: 10 日主力连续性 ──
        last10 = flow.tail(10)["main"]
        continuity = float((last10 > 0).sum() / max(len(last10), 1))

        # ── A3: 涨停后跟进度 ──
        follow_through = None
        cross_date = None
        if daily_df is not None and len(daily_df) >= 2:
            df = daily_df.copy()
            df["chg"] = df["收盘价"].pct_change()
            # 找最近 30 日内的涨停日
            recent = df.tail(30)
            limit_up_rows = recent[recent["chg"] >= self.limit_up_threshold]
            if not limit_up_rows.empty:
                lu_date = pd.Timestamp(limit_up_rows["日期"].iloc[-1])
                # 找该日在资金流中的索引
                flow_idx = flow.index[flow["date"] == lu_date]
                if len(flow_idx) > 0:
                    i = int(flow_idx[0])
                    d0_main = float(flow["main"].iloc[i])
                    after = flow["main"].iloc[i + 1 : i + 6]
                    if len(after) >= 1 and abs(d0_main) > 1e-3:
                        follow_through = float(after.sum() / d0_main)
                        cross_date = lu_date.strftime("%Y-%m-%d")

        # ── 一票否决 ──
        veto_reason = None
        if main_5d < -abs(self.flow_out_veto):
            veto_reason = f"5日主力净流出 {main_5d:.0f} 万 < -{self.flow_out_veto:.0f}"
        elif follow_through is not None and follow_through < self.follow_veto:
            veto_reason = (
                f"涨停后跟进度 {follow_through:.2f} < {self.follow_veto}"
                f"（{cross_date} 涨停后派发）"
            )

        # ── 通过判定 ──
        if veto_reason:
            passed = False
        else:
            if self.require_net_in and main_5d <= 0:
                passed = False
            else:
                # 主力净流入达到阈值或连续性达标
                passed = (main_5d >= self.net_in_pass_wan) or (continuity >= self.min_continuity and main_5d > 0)

        return {
            "passed": passed,
            "detail": {
                "main_net_5d_wan": round(main_5d, 1),
                "continuity_10d": round(continuity, 2),
                "limit_up_date": cross_date,
                "follow_through": round(follow_through, 3) if follow_through is not None else None,
                "veto_reason": veto_reason,
            },
        }
