# HTML 编写规范与避坑指南

> 本文档覆盖在飞书文档内嵌 HTML 块时的编写规则、调试技巧和 iframe 沙箱能力边界。

## 编写规则

### 1. 自包含（Self-contained）

所有 CSS/JS 必须内联或引用公共 CDN。不能依赖本地文件系统路径。

推荐 CDN：
- `https://cdn.jsdelivr.net/npm/` — 实测稳定可用
- `https://unpkg.com/` — 备选
- `https://cdnjs.cloudflare.com/` — 备选

### 2. 固定高度（Explicit Height）

body 或主容器**必须有明确的 height**（如 `480px`），否则 iframe 高度塌缩为 0 导致不可见。

```css
body { height: 480px; overflow: hidden; }
/* 或者 */
.container { height: 100vh; min-height: 400px; }
```

如果内容是动态高度，初始给一个安全值，内容渲染后调 `window.magic.updateHeight()`。

### 3. 宽度自适应

使用 `width: 100%`，不写固定像素宽度。文档编辑器列宽会变化。

```javascript
// ECharts 等图表库需要监听 resize
window.addEventListener('resize', () => chart.resize());
```

### 4. 深色背景推荐

飞书文档默认白底，HTML 块通常作为"特殊区域"突出。深色背景与文档形成对比，视觉效果更好：

```css
body {
  background: radial-gradient(ellipse at top, #0c1220, #000);
  color: #fff;
}
```

也可以用 `prefers-color-scheme` 做亮/暗适配。

### 5. CDN 脚本加载兜底

外部 `<script src>` 在 iframe 里是异步加载的。在使用库之前**必须轮询等待就绪**：

```javascript
function boot() {
  if (typeof echarts === 'undefined') return setTimeout(boot, 150);
  // ECharts 已就绪，开始初始化
  const chart = echarts.init(document.getElementById('chart'));
  // ...
}
boot();
```

### 6. 不使用 localStorage

iframe 沙箱隔离了 localStorage/sessionStorage，写入后下次打开为空。持久化数据**必须用 `window.magic.redis`**。

### 7. window.magic 判存

`window.magic` 只在飞书文档端注入，本地浏览器预览时为 undefined。代码中必须做降级处理：

```javascript
if (window.magic) {
  // 飞书环境：使用 magic API
} else {
  // 本地预览：使用 mock 数据或跳过
}
```

---

## iframe 沙箱能力边界

| 能做 | 不能做 |
|------|--------|
| 任意 HTML5 标签 | 跨域表单提交 |
| CSS 动画 (@keyframes/transition/grid/flex) | 弹窗 (alert/confirm/prompt) |
| 内联 JS (Canvas 2D/WebGL/rAF/Web Audio) | window.open / window.top 访问 |
| 加载 CDN (ECharts/Three.js/GSAP/D3) | 需用户授权的浏览器 API (camera/mic) |
| 内联 SVG + SMIL animate | 超大 base64 内联资源 (>5MB) |
| window.magic 全部能力 | localStorage / sessionStorage |
| Fetch 请求 (同源/CDN) | 访问宿主页面 DOM |
| CSS 变量 / CSS Grid / Container Queries | 读取飞书 Cookie |
| Web Workers (有限制) | IndexedDB (部分浏览器拒绝) |

---

## 调试指南

### 白屏问题排查

iframe 内的 JS 异常不会在外层控制台显示，导致"白屏但无报错"。排查流程：

1. **先在本地浏览器测试** — 直接用 Chrome 打开 HTML 文件，查看控制台
2. **检查高度** — 是否忘了设 body/container height
3. **检查 CDN** — 网络是否可达；是否在 boot() 轮询前就使用了库
4. **检查 magic** — 是否在 magic 未注入时就调用了 magic API（加判存）
5. **检查 base64 大小** — 内联图片/字体是否超过 5MB

### 开发流程建议

1. 本地 Chrome 开发 + 调试（此时 `window.magic` 为 undefined，用 mock）
2. 确认本地无报错后，用 `build_payload.py` 插入文档
3. 在飞书文档中验证 magic 功能
4. 如有问题，用 Read 操作把 HTML 取出来对比

---

## 性能建议

| 维度 | 建议值 | 超出后果 |
|------|--------|----------|
| HTML 文件大小 | < 500KB | 插入 API 可能超时 |
| 内联图片 | < 2MB 总计 | 白屏或加载缓慢 |
| 动画帧率 | 30-60fps | 文档滚动卡顿 |
| 轮询间隔 | >= 3s | 更短会增加平台负载 |
| 单 redis value | < 1MB | 读写延迟增大 |

---

## 字体加载

Google Fonts 在中国大陆可能被墙。替代方案：

```html
<!-- 通过 jsDelivr 加载字体（稳定） -->
<link href="https://cdn.jsdelivr.net/npm/@fontsource/inter@5/index.css" rel="stylesheet">
```

或直接用系统字体栈：

```css
font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
```

---

## 完整模板

```html
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>My Block</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { height: 480px; overflow: hidden; font-family: -apple-system, "PingFang SC", sans-serif; }
  body { background: #0f172a; color: #fff; }
  .container { padding: 20px; height: 100%; }
</style>
</head>
<body>
<div class="container" id="app">
  <!-- 内容 -->
</div>
<script>
function waitForMagic(cb, retries = 30) {
  if (window.magic) return cb(window.magic);
  if (--retries > 0) setTimeout(() => waitForMagic(cb, retries), 150);
  else { /* standalone mode */ initStandalone(); }
}

function initStandalone() {
  document.getElementById('app').textContent = 'Preview mode (no magic)';
}

waitForMagic(async (magic) => {
  const user = await magic.getCurrentUserInfo().catch(() => null);
  // ... 业务逻辑
});
</script>
</body>
</html>
```
