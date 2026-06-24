<p align="center">
  <img src="https://img.shields.io/badge/status-v0.1_Beta-FBBF24?style=flat-square" alt="Status" />
  <img src="https://img.shields.io/badge/license-MIT-22C55E?style=flat-square" alt="License" />
  <a href="https://github.com/orz0219/quant-lab">
    <img src="https://img.shields.io/badge/GitHub-orz0219/quant--lab-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub" />
  </a>
</p>

<h1 align="center">
  ⚡ QuantLab
</h1>

<p align="center">
  <b>面向 A 股的量化回测系统 · 让每一个交易想法都被数据认真验证</b><br/>
  <sub>纯本地运行 · 零配置启动 · 支持自然语言生成策略</sub>
</p>

---

## 一、是什么

QuantLab 是一个**可以在自己电脑上跑的 A 股量化回测工具**。

你有一个关于买卖股票的想法？输入「5 日均线上穿 20 日均线买入」—— QuantLab 会在历史 K 线上把这个策略跑一遍，告诉你：

- 过去几年胜率多少？
- 最大回撤多少？
- 每一笔交易具体是什么时候买/卖的？
- 如果拿 10 万本金开始，现在会变成多少？

### 核心功能

| 功能 | 说明 |
|------|------|
| **📊 交互式 K 线回测** | 选择股票 → 选策略 → 一键运行，几秒内得到完整回测报告 |
| **🔍 全市场选股扫描** | 用一个策略扫描全市场，找出最近出现买点信号的股票 |
| **📁 自选股票池** | 把看好的股票收集起来，按板块分类管理，强中选强 |
| **🔥 行业热力图** | 一眼看出哪些板块最近在走强，辅助选股判断 |
| **⚡ 策略库管理** | 预置多种经典策略，也可以自定义你的策略规则 |

所有数据和策略都保存在你的本地电脑上，**不上云、不联网**（除数据采集外）。

---

## 二、为什么

### 痛点：每个人都有「感觉能赚钱」的想法，但没人真正验证过

你有没有过这种感觉？

- 「5 日线上穿 20 日线，看起来总涨」
- 「最近这个板块很强，随便买一只应该都能赚」
- 「这个形态之前准过，再出现一次肯定没错」

**感觉会骗人，但数据不会。**

市面上的量化平台要么上手门槛太高（需要会编程、需要装数据库），要么把你的策略放在云端，缺乏安全感。

### QuantLab 的思路

**把「感觉能赚钱」这四个字，变成一个可回答的问题**：

1. **零配置启动** — 不需要装 MySQL/PostgreSQL/Docker。DuckDB 单文件即开即用
2. **自然语言友好** — 即使不会写策略代码，也能描述你的想法生成规则
3. **纯本地运行** — 你的策略、你的自选池、你的回测结果，都在你自己的电脑上
4. **漂亮但不花哨** — 玻璃态 UI，让数据可视化成为一种享受

---

## 三、怎么用

### 环境要求

- **Python 3.10+**
- **Node.js 18+**
- macOS / Linux / Windows 都支持

### 一键启动（macOS / Linux）

```bash
# 1. 克隆项目
git clone https://github.com/orz0219/quant-lab.git
cd quant-lab

# 2. 安装依赖
bash install.sh

# 3. 启动服务
bash start.sh
```

### Windows

```bat
双击 install.bat   # 安装依赖
双击 start.bat     # 启动服务
```

### 访问地址

启动后打开浏览器：

| 页面 | 地址 |
|------|------|
| 回测工作台 | http://localhost:3000/pages/backtest/ |
| 选股扫描 | http://localhost:3000/pages/screener/ |
| 自选股票池 | http://localhost:3000/pages/pool/ |
| 行业热力图 | http://localhost:3000/pages/forum/ |
| 策略库管理 | http://localhost:3000/pages/strategies/ |
| **产品蓝图** | http://localhost:3000/pages/roadmap/ |
| API 文档 | http://localhost:8000/docs |

### 关于数据

**第一次启动会引导你配置 Tushare Token**（用于自动更新 A 股行情数据）。

> 即使不配置 Tushare Token，系统自带示例数据，核心的 K 线回测和策略功能依然可用。

### 常用命令

```bash
bash start.sh          # 启动所有服务
bash start.sh stop     # 停止服务
bash start.sh restart  # 重启服务
bash start.sh status   # 查看服务运行状态
```

---

## 四、产品蓝图

QuantLab 目前是 v0.1 Beta 版本，正在快速迭代中。以下是正在推进的方向：

| 方向 | 说明 |
|------|------|
| **批量回测引擎** | 一个策略跑全市场，输出按板块/市值/波动率分组的胜率矩阵 |
| **策略适配度热力图** | 告诉你这个策略在哪些股票、哪些板块上表现最好 |
| **高级性能指标** | 夏普比率、卡玛比率、收益分布、滚动胜率等专业统计 |
| **图表深度可视化** | 回撤曲线、蒙特卡洛概率云、叠加面积图等 |
| **策略参数优化** | 网格搜索 + 贝叶斯优化，自动找到稳健的参数组合 |
| **AI 自然语言策略** | 输入中文描述，自动生成可回测的策略代码 |
| **实盘信号推送** | 每日开盘前，推送你关注的策略在自选股票中的信号 |

完整的路线图请访问应用内的「产品蓝图」页面。

---

## 五、免责声明

QuantLab 仅供**学习研究和策略回测演示**使用，不构成任何投资建议。

回测结果基于历史数据，**历史表现不代表未来收益**。实际交易请谨慎决策、做好风险管理。

---

<p align="center">
  <sub>Made with ❤️ for A-Share Quantitative Research</sub>
  <br/>
  <a href="https://github.com/orz0219/quant-lab">github.com/orz0219/quant-lab</a>
</p>
