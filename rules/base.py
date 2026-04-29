"""
规则基类 - 所有选股规则必须继承此类
"""
from abc import ABC, abstractmethod


class BaseRule(ABC):
    """选股规则基类

    子类需要实现 evaluate() 方法，返回 dict，至少包含：
        - passed (bool): 是否通过该规则
        - detail (dict): 详细结果，方便展示/保存
    """

    # 规则名称，子类可以覆盖
    name: str = "未命名规则"

    @abstractmethod
    def evaluate(self, daily_df, weekly_df=None, **kwargs) -> dict:
        """
        对单只股票执行规则判断。

        Args:
            daily_df (pd.DataFrame): 日线数据，列名见 data_fetcher._DAILY_COLS
            weekly_df (pd.DataFrame | None): 周线数据（部分规则不需要）
            **kwargs: 额外上下文（如 code=股票代码）供需要联网取数的规则使用

        Returns:
            dict: {
                "passed": bool,
                "detail": { ... }   # 规则相关的详细字段
            }
        """
        raise NotImplementedError
