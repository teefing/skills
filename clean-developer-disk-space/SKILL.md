---
name: clean-developer-disk-space
description: macOS 开发者磁盘空间清理 Skill：先盘点 Xcode、模拟器、Android、Node、JVM、Go、Kotlin、Docker、通用缓存与可选公司内 workspace 缓存，再按风险分层确认和清理。适用于“磁盘满了”“开发者内容占用很大”“帮我清理几十到几百 G”。
---

# clean-developer-disk-space

当用户遇到 macOS 磁盘爆满、系统设置显示「开发者」占用极大、或明确要求清理开发缓存时使用本 Skill。

## 适用范围

- macOS 开发机。
- 常见 iOS / Android / Web / Node / JVM / Go / Kotlin / Docker 开发缓存。
- 可选支持公司内 MBox / JoJo / Bazel workspace 缓存；未命中这些目录时自动跳过。

## 核心原则

1. **先盘点，后删除**：第一轮只读统计，不删除任何内容。
2. **删除前必须有清单**：任何 `rm -rf` 前，都要先展示路径、大小、风险级别和影响。
3. **清单后再次确认**：用户最初说“帮我清理”只代表授权盘点；展示具体删除清单后，必须获得用户对本轮具体路径的再次确认，才能删除。
4. **分风险清理**：低风险缓存可在二次确认后执行；中高风险项必须单独确认。
5. **每轮清理后验证**：用 `df -h /System/Volumes/Data`（失败则 `df -h /`）和关键目录 `du` 复查空间。
6. **预估必须保守**：`du` 看到的是目录逻辑占用，不等于 `df` 最终释放的物理空间；APFS clone、hardlink、Bazel / JoJo CAS 复用块会导致「目录少了几十 G，但系统可用空间只涨十几 G」。对外只能说「候选目录逻辑占用约 XG」，不要承诺「可回收 XG」。
7. **保护语义必停**：路径名包含 `DO_NOT_DELETE`、`DoNotDelete`、`不可删除`、`KEEP`、`重要` 等保护语义时，即使体积巨大，也不得直接删除；只能列为候选并要求用户确认或寻找官方清理方式。
8. **不动用户数据和源码**：默认不删除 `Downloads`、`Desktop`、`Documents`、照片、聊天数据、源码仓、共享仓库和包管理器源目录。
9. **命令要可移植**：使用 `$HOME`，不要写死具体用户名；目录不存在时用 `2>/dev/null || true` 跳过。

## 第 0 步：说明策略

先告诉用户：

- 会先做只读盘点。
- 删除前会按风险列候选。
- 明确的开发缓存 / 构建产物可以清；用户文件、源码仓和保护目录不直接删。

## 第 1 步：只读盘点

优先并行执行以下命令。命令只读，不删除。

```bash
df -h / /System/Volumes/Data 2>/dev/null || df -h /
```

```bash
du -xhd 1 "$HOME" 2>/dev/null | sort -h | tail -30
```

```bash
du -xhd 2 "$HOME/Library/Developer" 2>/dev/null | sort -h | tail -40
```

```bash
du -xhd 1 \
  "$HOME/Library/Caches" \
  "$HOME/.cache" \
  "$HOME/.gradle" \
  "$HOME/.m2" \
  "$HOME/.ivy2" \
  "$HOME/.cocoapods" \
  "$HOME/.npm" \
  "$HOME/.pnpm-store" \
  "$HOME/.yarn" \
  "$HOME/.swiftpm" \
  "$HOME/.ccache" \
  "$HOME/.cargo" \
  "$HOME/go" \
  "$HOME/.konan" \
  2>/dev/null | sort -h | tail -50
```

```bash
du -xhd 2 \
  "$HOME/Library/Android" \
  "$HOME/.android" \
  2>/dev/null | sort -h | tail -40
```

```bash
du -xhd 2 \
  "$HOME/MBoxWorkspace" \
  "$HOME/workspace" \
  "$HOME/Developer" \
  "$HOME/Projects" \
  2>/dev/null | sort -h | tail -50
```

```bash
tmutil listlocalsnapshots / 2>/dev/null || true
```

如果用户使用 Docker Desktop，再加：

```bash
docker system df 2>/dev/null || true
```

## 第 2 步：分类输出候选

把盘点结果整理成表格：

| 类型 | 路径 | 逻辑占用 | 风险 | 建议 |
|---|---:|---:|---|---|
| 明确可再生成 | `.../bazel_build` | `72G` | 低 | 可删；若含共享块，实际释放可能小于逻辑占用 |
| Xcode 缓存 | `~/Library/Developer/Xcode/iOS DeviceSupport` | `66G` | 低 | 可删，真机调试时会重新生成 |
| 包管理缓存 | `~/.gradle/caches` | `11G` | 低 | 可删，后续会重新下载 |
| 工具链 / SDK | `~/Library/Developer/Toolchains` | `18G` | 中 | 谨慎，可能影响构建 |
| 用户文件 | `~/Downloads` | `80G` | 高 | 不自动删 |
| 保护目录 | `~/.xxx_DO_NOT_DELETE` | `171G` | 高 | 不自动删，需确认 / 官方方式 |

输出候选清单时必须补一句：

> 表中的大小是 `du` 统计的目录逻辑占用，最终 `df` 增加的可用空间可能更少，尤其是 Bazel / JoJo / APFS clone / CAS 场景。

## 第 3 步：低风险清理项

满足以下条件时，才能执行删除：

- 已展示候选清单；
- 用户已经对本轮具体路径清单明确确认；
- 路径属于下列低风险缓存 / 构建产物；
- 路径不包含保护语义。

### 3.1 Xcode / iOS 可再生成缓存

常见可删：

```text
~/Library/Developer/Xcode/iOS DeviceSupport
~/Library/Developer/Xcode/DerivedData
~/Library/Developer/DVTDownloads
~/Library/Developer/CoreSimulator/Caches
~/Library/Developer/CoreSimulator/Temp
```

清理前复核：

```bash
du -xsh \
  "$HOME/Library/Developer/Xcode/iOS DeviceSupport" \
  "$HOME/Library/Developer/Xcode/DerivedData" \
  "$HOME/Library/Developer/DVTDownloads" \
  "$HOME/Library/Developer/CoreSimulator/Caches" \
  "$HOME/Library/Developer/CoreSimulator/Temp" \
  2>/dev/null || true
```

删除：

```bash
rm -rf \
  "$HOME/Library/Developer/Xcode/iOS DeviceSupport" \
  "$HOME/Library/Developer/Xcode/DerivedData" \
  "$HOME/Library/Developer/DVTDownloads" \
  "$HOME/Library/Developer/CoreSimulator/Caches" \
  "$HOME/Library/Developer/CoreSimulator/Temp"
```

### 3.2 包管理器和语言缓存

常见可删：

```text
~/Library/Caches/CocoaPods
~/.gradle/caches
~/.gradle/transform_cache
~/.ivy2/cache
~/.npm/_cacache
~/.npm/_npx
~/.pnpm-store
~/.yarn/cache
~/.cache/pip
~/.cache/pypoetry
~/.cache/go-build
~/.cargo/registry/cache
~/.swiftpm/cache
```

清理前复核：

```bash
du -xsh \
  "$HOME/Library/Caches/CocoaPods" \
  "$HOME/.gradle/caches" \
  "$HOME/.gradle/transform_cache" \
  "$HOME/.ivy2/cache" \
  "$HOME/.npm/_cacache" \
  "$HOME/.npm/_npx" \
  "$HOME/.pnpm-store" \
  "$HOME/.yarn/cache" \
  "$HOME/.cache/pip" \
  "$HOME/.cache/pypoetry" \
  "$HOME/.cache/go-build" \
  "$HOME/.cargo/registry/cache" \
  "$HOME/.swiftpm/cache" \
  2>/dev/null || true
```

删除：

```bash
rm -rf \
  "$HOME/Library/Caches/CocoaPods" \
  "$HOME/.gradle/caches" \
  "$HOME/.gradle/transform_cache" \
  "$HOME/.ivy2/cache" \
  "$HOME/.npm/_cacache" \
  "$HOME/.npm/_npx" \
  "$HOME/.pnpm-store" \
  "$HOME/.yarn/cache" \
  "$HOME/.cache/pip" \
  "$HOME/.cache/pypoetry" \
  "$HOME/.cache/go-build" \
  "$HOME/.cargo/registry/cache" \
  "$HOME/.swiftpm/cache"
```

### 3.3 App / AI 工具日志缓存

常见可删，但必须先列出大小：

```text
~/.claude-code-router/logs
~/.nvm/.cache
~/.cache/puppeteer
~/.cache/codex-runtimes
~/.cache/whisper
~/Library/Caches/com.openai.codex
~/Library/Caches/cn.trae.app.ShipIt
~/Library/Caches/Trae CN
~/Library/Caches/LarkShell
```

清理前复核：

```bash
du -xsh \
  "$HOME/.claude-code-router/logs" \
  "$HOME/.nvm/.cache" \
  "$HOME/.cache/puppeteer" \
  "$HOME/.cache/codex-runtimes" \
  "$HOME/.cache/whisper" \
  "$HOME/Library/Caches/com.openai.codex" \
  "$HOME/Library/Caches/cn.trae.app.ShipIt" \
  "$HOME/Library/Caches/Trae CN" \
  "$HOME/Library/Caches/LarkShell" \
  2>/dev/null || true
```

删除：

```bash
rm -rf \
  "$HOME/.claude-code-router/logs" \
  "$HOME/.nvm/.cache" \
  "$HOME/.cache/puppeteer" \
  "$HOME/.cache/codex-runtimes" \
  "$HOME/.cache/whisper" \
  "$HOME/Library/Caches/com.openai.codex" \
  "$HOME/Library/Caches/cn.trae.app.ShipIt" \
  "$HOME/Library/Caches/Trae CN" \
  "$HOME/Library/Caches/LarkShell"
```

### 3.4 Workspace 构建产物（通用）

只删除盘点后确认的具体绝对路径，不删除源码仓，不用宽泛通配批量删除。

低风险候选仅限语义明确的构建产物目录，例如：

```text
<workspace>/bazel_build
<workspace>/node_modules/.cache
<workspace>/.gradle/caches
```

注意：`build`、`.gradle` 这类名字过于通用，可能包含项目本地状态或用户产物；默认只列为候选，不直接删除。删除时必须把 shell 通配符展开成逐条具体路径，过滤掉任何包含保护语义的路径，展示清单并获得确认后逐项删除。

示例流程：

```bash
# 只复核大小，不删除
du -xsh "$HOME"/MBoxWorkspace/*/bazel_build 2>/dev/null | sort -h

# 删除前把上一步输出整理为具体路径清单，确认后逐项 rm -rf，不直接复制通配符删除
```

### 3.5 Docker 缓存（可选）

只有用户确认正在使用 Docker 且接受删除未使用镜像 / 容器 / 构建缓存时执行。

盘点：

```bash
docker system df 2>/dev/null || true
```

清理命令需要单独确认：

```bash
docker system prune -af
```

如用户确认也删除未使用 volume，再执行：

```bash
docker volume prune -f
```

## 第 4 步：中高风险项，必须确认

以下项目不能默认删除，只能列出并询问用户。

| 路径 / 类型 | 风险 |
|---|---|
| `~/Downloads`、`~/Desktop`、`~/Documents` | 用户文件，可能不可恢复 |
| 源码仓目录，如 `~/MBoxWorkspace/*/Aweme`、`~/workspace/*`、`~/Developer/*` | 可能有未提交代码 |
| `~/.mbox`、`.git`、`.svn` | 共享仓库 / VCS 元数据，删除可能破坏 workspace |
| 路径名含 `DO_NOT_DELETE` / `KEEP` / `重要` | 明确保留语义，必须停下确认 |
| `~/Library/JoJoIncreInstall` | JoJo 增量安装产物，删除后可能需要重新安装依赖 |
| `~/Library/Developer/Toolchains` | Swift 工具链，可能影响编译 |
| `~/Library/Android`、`~/.android/avd` | Android SDK / 模拟器，删除影响 Android 开发 |
| `~/.m2/repository` | Maven 本地仓，可能包含 `mvn install` 生成的私有 artifact |
| `~/go/pkg/mod` | Go module cache，删除后重新下载，项目多时成本高 |
| `~/.konan` | Kotlin/Native 工具链，删除后重新下载 |
| Docker volumes | 可能含数据库 / 本地服务数据 |

确认问题示例：

> 还剩一个大头 `~/.xxx_DO_NOT_DELETE`，大小 `171G`，目录名明确写了 `DO_NOT_DELETE`。我不建议直接 `rm -rf`。你要我继续找官方清理命令，还是你确认承担风险后删除？

## 第 5 步：验证和汇报

每轮删除后执行：

```bash
df -h /System/Volumes/Data 2>/dev/null || df -h /
```

以及关键目录复查：

```bash
du -xhd 1 "$HOME" 2>/dev/null | sort -h | tail -25
```

按本轮涉及目录选择复查：

```bash
du -xhd 1 "$HOME/Library/Caches" "$HOME/.gradle" "$HOME/.npm" 2>/dev/null | sort -h | tail -20
```

```bash
du -xhd 2 "$HOME/Library/Developer" 2>/dev/null | sort -h | tail -20
```

```bash
du -xhd 1 "$HOME/MBoxWorkspace" "$HOME/workspace" "$HOME/Developer" 2>/dev/null | sort -h | tail -30
```

汇报格式：

```markdown
已暂停 / 已完成本轮清理。

| 项目 | 清理前 | 清理后 |
|---|---:|---:|
| 系统 Data 卷可用空间（`df`） | `18Gi` | `191Gi` |
| `MBoxWorkspace` 逻辑占用（`du`） | `287G` | `30G` |
| `Library/Developer` 逻辑占用（`du`） | `86G` | `20G` |

已删除：
- `MBoxWorkspace/*/bazel_build`
- `~/Library/Developer/Xcode/iOS DeviceSupport`
- `~/Library/Caches/CocoaPods`

说明：`du` 目录逻辑占用下降不一定等于 `df` 可用空间上涨；APFS clone、hardlink、Bazel / JoJo CAS 复用块可能让实际释放小于目录减少量。

未删除的大头：

| 路径 | 大小 | 原因 |
|---|---:|---|
| `~/.xxx_DO_NOT_DELETE` | `171G` | 名字带保护语义，需确认 |
| `~/Downloads` | `80G` | 用户文件 |
```

## 可选：公司内 MBox / JoJo Profile

如果盘点发现以下目录，按公司内开发缓存处理；没有则跳过：

```text
~/MBoxWorkspace/*/bazel_build
~/Library/Caches/JoJo
~/Library/JoJoIncreInstall
~/.jojo_artifacts_DO_NOT_DELETE
```

规则：

- `~/MBoxWorkspace/*/bazel_build`：低风险，但必须先展开成具体路径清单，过滤保护语义路径，确认后逐项删除。
- `~/Library/Caches/JoJo`：普通缓存，可在确认后清理。
- `~/Library/JoJoIncreInstall`：中风险，删除后可能重新下载依赖，必须确认。
- `~/.jojo_artifacts_DO_NOT_DELETE`：高风险，名称带保护语义，不直接删除。

## 本次沉淀案例

2026/08/04 清理一台大型 iOS 开发机：

- 初始 `/System/Volumes/Data`：`872Gi used / 18Gi avail`。
- 最大低风险项：多个 `MBoxWorkspace/*/bazel_build`，合计约 `257G`。
- `~/Library/Developer/Xcode/iOS DeviceSupport`：`66G`。
- `~/Library/Caches/CocoaPods`：`25G`。
- `.gradle`、`.npm`、`Library/Caches/JoJo` 合计约 `20G`。
- 第一轮清理后：`697Gi used / 191Gi avail`，`df` 可用空间增加约 `173Gi`。
- 追加清理中出现过 `du` 与 `df` 不一致：`MBoxWorkspace` 逻辑占用下降约 `57G`，但 `df` 可用空间只增加约 `16Gi`，疑似 APFS clone / JoJo CAS 共享块导致。
- 剩余大头：`~/.jojo_artifacts_DO_NOT_DELETE` `171G`，因目录名保护未删除。
