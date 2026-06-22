import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// 多页面入口配置
const pages = {
  backtest: resolve(__dirname, 'src/pages/backtest/index.html'),
  strategies: resolve(__dirname, 'src/pages/strategies/index.html'),
  screener: resolve(__dirname, 'src/pages/screener/index.html'),
  pool: resolve(__dirname, 'src/pages/pool/index.html'),
  forum: resolve(__dirname, 'src/pages/forum/index.html'),
}

export default defineConfig({
  appType: 'mpa',
  plugins: [
    vue(),
    {
      name: 'inject-global-scripts',
      transformIndexHtml(html) {
        return html.replace(
          '</head>',
          '  <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>\n'
          + '  <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>\n'
          + '</head>'
        )
      },
    },
  ],
  root: 'src',
  base: '/',
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: resolve(__dirname, 'dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: pages,
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
