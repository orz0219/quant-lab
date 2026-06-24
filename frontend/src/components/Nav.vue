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
      <span class="badge-beta">v0.1 · Beta</span>
      <a class="gh-link" href="https://github.com/orz0219/quant-lab" target="_blank" title="GitHub">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.11.82-.26.82-.577 0-.285-.01-1.04-.015-2.04-3.338.725-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.807 1.305 3.492.998.108-.775.418-1.305.762-1.605-2.665-.305-5.467-1.332-5.467-5.93 0-1.31.468-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.4 3-.405 1.02.005 2.04.138 3 .405 2.295-1.552 3.3-1.23 3.3-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.295 24 12c0-6.63-5.37-12-12-12z"/>
        </svg>
      </a>
      <a class="btn-primary" href="/pages/backtest/">开始回测</a>
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
  { key: 'roadmap', path: '/pages/roadmap/', label: '产品蓝图' },
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
.topbar-right { display: flex; gap: 10px; align-items: center; }
.badge-beta {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 11px;
  letter-spacing: 1px;
  color: #FBBF24;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.25);
  font-weight: 600;
}
.gh-link {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  color: var(--text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: border-color .2s, background .2s, color .2s;
  text-decoration: none;
}
.gh-link:hover {
  color: var(--cyan);
  border-color: rgba(34, 211, 238, 0.4);
  background: rgba(34, 211, 238, 0.08);
}
a.btn-primary { text-decoration: none; }
</style>
