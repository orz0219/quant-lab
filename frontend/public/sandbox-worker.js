/**
 * sandbox-worker.js - 运行在 Web Worker 中的安全执行环境
 *
 * 职责:
 * 1. 接收 Wrapper + 用户策略代码
 * 2. 在独立作用域内 eval 用户代码
 * 3. 校验生命周期钩子 (init, onTick, onDestroy)
 * 4. 提供 context API (buy, sell, log) 通过 postMessage 回传
 * 5. 异常隔离 — 用户代码错误不会影响主线程
 */

/* 内置 Wrapper — 与用户代码拼接后一起执行 */
var WRAPPER_SOURCE = [
  '"use strict";',
  '',
  '// ========== Wrapper: 安全运行时环境 ==========',
  'var __userStrategy = {};',
  'var __context = {',
  '  params: {},',
  '  state: {},',
  '  _signals: [],',
  '  _logs: [],',
  '};',
  '',
  '// context.buy — 发出买入信号',
  '__context.buy = function (opts) {',
  '  opts = opts || {};',
  '  var signal = { type: "buy", price: opts.price || 0, reason: opts.reason || "", time: Date.now() };',
  '  __context._signals.push(signal);',
  '};',
  '',
  '// context.sell — 发出卖出信号',
  '__context.sell = function (opts) {',
  '  opts = opts || {};',
  '  var signal = { type: "sell", price: opts.price || 0, reason: opts.reason || "", time: Date.now() };',
  '  __context._signals.push(signal);',
  '};',
  '',
  '// context.log — 记录日志',
  '__context.log = function (msg) {',
  '  __context._logs.push(String(msg));',
  '};',
  '',
  '// ========== 用户代码 (在下方注入) ==========',
].join('\n');

var USER_CODE_PLACEHOLDER = '/* __USER_CODE__ */';

function buildStrategySource(userCode) {
  return WRAPPER_SOURCE + '\n' + userCode + '\n\n' + [
    '',
    '// ========== 生命周期校验 ==========',
    'if (typeof init !== "function") { throw new Error("缺少生命周期函数: init(context)"); }',
    'if (typeof onTick !== "function") { throw new Error("缺少生命周期函数: onTick(context, bar)"); }',
    'if (typeof onDestroy !== "function") { throw new Error("缺少生命周期函数: onDestroy(context)"); }',
    '',
    '// ========== 准备就绪 ==========',
    '__ready = true;',
  ].join('\n');
}

var __ready = false;

self.addEventListener('message', function (e) {
  var msg = e.data;
  if (!msg || !msg.type) return;
  switch (msg.type) {
    case 'LOAD_STRATEGY': handleLoad(msg); break;
    case 'TICK': handleTick(msg); break;
    case 'DESTROY': handleDestroy(); break;
  }
});

function handleLoad(msg) {
  var userCode = msg.code || '';
  var params = msg.params || {};
  try {
    var source = buildStrategySource(userCode);
    var F = new Function(source);
    F();
    if (!__ready) throw new Error('策略代码执行后未进入就绪状态');
    __context.params = params;
    init(__context);
    self.postMessage({ type: 'STRATEGY_READY', checksum: msg.checksum || '', logs: __context._logs.slice() });
    __context._logs = [];
  } catch (err) {
    self.postMessage({ type: 'STRATEGY_ERROR', error: '策略加载失败: ' + (err.message || String(err)) });
  }
}

function handleTick(msg) {
  if (!__ready) return;
  var bar = msg.bar;
  if (!bar) return;
  try {
    onTick(__context, bar);
    var signals = __context._signals.slice();
    var logs = __context._logs.slice();
    __context._signals = [];
    __context._logs = [];
    if (signals.length > 0 || logs.length > 0) {
      self.postMessage({ type: 'STRATEGY_SIGNAL', signals: signals, logs: logs });
    }
  } catch (err) {
    self.postMessage({ type: 'STRATEGY_ERROR', error: 'onTick 执行异常: ' + (err.message || String(err)) });
  }
}

function handleDestroy() {
  if (!__ready) return;
  try { onDestroy(__context); } catch (err) {}
  self.postMessage({ type: 'DESTROYED' });
}