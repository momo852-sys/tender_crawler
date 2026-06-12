# Tender Agent Architecture

## 推荐架构

你现在描述的是两种可选形态：

1. Dify 直接作为用户入口。
   用户在 Dify 里发链接，Dify 自定义工具调用后端爬虫 API。
2. 自研仿豆包聊天界面作为用户入口。
   用户只打开你的聊天页面，后端调用爬虫和 Dify，Dify 退为内部 AI 服务。

更推荐第 2 种，尤其适合事务所内部系统：界面、权限、日志、文件下载、客户名称都由你自己控制，Dify 只负责模型编排和分析。

## 完整链路

```text
用户聊天界面
  -> FastAPI 后端 /workflow/run
  -> 爬虫采集公开招投标公告
  -> 按北京广恒会计师事务所资质画像打分筛选
  -> SQLite/PostgreSQL 入库
  -> 导出 CSV
  -> 可选上传 Dify 知识库
  -> 可选调用 Dify App API 生成投标建议
  -> 返回给聊天界面
```

## Dify 负责什么

- 维护提示词。
- 连接大模型。
- 承载知识库。
- 根据标书数据输出投标建议、风险点、匹配理由、下一步动作。

## Python 后端负责什么

- 接收用户输入的网站链接或关键词。
- 启动爬虫。
- 翻页抓取。
- 按事务所业务资质筛选。
- 写数据库。
- 导出 CSV。
- 调 Dify API 上传文件或发起智能体对话。

## 当前已实现

- `GET /health`
- `GET /tenders/search`
- `POST /crawl/run`
- `POST /workflow/run`
- 中国政府采购网公开招标/竞争性磋商列表配置
- 北京广恒会计师事务所关键词画像
- CSV 导出
- Dify 知识库上传客户端占位

## 当前还需要补

- 中国招标投标公共服务平台专用解析器。
- 湖南等省公共资源交易中心专用解析器。
- 前端仿豆包聊天界面。
- Dify App API 的最终提示词和返回格式。
- 生产环境数据库 PostgreSQL。
- 定时任务和任务状态表。

## 本地数据库注意事项

当前项目目录在百度网盘同步目录下，SQLite 可能因为同步锁、路径或文件系统行为出现 `disk I/O error`。本地调试时建议把 `.env` 里的数据库放到普通本地路径：

```text
DATABASE_URL=sqlite:///C:/tender_agent_data/tenders.db
```

上线后建议使用 PostgreSQL，并让爬虫后端、Dify、数据库处于同一内网或同一 Docker 网络。
