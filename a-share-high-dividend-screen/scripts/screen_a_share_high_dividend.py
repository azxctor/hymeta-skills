#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""筛选A股高股息候选并生成综合分排序CSV。"""

import argparse
import json
import os
import re
import shutil
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# 钉钉企业内部应用凭证与工作通知接口；access_token 有效期 7200 秒。
DINGTALK_TOKEN_URL = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
DINGTALK_WORK_NOTICE_URL = (
    "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2"
)
DINGTALK_TOKEN_TTL = 7000
_dingtalk_token_cache = {}


DEFAULT_THEME_PATTERNS = {
    "tech": (
        "科技|半导体|芯片|存储|光模块|光通信|通信|通讯|电信|网络|"
        "光电|电子|微电|集成|海康|大华|亿联|沪电|生益|深南|鹏鼎|胜宏|"
        "光迅|中际|新易盛|天孚|剑桥|兆易|澜起|佰维|江波龙|寒武纪|海光"
    ),
    "ai_robot": (
        "机器人|人工智能|智能|AI|自动|电机|机电|伺服|控制|视觉|光电|"
        "传感|激光|软件|系统|科技|工业|工控|装备|仪器|仪表|网络|数据|"
        "海康|大华|汇川|埃斯顿|拓斯达|中控|科大讯飞|工业富联"
    ),
}

DEFAULT_THEME_INDUSTRIES = {
    "tech": {
        "半导体", "通信设备", "电信运营", "软件服务", "IT设备", "元器件",
        "互联网", "电器仪表",
    },
    "ai_robot": {
        "软件服务", "IT设备", "专用机械", "电气设备", "元器件", "通信设备",
        "电器仪表", "机械基件", "工程机械", "互联网", "半导体",
    },
}


def find_project_root() -> Path:
    """定位cbqpt项目根目录。"""
    here = Path.cwd().resolve()
    for path in [here, *here.parents]:
        if (path / "utils" / "tushare_config.py").exists():
            return path
    raise RuntimeError("请在cbqpt仓库内运行，未找到utils/tushare_config.py")


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="筛选A股高股息行业TopN并按综合分排序输出CSV"
    )
    parser.add_argument("--trade-date", help="行情日期，格式YYYYMMDD；默认向前找最近可用交易日")
    parser.add_argument("--lookback-days", type=int, default=14, help="未指定日期时向前查找天数")
    parser.add_argument("--report-period", default="20260331", help="AKShare业绩报表期，格式YYYYMMDD")
    parser.add_argument("--output-dir", default="data/outputs", help="输出目录")
    parser.add_argument("--top-n", type=int, default=3, help="每个行业保留数量")
    parser.add_argument("--dividend-min", type=float, default=3.0, help="最低股息率TTM")
    parser.add_argument("--market-cap-min", type=float, default=100.0, help="最低总市值，单位亿元")
    parser.add_argument("--no-built-in-themes", action="store_true", help="不使用内置tech/ai_robot主题追加")
    parser.add_argument(
        "--no-notify-dingding",
        action="store_true",
        help="关闭钉钉摘要通知",
    )
    parser.add_argument(
        "--theme",
        action="append",
        default=[],
        help="追加主题，格式 name=正则表达式；可重复",
    )
    parser.add_argument("--weight-pe-value", type=float, default=0.40)
    parser.add_argument("--weight-dividend", type=float, default=0.30)
    parser.add_argument("--weight-roe", type=float, default=0.20)
    parser.add_argument("--weight-market-cap", type=float, default=0.05)
    parser.add_argument("--weight-gross-margin", type=float, default=0.05)
    parser.add_argument("--weight-profit-yoy", type=float, default=0.0)
    parser.add_argument("--max-candidates", type=int, default=0, help="调试用：限制候选数量")
    return parser.parse_args()


def load_apis(project_root: Path):
    """加载项目内TuShare配置和AKShare。"""
    sys.path.insert(0, str(project_root))
    import akshare as ak  # noqa: WPS433
    from utils.tushare_config import pro  # noqa: WPS433

    return ak, pro


def _mask_secret(text: str, *secrets: str) -> str:
    """把凭证从日志和异常文本中抹掉。"""
    masked = str(text)
    for secret in secrets:
        value = str(secret or "").strip()
        if len(value) >= 6:
            masked = masked.replace(value, "***")
    return masked


def _split_id_list(value) -> list[str]:
    """把逗号分隔字符串或列表统一成去重后的ID列表。"""
    if value is None:
        return []
    if isinstance(value, (str, int)):
        items = str(value).replace("，", ",").split(",")
    else:
        items = [str(item) for item in value]
    cleaned = [item.strip() for item in items if str(item).strip()]
    return list(dict.fromkeys(cleaned))


def _is_true(value) -> bool:
    """兼容中文真假和常见布尔写法。"""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"真", "true", "1", "yes", "y", "是"}


def load_dingding_app_config(project_root: Path) -> tuple[bool, dict, str]:
    """读取钉钉企业内部应用机器人配置，环境变量优先。"""
    config_path = project_root / "分析配置.json"
    config = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            return False, {}, f"分析配置.json读取失败: {exc}"
    elif not os.environ.get("DINGTALK_CLIENT_ID"):
        return False, {}, "分析配置.json不存在"

    if config and config.get("发送通知") != "真":
        return False, {}, "发送通知未开启"
    if config and config.get("发送方式") != "钉钉":
        return False, {}, "发送方式不是钉钉"

    app_config = config.get("钉钉应用机器人") or {}
    if not isinstance(app_config, dict):
        return False, {}, "钉钉应用机器人配置格式错误"
    if app_config and not _is_true(app_config.get("启用", "真")):
        return False, {}, "钉钉应用机器人未启用"

    # 敏感项一律环境变量优先，配置文件只作为本机兜底。
    client_id = (
        os.environ.get("DINGTALK_CLIENT_ID")
        or str(app_config.get("client_id") or "")
    ).strip()
    client_secret = (
        os.environ.get("DINGTALK_CLIENT_SECRET")
        or str(app_config.get("client_secret") or "")
    ).strip()
    agent_id = (
        os.environ.get("DINGTALK_AGENT_ID")
        or str(app_config.get("agent_id") or "")
    ).strip()
    if not client_id or not client_secret:
        return False, {}, "缺少钉钉应用机器人client_id或client_secret"
    if not agent_id:
        return False, {}, "缺少钉钉应用机器人agent_id"

    userid_list = _split_id_list(
        os.environ.get("DINGTALK_USERID_LIST")
        or app_config.get("userid_list")
    )
    dept_id_list = _split_id_list(
        os.environ.get("DINGTALK_DEPT_ID_LIST")
        or app_config.get("dept_id_list")
    )
    to_all_user = _is_true(
        os.environ.get("DINGTALK_TO_ALL_USER")
        or app_config.get("发给全部可见范围", False)
    )
    # 工作通知必须至少命中一个收件范围，否则钉钉直接报错。
    if not userid_list and not dept_id_list and not to_all_user:
        return False, {}, "未配置userid_list/dept_id_list且未开启发给全部可见范围"

    return True, {
        "client_id": client_id,
        "client_secret": client_secret,
        "agent_id": agent_id,
        "userid_list": userid_list,
        "dept_id_list": dept_id_list,
        "to_all_user": to_all_user,
    }, "ok"


def fetch_dingding_access_token(client_id: str, client_secret: str) -> str:
    """获取企业内部应用access_token，进程内按有效期缓存。"""
    cached = _dingtalk_token_cache.get(client_id)
    if cached and cached["expire_at"] > time.time():
        return cached["token"]

    last_error = ""
    for attempt in range(3):
        try:
            # Secret 放 body 而非 URL，异常文本不会带出凭证。
            response = requests.post(
                DINGTALK_TOKEN_URL,
                json={"appKey": client_id, "appSecret": client_secret},
                timeout=15,
            )
            payload = response.json()
            token = str(payload.get("accessToken") or "").strip()
            if not token:
                raise RuntimeError(
                    f"钉钉返回缺少accessToken: {payload.get('message') or payload}"
                )
            expire_in = float(payload.get("expireIn") or DINGTALK_TOKEN_TTL)
            _dingtalk_token_cache[client_id] = {
                "token": token,
                "expire_at": time.time() + min(expire_in, DINGTALK_TOKEN_TTL),
            }
            return token
        except Exception as exc:  # noqa: BLE001
            last_error = _mask_secret(
                f"{type(exc).__name__}: {exc}", client_secret
            )
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"获取钉钉access_token失败: {last_error}")


def send_dingding_text(project_root: Path, message: str) -> dict:
    """通过钉钉应用机器人发送工作通知文本，失败不抛出凭证。"""
    enabled, app_config, reason = load_dingding_app_config(project_root)
    if not enabled:
        return {"sent": False, "reason": reason}

    client_secret = app_config["client_secret"]
    try:
        token = fetch_dingding_access_token(
            app_config["client_id"], client_secret
        )
    except Exception as exc:  # noqa: BLE001
        return {"sent": False, "reason": _mask_secret(exc, client_secret)}

    payload = {
        "agent_id": app_config["agent_id"],
        "msg": {"msgtype": "text", "text": {"content": message}},
    }
    if app_config["userid_list"]:
        payload["userid_list"] = ",".join(app_config["userid_list"])
    if app_config["dept_id_list"]:
        payload["dept_id_list"] = ",".join(app_config["dept_id_list"])
    if app_config["to_all_user"]:
        payload["to_all_user"] = True

    try:
        response = requests.post(
            DINGTALK_WORK_NOTICE_URL,
            params={"access_token": token},
            json=payload,
            timeout=15,
        )
        result = response.json()
    except Exception as exc:  # noqa: BLE001
        return {
            "sent": False,
            "reason": _mask_secret(
                f"钉钉工作通知发送失败: {exc}", client_secret, token
            ),
        }

    if result.get("errcode") == 0:
        return {"sent": True, "response": result}
    return {
        "sent": False,
        "reason": _mask_secret(
            f"钉钉工作通知发送失败: errcode={result.get('errcode')} "
            f"errmsg={result.get('errmsg')}",
            client_secret,
            token,
        ),
    }


def _format_float(value, digits=2) -> str:
    """格式化数字。"""
    try:
        if pd.isna(value):
            return "N/A"
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "N/A"


def build_success_message(summary: dict) -> str:
    """构建高股息筛选成功摘要。"""
    lines = [
        "✅ A股高股息筛选 执行完成",
        f"⏱️ 执行耗时：{_format_float(summary.get('execution_time'))}秒",
        f"📅 完成时间：{summary.get('completed_at')}",
        f"📈 行情日期：{summary.get('trade_date')}",
        "",
        "📊 筛选结果：",
        f"- 最终入选：{summary.get('final_rows')}只",
        f"- 覆盖行业：{summary.get('industry_count')}个",
        f"- 主题候选：{summary.get('theme_candidates')}只",
        f"- 主题追加：{summary.get('theme_append')}只",
        "",
        "🏆 综合分Top10：",
    ]

    top_rows = summary.get("top_rows")
    if top_rows is None or len(top_rows) == 0:
        lines.append("- 暂无入选标的")
    else:
        for index, (_, row) in enumerate(top_rows.head(10).iterrows(), start=1):
            lines.append(
                f"{index}. {row.get('证券名称')} {row.get('证券代码')} | "
                f"{row.get('行业')} | 综合分 {_format_float(row.get('综合分'))} | "
                f"股息率 {_format_float(row.get('股息率TTM'))}% | "
                f"PE分位 {_format_float(row.get('10年PE历史分位'))}%"
            )

    main_path = Path(summary.get("main_path", ""))
    latest_value = summary.get("latest_path")
    lines.extend([
        "",
        "📁 输出：",
        main_path.name,
    ])
    if latest_value:
        lines.append(Path(latest_value).name)
    return "\n".join(lines)


def build_failure_message(error: Exception, execution_time: float) -> str:
    """构建高股息筛选失败摘要。"""
    return "\n".join([
        "❌ A股高股息筛选 执行失败",
        f"⏱️ 执行耗时：{_format_float(execution_time)}秒",
        f"📅 失败时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"⚠️ 错误信息：{str(error)[:500]}",
    ])


def fetch_daily_basic(pro, trade_date: str | None, lookback_days: int) -> tuple[str, pd.DataFrame]:
    """获取指定或最近可用日的daily_basic。"""
    fields = (
        "ts_code,trade_date,close,pe,pe_ttm,pb,dv_ratio,dv_ttm,"
        "total_mv,circ_mv,turnover_rate"
    )
    if trade_date:
        df = pro.daily_basic(trade_date=trade_date, fields=fields)
        if df.empty:
            raise RuntimeError(f"TuShare daily_basic在{trade_date}无数据")
        return trade_date, df

    for offset in range(lookback_days + 1):
        date = (datetime.now() - timedelta(days=offset)).strftime("%Y%m%d")
        df = pro.daily_basic(trade_date=date, fields=fields)
        if not df.empty:
            return date, df
    raise RuntimeError(f"{lookback_days}天内未找到可用daily_basic数据")


def fetch_report(ak, report_period: str) -> pd.DataFrame:
    """获取东方财富业绩报表并规范字段。"""
    last_error = None
    for attempt in range(3):
        try:
            report = ak.stock_yjbb_em(date=report_period)
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    else:
        raise RuntimeError(
            f"AKShare stock_yjbb_em({report_period})获取失败: {last_error}"
        )
    columns = [
        "股票代码", "净资产收益率", "净利润-同比增长", "销售毛利率",
        "所处行业", "最新公告日期",
    ]
    report = report[columns].copy()
    report["股票代码"] = report["股票代码"].astype(str).str.zfill(6)
    return report


def build_filtered_candidates(pro, ak, args: argparse.Namespace) -> tuple[str, pd.DataFrame, pd.DataFrame]:
    """拉取数据并应用高股息硬过滤。"""
    trade_date, daily = fetch_daily_basic(pro, args.trade_date, args.lookback_days)
    basic = pro.stock_basic(
        exchange="",
        list_status="L",
        fields="ts_code,symbol,name,area,industry,market,list_date",
    )
    report = fetch_report(ak, args.report_period)

    data = daily.merge(basic, on="ts_code", how="inner")
    data = data.merge(report, left_on="symbol", right_on="股票代码", how="left")

    numeric_cols = [
        "close", "pe", "pe_ttm", "pb", "dv_ttm", "total_mv", "circ_mv",
        "净资产收益率", "净利润-同比增长", "销售毛利率",
    ]
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data["行业"] = data["industry"].fillna(data["所处行业"])
    data["总市值亿元"] = data["total_mv"] / 10000.0
    data["PE"] = data["pe_ttm"].where(data["pe_ttm"].notna(), data["pe"])

    bad_name = data["name"].astype(str).str.contains("ST|退", case=False, regex=True, na=False)
    market_ok = data["market"].isin(["主板", "创业板", "科创板"])
    filtered = data[
        (~bad_name)
        & market_ok
        & data["行业"].notna()
        & (data["dv_ttm"] >= args.dividend_min)
        & (data["总市值亿元"] >= args.market_cap_min)
        & (data["PE"] > 0)
        & (data["pb"] > 0)
        & (data["净资产收益率"] > 0)
    ].copy()

    if args.max_candidates and args.max_candidates > 0:
        filtered = filtered.head(args.max_candidates).copy()

    return trade_date, filtered, basic


def calc_pe_percentile(pro, code: str, current_pe: float, start_date: str, end_date: str) -> tuple[float | None, int, str]:
    """计算当前PE_TTM在历史正PE_TTM序列中的分位。"""
    last_error = ""
    for attempt in range(3):
        try:
            hist = pro.daily_basic(
                ts_code=code,
                start_date=start_date,
                end_date=end_date,
                fields="ts_code,trade_date,pe_ttm",
            )
            if hist.empty:
                return None, 0, "无历史PE"
            pe = pd.to_numeric(hist["pe_ttm"], errors="coerce")
            pe = pe[(pe > 0) & np.isfinite(pe)]
            if pe.empty:
                return None, 0, "无有效正PE"
            return round(float((pe <= current_pe).mean() * 100), 2), int(len(pe)), ""
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(0.8 * (attempt + 1))
    return None, 0, last_error


def add_pe_percentiles(pro, candidates: pd.DataFrame, basic: pd.DataFrame, trade_date: str, output_dir: Path) -> pd.DataFrame:
    """为候选池追加10年PE历史分位并写缓存。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = output_dir / f"a_share_high_dividend_pe_percentile_{trade_date}_cache.csv"
    end_dt = datetime.strptime(trade_date, "%Y%m%d")
    ten_year_start = end_dt.replace(year=end_dt.year - 10).strftime("%Y%m%d")
    list_date_map = dict(zip(basic["ts_code"], basic["list_date"].astype(str)))

    existing = {}
    if cache_path.exists():
        cache = pd.read_csv(cache_path, encoding="utf-8-sig")
        for _, row in cache.iterrows():
            existing[str(row["证券代码"])] = row.to_dict()

    rows = []
    codes = candidates["ts_code"].astype(str).tolist()
    for index, item in candidates.reset_index(drop=True).iterrows():
        code = str(item["ts_code"])
        current_pe = pd.to_numeric(item["PE"], errors="coerce")
        if code in existing and not pd.isna(existing[code].get("10年PE历史分位")):
            row = existing[code]
        elif pd.isna(current_pe) or current_pe <= 0:
            row = {
                "证券代码": code,
                "证券名称": item["name"],
                "当前PE": current_pe,
                "10年PE历史分位": None,
                "PE样本数": 0,
                "PE起始日期": None,
                "备注": "当前PE无效",
            }
        else:
            list_date = list_date_map.get(code, ten_year_start)
            start_date = max(ten_year_start, list_date if list_date and list_date != "nan" else ten_year_start)
            percentile, sample_count, note = calc_pe_percentile(
                pro, code, float(current_pe), start_date, trade_date
            )
            row = {
                "证券代码": code,
                "证券名称": item["name"],
                "当前PE": round(float(current_pe), 4),
                "10年PE历史分位": percentile,
                "PE样本数": sample_count,
                "PE起始日期": start_date,
                "备注": note,
            }
        rows.append(row)
        if (index + 1) % 20 == 0 or (index + 1) == len(codes):
            pd.DataFrame(rows).to_csv(cache_path, index=False, encoding="utf-8-sig")
            print(f"PE percentile progress {index + 1}/{len(codes)}")

    cache = pd.DataFrame(rows)
    cache.to_csv(cache_path, index=False, encoding="utf-8-sig")
    pct_map = dict(zip(cache["证券代码"].astype(str), cache["10年PE历史分位"]))
    candidates = candidates.copy()
    candidates["10年PE历史分位"] = candidates["ts_code"].astype(str).map(pct_map)
    return candidates


def add_scores(candidates: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    """按权重计算综合分。"""
    scored = candidates.copy()
    scored["股息率分位"] = scored["dv_ttm"].rank(pct=True) * 100
    scored["总市值分位"] = scored["总市值亿元"].rank(pct=True) * 100
    scored["ROE分位"] = scored["净资产收益率"].rank(pct=True) * 100
    scored["PE估值分"] = 100 - pd.to_numeric(scored["10年PE历史分位"], errors="coerce")
    gross_margin = pd.to_numeric(scored["销售毛利率"], errors="coerce").fillna(0)
    profit_yoy = pd.to_numeric(scored["净利润-同比增长"], errors="coerce").fillna(0)

    scored["综合分"] = (
        scored["PE估值分"] * args.weight_pe_value
        + scored["股息率分位"] * args.weight_dividend
        + scored["ROE分位"] * args.weight_roe
        + scored["总市值分位"] * args.weight_market_cap
        + gross_margin * args.weight_gross_margin
        + profit_yoy * args.weight_profit_yoy
    ).round(2)
    return scored


def parse_themes(args: argparse.Namespace) -> dict[str, tuple[str, set[str]]]:
    """解析内置和自定义主题。"""
    themes = {}
    if not args.no_built_in_themes:
        for name, pattern in DEFAULT_THEME_PATTERNS.items():
            themes[name] = (pattern, DEFAULT_THEME_INDUSTRIES.get(name, set()))
    for raw in args.theme:
        if "=" not in raw:
            raise ValueError(f"--theme格式应为 name=正则表达式: {raw}")
        name, pattern = raw.split("=", 1)
        themes[name.strip()] = (pattern.strip(), set())
    return themes


def select_outputs(scored: pd.DataFrame, args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """选择行业TopN并追加主题候选。"""
    ranked = scored.sort_values(["行业", "综合分", "总市值亿元"], ascending=[True, False, False]).copy()
    ranked["行业内排名"] = ranked.groupby("行业").cumcount() + 1
    industry_top = ranked.groupby("行业", as_index=False).head(args.top_n).copy()

    themes = parse_themes(args)
    if not themes:
        empty = ranked.iloc[0:0].copy()
        final = industry_top.sort_values("综合分", ascending=False, kind="mergesort")
        return final, empty, empty

    masks = []
    for _, (pattern, industries) in themes.items():
        name_hit = ranked["name"].astype(str).str.contains(pattern, regex=True, na=False)
        industry_hit = ranked["行业"].isin(industries) if industries else False
        masks.append(name_hit | industry_hit)
    theme_mask = masks[0]
    for mask in masks[1:]:
        theme_mask = theme_mask | mask

    theme_candidates = ranked[theme_mask].sort_values("综合分", ascending=False).copy()
    selected_codes = set(industry_top["ts_code"].astype(str))
    theme_append = theme_candidates[
        ~theme_candidates["ts_code"].astype(str).isin(selected_codes)
    ].copy()
    final = pd.concat([industry_top, theme_append], ignore_index=True)
    final = final.drop_duplicates(subset=["ts_code"], keep="first")
    final = final.sort_values("综合分", ascending=False, kind="mergesort")
    return final, theme_candidates, theme_append


def to_output_frame(data: pd.DataFrame) -> pd.DataFrame:
    """转换为用户可读的中文列CSV。"""
    data = data.copy()
    if "行业内排名" not in data.columns:
        data = data.sort_values(["行业", "综合分"], ascending=[True, False])
        data["行业内排名"] = data.groupby("行业").cumcount() + 1
    cols = [
        "行业", "行业内排名", "ts_code", "name", "dv_ttm", "总市值亿元", "PE",
        "10年PE历史分位", "pb", "净资产收益率", "净利润-同比增长", "销售毛利率",
        "综合分", "行业候选数", "market", "trade_date", "最新公告日期",
    ]
    rename = {
        "ts_code": "证券代码",
        "name": "证券名称",
        "dv_ttm": "股息率TTM",
        "pb": "PB",
        "净资产收益率": "ROE_2026Q1",
        "净利润-同比增长": "净利润同比_2026Q1",
        "销售毛利率": "销售毛利率_2026Q1",
        "market": "市场板块",
        "trade_date": "行情日期",
    }
    out = data[cols].rename(columns=rename).copy()
    numeric_cols = [
        "股息率TTM", "总市值亿元", "PE", "10年PE历史分位", "PB", "ROE_2026Q1",
        "净利润同比_2026Q1", "销售毛利率_2026Q1", "综合分",
    ]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").round(2)
    return out


def write_outputs(output_dir: Path, trade_date: str, scored: pd.DataFrame, final: pd.DataFrame, theme_candidates: pd.DataFrame, theme_append: pd.DataFrame) -> dict[str, Path]:
    """写出所有CSV产物。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    final_out = to_output_frame(final)
    all_out = to_output_frame(scored.sort_values("综合分", ascending=False))
    theme_out = to_output_frame(theme_candidates)
    append_out = to_output_frame(theme_append)

    main_path = output_dir / f"a_share_high_dividend_industry_top3_{trade_date}.csv"
    latest_path = output_dir / f"a_share_high_dividend_industry_top3_{trade_date}_latest.csv"
    all_path = output_dir / f"a_share_high_dividend_all_candidates_{trade_date}.csv"
    theme_path = output_dir / f"a_share_high_dividend_theme_candidates_{trade_date}.csv"
    append_path = output_dir / f"a_share_high_dividend_theme_append_{trade_date}.csv"

    final_out.to_csv(main_path, index=False, encoding="utf-8-sig")
    shutil.copy2(main_path, latest_path)
    all_out.to_csv(all_path, index=False, encoding="utf-8-sig")
    theme_out.to_csv(theme_path, index=False, encoding="utf-8-sig")
    append_out.to_csv(append_path, index=False, encoding="utf-8-sig")
    return {
        "main": main_path,
        "latest": latest_path,
        "all_candidates": all_path,
        "theme_candidates": theme_path,
        "theme_append": append_path,
    }


def validate_output(path: Path) -> pd.DataFrame:
    """校验主CSV。"""
    data = pd.read_csv(path, encoding="utf-8-sig")
    required = [
        "行业", "证券代码", "证券名称", "股息率TTM", "总市值亿元", "PE",
        "10年PE历史分位", "PB", "ROE_2026Q1", "净利润同比_2026Q1",
        "销售毛利率_2026Q1", "综合分",
    ]
    missing = [col for col in required if col not in data.columns]
    if missing:
        raise RuntimeError(f"输出缺少列: {missing}")
    if not data["综合分"].is_monotonic_decreasing:
        raise RuntimeError("输出未按综合分降序排列")
    return data


def run_screen(args: argparse.Namespace, project_root: Path) -> dict:
    """执行筛选并返回摘要数据。"""
    ak, pro = load_apis(project_root)
    output_dir = (project_root / args.output_dir).resolve()

    trade_date, filtered, basic = build_filtered_candidates(pro, ak, args)
    if filtered.empty:
        raise RuntimeError("硬过滤后没有候选股票")
    filtered["行业候选数"] = filtered.groupby("行业")["ts_code"].transform("count")
    filtered = add_pe_percentiles(pro, filtered, basic, trade_date, output_dir)
    filtered = filtered[filtered["10年PE历史分位"].notna()].copy()
    scored = add_scores(filtered, args)
    final, theme_candidates, theme_append = select_outputs(scored, args)
    paths = write_outputs(output_dir, trade_date, scored, final, theme_candidates, theme_append)
    out = validate_output(paths["main"])

    print(f"trade_date: {trade_date}")
    print(f"filtered_candidates: {len(filtered)}")
    print(f"final_rows: {len(out)}")
    print(f"industries: {out['行业'].nunique()}")
    print(f"theme_candidates: {len(theme_candidates)}")
    print(f"theme_append: {len(theme_append)}")
    for name, path in paths.items():
        print(f"{name}: {path}")
    print("\nTop 20:")
    print(
        out[
            ["行业", "证券代码", "证券名称", "股息率TTM", "10年PE历史分位", "ROE_2026Q1", "综合分"]
        ].head(20).to_string(index=False)
    )
    return {
        "trade_date": trade_date,
        "filtered_candidates": len(filtered),
        "final_rows": len(out),
        "industry_count": out["行业"].nunique(),
        "theme_candidates": len(theme_candidates),
        "theme_append": len(theme_append),
        "main_path": paths["main"],
        "latest_path": paths["latest"],
        "paths": paths,
        "top_rows": out.head(10),
    }


def main() -> None:
    """执行筛选并发送钉钉摘要。"""
    start_time = time.time()
    args = parse_args()
    project_root = find_project_root()

    try:
        summary = run_screen(args=args, project_root=project_root)
        summary["execution_time"] = time.time() - start_time
        summary["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not args.no_notify_dingding:
            message = build_success_message(summary)
            result = send_dingding_text(project_root, message)
            status = "sent" if result.get("sent") else "skipped"
            reason = result.get("reason", "ok")
            print(f"dingding_notify: {status} ({reason})")
    except Exception as exc:  # noqa: BLE001
        execution_time = time.time() - start_time
        if not args.no_notify_dingding:
            message = build_failure_message(exc, execution_time)
            result = send_dingding_text(project_root, message)
            status = "sent" if result.get("sent") else "skipped"
            reason = result.get("reason", "ok")
            print(f"dingding_notify: {status} ({reason})")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
