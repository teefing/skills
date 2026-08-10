# 数据交互模式（Data Interaction Patterns）

> 本文档覆盖使用 `window.magic` 构建协作型、实时型、多人交互型 HTML 块的典型设计模式。

## 模式一：多人协作状态（Collaborative State）

**核心原语**: `redis.global_get` / `redis.global_set`

所有协作功能的本质是：多个访客共享一块可读写的全局状态。飞书的 `redis.global_*` 就是这块共享内存。

### 标准写法

```javascript
// 读取当前状态
async function loadState() {
  const raw = await window.magic.redis.global_get('my_feature_state');
  return raw ? JSON.parse(raw) : { items: [], version: 0 };
}

// 写入更新（last-write-wins）
async function saveState(state) {
  state.version++;
  await window.magic.redis.global_set('my_feature_state', JSON.stringify(state));
}
```

### 适用场景
- 投票/点赞计数
- 共享留言墙/弹幕
- 协作画布（每笔画作为数组元素追加）
- 游戏排行榜
- 协作音乐盒（共享音序器状态）

### 容量建议
- 单个 key 的 value 建议不超过 1MB
- 数组型数据建议设置上限（如最近 200 条消息），超出时 `.slice(-200)` 截断

---

## 模式二：轮询刷新（Polling）

`window.magic.redis` 没有 pub/sub 或 WebSocket 推送。多人实时同步靠**客户端轮询**实现。

### 轮询频率建议

| 场景 | 间隔 | 理由 |
|------|------|------|
| 聊天/弹幕/实时协作 | 3-5 秒 | 体验优先，延迟感可接受 |
| 投票/排行榜 | 5-8 秒 | 数据变化频率中等 |
| 文档统计/仪表盘 | 30 秒 | 数据本身更新慢 |
| 一次性加载（AI 结果） | 不轮询 | 请求时获取一次即可 |

### 标准轮询模板

```javascript
let pollTimer = null;

async function poll() {
  const state = await loadState();
  renderUI(state);
}

function startPolling(intervalMs = 5000) {
  poll(); // 首次立即执行
  pollTimer = setInterval(poll, intervalMs);
}

function stopPolling() {
  if (pollTimer) clearInterval(pollTimer);
}

// 页面初始化后启动
startPolling(5000);
```

---

## 模式三：用户身份 + 归属（Identity Attribution）

每条用户产生的数据都应携带身份信息，用于展示"谁做了什么"。

### 标准数据结构

```javascript
const user = await safeGetUser(); // 见 window-magic-api.md

const newItem = {
  id: crypto.randomUUID(),        // 唯一标识
  by: {
    open_id: user.open_id,
    name: user.name,
    avatar: user.avatar_url
  },
  content: '用户输入的内容',
  t: Date.now()                    // 时间戳
};
```

### 去重与更新
- 排行榜：按 `open_id` 查找已有记录，只在分数更高时更新
- 投票：按 `open_id` 检查是否已投过（一人一票）
- 留言：不去重，追加即可

---

## 模式四：Per-user 私有状态

某些数据只对当前用户可见（偏好设置、"已读"标记、个人草稿）。

```javascript
// 私有读写（其他人看不到）
await window.magic.redis.set('user_theme', 'dark');
const theme = await window.magic.redis.get('user_theme'); // 'dark'
```

### 与 global 的搭配

```javascript
// 全局存投票结果（所有人可见）
await window.magic.redis.global_set('poll_results', JSON.stringify(results));

// 私有存"我是否已投票"（防止同一人重复投）
await window.magic.redis.set('poll_voted', 'true');
```

---

## 模式五：冲突处理

`redis.global_set` 是 last-write-wins，两人同时写可能丢数据。

### 策略一：乐观追加（适合列表型数据）

```javascript
async function addItem(newItem) {
  const state = await loadState();          // 读最新
  state.items.push(newItem);                // 追加
  state.items = state.items.slice(-200);    // 截断
  await saveState(state);                   // 写回
}
```

丢失概率低（两人在同一秒内同时读+写才会冲突），对于文档内交互场景通常可接受。

### 策略二：版本号检查（适合关键数据）

```javascript
async function updateWithCheck(updater) {
  const state = await loadState();
  const newState = updater(state);
  // 简单版本号校验（非原子，但降低冲突窗口）
  const current = await loadState();
  if (current.version !== state.version) {
    // 有人在我读写之间更新了，重试
    return updateWithCheck(updater);
  }
  await saveState(newState);
}
```

---

## 模式六：AI 集成

```javascript
async function generateWithAI(prompt) {
  showLoading();
  try {
    const result = await Promise.race([
      window.magic.ai(prompt),
      new Promise((_, rej) => setTimeout(() => rej('timeout'), 20000))
    ]);
    return result;
  } catch (e) {
    return '生成失败，请重试';
  } finally {
    hideLoading();
  }
}
```

### 注意事项
- AI 延迟 5-15 秒，**必须有 loading 态**
- 不要在轮询中调 AI（成本高、延迟大）
- AI 结果可缓存到 redis 避免重复调用

---

## 模式七：初始化顺序（Boot Sequence）

标准的 HTML 块初始化顺序：

```javascript
// 1. 等待 magic 注入
waitForMagic(async (magic) => {
  // 2. 获取用户身份（带重试）
  const user = await safeGetUser();
  
  // 3. 加载全局状态
  const state = await loadState();
  
  // 4. 首次渲染
  renderUI(state, user);
  
  // 5. 启动轮询
  startPolling(5000);
  
  // 6. 绑定用户交互事件
  bindEvents(user);
});
```

---

## 典型应用参考

| 应用类型 | 用到的模式 | 关键 API |
|----------|-----------|----------|
| 投票组件 | 协作状态 + 身份归属 + 私有标记 | `global_get/set` + `getCurrentUserInfo` + `redis.set` |
| 实时弹幕 | 协作状态 + 轮询(3s) + 身份 | `global_get/set` + `getCurrentUserInfo` |
| 排行榜游戏 | 协作状态 + 身份 + 乐观追加 | `global_get/set` + `getCurrentUserInfo` |
| 文档仪表盘 | 文档元数据 + 轮询(30s) | `getPageMeta` |
| 匿名表单 | 协作状态（无身份） | `global_get/set` |
| AI 问答 | AI + 私有缓存 | `ai` + `redis.set` |
