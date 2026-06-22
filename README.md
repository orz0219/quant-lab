<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Vue-3.4-4FC08D?style=flat-square&logo=vue.js&logoColor=white" alt="Vue" />
  <img src="https://img.shields.io/badge/Vite-5.4-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/DuckDB-1.0-FFF000?style=flat-square&logo=duckdb&logoColor=black" alt="DuckDB" />
  <img src="https://img.shields.io/badge/ECharts-5.4-AA344D?style=flat-square&logo=apacheecharts&logoColor=white" alt="ECharts" />
  <br/>
  <img src="https://img.shields.io/badge/status-beta-8B5CF6?style=flat-square" alt="Status: Beta" />
  <img src="https://img.shields.io/badge/license-MIT-22C55E?style=flat-square" alt="License" />
</p>

<h1 align="center">
  ⚡ QuantLab
</h1>

<p align="center">
  <b>AI 驱动的量化回测系统 · 用自然语言描述策略，一键验证</b><br/>
  <sub>面向 A 股 · 纯本地运行 · 无需数据库</sub>
</p>

<br/>

---

## ✨ 亮点速览

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   ⚡ 自然语言生成策略 → 输入"5日均线上穿20日均线买入"     │
│   📊 交互式 K 线回测  → 可视化交易信号与权益曲线         │
│   🔍 全市场选股扫描  → 按策略 Pick 买点信号              │
│   🛢️ 零配置数据库     → DuckDB 单文件，启动即用          │
│   🌐 多页面架构       → 回测 / 选股 / 股票池 / 行业热力图 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

<br/>

## 🧭 页面一览

### 1. 回测工作台 <sub>`/pages/backtest/`</sub>

选择股票 → 选策略 → 点运行，几秒内得到完整的回测报告。支持：

- **K 线图** 含 MA 均线、成交量、买卖信号标记
- **权益曲线** 可视化资金变化
- **交易明细表** 每笔交易的买入/卖出时间与盈亏
- **AI 策略生成** 描述你的想法，自动生成回测代码
- **指标设置抽屉** 自定义 K 线颜色、均线周期

### 2. 选股扫描器 <sub>`/pages/screener/`</sub>

- 选择一个策略，扫描全市场股票
- 找出最近一周内出现 **买点信号** 的标的
- 一键 **加入自选池**

### 3. 股票池 <sub>`/pages/pool/`</sub>

- 管理自选股票
- 按行业板块归类，支持一键跳转回测
- **强中选强**，锁定主线

### 4. 行业热力图 <sub>`/pages/forum/`</sub>

- 各行业板块的 **RS（相对强度）时序热力图**
- RS = 板块过去 20 日累积涨幅 / 全市场涨幅
- 按最后一天 RS 降序排列，一眼看出强势板块轮动

<br/>

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    🌐 前端 (Port 3000)                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Vite 5 + Vue 3 + vue-router                      │  │
│  │  多页面 MPA：backtest / screener / pool / forum    │  │
│  │  ECharts 5 图表 · lightweight-charts K线          │  │
│  └──────────┬────────────────────────────────────────┘  │
│             │  /api/* 代理                              │
├─────────────┼───────────────────────────────────────────┤
│             ▼  http://localhost:8000                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │  FastAPI + Uvicorn                                │  │
│  │  RESTful API /api/v1/*                            │  │
│  └──────────┬────────────────────────────────────────┘  │
│             │                                            │
├─────────────┼───────────────────────────────────────────┤
│             ▼                                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │  DuckDB (单文件数据库)                              │  │
│  │  📁 backend/data/db/stock.duckdb                   │  │
│  │  表: daily / weekly / stock_info / user_strategies  │  │
│  │      sector_rs_cache / indicator_settings           │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  数据源: Tushare Pro (可选)                               │
│  回测引擎: 内置纯 Python · 不依赖 backtrader              │
│  AI 策略生成: 内置规则引擎 (可替换为 LLM)                 │
└─────────────────────────────────────────────────────────┘
```

<br/>

## 🚀 快速开始

### 前置条件

- **Python 3.10+**
- **Node.js 18+**
- **curl**（macOS 自带 / Linux 需安装）

### macOS / Linux / Git Bash

```bash
# 1. 一键安装所有依赖
bash install.sh

# 2. 启动服务（后端 + 前端 + 数据更新）
bash start.sh

# 其他命令
bash start.sh stop       # 停止服务
bash start.sh restart    # 重启服务
bash start.sh status     # 查看服务状态
```

### Windows PowerShell

```bat
双击 install.bat    # 安装依赖
双击 start.bat      # 启动服务
双击 stop.bat       # 停止服务
```

> 第一次启动会引导你配置 Tushare Token（数据采集用）。即使不配置，回测功能依然可用（使用示例数据）。

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端界面 | [http://localhost:3000](http://localhost:3000) |
| 后端 API | [http://localhost:8000](http://localhost:8000) |
| API 文档 | [http://localhost:8000/docs](http://localhost:8000/docs) |

<br/>

## 📡 API 概览

| 路径 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/v1/stocks` | GET | 股票列表搜索 |
| `/api/v1/stocks/{ts_code}/kline` | GET | K 线数据 |
| `/api/v1/stocks/by_industry` | GET | 按行业分组股票 |
| `/api/v1/backtest` | POST | 执行回测 |
| `/api/v1/strategy/generate` | POST | AI 策略生成 |
| `/api/v1/strategies` | GET/POST | 用户策略 CRUD |
| `/api/v1/strategies/{id}` | GET/PUT/DELETE | 策略详情 |
| `/api/v1/sectors/rs` | GET | 板块 RS 热力图数据 |
| `/api/v1/settings/indicators` | GET/PUT | 指标显示设置 |

<br/>

## 📂 项目结构

```
tvp/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/            # RESTful 接口
│   │   ├── core/
│   │   │   ├── config.py      # 全局配置
│   │   │   ├── database.py    # DuckDB 连接池
│   │   │   └── models.py      # 数据表 DDL
│   │   ├── data/
│   │   │   ├── pipeline/      # 数据采集流水线
│   │   │   └── sources/       # 数据源 (Tushare)
│   │   ├── exporter/          # 导出 (Excel/图片)
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── services/          # 业务逻辑
│   │   │   ├── backtest_service.py   # 回测引擎
│   │   │   ├── stock_service.py      # 股票查询
│   │   │   └── strategy_service.py   # AI 策略生成
│   │   └── strategy/          # 策略模块
│   ├── scripts/               # 命令行脚本
│   ├── data/db/               # DuckDB 数据库文件
│   └── .venv/                 # Python 虚拟环境
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── backtest/      # 回测工作台
│   │   │   ├── screener/      # 选股扫描器
│   │   │   ├── pool/          # 股票池
│   │   │   ├── strategies/    # 策略管理
│   │   │   └── forum/         # 行业热力图
│   │   ├── components/        # 通用组件
│   │   ├── hooks/             # 组合式函数
│   │   ├── utils/             # 工具函数
│   │   └── assets/            # 样式
│   └── public/                # 静态资源
├── install.sh / install.ps1   # 环境安装
├── start.sh   / start.ps1     # 启动脚本
└── stop.sh    / stop.ps1      # 停止脚本
```

<br/>

## 📊 数据流水线

```
Tushare Pro (可选)
      │
      ▼
  fetch_daily_data.py    ── 日线数据采集
      │
      ▼
  weekly_builder.py      ── 周线数据聚合
      │
      ▼
  calc_sector_rs.py      ── 板块 RS 计算
      │
      ▼
  DuckDB (stock.duckdb)  ── 本地查询
```

> 数据采集为可选功能。系统内置了示例数据，即使不配置 Tushare Token，K 线回测和策略功能依然可用。

<br/>

## 🧪 本地开发

```bash
# 后端热重载
cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端开发服务器
cd frontend && npx vite --host 0.0.0.0 --port 3000
```

<br/>

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **前端框架** | Vue 3 + Vite 5 (MPA 多页面) |
| **图表** | ECharts 5 + lightweight-charts |
| **后端框架** | FastAPI + Uvicorn |
| **数据库** | DuckDB (嵌入式 OLAP) |
| **数据源** | Tushare Pro |
| **样式** | 极简玻璃态 (Glassmorphism) |
| **AI 策略** | 内置规则引擎 (可接 LLM) |
| **启动脚本** | Bash + PowerShell 双平台 |

<br/>

---

<p align="center">
  <sub>Made with ❤️ for A-Share Quantitative Research · 仅供研究演示</sub>
  <br/>
  <sub>© 2026 QuantLab</sub>
</p>
