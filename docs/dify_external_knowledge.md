# Dify External Knowledge Setup

推荐使用外部知识库 API 连接本项目，因为标书数据由爬虫持续更新，保存在本项目数据库中。Dify 查询知识时直接调用本项目后端，不需要每次上传 CSV。

## Dify 页面填写

在 Dify 知识库页面点击：

```text
外部知识库 API -> 添加外部知识库 API
```

建议填写：

```text
名称：北京广恒标书外部知识库
API Endpoint：http://宿主机IP:8010/external-knowledge
外部知识库 ID：a7497789-b9fb-4a21-9821-527291b92740
```

如果 Dify 和爬虫后端在同一台 Windows 主机上，但 Dify 在 Docker 里，不要填 `http://127.0.0.1:8010`。请填宿主机局域网 IP，例如：

```text
http://192.168.1.10:8010/external-knowledge
```

Dify 会自动在你填写的 API Endpoint 后追加 `/retrieval`，所以不要在界面里手动填 `/retrieval`。

鉴权方式：

```text
Authorization: Bearer tender-agent-local-token
```

其中 `tender-agent-local-token` 对应 `.env`：

```text
API_TOKEN=tender-agent-local-token
```

## 当前知识库 ID

你当前的 Dify 知识库地址：

```text
http://localhost/datasets/a7497789-b9fb-4a21-9821-527291b92740/documents
```

所以知识库 ID 是：

```text
a7497789-b9fb-4a21-9821-527291b92740
```

已写入 `.env`：

```text
DIFY_DATASET_ID=a7497789-b9fb-4a21-9821-527291b92740
```

## 推荐工作方式

1. 后端定时或手动爬取标书。
2. 标书入本项目数据库。
3. Dify Agent 需要回答问题时，通过外部知识库 API 调用 `/external-knowledge/retrieval`。
4. 后端根据 query 检索本地数据库，返回 Dify 需要的 records。
5. Qwen 基于 records 生成投标建议。

## 和 CSV 上传方式的区别

CSV 上传方式：

```text
爬虫 -> CSV -> 上传 Dify 知识库 -> Dify 内部索引
```

外部知识库方式：

```text
爬虫 -> 本地数据库 -> Dify 查询时调用后端 API
```

目前更推荐外部知识库方式，因为标书数据会持续更新，外部 API 更实时。

## 数据存储位置

爬虫抓到的数据会先写入 `.env` 中 `DATABASE_URL` 指向的数据库。

当前配置：

```text
DATABASE_URL=sqlite:///D:/tender_agent_data/tenders.db
```

也就是：

```text
D:\tender_agent_data\tenders.db
```

数据表是：

```text
tenders
```

如果调用 `/workflow/run` 且 `export_csv=true`，还会导出 CSV。默认导出目录是运行后端命令所在目录下的：

```text
data/exports/
```

外部知识库 API 不依赖 CSV，它直接从 SQLite 数据库检索 `tenders` 表。
