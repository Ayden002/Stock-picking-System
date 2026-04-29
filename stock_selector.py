"""
选股筛选模块 - 使用可插拔规则体系

默认规则组合：
  - GoldenCrossRule（周线 MA5 > MA10）
  - LimitUpRule（15 日内涨停）
  - VolumeSpikeRule（5 日内倍量）

可通过传入自定义 rules 列表来替换或扩展规则。
"""
import pandas as pd
from datetime import datetime
from logger import get_logger
from data_fetcher import DataFetcher
from config import STOCK_FILTER_CONFIG, FILTER_OPTIONS

# 规则模块
from rules import (
    GoldenCrossRule,
    LimitUpRule,
    VolumeSpikeRule,
    MainFlowRule,
    RiskFilterRule,
    VCPRule,
    BoxBreakoutRule,
    LiquidityRule,
)

logger = get_logger(__name__)

# 评分权重（合计 1.0）
#   资金面 0.25 + 形态(VCP+箱体) 0.30 + 趋势 0.15 + 量能 0.10 + 涨停 0.10 + 风险过滤 0.10
SCORE_WEIGHTS = {
    "主力资金"      : 0.25,
    "波动收敛VCP"   : 0.15,
    "箱体突破"      : 0.15,
    "均线金叉"      : 0.15,
    "倍量检测"      : 0.10,
    "涨停检测"      : 0.10,
    "风险过滤"      : 0.10,
}

# 一票否决规则：流动性 / 资金面 / 超买
VETO_RULES = {"流动性过滤", "主力资金", "风险过滤"}


def _build_default_rules():
    """根据 config.py 中的参数构建默认规则列表。"""
    cfg = STOCK_FILTER_CONFIG
    return [
        # ── Layer-1 一票否决：流动性预过滤（最便宜的剔除，先做）──
        LiquidityRule(
            avg_period=cfg.get("liq_avg_period", 20),
            min_amount_wan=cfg.get("liq_min_amount_wan", 5000.0),
            min_turnover_pct=cfg.get("liq_min_turnover_pct", 0.5),
        ),
        # ── Layer-1 一票否决：资金面 + 超买 ──
        MainFlowRule(
            flow_out_veto=cfg.get("mf_flow_out_veto_wan", 5000.0),
            follow_veto=cfg.get("mf_follow_veto", -0.3),
            require_net_in=cfg.get("mf_require_net_in", False),
            min_continuity=cfg.get("mf_min_continuity", 0.4),
            limit_up_threshold=cfg.get("limit_up_threshold", 0.095),
            net_in_pass_wan=cfg.get("mf_net_in_pass_wan", 2000.0),
        ),
        RiskFilterRule(
            rsi_period=cfg.get("rf_rsi_period", 14),
            rsi_overbought=cfg.get("rf_rsi_overbought", 80.0),
            kdj_n=cfg.get("rf_kdj_n", 9),
            kdj_j_overbought=cfg.get("rf_kdj_j_overbought", 100.0),
            boll_warn_z=cfg.get("rf_boll_warn_z", 0.8),
        ),
        # ── Layer-2 形态 / 趋势 / 动量 / 量能 / 涨停 ──
        VCPRule(
            short_n=cfg.get("vcp_short_n", 10),
            long_n=cfg.get("vcp_long_n", 30),
            threshold=cfg.get("vcp_threshold", 0.6),
            max_drawdown_in_long=cfg.get("vcp_max_drawdown", 0.2),
            max_dist_to_high=cfg.get("vcp_max_dist_to_high", 0.05),
        ),
        BoxBreakoutRule(
            box_window=cfg.get("box_window", 30),
            lookback_days=cfg.get("box_lookback_days", 3),
            min_break_pct=cfg.get("box_min_break_pct", 0.005),
            vol_ratio=cfg.get("box_vol_ratio", 1.5),
        ),
        GoldenCrossRule(
            ma_short=cfg['ma5_period'],
            ma_long=cfg['ma10_period'],
            use_weekly=cfg.get('use_weekly', True),
            lookback_weeks=cfg.get('lookback_weeks', 2),
            require_ma_long_up=cfg.get('require_ma_long_up', True),
        ),
        LimitUpRule(
            days=cfg['limit_up_days'],
            threshold=cfg['limit_up_threshold'],
        ),
        VolumeSpikeRule(
            days=cfg['volume_multiple_days'],
            ratio=cfg['volume_multiple_ratio'],
            avg_period=cfg['volume_avg_period'],
        ),
    ]

class StockSelector:
    """股票选择器

    Args:
        rules: 规则列表（继承自 BaseRule），默认使用配置文件中定义的三条规则。
               传入自定义列表即可替换全部规则，或在默认基础上追加。
    """

    def __init__(self, rules=None):
        self.fetcher = DataFetcher()
        self.rules = rules if rules is not None else _build_default_rules()
        self.logger = get_logger(__name__)

    def filter_stock(self, code):
        """对单个股票执行所有规则，返回结果字典。

        Args:
            code: 股票代码

        Returns:
            dict | None: 包含各规则结果的字典；数据不足时返回 None
        """
        try:
            self.logger.info(f"开始筛选股票 {code}")

            # 预过滤：ST / 北交所
            if FILTER_OPTIONS.get('exclude_st') and (code.startswith('ST') or code.startswith('*')):
                self.logger.debug(f"{code} 为 ST 股票，跳过")
                return None
            if FILTER_OPTIONS.get('exclude_bj') and (code.startswith('4') or code.startswith('8')):
                self.logger.debug(f"{code} 为北交所股票，跳过")
                return None

            # 获取数据
            daily_df  = self.fetcher.get_stock_daily(code, days=120)
            weekly_df = self.fetcher.get_stock_weekly(code, weeks=52)

            if daily_df is None or weekly_df is None:
                self.logger.warning(f"{code} 数据获取失败")
                return None

            min_list_days = FILTER_OPTIONS.get('min_list_days', 60)
            if len(daily_df) < min_list_days or len(weekly_df) < 11:
                self.logger.warning(f"{code} 数据长度不足（日线={len(daily_df)}，周线={len(weekly_df)}）")
                return None

            # 逐条规则执行（传入 code 以支持联网类规则）
            rule_results = {}
            for rule in self.rules:
                try:
                    rule_results[rule.name] = rule.evaluate(daily_df, weekly_df, code=code)
                except TypeError:
                    # 兼容旧版 evaluate(daily_df, weekly_df) 签名
                    rule_results[rule.name] = rule.evaluate(daily_df, weekly_df)

            # 一票否决
            vetoed = any(
                (not rule_results.get(n, {}).get("passed", False))
                for n in VETO_RULES
                if n in rule_results
            )

            # 综合评分（0-1）
            if vetoed:
                score = 0.0
            else:
                score = 0.0
                for n, w in SCORE_WEIGHTS.items():
                    if rule_results.get(n, {}).get("passed", False):
                        score += w
            score = round(score, 4)

            all_passed = (not vetoed) and all(r["passed"] for r in rule_results.values())

            result = {
                "code": code,
                "timestamp": datetime.now().isoformat(),
                "passed": all_passed,
                "vetoed": vetoed,
                "score": score,
                "rules": rule_results,
                "details": {
                    "latest_close": float(daily_df["收盘价"].iloc[-1]),
                    "latest_date": daily_df["日期"].iloc[-1].strftime("%Y-%m-%d"),
                    # 兼容字段（供旧版 main.py / CLI 打印使用）
                    "weekly_golden_cross": rule_results.get("均线金叉", {}).get("passed", False),
                    "limit_up_dates": rule_results.get("涨停检测", {}).get("detail", {}).get("limit_up_dates", []),
                    "max_increase": rule_results.get("涨停检测", {}).get("detail", {}).get("max_increase", 0.0),
                    "volume_dates": rule_results.get("倍量检测", {}).get("detail", {}).get("volume_dates", []),
                    "max_multiple": rule_results.get("倍量检测", {}).get("detail", {}).get("max_multiple", 0.0),
                },
            }

            if all_passed:
                self.logger.info(f"✓ {code} 通过全部 {len(self.rules)} 条规则（评分 {score}）")
            elif vetoed:
                self.logger.debug(f"✗ {code} 一票否决（资金/风险面未过）")
            else:
                failed = [n for n, r in rule_results.items() if not r["passed"]]
                self.logger.debug(f"✗ {code} 未通过规则: {failed}（评分 {score}）")

            return result

        except Exception as e:
            self.logger.error(f"{code} 筛选失败: {str(e)}", exc_info=True)
            return None
    
    def filter_stocks_batch(self, codes, max_workers=5):
        """批量筛选股票
        
        Args:
            codes: 股票代码列表
            max_workers: 最大并发数（保留用途，当前为顺序执行）
            
        Returns:
            list: 通过筛选的股票列表
        """
        results = []
        total = len(codes)
        
        self.logger.info(f"开始批量筛选 {total} 个股票")
        
        for i, code in enumerate(codes, 1):
            self.logger.info(f"[{i}/{total}] 正在处理 {code}")
            
            result = self.filter_stock(code)
            if result is not None:
                results.append(result)
        
        # 提取通过筛选的股票
        passed_stocks = [r for r in results if r['passed']]
        
        self.logger.info(f"筛选完成: 总共检查 {total} 个股票，{len(passed_stocks)} 个通过筛选")
        
        return passed_stocks, results
    
    def save_results(self, results, filename='stock_filter_results.csv'):
        """保存筛选结果到CSV文件

        Args:
            results: 筛选结果列表
            filename: 保存文件名（相对于 data/ 目录）
        """
        if not results:
            self.logger.warning("没有结果可保存")
            return

        try:
            data = []
            for r in results:
                row = {
                    '代码': r['code'],
                    '选股日期': r['details']['latest_date'],
                    '最新收盘价': r['details']['latest_close'],
                    '评分': r.get('score', 0.0),
                    '否决': '是' if r.get('vetoed') else '否',
                }
                # 每条规则的通过情况
                for rule_name, rule_res in r.get('rules', {}).items():
                    row[rule_name] = '是' if rule_res['passed'] else '否'
                row['通过筛选'] = '是' if r['passed'] else '否'
                data.append(row)

            df = pd.DataFrame(data)
            # 按评分降序，否决的排后面
            df['_veto_sort'] = df['否决'] == '是'
            df = df.sort_values(['_veto_sort', '评分'], ascending=[True, False]).drop(columns=['_veto_sort'])

            filepath = f'data/{filename}'
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            self.logger.info(f"结果已保存到 {filepath}")

        except Exception as e:
            self.logger.error(f"保存结果失败: {str(e)}", exc_info=True)

def get_recommended_stocks(code_list=None, sample_size=None):
    """获取推荐的股票列表
    
    Args:
        code_list: 股票代码列表（如果为None则获取所有A股）
        sample_size: 样本大小（用于测试，获取前N个股票）
        
    Returns:
        tuple: (通过筛选的股票, 所有筛选结果)
    """
    selector = StockSelector()
    
    # 获取股票代码列表
    if code_list is None:
        codes = selector.fetcher.get_all_stock_codes()
    else:
        codes = code_list
    
    # 样本处理（用于测试）
    if sample_size is not None and len(codes) > sample_size:
        codes = codes[:sample_size]
        logger.info(f"仅处理前 {sample_size} 个股票进行测试")
    
    if not codes:
        logger.error("无法获取股票代码列表")
        return [], []
    
    # 筛选
    passed_stocks, all_results = selector.filter_stocks_batch(codes)
    
    # 保存结果
    selector.save_results(all_results)
    
    return passed_stocks, all_results
