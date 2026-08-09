# Go 语言专属 Prompt

## 文档定位

本文件只承载本 skill 定制化的、基座模型未包含的 Go 单元测试规范和知识，主要涵盖：执行调度建议、产物风格约定，以及推荐模型按需加载 RAG 内容的场景。模型已知的 Go 基础知识不在此重复。

本文件中的内容依然遵循全局优先级规则：用户显式指令 > `AGENTS.md` / `CLAUDE.md` > 目标目录已有测试风格 > 本文件默认规则。

---

## 1. 执行调度
Go 的执行单元（编译和验证单位）是 **package**，不是单个文件或单个函数。
调度规则：

1. 按 package 串行处理。
2. 同一 package 内的多个目标函数一起生成/更新测试，统一维护 import、fixture 和 mock。
3. 当前 package 写入完成后，以 package 为单位验证和修复。
4. 当前 package 收敛后再进入下一个 package。

对每个被选中的 package，必须记录并在报告中沿用以下信息：

- package 导入路径或模块内相对路径
- 被选中的源文件、函数/方法、起始行
- 方法接收者类型
- 对应测试文件
- 实际执行的 `go test` 命令和工作目录

不要在仓库根目录强行执行跨模块 `go test ./...`。必须在目标 package 所属的最近 `go.mod` 目录下运行，package 参数使用模块内相对路径。

---

## 2. 默认测试约定

无现有测试风格可参考，且未发现用户或项目倾向时，使用以下默认约定：

| 项目 | 默认规则 |
| --- | --- |
| Package 名 | 无既有测试时使用源码 package 名 |
| 断言库 | `testing` + `github.com/stretchr/testify/assert` |
| Mock 框架 | `github.com/bytedance/mockey` |
| 测试命名 | `Test{Struct}{Method}_BitsUT` 或 `Test{Func}_BitsUT` |
| 测试文件 | 与源文件同目录的 `*_test.go`，优先追加到既有测试文件 |

---

## 3. mockey 注意事项

- 执行命令必须带 `-gcflags="all=-l -N"`，否则内联会导致 mock 不生效。

如需了解 mockey 框架或用法示例、解决报错时，建议通过 RAG 来获取相关参考知识。可以查询的内容包含：
- "mockey 核心 API 指南"
- "mockey 特定库(GORM、TOS、TCC、RocketMQ、Overpass、MongoDB、GoRedis 或 Hertz) mock 示例"
- "mockey 泛型函数、接口、嵌套/内嵌结构体方法"

---

## 4. 验证命令

```bash
go test -v -gcflags="all=-l -N" ./path/to/pkg
```

覆盖率（建议覆盖率文件放在 ${TMP_ROOT} 下）：

```bash
go test -v -gcflags="all=-l -N" -coverprofile=${TMP_ROOT}/coverage.out ./path/to/pkg
go tool cover -func=${TMP_ROOT}/coverage.out
```

---

## 5. 异常特殊处理建议

遇到以下异常场景时，带着报错信息和场景描述查询 RAG 获取修复方案：

| 异常场景 | RAG query 示例 |
| --- | --- |
| init 阶段 panic（通常由依赖包的 init() 失败导致） | `"go test init panic"` |
| 下载依赖包时因无代码权限而失败 | `"repository permission denied or access denied"` |
---

