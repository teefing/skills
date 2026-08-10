# window.magic API 参考

> `window.magic` 是飞书宿主在文档内嵌 HTML 的 iframe 加载完成后异步注入的全局桥接对象。通过它可以获取用户身份、文档元数据、持久化存储、AI 和多维表格能力。

## 可用性

- **仅在飞书文档的内嵌 HTML 块中可用**（AddOns iframe 沙箱内）
- 本地浏览器预览时为 `undefined`
- 独立妙搭应用中**不可用**
- 注入时机：DOMContentLoaded 之后异步注入（可能延迟 200-2000ms）

## Feature Detection（必须）

```javascript
function waitForMagic(cb, retries = 30) {
  if (window.magic) return cb(window.magic);
  if (--retries > 0) setTimeout(() => waitForMagic(cb, retries), 150);
  else console.warn('[lark-html] magic not available, standalone mode');
}

waitForMagic(async (magic) => {
  // 在这里使用 magic API
});
```

---

## 用户身份

### getCurrentUserInfo()

获取当前文档访问者的身份信息。

```javascript
const user = await window.magic.getCurrentUserInfo();
// Returns: { name: string, avatar_url: string, open_id: string, union_id: string }
```

⚠ **Race Condition**: 如果在 magic HMAC 初始化完成前调用，会抛出 `"HMAC key data must not be empty"`。使用指数退避重试：

```javascript
async function safeGetUser(retries = 4, delay = 300) {
  for (let i = 0; i < retries; i++) {
    try { return await window.magic.getCurrentUserInfo(); }
    catch (e) { await new Promise(r => setTimeout(r, delay * Math.pow(2, i))); }
  }
  return null;
}
```

### getUserInfoById(open_id)

根据 open_id 查询任意用户的基本信息。

```javascript
const other = await window.magic.getUserInfoById('ou_xxxxxxxx');
// Returns: { name: string, avatar_url: string, open_id: string }
```

---

## 文档元数据

### getPageMeta()

获取当前文档的实时统计和元信息。

```javascript
const meta = await window.magic.getPageMeta();
// Returns:
// {
//   pv: number,              // 累计页面浏览量
//   uv: number,              // 累计独立访客数
//   pv_today: number,        // 今日 PV
//   uv_today: number,        // 今日 UV
//   like_count: number,      // 点赞数
//   comments_count: number,  // 评论数
//   char_count: number,      // 文档字符数
//   file_size: number,       // 文档大小(bytes)
//   owner_user: string,      // 文档所有者
//   title: string,           // 文档标题
//   revision: number         // 当前版本号
// }
```

### getDocAsMarkdown()

将整篇文档导出为 Markdown 字符串。

```javascript
const md = await window.magic.getDocAsMarkdown();
// Returns: string (完整 Markdown 内容)
```

---

## 持久化存储（Redis）

飞书为每篇文档提供一套类 Redis 的 KV 存储。**值只能是字符串**，存储复杂数据需 `JSON.stringify/parse`。

### 共享存储（所有访客可见）

```javascript
// 写入（所有访客都能读到这个值）
await window.magic.redis.global_set('key', 'value');

// 读取
const val = await window.magic.redis.global_get('key');
// Returns: string | null
```

### 私有存储（仅当前用户可见）

```javascript
// 写入（只有同一 open_id 的用户能读到）
await window.magic.redis.set('my_preference', 'dark');

// 读取
const pref = await window.magic.redis.get('my_preference');
```

### 存储特性

| 特性 | 说明 |
|------|------|
| 作用域 | 同一文档的所有 HTML 块**共享同一 key namespace** |
| 生命周期 | 与文档一致，文档删除则数据销毁 |
| 大小限制 | 单个 value 建议 < 1MB |
| 并发 | Last-write-wins，无事务保证 |
| 数据类型 | 仅字符串，复杂结构用 JSON |

⚠ **Key 冲突风险**: 同文档多个 HTML 块共享 namespace。建议 key 加功能前缀（如 `vote_results_`、`chat_messages_`）。

---

## AI

### ai(prompt)

调用飞书内置 AI 能力，输入 prompt 返回文本结果。

```javascript
const answer = await window.magic.ai('用一句话总结：什么是 Transformer？');
// Returns: string
// 延迟: 5-15 秒，务必显示 loading 状态
```

建议加超时保护：

```javascript
const result = await Promise.race([
  window.magic.ai(prompt),
  new Promise((_, reject) => setTimeout(() => reject('timeout'), 20000))
]).catch(() => '生成超时，请重试');
```

---

## 多维表格（Bitable）

对同文档内的多维表格进行 CRUD 操作：

```javascript
// 搜索记录
const records = await window.magic.base_records_search(app_token, table_id, filter);

// 读取单条
const record = await window.magic.base_records_get(app_token, table_id, record_id);

// 创建记录
await window.magic.base_records_create(app_token, table_id, { fields: {...} });

// 更新记录
await window.magic.base_records_update(app_token, table_id, record_id, { fields: {...} });
```

---

## iframe 高度管理

HTML 块在文档中以 iframe 渲染，高度不会自动扩展。内容变化后需手动通知宿主：

```javascript
window.magic.updateHeight();   // 重新计算并更新 iframe 高度
window.magic.refreshHeight();  // 强制刷新
window.magic.resize();         // resize 事件触发时调用
```

建议在内容动态变化后（DOM 更新、展开/折叠）调用 `updateHeight()`。

---

## API 一览表

| 方法 | 类别 | 异步 | 说明 |
|------|------|------|------|
| `getCurrentUserInfo()` | 身份 | ✅ | 当前访客 |
| `getUserInfoById(id)` | 身份 | ✅ | 按 open_id 查人 |
| `getPageMeta()` | 文档 | ✅ | 实时统计 |
| `getDocAsMarkdown()` | 文档 | ✅ | 导出全文 |
| `redis.global_get(key)` | 存储 | ✅ | 共享读 |
| `redis.global_set(key, val)` | 存储 | ✅ | 共享写 |
| `redis.get(key)` | 存储 | ✅ | 私有读 |
| `redis.set(key, val)` | 存储 | ✅ | 私有写 |
| `ai(prompt)` | AI | ✅ | 文本生成 |
| `base_records_search/get/create/update` | Bitable | ✅ | 多维表格 CRUD |
| `updateHeight()` | 布局 | ❌ | 更新高度 |
| `refreshHeight()` | 布局 | ❌ | 强制刷新高度 |
| `resize()` | 布局 | ❌ | resize 触发 |
