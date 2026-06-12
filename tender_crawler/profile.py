from __future__ import annotations

from typing import List, Optional, Tuple

DEFAULT_BUSINESS_PROFILE = "beijing_guangheng_accounting_firm"

DEFAULT_INCLUDE_KEYWORDS = [
    "审计",
    "财务审计",
    "年报审计",
    "决算审计",
    "竣工财务决算",
    "财务决算",
    "预算绩效",
    "绩效评价",
    "绩效评估",
    "内部控制",
    "内控评价",
    "清产核资",
    "资产清查",
    "会计师事务所",
    "注册会计师",
    "财务咨询",
    "税务咨询",
    "专项债",
    "债券",
    "发债",
    "上市公司",
    "证券服务",
    "证券备案",
    "IPO",
    "并购重组",
]

DEFAULT_EXCLUDE_KEYWORDS = [
    "食材",
    "物业",
    "保洁",
    "保安",
    "车辆维修",
    "家具",
    "医疗设备",
    "办公设备",
    "服装",
]

KEYWORD_WEIGHTS = {
    "会计师事务所": 5,
    "注册会计师": 5,
    "证券服务": 5,
    "证券备案": 5,
    "上市公司": 5,
    "IPO": 5,
    "并购重组": 5,
    "年报审计": 4,
    "竣工财务决算": 4,
    "财务决算": 4,
    "清产核资": 4,
    "资产清查": 4,
    "预算绩效": 4,
    "绩效评价": 4,
    "绩效评估": 4,
    "内控评价": 4,
    "内部控制": 3,
    "财务审计": 4,
    "审计": 3,
    "财务咨询": 3,
    "税务咨询": 3,
    "专项债": 3,
    "债券": 3,
    "发债": 3,
}


def evaluate_relevance(
    text: str,
    include_keywords: Optional[List[str]] = None,
    exclude_keywords: Optional[List[str]] = None,
) -> Tuple[int, List[str]]:
    include = include_keywords or DEFAULT_INCLUDE_KEYWORDS
    exclude = exclude_keywords or DEFAULT_EXCLUDE_KEYWORDS
    normalized_text = text.lower()

    matched: List[str] = []
    score = 0
    for keyword in include:
        if keyword.lower() in normalized_text:
            matched.append(keyword)
            score += KEYWORD_WEIGHTS.get(keyword, 2)

    for keyword in exclude:
        if keyword.lower() in normalized_text:
            score -= 2

    return max(score, 0), matched
