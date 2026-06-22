<template>
  <header class="topbar">
    <div class="topbar-left">
      <div class="logo">
        <span class="logo-mark">Q</span>
        <div>
          <div class="logo-name">QuantLab</div>
          <div class="logo-sub">AI 股票策略回测</div>
        </div>
      </div>
    </div>
    <nav class="topbar-nav">
      <a v-for="item in navItems" :key="item.path"
         :class="['nav-item', { active: active === item.key }]"
         :href="item.path">{{ item.label }}</a>
    </nav>
    <div class="topbar-right">
      <button class="btn-ghost" type="button">⚡ 演示</button>
      <button class="btn-primary" type="button">立即体验</button>
    </div>
  </header>
</template>

<script setup>
defineProps({ active: { type: String, default: 'backtest' } })
const navItems = [
  { key: 'backtest', path: '/pages/backtest/', label: '回测' },
  { key: 'strategies', path: '/pages/strategies/', label: '策略库' },
  { key: 'screener', path: '/pages/screener/', label: '选股' },
  { key: 'pool', path: '/pages/pool/', label: '股票池分析' },
  { key: 'forum', path: '/pages/forum/', label: '论坛(开发中)' },
]
</script>

<style scoped>
.topbar { position: sticky; top: 0; z-index: 20; display: flex; align-items: center; justify-content: space-between; padding: 14px 32px; background: rgba(10, 18, 40, 0.55); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border-bottom: 1px solid var(--border); }
.logo { display: flex; align-items: center; gap: 12px; }
.logo-mark { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center; font-weight: 800; background: var(--grad-primary); color: #06101F; box-shadow: 0 10px 30px -10px rgba(34, 211, 238, 0.6); font-size: 18px; }
.logo-name { font-weight: 700; letter-spacing: 0.3px; }
.logo-sub { font-size: 12px; color: var(--muted); }
.topbar-nav { display: flex; gap: 6px; }
.nav-item { padding: 8px 14px; border-radius: 10px; font-size: 14px; color: var(--muted); border: 1px solid transparent; cursor: pointer; transition: color .2s, background .2s, border-color .2s; }
.nav-item:hover { color: var(--text); background: var(--panel); }
.nav-item.active { color: var(--text); background: linear-gradient(90deg, rgba(34,211,238,0.12), rgba(168,85,247,0.12)); border-color: rgba(34, 211, 238, 0.3); }
.topbar-right { display: flex; gap: 10px; }
</style>
