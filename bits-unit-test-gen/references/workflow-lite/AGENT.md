---
name: workflow-lite
description: Lite Workflow — Single-agent lightweight mode, suitable for quick generation of a small number of local functions. No multi-agent dispatching, no targets directory or task.json. Generation and verification are completed directly within the main agent.
---

# Lite Workflow

This document defines the execution flow for **lite mode**. When the Orchestrator determines `workflow = lite`, it reads this document and executes accordingly.

Lite mode is a single-agent direct-output mode. It does not use multi-agent orchestration, does not write task.json, targets directory, or results directory. The main agent directly completes test generation (or fixing) and verification, and outputs the conversation summary directly from memory.

## Table of Contents

- [Preconditions](#preconditions)
- [Knowledge Loading](#knowledge-loading)
- [Execution Flow](#execution-flow)
  - [Step 2: Direct Generation and Verification](#step-2-direct-generation-and-verification)
  - [Step 3: Output Summary](#step-3-output-summary)
- [Key Differences from Pipeline Mode](#key-differences-from-pipeline-mode)

---

## Preconditions

The following conditions have been completed by the Orchestrator (SKILL.md Step 1) before entering this workflow:

- Environment setup complete (prepare_test.sh executed, TMP_ROOT created)
- Language-specific prompt determined (`assets/${LANG}/prompt.md`)
- Target function list determined (in memory, not written to targets directory)
- `MODE` (`default` / `fix_only`) and `DEFECT_DETECTION` (`basic` / `deep`) determined
- The following variables are available: `SKILL_ROOT`, `PROJECT_ROOT`, `TMP_ROOT`, `LANG`, `MODE`, `DEFECT_DETECTION`

---

## Knowledge Loading

In lite mode, documents are read **on-demand**. Do not read everything at the start. Each step specifies which documents to read:

| # | Document | When to Read | Content to Obtain |
|---|------|---------|---------|
| 1 | `assets/${LANG}/prompt.md` | Before Step 2 starts (during pre-check) | Language-specific rules: test conventions, mock framework, compile/run commands, code style, pre-check requirements, results JSON structure |
| 2 | `references/test-writer/AGENT.md` | When generating tests | Semantic review flow, generation strategy, test case planning, assertion & scenario naming conventions, hard constraints |
| 3 | `references/test-fixer/AGENT.md` | When performing verify-and-fix | Verify-and-fix strategy: verify-and-fix loop, failure triage flow, fix strategy, reflection mechanism, exit conditions |
| 4 | `references/code-reviewer/AGENT.md` | Only when `DEFECT_DETECTION=deep` | Deep defect mining checklist (extends the 4 basic checks in Writer Step 2) |
| 5 | `references/issue-severity-triage/AGENT.md` | Only when defects are found | Three-dimension classification flow (Impact Severity × Blast Radius × Trigger Probability → P0–P3) |
| 6 | `references/issue-severity-triage-refs/<category>.md` | Only when classification needs cross-validation; read the single file matching `bug_type` | P0–P3 anchors and secondary sub-categories for that category |

> In lite mode, there is no distinction between Writer/Fixer/Reviewer agent roles, but the rules and constraints defined in the corresponding documents MUST be **followed**.

---

## Execution Flow

### Step 2: Direct Generation and Verification

Do not write to the targets directory or dispatch subagents. Complete the work directly in the main agent based on `MODE`:

#### default Mode

For each function in the target function list:

1. **Pre-check**: Read `assets/${LANG}/prompt.md` and complete environment detection and project test pattern learning per the language-specific prompt's requirements (execute once for the first function)
2. **Context analysis**: Read the target function source code and its dependency context (see the context analysis requirements in the language-specific prompt)
3. **Generate tests**: Read `references/test-writer/AGENT.md` and generate test code per its workflow
   - Execute generation strategy decision (no existing tests → generate from scratch; existing tests → incremental supplement)
   - Perform semantic review (Step 2 in Writer): establish expected semantics, then check implementation consistency (basic mode: 4 high-signal patterns; deep mode: full code-reviewer checklist)
   - Design test cases based on the semantic anchor, generate test code and write to the test file
   - For p0/p1 defects: generate defect-probing cases with assertions reflecting correct expected behavior
4. **Verify-and-fix**: Read `references/test-fixer/AGENT.md` and verify/fix per its workflow
   - Execute the run tests → failure triage → fix loop
   - Follow the verify-and-fix round limit defined in the language-specific prompt
   - Follow the Fixer's failure triage flow and defect determination criteria
   - Defect-probing cases that fail due to confirmed production bugs are preserved, not fixed

> Steps 3-4 above are organized per the minimum execution unit granularity defined in the language-specific prompt. For example, Go uses packages as units — functions within the same package are generated individually first, then compiled and verified/fixed together.

#### fix_only Mode

Skip the generation step; directly perform verify-and-fix on existing tests for the target functions:

1. **Pre-check**: Read `assets/${LANG}/prompt.md`, same as default mode
2. **Locate existing tests**: Find existing test files and test functions corresponding to target functions
3. **Verify-and-fix**: Read `references/test-fixer/AGENT.md` and verify/fix per its workflow

---

### Step 3: Output Summary

> `utree flush` has been executed uniformly by SKILL.md Step 3.2; no need to repeat here.

**Conversation output summary**: Directly from memory, aggregate test-file and defect details collected during Step 2, and provide a concise conversation summary organized by test file dimension. See the "Conversation Output Rules" in `references/output-contract/FORMATS.md` for display rules.

> Output SHOULD be compact — omit the defects section if no defects are found.
> Lite mode does NOT write `${TMP_ROOT}/results/` JSON files. All execution state is kept in agent memory.

---

## Key Differences from Pipeline Mode

| Dimension | Lite | Pipeline |
|------|------|----------|
| Agent architecture | Single agent completes directly | Orchestrator dispatches Writer + Fixer |
| task.json | Not needed | Required |
| targets/ directory | Not needed | Required |
| results/ directory | Not needed | Required |
| utree flush | Required | Required |
| Artifact check | None (output directly from memory) | Full artifact check (see ARTIFACTS.md) |
