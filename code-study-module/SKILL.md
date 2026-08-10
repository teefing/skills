---
name: code-study-module
description: Use only when the user explicitly invokes `code-study-module` or `$code-study-module` to study a named code module and produce a readable source-linked architecture/code-reading document. Do not trigger this skill implicitly for ordinary code analysis, reviews, debugging, or implementation tasks. The user must provide a module name; if they do not, ask for it before doing any research.
---

# Code Study Module

Use this skill to turn a codebase investigation for a specified module into a teachable, source-linked document. The goal is not to dump every related file. The goal is to help a human reader understand how the module works from the most useful runtime or ownership path, while still giving enough external framework context to avoid mystery.

This skill is explicitly invoked only. If the user asks for code study but does not name `code-study-module`, do not use this skill.

## Intake

Before reading code, settle these inputs:

1. **Module name is required.** If the user did not provide a concrete module name, ask for it and stop. Examples: `activity_tab`, `payment_router`, `outfit_tab`, `FeedTabCampaignFragment`.
2. **Motivation or focus is optional.** If missing, ask whether the user wants to add a reading motivation or focus, such as "for onboarding", "compare with another module", "find a lightweight replacement path", or "understand lifecycle and data source". If they decline, proceed with a general architecture/code-reading study.
3. **Output directory is configurable.** Default to `<project-root>/docs/<module-name>/`. Before writing, ask whether the user wants to change it. If they accept the default or provide a new path, continue.

Keep the intake compact. A good combined question is:

```text
我会分析模块 `<module>`，默认输出到 `<project-root>/docs/<module>/`。
开始前你要补充本次阅读动机/侧重点吗？输出目录需要更改吗？
```

Do not start the code study until the required module name is known and the output directory question has been answered.

## Respect The Repository

Work inside the current project unless the user points elsewhere.

- Detect the project root with `git rev-parse --show-toplevel` when possible; otherwise use the current working directory.
- Read local agent/contributor instructions before entering a subtree when the repo has files such as `AGENTS.md`, `CONTRIBUTING.md`, or nearby ownership docs.
- Prefer `rg` and `rg --files` for source discovery.
- Do not run builds, tests, app launches, migrations, or network commands unless the user explicitly asks or the repository instructions require them for the requested output.
- Treat generated docs as source artifacts: update them with normal file-edit discipline and do not revert unrelated user changes.

## Research Workflow

### 1. Locate the module by evidence

Search the literal module name, common naming variants, registrations, config keys, route names, service interfaces, and file/class names. Record candidates, then narrow to the smallest set that actually explains the module.

For a module with framework integration, separate:

- **Main module logic:** the classes/functions owned by the module that implement its behavior.
- **Framework support:** generic host systems that instantiate, mount, route, schedule, or dispatch callbacks to the module.
- **Data/config inputs:** config fields, schemas, service data, generated metadata, or remote/local data that influence behavior.
- **Rendering/container/output:** the final UI, API response, job, command, or side effect the module produces.

Also identify the module's **codebase macro structure** before writing the mainline:

- top-level components/packages/directories that make up the module;
- which parts are API/contract, common model/data, runtime implementation, resources, tests, generated code, or legacy/read-only surfaces;
- feature-domain slices inside the module, such as `framework`, `service`, `routing`, `data`, `ui`, `jobs`, `adapters`, or business-specific domains;
- ownership or modification boundaries when local instructions say a component is sealed, deprecated, generated, or only for reference.

This macro map is not a file dump. Keep it small and explanatory: enough that a reader knows where to jump first and which directories to avoid editing.

### 2. Find the reader-friendly entry point

Choose a concrete entry point that best explains the module. Usually this is the function/class where the module becomes visible at runtime: a controller action, Fragment factory, service method, route handler, command handler, task entry, adapter, plugin registration, or public API.

Avoid starting with a broad module inventory. A module list is useful after the reader understands the main flow.

Avoid rhetorical teaching gimmicks such as "the best first question is..." unless the user explicitly likes that style. Prefer direct prose:

```text
理解 `<module>` 可以先从 `<EntryPoint>` 开始，因为这里决定了它最终创建/输出/承接什么。
```

### 3. Build the mainline first

Write down the shortest true chain from input to output. Then expand one branch at a time.

Good shapes:

```text
config / request / event
  -> module registration or lookup
  -> primary module class/function
  -> data preparation
  -> output/container/side effect
```

For Android, the chain may look like `tab config -> BaseHomeTab -> fragment() -> Fragment -> container`. For backend code, it may look like `route -> handler -> service -> repository -> response`. For CLIs, it may look like `command -> parser -> executor -> output`.

When writing a chain, make the process easy to follow: name who calls whom, what value or object crosses the boundary, and what the next step produces. Each important logic step, callback path, data-flow edge, routing edge, or container-selection edge should have a nearby source link with a visible line number. Avoid long arrow chains that are not anchored to source code.

### 4. Keep external framework context proportional

When the module depends on a complex framework, add just enough context to explain how the module is mounted or called. Do not let framework internals take over the section that is supposed to explain the module.

Use a short "context capsule" near the relevant mainline section:

- what framework object holds or calls the module;
- where the module is stored or registered;
- which callback or method crosses the boundary;
- how this differs from a similarly named platform concept, if readers may confuse them.

Keep the capsule short unless the user asks for a deep framework study. The module remains the protagonist.

## Document Output

Create Markdown under the chosen output directory. Use one primary document unless the user asks for multiple files. A good default filename is `<module-name>_architecture.md`.

### Required document qualities

- The document should be readable for someone learning the code, not just a file map.
- Include a source-linked codebase macro structure section near the front, before or immediately after the runtime overview.
- In that macro section, module/component/directory names should be Markdown links to real local paths, not plain backticked names only.
- The macro section should cover the whole named module's code organization, not only the parts the user happened to mention.
- Start from the concrete mainline and expand outward.
- Include a full-chain diagram early when it helps orientation.
- Embed source links inside the architectural discussion. Do not put all source references in a detached appendix.
- Logic, lifecycle/callback paths, request/data flows, routing decisions, and container-selection chains should cite the corresponding source file and line near the explanation itself.
- Every referenced source filename in prose or tables should be a Markdown link to the real local file.
- Use line numbers in visible text, for example `（L139）`, and verify that linked files exist.
- Flow descriptions should be clear enough to follow without opening every file: state the trigger/input, the current owner, the called method or handoff, and the produced output/state.
- Explain value provenance: where key fields, types, config values, IDs, routes, or schema values come from before saying how they are used.
- Mark uncertain claims as inference and separate them from confirmed source facts.
- Avoid over-weighting external framework internals. Add proportional context, then return to the module.

### Recommended structure

Adapt the structure to the module, but this order usually works:

1. **Document Snapshot**
   - project root;
   - branch;
   - HEAD;
   - HEAD time and subject;
   - document update time;
   - note about source link style and whether docs are ignored.
2. **Codebase Macro Structure**
   - source-linked component/package/directory map for the whole named module;
   - API/common/implementation/resource/test/generated or legacy boundaries;
   - feature-domain slices and their responsibilities;
   - modification/read-only/deprecated boundaries from local instructions.
3. **Runtime/Mainline Overview**
   - the shortest true chain;
   - source references for the key chain edges;
   - a diagram if useful;
   - one-paragraph summary of what the module is and is not.
4. **Primary Entry Point**
   - the central class/function;
   - why it is the best place to start reading;
   - source-linked responsibilities.
5. **Core Flow**
   - lifecycle/callback/request/data-flow table for the module-owned logic;
   - source-linked rows for important logic and chain steps;
   - include small framework context only where the callback source would otherwise be unclear.
6. **Data And Configuration**
   - where inputs come from;
   - how values are transformed;
   - defaults, compatibility mappings, and fallbacks.
7. **Rendering / Container / Output**
   - final Fragment/View/API response/job output/etc.;
   - container or adapter choices and their source of truth.
8. **Capabilities And Complexity**
   - optional abilities, events, timers, caching, monitoring, hot updates, or cleanup.
9. **Detailed Module Map**
   - optional deeper map after the reader knows the flow, if the early macro map stayed intentionally compact.
10. **Suggested Reading Order**
   - source-linked sequence for a human reader.
11. **Takeaways**
   - practical conclusions, tradeoffs, and what to reuse or avoid if relevant.

Do not force every heading if the module is small. Prefer a smaller, clearer document over a template-shaped document.

## Source Link Policy

Use links that the local Markdown renderer can open. In local repository docs, absolute file paths are usually the safest:

```markdown
[ActivityHomeTab.kt](/abs/path/to/ActivityHomeTab.kt)（L139）
```

If the repository already has a working convention, follow it. After writing, verify every linked file path exists. If line-specific links are not reliably clickable in the user's environment, keep the file link clickable and put the line number in nearby text.

## Self-Review Before Delivery

After producing the document, review it before telling the user it is done.

Check for:

- **Unclear claims:** Replace vague phrases like "maybe", "probably", "some logic", or "the framework handles it" with either source-backed facts or explicit "inference" labels.
- **Missing macro map:** If the document lacks an early codebase macro structure section, add one unless the module is truly a single-file/single-package case.
- **Unlinked module names:** In the macro map, replace plain module/directory names with Markdown links to real local paths.
- **Too-narrow macro map:** If the macro section only covers the slices mentioned in the user's prompt, expand it to cover the named module's overall code organization.
- **Missing provenance:** If a key value appears, explain where it came from before explaining how it is consumed.
- **Unanchored logic or chain claims:** If a flow, callback, route, data transformation, or container choice is described without a nearby source link and line number, add one or soften the claim.
- **Unclear process description:** If a reader cannot tell the trigger, current owner, handoff method, and output for a flow step, rewrite the step before delivery.
- **Overgrown framework detours:** If an external framework section interrupts the module story, compress it into a context capsule and move on.
- **Module-list-first drift:** If the doc begins as a directory inventory, restructure it around the mainline entry point.
- **Detached source index:** If source links live only in a separate section, move important links into the relevant analysis paragraphs or tables.
- **Broken file links:** Verify every linked file exists.
- **Overly verbose writing:** Remove repeated explanations, generic background, and paragraphs that do not help the reader navigate source code.
- **Missing output promise:** Ensure the final answer names the generated document path and summarizes the main additions.

Make fixes from this review before responding.

## Final Response

Keep the final response short. Include:

- the document path;
- what was covered;
- what verification/self-review was performed;
- any skipped verification, such as builds or tests not requested.

If evals were not run for the skill itself, say that explicitly when creating or modifying this skill.
