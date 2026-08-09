# 常见问题与处理

## 1. 安装报错：Unknown command: collection

**错误**: 执行 `npx skills` 相关命令时报 `Unknown command: collection` 或找不到 skills 包

**原因**:
- 未配置 bnpm 源，默认从 npm 公共源拉取，找不到 `skills` 内部包

**处理**:
所有 `npx skills` 命令都需要加上 bnpm 源前缀：
```bash
npm_config_registry=https://bnpm.byted.org/ npx -y skills@latest <command>
```

示例：
```bash
npm_config_registry=https://bnpm.byted.org/ npx -y skills@latest collection add
npm_config_registry=https://bnpm.byted.org/ npx -y skills@latest login
npm_config_registry=https://bnpm.byted.org/ npx -y skills@latest get-jwt
```

---

## 2. 获取 JWT 失败

**错误**: skills CLI 获取 JWT 失败或报 `AUTH_REQUIRED`

**原因**: 
- 未登录 skills
- Token 已过期

**处理**:
```bash
# 登录
npx skills@latest login

# 重新获取 JWT
npm_config_registry=https://bnpm.byted.org/ npx -y skills@latest get-jwt
```

---

## 3. 401 Unauthorized

**错误**: API 返回 `{"err_no": 401, "err_msg": "unauthorized"}`

**原因**: 
- JWT Token 无效或过期
- Header 缺失

**处理**:
1. 重新获取 JWT:
   ```bash
   npx skills@latest get-jwt
   ```
2. 确认请求包含所有必需 Header:
   ```bash
   -H "x-jwt-token: $TOKEN"
   -H "Content-Type: application/json"
   ```

---

## 4. 429 Rate Limited

**错误**: API 返回 `{"err_no": 429, "err_msg": "rate limited"}`

**原因**: 请求频率超限

**限制**:
- 每分钟: 10 次
- 每日: 100 次

**处理**:
- 等待 1 分钟后重试
- 减少请求频率
- 使用 `limit` 参数控制单次返回数量

---

## 5. 网络连接失败

**错误**: `curl: (7) Failed to connect` 或 `ECONNREFUSED`

**原因**:
- 非内网环境
- VPN 未连接

**处理**:
- 确认已连接公司 VPN
- 确认可访问 `bytetech.info`

---

## 6. JSON 解析失败

**错误**: `jq: parse error` 或返回非 JSON 内容

**原因**:
- API 返回 HTML（可能是登录页）
- 网络中间件拦截

**处理**:
1. 先用 `curl -v` 查看完整响应
2. 检查是否被重定向到登录页
3. 重新登录:
   ```bash
   npx skills@latest login
   ```

---

## 7. 分页游标无效

**错误**: 翻页时返回空数据或重复数据

**原因**:
- 使用了过期的 cursor
- cursor 格式错误

**处理**:
- cursor 必须使用上一次请求返回的 `.cursor` 值
- 首页请求传 `"0"` 或不传
- 每次翻页需使用最新返回的 cursor
