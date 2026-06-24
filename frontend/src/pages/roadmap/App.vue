<template>
  <div>
    <div class="bg-aurora"></div>
    <div class="bg-grid"></div>
    <Nav active="roadmap" />

    <main class="workspace-single">
      <!-- Hero -->
      <section class="headline center">
        <span class="pill"><span class="pill-dot"></span>Product Roadmap · 2026 → 2027</span>
        <h1 class="head-title"><span class="grad-text">从回测到实战</span><br/>一个量化系统的成长路径</h1>
        <p class="head-sub">
          今天的 QuantLab 是一个优雅的回测引擎。<br/>
          而这只是起点——以下是我们正在构建的，面向 A 股投资者的完整量化平台。
        </p>

        <div class="milestone-row">
          <div v-for="(m, i) in milestones" :key="i" class="milestone">
            <div class="milestone-time">{{ m.time }}</div>
            <div class="milestone-title">{{ m.title }}</div>
          </div>
        </div>
      </section>

      <!-- 三大阶段 -->
      <section v-for="(phase, pi) in phases" :key="pi" class="phase-wrap">
        <div class="phase-head">
          <div class="phase-label">PHASE {{ pi + 1 }}</div>
          <h2 class="phase-title">
            <span class="phase-emoji">{{ phase.emoji }}</span>
            <span>{{ phase.title }}</span>
          </h2>
          <p class="phase-sub">{{ phase.subtitle }}</p>
          <div class="phase-timing">{{ phase.timing }}</div>
        </div>

        <div class="feature-grid">
          <article v-for="(f, i) in phase.features" :key="i" class="glass feature-card">
            <div class="feature-num">{{ String(i + 1).padStart(2, '0') }}</div>
            <div class="feature-icon">{{ f.icon }}</div>
            <h3 class="feature-title">{{ f.title }}</h3>
            <p class="feature-desc">{{ f.desc }}</p>
            <div v-if="f.highlights" class="feature-highlights">
              <span v-for="h in f.highlights" :key="h" class="highlight-chip">{{ h }}</span>
            </div>
            <div class="feature-meta">
              <span class="feature-status">{{ f.status }}</span>
              <span class="feature-value">{{ f.value }}</span>
            </div>
          </article>
        </div>
      </section>

      <!-- 技术栈展望 -->
      <section class="phase-wrap">
        <div class="phase-head center">
          <div class="phase-label">TECHNOLOGY STACK</div>
          <h2 class="phase-title"><span class="phase-emoji">🏗️</span><span>我们正在用什么构建</span></h2>
          <p class="phase-sub">从轻量 Demo 到生产级平台——技术栈同步演进</p>
        </div>

        <div class="tech-grid">
          <div v-for="t in techStack" :key="t.name" class="glass tech-card">
            <div class="tech-name">{{ t.name }}</div>
            <div class="tech-desc">{{ t.desc }}</div>
            <div class="tech-chips">
              <span v-for="c in t.chips" :key="c" class="tech-chip">{{ c }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 愿景 -->
      <section class="glass vision-card">
        <div class="vision-quote">"</div>
        <h2 class="vision-title"><span class="grad-text">愿景</span> · 让每一个交易者，都拥有一支量化团队</h2>
        <p class="vision-text">
          在 QuantLab，我们相信好的投资决策应该被数据支撑，而不是被情绪驱动。
          我们正在把过去只有机构才能拥有的回测能力、策略引擎和数据分析能力，
          变成每一个 A 股投资者打开浏览器就能使用的工具。<br/><br/>
          <span class="grad-text-2">这是一个从「回测 Demo」到「交易操作系统」的旅程。</span><br/>
          欢迎和我们一起，见证它的成长。
        </p>
        <div class="vision-meta">
          <div class="vision-meta-item">
            <div class="v-num grad-text">3</div>
            <div class="v-label">阶段</div>
          </div>
          <div class="vision-meta-item">
            <div class="v-num grad-text">12+</div>
            <div class="v-label">核心功能</div>
          </div>
          <div class="vision-meta-item">
            <div class="v-num grad-text">2027</div>
            <div class="v-label">完整路线图</div>
          </div>
        </div>
      </section>

      <div class="foot-note">
        QuantLab · 面向 A 股的量化回测与交易平台 · 发展蓝图持续更新中
      </div>
    </main>
  </div>
</template>

<script setup>
import Nav from '@/components/Nav.vue'

const milestones = [
  { time: '2026 Q3', title: '回测引擎 V1' },
  { time: '2026 Q4', title: '策略工厂 + 批量回测' },
  { time: '2027 Q1', title: '实盘信号推送' },
  { time: '2027 Q2+', title: '交易操作系统' },
]

const phases = [
  {
    emoji: '🧪',
    title: '阶段一：让回测「认真起来」',
    subtitle: '从单策略单股票的定性验证 → 多策略多维度的定量分析',
    timing: '时间线：2026 Q3',
    features: [
      {
        num: '01',
        icon: '⚡',
        title: '批量回测引擎',
        desc: '一套策略不再只回测一只股票。自动批量跑过全市场或指定板块，输出胜率、盈亏比、收益分布的全景报告。',
        highlights: ['全市场扫描', '按板块/市值分组', '并行加速'],
        status: '开发中',
        value: '↑ 验证效率提升 50×',
      },
      {
        num: '02',
        icon: '📊',
        title: '策略适配度热力图',
        desc: '用热力图一眼看出：哪些板块、哪类市值的股票，最适配当前策略。用数据而不是直觉，回答「这个策略到底该买什么」。',
        highlights: ['板块热力图', '市值-胜率矩阵', '策略推荐'],
        status: '设计完成',
        value: '↓ 选股决策成本 80%',
      },
      {
        num: '03',
        icon: '🎯',
        title: '高级性能指标',
        desc: '夏普比率、最大回撤、卡玛比率、索提诺比率、收益分布直方图、滚动胜率曲线——给专业的人，看专业的数。',
        highlights: ['Sharpe / Sortino', '回撤水下图', '滚动胜率'],
        status: '开发中',
        value: '✓ 机构级指标',
      },
      {
        num: '04',
        icon: '🎨',
        title: '图表深度可视化',
        desc: '每一个策略跑出来的结果，不再只是一张表。叠加面积图、箱线图、蒙特卡洛概率云——数据讲故事，图表做翻译。',
        highlights: ['ECharts 深度应用', '交互式 K线', '概率云模拟'],
        status: '规划中',
        value: '📈 视觉说服力',
      },
    ],
  },
  {
    emoji: '🏭',
    title: '阶段二：让策略「自己生长」',
    subtitle: '从人工写策略 → 策略工厂自动生成、自动优化、自动筛选',
    timing: '时间线：2026 Q4',
    features: [
      {
        num: '05',
        icon: '🤖',
        title: '策略工厂 · 参数自动优化',
        desc: '输入你的策略骨架，系统在合理范围内做网格搜索 + 贝叶斯优化，输出稳健的参数组合，避免过拟合。',
        highlights: ['网格搜索', '贝叶斯优化', '稳健性分析'],
        status: '规划中',
        value: '↓ 参数调优时间 90%',
      },
      {
        num: '06',
        icon: '📚',
        title: '内置策略库 · 开箱即用',
        desc: '双均线、布林带、RSI、动量反转、海龟法则、PinBar……经典策略预置入库，选好股票一键跑，不用写一行代码。',
        highlights: ['10+ 经典策略', '零代码运行', '一键对比'],
        status: '开发中',
        value: '↑ 上手效率 10×',
      },
      {
        num: '07',
        icon: '💡',
        title: 'AI 自然语言策略',
        desc: '用中文描述你的交易想法——「当 5 日均线穿越 20 日均线且成交量放大 1.5 倍时买入」——系统自动为你生成回测代码。当前版本提供结构化提示词生成器，配合外部 LLM 使用；未来将内置 AI 推理引擎，一句话直达可执行策略。',
        highlights: ['提示词生成器', '自然语言 → 代码', 'LLM 可替换', '可解释'],
        status: '规划中',
        value: '💬 一句话策略',
      },
      {
        num: '08',
        icon: '🗂️',
        title: '策略组合 · 组合优化器',
        desc: '把多个策略按资金权重、相关性、波动率做组合优化。单策略不稳，组合稳——给每一个账户找到合适的策略篮子。',
        highlights: ['均值-方差', '风险平价', '相关性矩阵'],
        status: '规划中',
        value: '🎯 组合优化',
      },
    ],
  },
  {
    emoji: '🚀',
    title: '阶段三：从回测，走向实盘交易',
    subtitle: '让 QuantLab 从「事后复盘工具」升级为「事前决策 + 事中执行 + 事后归因」的交易操作系统',
    timing: '时间线：2027 Q1 及以后',
    features: [
      {
        num: '09',
        icon: '🔔',
        title: '实时信号推送',
        desc: '自选股 + 启用策略 → 每天收盘后自动扫描。第二天开盘前，你收到一份清晰的「今日信号清单」。',
        highlights: ['邮件 / 站内信', '可配置阈值', '开盘前推送'],
        status: '规划中',
        value: '⏰ 开盘前决策',
      },
      {
        num: '10',
        icon: '💼',
        title: '多账户 / 多策略资金管理',
        desc: '支持不同账户配置不同策略组合、不同风险偏好。系统统一监控各账户的盈亏、信号、仓位——你的个人对冲基金操作台。',
        highlights: ['多账户隔离', '仓位调度', '风险矩阵'],
        status: '规划中',
        value: '🏢 个人级机构工具',
      },
      {
        num: '11',
        icon: '📈',
        title: '实盘交易 · 券商接口对接',
        desc: '通过券商标准接口（QMT / 量化接口）接入实盘交易。从信号 → 下单 → 成交回报 → 绩效归因全链路打通。',
        highlights: ['券商接口', '信号 → 下单', '成交归因'],
        status: '调研中',
        value: '🔗 实盘闭环',
      },
      {
        num: '12',
        icon: '🌐',
        title: '社区 / 策略市场',
        desc: '让好的策略被看见、让好的想法被验证。用户可以分享已验证的策略、订阅优秀交易者的信号池——一个开放的量化社区。',
        highlights: ['策略分享', '信号订阅', '排行榜'],
        status: '愿景',
        value: '🌍 社区网络效应',
      },
    ],
  },
]

const techStack = [
  {
    name: '前端',
    desc: '以 Vue 3 + Vite 为核心的轻量前端。图表深度依赖 ECharts 与 lightweight-charts。未来引入 React 做更复杂的工作台。',
    chips: ['Vue 3', 'Vite', 'ECharts', 'lightweight-charts'],
  },
  {
    name: '后端',
    desc: 'FastAPI + Python 回测引擎。内置规则解析器可自然语言生成策略代码；长期计划接入自研高性能回测引擎。',
    chips: ['FastAPI', 'Python', '策略 DSL', 'LLM'],
  },
  {
    name: '数据',
    desc: '当前以 DuckDB 单文件嵌入式分析数据库作为轻量核心。生产环境平滑演进到 PostgreSQL + ClickHouse 数据湖。',
    chips: ['DuckDB', 'Tushare Pro', '→ PostgreSQL', '→ ClickHouse'],
  },
  {
    name: '部署',
    desc: '一键脚本安装，Demo 即开即用。生产路径准备 Docker Compose 一键部署，支持 Kubernetes 水平扩展。',
    chips: ['Shell 脚本', 'Docker', 'Docker Compose', 'Kubernetes'],
  },
]
</script>

<style scoped>
.workspace-single {
  max-width: 1200px;
}

.headline {
  padding: 60px 20px 40px;
}

.headline .pill {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 18px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  font-size: 12px;
  letter-spacing: 2px;
  color: var(--muted);
}

.headline .pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--cyan);
  box-shadow: 0 0 8px var(--cyan);
}

.head-title {
  font-size: 48px;
  font-weight: 800;
  line-height: 1.3;
  margin: 24px 0 16px;
  letter-spacing: 0.5px;
}

.head-sub {
  font-size: 15px;
  color: var(--muted);
  max-width: 720px;
  margin: 0 auto 36px;
  line-height: 1.8;
}

/* Milestones */
.milestone-row {
  display: flex;
  justify-content: space-between;
  max-width: 900px;
  margin: 40px auto 0;
  position: relative;
  padding: 20px 10px 40px;
}

.milestone-row::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 5%;
  right: 5%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(34,211,238,0.4), rgba(168,85,247,0.4), rgba(236,72,153,0.4), transparent);
  transform: translateY(-50%);
}

.milestone {
  position: relative;
  z-index: 1;
  text-align: center;
  flex: 1;
  padding: 0 6px;
}

.milestone::before {
  content: '';
  display: block;
  width: 14px;
  height: 14px;
  margin: 0 auto 16px;
  border-radius: 50%;
  background: var(--grad-primary);
  box-shadow: 0 0 20px rgba(34, 211, 238, 0.6);
}

.milestone-time {
  font-size: 11px;
  color: var(--cyan);
  letter-spacing: 1px;
  font-weight: 600;
  margin-bottom: 6px;
}

.milestone-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.4;
}

/* Phase */
.phase-wrap {
  margin-top: 60px;
}

.phase-head {
  margin-bottom: 28px;
  padding: 0 10px;
}

.phase-head.center {
  text-align: center;
}

.phase-label {
  font-size: 11px;
  letter-spacing: 4px;
  color: var(--cyan);
  font-weight: 700;
  margin-bottom: 10px;
}

.phase-title {
  font-size: 30px;
  font-weight: 700;
  line-height: 1.4;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 8px;
}

.phase-emoji {
  font-size: 32px;
}

.phase-sub {
  font-size: 14px;
  color: var(--muted);
  line-height: 1.6;
  margin-bottom: 6px;
}

.phase-timing {
  display: inline-block;
  font-size: 11px;
  color: var(--pink);
  padding: 4px 12px;
  border: 1px solid rgba(236, 72, 153, 0.3);
  border-radius: 999px;
  background: rgba(236, 72, 153, 0.08);
  letter-spacing: 1px;
  margin-top: 6px;
}

/* Feature Grid */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.feature-card {
  padding: 24px 26px 22px;
  position: relative;
  overflow: hidden;
  transition: transform .25s ease, border-color .25s ease;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--grad-primary);
  opacity: 0.6;
}

.feature-num {
  font-family: "SF Mono", Consolas, monospace;
  font-size: 13px;
  color: var(--muted);
  letter-spacing: 2px;
  opacity: 0.5;
  margin-bottom: 12px;
}

.feature-icon {
  font-size: 34px;
  margin-bottom: 12px;
}

.feature-title {
  font-size: 19px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 10px;
  line-height: 1.4;
}

.feature-desc {
  font-size: 13.5px;
  color: var(--muted);
  line-height: 1.75;
  margin-bottom: 14px;
}

.feature-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.highlight-chip {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 6px;
  background: rgba(168, 85, 247, 0.1);
  color: #C084FC;
  border: 1px solid rgba(168, 85, 247, 0.2);
}

.feature-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 14px;
  border-top: 1px dashed var(--border);
  font-size: 12px;
}

.feature-status {
  color: var(--cyan);
  font-weight: 600;
  letter-spacing: 0.5px;
}

.feature-value {
  color: var(--pink);
  font-weight: 600;
}

/* Tech */
.tech-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.tech-card {
  padding: 22px 26px;
}

.tech-name {
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
}

.tech-desc {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.7;
  margin-bottom: 14px;
}

.tech-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tech-chip {
  font-size: 11.5px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(34, 211, 238, 0.08);
  color: var(--cyan);
  border: 1px solid rgba(34, 211, 238, 0.2);
  font-family: "SF Mono", Consolas, monospace;
}

/* Vision */
.vision-card {
  margin-top: 60px;
  padding: 60px 48px 48px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.vision-card::before {
  content: '';
  position: absolute;
  top: -80px;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  height: 200px;
  background: radial-gradient(ellipse, rgba(34, 211, 238, 0.25), transparent 70%);
  filter: blur(30px);
  pointer-events: none;
}

.vision-quote {
  font-size: 80px;
  color: var(--cyan);
  opacity: 0.15;
  line-height: 1;
  font-family: Georgia, serif;
  margin-bottom: -20px;
}

.vision-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 20px;
  line-height: 1.4;
  position: relative;
}

.vision-text {
  font-size: 14.5px;
  color: var(--muted);
  line-height: 2;
  max-width: 760px;
  margin: 0 auto 40px;
  text-align: center;
}

.grad-text-2 {
  background: linear-gradient(90deg, #A855F7, #EC4899);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  font-weight: 700;
}

.vision-meta {
  display: flex;
  justify-content: center;
  gap: 60px;
  padding-top: 30px;
  border-top: 1px dashed var(--border);
}

.vision-meta-item {
  text-align: center;
}

.v-num {
  font-size: 44px;
  font-weight: 800;
  line-height: 1;
}

.v-label {
  font-size: 12px;
  color: var(--muted);
  margin-top: 8px;
  letter-spacing: 1px;
}

.foot-note {
  text-align: center;
  padding: 60px 20px 40px;
  font-size: 12px;
  color: var(--muted);
  letter-spacing: 1px;
  opacity: 0.6;
}

@media (max-width: 780px) {
  .head-title { font-size: 32px; }
  .feature-grid { grid-template-columns: 1fr; }
  .tech-grid { grid-template-columns: 1fr; }
  .milestone-row { flex-direction: column; gap: 20px; }
  .milestone-row::before { display: none; }
  .milestone::before { margin-bottom: 8px; }
  .phase-title { font-size: 22px; flex-direction: column; align-items: flex-start; gap: 6px; }
  .vision-card { padding: 40px 24px 36px; }
  .vision-meta { gap: 30px; flex-wrap: wrap; }
  .vision-title { font-size: 22px; }
}
</style>
