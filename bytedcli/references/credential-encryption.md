# 凭证落盘加密

该能力默认关闭。未配置开关的进程保持现有凭证路径、身份选择及文件格式，不读取加密密钥，也不增加网络请求。

开启后，主登录及共用凭证缓存使用 AES-256-GCM 加密。SDK 管理的主登录凭据由 bytedcli 的加密状态快照适配，不修改 SDK 或其依赖版本。每次写入使用随机 nonce；主密钥不写入凭证文件。

## 首版覆盖范围

| 存储入口                                     | 覆盖内容                                                                                                             |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| ByteCloud Auth SDK                           | 主登录用户凭证、refresh token、SDK 应用 AK/SK 和登录挑战                                                             |
| TokenStorage / SiteTokenStorage / PatStorage | 共用 token、PAT，以及 PatStorage 管理的应用配置                                                                      |
| CookieJar / AuthFileCache                    | SSO Cookie 和共用认证缓存；业务通过这些入口保存的缓存也随之加密                                                      |
| 主登录配套缓存                               | ByteCloud session JWT、JWT override、ZTI JWT、通用 auth 主入口创建的登录挑战及配套读写入口；Maxwell 创建入口例外见下 |

各业务独立保存的凭证暂不覆盖，包括独立的 AK/SK、应用 secret、派生 JWT、专用 session，以及 Meego/Feishu 的独立登录挑战。这些文件保持原来的存储方式，开启本开关不会自动加密它们。例如，FG 的共用 access-token 缓存受保护，但其独立 app secret 不受保护；主登录后自动生成的 Starling 业务 AK/SK 也仍按原方式保存。Codebase 的 PAT/共用应用配置受保护，独立的派生 JWT 缓存暂不覆盖。

Maxwell 发起的扫码登录挑战在创建阶段沿用原明文写入，不在首版加密承诺内；后续通用 auth 的 session 完成流程兼容读取原明文，等待确认时不回写，成功或过期后清理记录。XPA 继续使用共用 AuthFileCache，缓存仍随之加密；该模块保留原有刷新重试和错误包装，部分加解密失败可能显示为需要重新登录。

非敏感用户元信息、通用业务缓存、调用方提供的 JWT 文件、浏览器文件、显式导出文件及外部 CLI 的存储沿用各自格式。本开关不表示整个 profile 目录或所有业务凭证都已加密。

## 配置

| 环境变量                                  | 含义                                                                              |
| ----------------------------------------- | --------------------------------------------------------------------------------- |
| `BYTEDCLI_CREDENTIAL_ENCRYPTION_ENABLED`  | `1` 或 `true` 开启，默认关闭；`0` 或 `false` 关闭                                 |
| `BYTEDCLI_CREDENTIAL_ENCRYPTION_KEY`      | 可信宿主注入的主密钥，严格 base64 编码的 32 字节随机值                            |
| `BYTEDCLI_CREDENTIAL_ENCRYPTION_KEY_FILE` | 存有同一格式主密钥的绝对路径；POSIX 上文件须仅所有者可访问，例如 `0400` 或 `0600` |

开启时必须配置且只能配置一个密钥来源。密钥不接受命令行参数，以免进入 shell 历史或进程参数。

本地文件示例：

```bash
# 文件由可信管理员预先配置，内容为 base64 编码的 32 字节随机密钥。
export BYTEDCLI_CREDENTIAL_ENCRYPTION_ENABLED=1
export BYTEDCLI_CREDENTIAL_ENCRYPTION_KEY_FILE=/run/secrets/demo-credential-key
bytedcli --json auth status
```

## TCC 与受管宿主

rd-bot 等可信宿主可用自己的配置读取身份从 TCC 取得主密钥，并在创建 bytedcli 子进程时设置 `BYTEDCLI_CREDENTIAL_ENCRYPTION_KEY`。宿主负责密钥配置；bytedcli 负责凭证文件的加解密。

bytedcli 不使用当前用户的 TCC 业务接口获取此主密钥：该接口需要本地登录态，会形成先解密登录态才能取得解密密钥的启动循环。关闭开关时不读取 TCC 或密钥文件。

主密钥不应进入模型上下文、普通 Worker 环境、命令参数或日志。该能力保护静态文件内容，不提供同 UID/root 的进程隔离。

## SDK 状态与 Linux 内存文件系统

主登录 SDK 是独立进程，没有外部加密主密钥接口。bytedcli 使用 SDK 既有的 `baseDir` 参数，将它的工作目录放到 Linux `/dev/shm` 内存文件系统中；每次 SDK 调用完成后关闭该进程，将相对路径状态保存到加密快照，再清理内存目录。refresh token、应用 SK 和登录挑战仍由原 SDK 管理。

- 需要 SDK 的加密操作仅支持 Linux，并实际检查 `/dev/shm` 是 tmpfs。其他平台或缺少 tmpfs 时明确报错，不使用普通磁盘临时目录。默认关闭时各平台继续沿用原实现。
- 持久化快照位于当前 profile 的 `data/bytecloud-auth-vault.enc`；profile、用户目录和应用身份沿用原配置。主密钥不传给 SDK 子进程。
- 同 profile 的加密 SDK 操作通过已有进程文件锁串行执行；获取锁失败时不能跳过锁继续运行。登录挑战按原相对目录恢复，可跨 CLI 调用继续处理。
- 首次迁移前先停止同 profile 的旧 CLI/MCP 实例，不支持混用不同开关或密钥。旧 SDK 目录只在快照成功加密并验证后清理；密钥文件须放在 SDK 缓存目录之外。
- 快照提交完成后才认为本次持久化成功。进程被强制终止时，尚未提交的状态可能需要重新登录；正常完成或抛错时会关闭 SDK 并清理内存目录。

这条路径使用现有固定版本的 SDK，不需要修改、发布或升级 bytecloud-auth。

保护范围限于上表所列凭证文件。tmpfs 可能使用 swap；交换分区、进程转储和同 UID/root 对运行时数据的访问，需要由运行环境的安全策略控制。

## 迁移与失败行为

- 覆盖范围内原生缓存的旧明文可兼容读取，在开启后的下一次成功写入（例如刷新或重新登录）时原子转为密文。读取不回写，避免覆盖并发刷新的新凭证。未更新的原生旧缓存仍是明文；SDK 目录按上文整体迁移到加密快照。
- 覆盖范围内的读写遇到缺少密钥、格式错误、密文损坏或密钥不匹配会报错，不会退回明文写入，也不会用错误密钥覆盖已有密文。
- 关闭开关后，仍不能读取或覆盖已有密文。恢复读取需重新开启并提供原密钥；关闭开关不是数据解密或迁移操作。
- 更换密钥、密钥来源或开关后重启宿主创建的 CLI/MCP 进程。该接口不提供自动密钥轮换；已加密的数据需要保留原密钥。
- 凭证导入、导出继续遵循原格式和操作授权；显式导出的内容可能包含凭证，需要按原有秘密文件规则保管。

存储格式为 `bytedcli:enc:v1:` 加标准 base64 编码的 `nonce(12B) || ciphertext || tag(16B)`，AAD 为 `bytedcli:credential:v1`。使用固定测试向量验证认证解密。
