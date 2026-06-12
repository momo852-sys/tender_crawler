# Tender Crawler Agent

独立的标书/招投标信息采集服务，用于给 Dify 智能体提供结构化数据。

## 你要做什么

1. 明确采集来源：例如全国公共资源交易平台、各省交易中心、采购与招标网、企业采购平台等。
2. 确认合规边界：只采集公开页面，遵守目标网站 robots、访问频率、版权和账号条款。
3. 准备 Dify 侧工作流：通过 HTTP 工具调用本服务的检索接口，或者把采集结果同步到 Dify 知识库。
4. 如果要部署到服务器，准备数据库连接信息，建议 PostgreSQL。

## 我能继续帮你做什么

1. 根据你指定的网站，补对应的爬虫解析规则。
2. 把 SQLite 切换成 PostgreSQL/MySQL。
3. 增加定时任务、去重、附件下载、PDF 文本抽取。
4. 给 Dify 配 OpenAPI Schema，让智能体能直接调用查询接口。
5. 做成 Docker Compose，和 Dify 独立部署但可互相访问。

## 快速开始

```powershell
cd tender_crawler_agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m tender_crawler.db init
python -m tender_crawler.cli seed-sample
uvicorn tender_crawler.api:app --host 0.0.0.0 --port 8010
```

如果项目已迁移到 `D:\python_part\python\tender_crawler_agent`，启动命令改为：

```powershell
cd D:\python_part\python\tender_crawler_agent
.\.venv\Scripts\Activate.ps1
uvicorn tender_crawler.api:app --host 0.0.0.0 --port 8010
```

打开接口文档：

```text
http://127.0.0.1:8010/docs
```

## 常用命令

注意：如果项目目录位于百度网盘、OneDrive 等同步目录，不建议把 SQLite 数据库放在项目目录内。请在 `.env` 中把 `DATABASE_URL` 改到普通本地目录，例如：

```text
DATABASE_URL=sqlite:///C:/tender_agent_data/tenders.db
```

生产部署建议改用 PostgreSQL。

初始化数据库：

```powershell
python -m tender_crawler.db init
```

采集配置文件中的来源：

```powershell
python -m tender_crawler.cli crawl --config configs/sources.example.yaml
```

按北京广恒会计师事务所业务画像采集：

```powershell
python -m tender_crawler.cli crawl --config configs/sources.guangheng.yaml
```

查询最近标书：

```powershell
python -m tender_crawler.cli search --keyword "道路施工" --limit 10
```

启动 API：

```powershell
uvicorn tender_crawler.api:app --host 0.0.0.0 --port 8010
```

## 北京广恒会计师事务所采集建议

当前已内置一份业务画像配置：

```text
configs/sources.guangheng.yaml
```

它会优先匹配这些类型的公告：审计、财务审计、年报审计、竣工财务决算、预算绩效、绩效评价、内控评价、清产核资、会计师事务所、注册会计师、债券、发债、上市公司、证券服务、证券备案、IPO、并购重组。

默认启用中国政府采购网的中央/地方公开招标和竞争性磋商列表；中国招标投标公共服务平台、湖南省公共资源交易中心先保留为占位配置，等确认稳定列表页或接口后开启。

## Dify 对接方式

推荐方式：Dify 工作流 / Agent 使用 HTTP 工具调用本服务。

可导入的 OpenAPI 示例：

```text
docs/dify_openapi.yaml
```

可用接口：

- `GET /health`：健康检查。
- `GET /tenders/search?keyword=...&province=...&limit=10`：检索标书。
- `POST /crawl/run`：触发一次采集。
- `POST /workflow/run`：采集、筛选、导出 CSV，并可选上传 Dify 知识库。

如果 Dify 和本服务都在 Docker 中，注意不要在 Dify 里填 `127.0.0.1`，要填宿主机地址或同一 Docker 网络里的服务名。

如果你要做仿豆包聊天界面，推荐让自研前端调用 `/workflow/run`，然后由后端再调用 Dify。完整说明见：

```text
docs/architecture.md
docs/dify_agent_prompt.md
docs/dify_external_knowledge.md
```

## 数据表字段

核心表 `tenders`：

- `id`
- `source`
- `source_url`
- `title`
- `summary`
- `province`
- `city`
- `buyer`
- `agency`
- `budget`
- `publish_date`
- `deadline`
- `category`
- `raw_text`
- `created_at`
- `updated_at`

## 下一步

把你要爬取的 2-3 个目标网站链接发给我，我会继续补具体适配器。最好包含列表页和详情页各一个示例链接。
