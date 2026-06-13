# 审计标书筛选助手

面向北京广恒会计师事务所的招投标公告采集与智能筛选服务。项目通过 Python 爬虫采集公开招标公告，将审计、财务审计、预算绩效评价、会计师事务所等相关项目结构化入库，并通过 FastAPI 向 Dify 提供外部知识库检索接口，让 Dify Agent 可以基于本地实时标书数据完成批量筛选和单条标书研判。

## 项目定位

本项目不是直接运行在 Dify 里的 Python 脚本，而是一个独立后端服务：

```text
公开招投标网站
    -> Python 爬虫采集
    -> 关键词与资质规则筛选
    -> SQLite 数据库存储
    -> FastAPI 检索接口
    -> Dify 外部知识库 / Agent
    -> 输出投标机会清单或单条研判结果
```

Dify 负责对话、提示词编排和大模型推理；本项目负责数据采集、数据存储、结构化检索和外部知识库接口。

## 核心功能

- 采集中国政府采购网公开招标、竞争性磋商等公告列表。
- 按北京广恒会计师事务所业务画像筛选审计类、财务类、会计师事务所类机会。
- 提取并保存公告标题、链接、地区、采购人、代理机构、预算、发布时间、截止时间、摘要、匹配关键词和相关度评分。
- 使用 SQLite 持久化存储标书数据，支持后续切换 PostgreSQL / MySQL。
- 提供 REST API，支持健康检查、标书检索、触发爬取、工作流执行。
- 实现 Dify 外部知识库接口，Dify 可实时检索本地数据库中的标书数据。
- 支持导出 CSV，用于人工复核、归档或后续知识库导入。

## 技术栈

- Python 3.8+
- FastAPI
- Uvicorn
- SQLAlchemy
- SQLite
- BeautifulSoup4
- HTTPX
- PyYAML
- Pydantic / Pydantic Settings
- Dify External Knowledge API
- Qwen / 其他 Dify 支持的大模型

## 目录结构

```text
tender_crawler_agent/
├── configs/
│   ├── sources.example.yaml        # 示例采集配置
│   └── sources.guangheng.yaml      # 北京广恒会计师事务所业务画像配置
├── docs/
│   ├── architecture.md             # 架构说明
│   ├── dify_agent_prompt.md        # Dify Agent 提示词
│   ├── dify_external_knowledge.md  # Dify 外部知识库配置说明
│   ├── dify_openapi.yaml           # Dify 自定义工具 OpenAPI 示例
│   └── dify_seed_knowledge.md      # 知识库初始化说明
├── tender_crawler/
│   ├── api.py                      # FastAPI 接口
│   ├── cli.py                      # 命令行入口
│   ├── crawler.py                  # 爬虫与页面解析
│   ├── db.py                       # 数据库初始化与会话
│   ├── exporter.py                 # CSV 导出
│   ├── models.py                   # SQLAlchemy 数据模型
│   ├── repository.py               # 数据写入与查询
│   ├── schemas.py                  # Pydantic 请求/响应模型
│   ├── service.py                  # 爬取与工作流编排
│   └── settings.py                 # 环境变量配置
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## 环境准备

建议将项目放在普通本地目录，不要放在百度网盘、OneDrive 等同步目录中。当前推荐路径示例：

```powershell
D:\python_part\python\tender_crawler_agent
```

创建虚拟环境并安装依赖：

```powershell
cd D:\python_part\python\tender_crawler_agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

复制环境变量模板：

```powershell
copy .env.example .env
```

推荐 `.env` 配置：

```env
DATABASE_URL=sqlite:///D:/tender_agent_data/tenders.db
REQUEST_TIMEOUT_SECONDS=20
REQUEST_DELAY_SECONDS=1.5
USER_AGENT=TenderCrawlerAgent/0.1 (+contact@example.com)
API_TOKEN=tender-agent-local-token
DIFY_BASE_URL=http://127.0.0.1
DIFY_API_KEY=
DIFY_DATASET_ID=a7497789-b9fb-4a21-9821-527291b92740
DIFY_APP_API_KEY=
DIFY_APP_ENDPOINT=/v1/chat-messages
```

说明：

- `DATABASE_URL` 是爬取后的标书数据库位置。建议放到 `D:/tender_agent_data/tenders.db`。
- `API_TOKEN` 是 Dify 调用本服务时使用的接口密钥。
- `DIFY_DATASET_ID` 是 Dify 外部知识库 ID，需要和 Dify 中配置的一致。
- `.env` 包含本地密钥和环境配置，不要提交到 GitHub。

## 初始化数据库

启动 API 时会自动初始化数据库。也可以先插入一条示例数据验证链路：

```powershell
python -m tender_crawler.cli seed-sample
```

## 爬取标书数据

按北京广恒会计师事务所画像爬取：

```powershell
python -m tender_crawler.cli crawl --config configs/sources.guangheng.yaml
```

运行后，数据会写入 `.env` 中 `DATABASE_URL` 指向的 SQLite 数据库，例如：

```text
D:\tender_agent_data\tenders.db
```

当前配置默认启用中国政府采购网以下栏目：

- 中央公告 / 公开招标
- 地方公告 / 公开招标
- 中央公告 / 竞争性磋商
- 地方公告 / 竞争性磋商

中国招标投标公共服务平台、湖南省公共资源交易中心在配置中保留为占位来源，待确认稳定列表页或接口后可继续扩展。

## 本地查询

按关键词查询：

```powershell
python -m tender_crawler.cli search --keyword 审计 --limit 10
```

按最低相关度筛选：

```powershell
python -m tender_crawler.cli search --keyword 财务 --limit 20 --min-relevance-score 2
```

## 启动 API 服务

```powershell
uvicorn tender_crawler.api:app --host 0.0.0.0 --port 8010
```

服务启动后保持运行是正常现象。接口文档地址：

```text
http://127.0.0.1:8010/docs
```

健康检查：

```text
GET http://127.0.0.1:8010/health
```

主要接口：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/health` | 服务健康检查 |
| `GET` | `/tenders/search` | 查询数据库中的标书 |
| `POST` | `/crawl/run` | 触发一次爬虫采集 |
| `POST` | `/workflow/run` | 爬取、筛选、导出 CSV 的完整流程 |
| `POST` | `/external-knowledge/retrieval` | Dify 外部知识库检索接口 |
| `POST` | `/retrieval` | 兼容 Dify 自动拼接路径的检索接口 |

需要鉴权的接口请在请求头中加入：

```text
Authorization: Bearer tender-agent-local-token
```

## CSV 导出

调用 `/workflow/run` 且设置 `export_csv=true` 时，会导出 CSV 文件：

```text
data/exports/tenders_YYYYMMDD_HHMMSS.csv
```

CSV 字段包括：

- `id`
- `title`
- `source`
- `source_url`
- `province`
- `city`
- `buyer`
- `agency`
- `budget`
- `publish_date`
- `deadline`
- `category`
- `matched_keywords`
- `relevance_score`
- `summary`

## Dify 外部知识库配置

推荐使用 Dify 外部知识库方式接入，不需要把 CSV 手动上传到 Dify。Dify 在对话中检索知识库时，会实时调用本服务查询 SQLite 数据库。

在 Dify 中添加外部知识库时填写：

```text
名称：北京广恒标书外部知识库
API Endpoint：http://你的电脑IP:8010/external-knowledge
API Key：tender-agent-local-token
External Knowledge ID：a7497789-b9fb-4a21-9821-527291b92740
Top K：5
Score threshold：0 或关闭阈值过滤
```

如果 Dify 和本服务在同一台 Windows 主机上，但 Dify 运行在 Docker 中，不要填 `127.0.0.1`。应填写宿主机局域网 IP，例如：

```text
http://192.168.31.129:8010/external-knowledge
```

Dify 会自动请求：

```text
POST /external-knowledge/retrieval
```

本服务也提供 `/retrieval` 作为兼容路径。

## Dify Agent 功能设计

Agent 建议包含两个场景：

### 场景 A：批量采集合规标书

当用户提供招标网站、公告列表页，或询问“最近有哪些审计类标书机会”时触发。

Agent 应优先检索外部知识库，围绕审计、财务审计、财务决算、预算绩效评价、会计师事务所、注册会计师、证券服务备案等关键词筛选项目，并输出合规标书汇总清单。

### 场景 B：单条标书资质研判

当用户提供单条公告链接或完整公告文本时触发。

Agent 应结合北京广恒会计师事务所资质，对硬性门槛、预算合理性、时间安排、经验匹配度和中标概率进行分析，给出是否建议投标及下一步行动。

提示词示例见：

```text
docs/dify_agent_prompt.md
```

## 当前业务画像

项目内置的北京广恒会计师事务所画像：

- 具有证券业务备案资格
- 2024 年业务收入约 2800 万元
- 注册会计师约 35 人
- 擅长国企审计、年报审计、经济责任审计
- 近三年无重大违法记录

重点匹配关键词：

```text
审计、财务审计、年报审计、决算审计、竣工财务决算、预算绩效、
绩效评价、内部控制、清产核资、资产清查、会计师事务所、注册会计师、
财务咨询、税务咨询、专项债、债券、上市公司、证券服务、证券备案、IPO
```

