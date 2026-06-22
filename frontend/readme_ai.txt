# QuantLab 前端项目规范 — AI 重构指南

## 项目架构

本项目是基于 **Vue3 + Vite** 的多页面应用。

```
frontend/
├── package.json              # 依赖: vue, vue-router, echarts, vite, @vitejs/plugin-vue
├── vite.config.js            # Vite 多页面配置 + /api 代理到 localhost:8000
├── public/                   # 静态资源（sandbox 沙箱文件）
│   ├── sandbox.html          # iframe 安全沙箱容器
│   └── sandbox-worker.js     # Web Worker 策略执行器
└── src/
    ├── assets/
    │   └── common.css        # 全局公共样式（CSS 变量、按钮、布局、组件样式）
    ├── utils/                # 纯函数工具（无 Vue 依赖，ES module）
    │   ├── format.js         # fmtNum / fmtPct / fmtPctOnly
    │   ├── date.js           # toDateInt / todayISO / parseTsCode / parseDate
    │   ├── math.js           # simpleMA / sharpeRatio / resample（日K→周K）
    │   ├── watchlist.js      # 自选池 getAll / add / remove / has（localStorage）
    │   └── request.js        # API 封装: fetchStocks / fetchKline / strategyApi
    ├── hooks/                # Vue3 Composition API 组合式函数
    │   ├── useModal.js       # 弹窗 visible / open / close
    │   ├── useStopSettings.js # 止损止盈设置持久化（localStorage）
    │   ├── useStrategyCache.js # 策略选择缓存
    │   ├── useScreenerCache.js # 选股结果缓存
    │   └── useKlineChart.js  # lightweight-charts 图表生命周期管理
    ├── components/           # 公共 Vue 组件
    │   ├── Nav.vue           # 顶部导航栏（props: active）
    │   ├── Modal.vue         # 通用弹窗（props: visible, title; slots: default）
    │   ├── EmptyState.vue    # 空状态占位（props: icon, title, desc）
    │   ├── Pagination.vue    # 分页（props: current, total, pageSize; emit: change）
    │   ├── KLineInfo.vue     # K 线信息面板（props: data, prevClose, maValues）
    │   ├── IndicatorDrawer.vue # 指标设置抽屉（v-model 双向绑定）
    │   ├── StopSettings.vue  # 止损止盈面板（props: settings; emit: update）
    │   ├── StockCombobox.vue # 股票代码搜索自动补全（v-model + @select）
    │   ├── MetricCards.vue   # 6个回测指标卡片（props: metric）
    │   ├── TradeTable.vue    # 交易明细表格（props: trades）
    │   └── ScreenerItem.vue  # 选股结果卡片（props: stock）
    └── pages/                # 5个独立页面，每个含 index.html + main.js + App.vue
        ├── backtest/         # 回测主页面 /pages/backtest/
        ├── strategies/       # 策略库 /pages/strategies/
        ├── screener/         # 选股扫描 /pages/screener/
        ├── pool/             # 股票池分析 /pages/pool/
        └── forum/            # 论坛讨论 /pages/forum/
```

## 关键技术选择

| 技术 | 选型 | 原因 |
|------|------|------|
| UI 框架 | Vue 3 (Composition API + `<script setup>`) | 轻量、高性能、多页面友好 |
| 构建工具 | Vite 5 | 极速 HMR、多页面入口、内置代理 |
| 图表库 | lightweight-charts (K线) + ECharts 5 (曲线) | K线用轻量级、曲线用 ECharts |
| K线周期 | 前端聚合（日K→周K） | 减少后端请求，`math.js` 的 `resample()` |
| 样式 | 全局 CSS 变量 + scoped 组件样式 | 统一主题色、组件隔离 |
| API 代理 | Vite proxy | 开发环境自动代理 `/api` → 后端 |
| 沙箱策略 | iframe + Web Worker | 安全执行用户代码，不污染主进程 |

## 编码规范

### 1. 组件规则
- 所有组件使用 `<script setup>` 语法
- 公共 DOM 必须抽为 `components/` 下的独立组件
- 组件通过 `props` 接收数据，通过 `emit` 发送事件
- 全局通用组件在各自页面 `main.js` 中注册
- 禁止使用唯一 `id` 做通用样式/事件，全部使用 `class`

### 2. 样式规则
- 全局公共样式只写在 `src/assets/common.css`
- 每个组件内部样式添加 `<style scoped>`
- CSS 变量定义在 `:root` 中（主题色、渐变、面板样式）
- 差异化内容通过 `props` 传递给公共组件，不复制组件

### 3. Hook 规则
- 复用交互逻辑全部抽为 `hooks/` 下的组合式函数
- 页面仅导入调用 hooks，不重复写逻辑
- localStorage 缓存逻辑放在 hook 内封装

### 4. Utils 规则
- 纯函数放在 `utils/`（无 Vue 依赖）
- 使用 ES module 的 `export` / `import`
- API 请求统一在 `request.js` 中封装

### 5. 页面规则
- 每个页面位于 `pages/` 下的独立子目录
- 包含 `index.html`（Vite 入口）+ `main.js`（挂载点）+ `App.vue`（页面组件）
- `index.html` 头部加载独立 CDN 资源（lightweight-charts, echarts）
- 页面内只保留当前页面独有的 DOM、独有样式、独有业务逻辑
- 公共内容一律从 `components/` 引入

### 6. 启动方式
```bash
cd frontend
npm install           # 首次安装依赖
npx vite              # 开发服务器（端口3000，自动代理 /api 到 localhost:8000）
npx vite build        # 生产构建，输出到 dist/
npx vite preview      # 预览构建结果
```

Vite 已配置 `vite.config.js`：
- 多页面入口（5个页面）
- `/api` 路径代理到 `http://localhost:8000`
- `@` 别名指向 `src/`

### 7. 目录变更规范
- **新增页面**：在 `src/pages/` 下创建目录，包含 index.html + main.js + App.vue
- **新增组件**：在 `src/components/` 下创建 `.vue` 文件
- **新增工具**：在 `src/utils/` 下创建 `.js` 文件
- **新增 Hook**：在 `src/hooks/` 下创建 `.js` 文件
- **公共样式**：追加到 `src/assets/common.css`
- **非 Vue 静态资源**：放入 `public/` 目录

### 8. 旧代码清理说明
本项目由原生 HTML/CSS/JS 重构为 Vue3。以下旧文件已不再使用（可安全删除）：
- `frontend/*.html`（除 Vite 配置和 public/ 外）
- `frontend/*.js`（除 vite.config.js 和 src/ 内文件外）
- `frontend/styles.css`
- `frontend/server.js`

所有功能已迁移到 `frontend/src/` 目录下的 Vue3 架构中。
