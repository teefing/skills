#!/usr/bin/env node

/**
 * Deterministic final-report gate.
 *
 * It validates the fixed eight-column five-tuple table before publication and,
 * when a docs +fetch JSON response is supplied, compares the persisted table
 * against the local renderer output. It never performs network requests.
 */

import { Buffer } from "node:buffer";
import fs from "node:fs";
import process from "node:process";

const EXPECTED_HEADERS = [
  "PSM",
  "Method",
  "Outbound PSM",
  "Outbound Method",
  "Diff Path",
  "Diff Value",
  "修复建议",
  "Diff 链接",
];
const ALLOWED_SUGGESTIONS = new Set([
  "add_noise_template",
  "set_time_offset",
  "update_array_match",
  "outbound_mock_unmatched",
  "undecided",
]);
const SENSITIVE_DIFF_PATH_TOKENS = new Set([
  "authorization",
  "address",
  "bankaccount",
  "birthdate",
  "birthday",
  "cardnumber",
  "cookie",
  "cvv",
  "did",
  "dob",
  "email",
  "idcard",
  "iban",
  "jwt",
  "mobile",
  "password",
  "passport",
  "phone",
  "secret",
  "session",
  "signature",
  "ssn",
  "ticket",
  "token",
  "uid",
]);
const SENSITIVE_ID_PREFIX_TOKENS = new Set([
  "account",
  "buyer",
  "customer",
  "device",
  "merchant",
  "order",
  "product",
  "seller",
  "shop",
  "user",
]);
const SENSITIVE_NAME_PREFIX_TOKENS = new Set([
  "buyer",
  "consignee",
  "contact",
  "customer",
  "recipient",
  "seller",
  "user",
]);
const ALWAYS_CREDENTIAL_FIELD_TOKENS = new Set(["password", "passwd", "secret"]);
const CREDENTIAL_METADATA_FIELD_NAMES = new Set(["authorizationstatus", "credentialtype"]);
const CONTEXTUAL_CREDENTIAL_FIELD_TOKENS = new Set(["credential", "credentials", "authorization"]);
const COMPACT_CREDENTIAL_KEY_TOKENS = new Set(["privatekey", "accesskey", "apikey"]);
const CREDENTIAL_KEY_FOLLOWERS = new Set([
  "bytes",
  "content",
  "data",
  "header",
  "id",
  "material",
  "pem",
  "secret",
  "token",
  "value",
]);
const CREDENTIAL_KEY_PREFIXES = new Set([
  "access",
  "api",
  "client",
  "encryption",
  "private",
  "signing",
]);
const CREDENTIAL_FIELD_SUFFIXES = [
  "token",
  "jwt",
  "cookie",
  "session",
  "sessionid",
  "sessiontoken",
  "signature",
  "sig",
  "ticket",
  "csrf",
  "csrftoken",
  "otp",
  "authcode",
  "authurl",
  "authaddr",
  "pwd",
  "passphrase",
  "passcode",
  "clientkey",
  "signingkey",
  "encryptionkey",
  "secret",
];
const CREDENTIAL_VALUE_TOKENS = new Set([
  "token",
  "jwt",
  "cookie",
  "session",
  "signature",
  "sig",
  "ticket",
  "csrf",
  "otp",
  "auth",
  "pwd",
  "passphrase",
  "passcode",
]);
const CREDENTIAL_TOKEN_FOLLOWERS = new Set(["header", "value"]);
const REDACTED_BODY_FIELD_NAMES = new Set([
  "authorization",
  "codebasetoken",
  "cookie",
  "credential",
  "credentials",
  "deviceid",
  "did",
  "email",
  "envvalue",
  "envvariables",
  "mobile",
  "mobilenum",
  "privatekey",
  "titanpassportid",
  "uid",
  "uids",
  "userid",
]);
const EXACT_ONLY_REDACTED_BODY_FIELD_NAMES = new Set(["user_name"]);
const FTF_PAGE_ORIGINS = {
  cn: "https://tesla-x.bytedance.net",
  "i18n-tt": "https://tesla-x-us.tiktok-row.net",
  zg: "https://tesla-x-zg.bytedance.net",
};
const TERMINAL_CONTROL_PATTERN =
  // eslint-disable-next-line no-control-regex
  /\u001b\][^\u0007\u001b]*(?:\u0007|\u001b\\)?|\u001b\[[0-9;?]*[ -/]*[@-~]|\u001b[@-Z\\-_]|[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]/gu;

function fail(message, details = {}) {
  throw new Error(
    JSON.stringify({ code: "FTF_REMEDIATION_REPORT_GATE_FAILED", message, ...details }),
  );
}

function parseArgs(argv) {
  const args = {};
  for (let index = 2; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith("--")) fail(`Unexpected argument: ${value}`);
    const key = value.slice(2);
    const next = argv[index + 1];
    if (!next || next.startsWith("--")) fail(`Missing value for --${key}`);
    args[key] = next;
    index += 1;
  }
  if (!args.markdown || !args.plan) {
    fail("Both --markdown and --plan are required.");
  }
  return args;
}

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (error) {
    fail(`Unable to read JSON: ${file}`, { cause: String(error) });
  }
}

function stripOuterPipes(line) {
  let value = line.trim();
  if (value.startsWith("|")) value = value.slice(1);
  if (value.endsWith("|") && !value.endsWith("\\|")) value = value.slice(0, -1);
  return value;
}

function splitMarkdownRow(line) {
  const source = stripOuterPipes(line);
  const cells = [];
  let cell = "";
  let escaped = false;
  for (const character of source) {
    if (character === "|" && !escaped) {
      cells.push(cell.trim());
      cell = "";
      continue;
    }
    if (character === "\\" && !escaped) {
      escaped = true;
      cell += character;
      continue;
    }
    escaped = false;
    cell += character;
  }
  cells.push(cell.trim());
  return cells;
}

function normalizeCell(value) {
  return value
    .replace(/\[([^\]]+)\]\(\s*<([^>]+)>\s*\)/gu, "$1 ($2)")
    .replace(/\[([^\]]+)\]\(\s*([^)]+)\s*\)/gu, "$1 ($2)")
    .replace(/\\([|`*_[\]{}()#+\-.!>])/gu, "$1")
    .replace(/\s+/gu, " ")
    .trim();
}

function markdownEscape(value) {
  return sanitizeLine(value)
    .replace(/\\/gu, "\\\\")
    .replace(/([`*_[\]{}()#+\-.!|>])/gu, "\\$1");
}

function isTableSeparator(line) {
  const cells = splitMarkdownRow(line);
  return (
    cells.length === EXPECTED_HEADERS.length &&
    cells.every((cell) => /^:?-{3,}:?$/u.test(cell.trim()))
  );
}

function isExpectedHeader(line) {
  const cells = splitMarkdownRow(line);
  return (
    cells.length === EXPECTED_HEADERS.length &&
    cells.every((cell, index) => normalizeCell(cell) === EXPECTED_HEADERS[index])
  );
}

function findTable(content, { requireHeading = true } = {}) {
  const lines = content.split(/\r?\n/u);
  let headerIndex = lines.findIndex(isExpectedHeader);
  if (headerIndex < 0) {
    fail("The fixed eight-column five-tuple header was not found.", {
      expected_headers: EXPECTED_HEADERS,
    });
  }
  if (requireHeading) {
    const headingIndex = lines.findIndex((line) => /^##\s+五元组下钻\s*$/u.test(line.trim()));
    if (headingIndex < 0 || headingIndex > headerIndex) {
      fail("The five-tuple table must appear under the ## 五元组下钻 section.");
    }
    const fullAnalysisIndex = lines.findIndex((line) =>
      /^##\s+接口级全量分析\s*$/u.test(line.trim()),
    );
    if (fullAnalysisIndex < 0 || fullAnalysisIndex > headingIndex) {
      fail("接口级全量分析 must precede the five-tuple section.");
    }
  }
  const rows = [];
  while (headerIndex >= 0) {
    if (!isTableSeparator(lines[headerIndex + 1] ?? "")) {
      fail("The five-tuple table separator is invalid or has the wrong column count.");
    }
    let nextIndex = headerIndex + 2;
    let blockRows = 0;
    for (; nextIndex < lines.length; nextIndex += 1) {
      const line = lines[nextIndex].trim();
      if (!line.startsWith("|")) break;
      const cells = splitMarkdownRow(line);
      if (cells.length !== EXPECTED_HEADERS.length) {
        fail("A five-tuple row does not have exactly eight cells.", {
          line: nextIndex + 1,
          cells: cells.length,
        });
      }
      rows.push(cells);
      blockRows += 1;
    }
    if (blockRows === 0) fail("The five-tuple table has no data rows.");
    while (nextIndex < lines.length && lines[nextIndex].trim() === "") nextIndex += 1;
    headerIndex =
      isExpectedHeader(lines[nextIndex] ?? "") && isTableSeparator(lines[nextIndex + 1] ?? "")
        ? nextIndex
        : -1;
  }
  if (rows.length === 0) fail("The five-tuple table has no data rows.");
  return { headers: EXPECTED_HEADERS, rows };
}

function queryForFinding(plan, finding) {
  return plan.repair_denoise?.queries?.find(
    (query) =>
      query.cluster_id === finding.cluster_id &&
      query.psm_task_id === finding.psm_task_id &&
      query.psm === finding.psm &&
      query.method === finding.method &&
      query.direction === finding.direction,
  );
}

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function sanitizeLine(value) {
  return value.replace(TERMINAL_CONTROL_PATTERN, "").replace(/[\t\r\n\u2028\u2029]+/gu, " ");
}

function boundedText(value, maxLength = 320) {
  const normalized = sanitizeLine(value).replace(/\s+/gu, " ").trim();
  return normalized.length <= maxLength ? normalized : `${normalized.slice(0, maxLength - 3)}...`;
}

function textValue(value, fallback) {
  if (typeof value !== "string") return fallback;
  const normalized = boundedText(value);
  return normalized || fallback;
}

function decodeValue(value) {
  let decoded = value;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const next = decodeURIComponent(decoded);
      if (next === decoded) break;
      decoded = next;
    } catch {
      break;
    }
  }
  return decoded;
}

function fieldTokens(value) {
  return decodeValue(value)
    .replace(/([a-z\d])([A-Z])/gu, "$1_$2")
    .replace(/([A-Z]+)([A-Z][a-z])/gu, "$1_$2")
    .toLowerCase()
    .split(/[^a-z\d]+/gu)
    .filter(Boolean);
}

function isCredentialLikeFieldName(value) {
  const decodedLower = decodeValue(value).toLowerCase();
  if (/^(?:__host_)?bd_sso(?:_|$)|^bdsso_lt(?:_|$)/u.test(decodedLower)) return true;
  const tokens = fieldTokens(value);
  const normalized = tokens.join("");
  if (CREDENTIAL_METADATA_FIELD_NAMES.has(normalized)) return false;
  const hasCredentialKeyPair = tokens.some(
    (token, index) =>
      CREDENTIAL_KEY_PREFIXES.has(token) &&
      tokens[index + 1] === "key" &&
      (index + 2 === tokens.length || CREDENTIAL_KEY_FOLLOWERS.has(tokens[index + 2] ?? "")),
  );
  return (
    tokens.some((token) => ALWAYS_CREDENTIAL_FIELD_TOKENS.has(token)) ||
    tokens.some(
      (token, index) =>
        COMPACT_CREDENTIAL_KEY_TOKENS.has(token) &&
        (index === tokens.length - 1 || CREDENTIAL_KEY_FOLLOWERS.has(tokens[index + 1] ?? "")),
    ) ||
    hasCredentialKeyPair ||
    CREDENTIAL_FIELD_SUFFIXES.some(
      (suffix) => normalized === suffix || normalized.endsWith(suffix),
    ) ||
    tokens.some(
      (token, index) =>
        CREDENTIAL_VALUE_TOKENS.has(token) &&
        CREDENTIAL_TOKEN_FOLLOWERS.has(tokens[index + 1] ?? ""),
    ) ||
    tokens.some((token) => CONTEXTUAL_CREDENTIAL_FIELD_TOKENS.has(token))
  );
}

function redactBodyValue(value) {
  if (value === null || typeof value !== "object") return value;
  if (Array.isArray(value)) return value.map(redactBodyValue);
  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => {
      const normalized = fieldTokens(key).join("");
      return [
        key,
        EXACT_ONLY_REDACTED_BODY_FIELD_NAMES.has(decodeValue(key).toLowerCase()) ||
        isCredentialLikeFieldName(key) ||
        REDACTED_BODY_FIELD_NAMES.has(normalized)
          ? "[REDACTED]"
          : redactBodyValue(item),
      ];
    }),
  );
}

function safeHttpUrl(value) {
  if (typeof value !== "string" || value.trim() === "") return undefined;
  try {
    const url = new URL(sanitizeLine(value));
    return url.protocol === "https:" || url.protocol === "http:" ? url.toString() : undefined;
  } catch {
    return undefined;
  }
}

function normalizeDiffLinkCell(value) {
  if (normalizeCell(value) === "链接不可用") return "链接不可用";
  const angleTarget = value.match(/\[[^\]]+\]\(\s*<([^>]+)>\s*\)/u)?.[1];
  const markdownTarget = value.match(/\[[^\]]+\]\(\s*([^)]+)\s*\)/u)?.[1];
  const bareTarget = value.match(/https?:\/\/\S+/u)?.[0];
  return safeHttpUrl(angleTarget ?? markdownTarget ?? bareTarget) ?? normalizeCell(value);
}

function flowDiffUrlFromContext(context) {
  if (
    !isRecord(context) ||
    !context.space_id ||
    !context.protocol ||
    !context.log_id ||
    !context.method ||
    !context.similar_diff_id
  ) {
    return undefined;
  }
  const origin = FTF_PAGE_ORIGINS[context.site];
  if (!origin) return undefined;
  const methodBase64 = Buffer.from(String(context.method), "utf8").toString("base64");
  return `${origin}/space/${encodeURIComponent(String(context.space_id))}/f_app/task/new/diff/${encodeURIComponent(String(context.task_id))}/${encodeURIComponent(String(context.psm_task_id))}/${encodeURIComponent(methodBase64)}/${encodeURIComponent(String(context.protocol))}/${encodeURIComponent(String(context.log_id))}/${encodeURIComponent(String(context.similar_diff_id))}`;
}

function flowDiffCell(finding) {
  const url =
    safeHttpUrl(finding.flow_diff_url) ??
    safeHttpUrl(flowDiffUrlFromContext(finding.diff_link_context));
  return url ?? "链接不可用";
}

function isSensitiveDiffPath(value) {
  if (isCredentialLikeFieldName(value)) return true;
  const tokens = decodeValue(value)
    .replace(/([a-z\d])([A-Z])/gu, "$1 $2")
    .toLowerCase()
    .split(/[^a-z\d]+/gu)
    .filter(Boolean);
  return tokens.some(
    (token, index) =>
      SENSITIVE_DIFF_PATH_TOKENS.has(token) ||
      (token === "id" && index > 0 && SENSITIVE_ID_PREFIX_TOKENS.has(tokens[index - 1])) ||
      (token === "name" && index > 0 && SENSITIVE_NAME_PREFIX_TOKENS.has(tokens[index - 1])) ||
      (token === "card" && (tokens[index - 1] === "id" || tokens[index + 1] === "number")) ||
      (token === "account" && tokens[index - 1] === "bank"),
  );
}

function renderValue(value, sensitive) {
  if (value === undefined) return "未返回";
  if (value === null) return "null";
  if (sensitive) return "[敏感值已脱敏]";
  const parsed =
    typeof value === "string"
      ? (() => {
          try {
            return JSON.parse(value);
          } catch {
            return value;
          }
        })()
      : value;
  const redacted = redactBodyValue(parsed);
  const rendered = typeof redacted === "string" ? redacted : JSON.stringify(redacted);
  return boundedText(String(rendered), 120);
}

function renderDiffValues(detail, diffPath) {
  if (!detail || !Array.isArray(detail.diff_value_list) || detail.diff_value_list.length === 0) {
    return "repair denoise 未返回 diff_value_list";
  }
  const sensitive = isSensitiveDiffPath(diffPath);
  const rendered = detail.diff_value_list
    .slice(0, 3)
    .map((item) =>
      isRecord(item)
        ? `base: ${renderValue(item.base_value ?? item.baseValue, sensitive)}; replay: ${renderValue(item.replay_value ?? item.replayValue, sensitive)}`
        : renderValue(item, sensitive),
    );
  const count =
    Number.isSafeInteger(detail.diff_value_count) &&
    detail.diff_value_count >= detail.diff_value_list.length
      ? detail.diff_value_count
      : detail.diff_value_list.length;
  if (count > 3) {
    const retained =
      detail.diff_values_truncated === true
        ? `，JSON 保留前 ${String(detail.diff_value_list.length)} 组`
        : "";
    rendered.push(`...共 ${String(count)} 组${retained}`);
  }
  return rendered.join("<br>");
}

function detailSuggestion(detail, finding) {
  return ALLOWED_SUGGESTIONS.has(detail?.denoise_op_type)
    ? detail.denoise_op_type
    : finding.repair_suggestion;
}

function expectedRows(plan) {
  return plan.findings.flatMap((finding) => {
    const query = queryForFinding(plan, finding);
    const details = Array.isArray(query?.details)
      ? query.details.filter(isRecord)
      : isRecord(query?.details)
        ? [query.details]
        : [];
    return (details.length > 0 ? details : [null]).map((detail) => {
      const diffPath = textValue(detail?.noise_key, finding.diff_path);
      let diffValue = renderDiffValues(detail, diffPath);
      if (query?.status === "failed") {
        diffValue = `获取失败：${query.error?.message ?? "repair denoise dry-run 未返回错误原因"}`;
      } else if (query?.status === "skipped") {
        diffValue = `已跳过：${query.reason ?? "repair denoise dry-run 未返回跳过原因"}`;
      }
      const cells = [
        finding.psm,
        textValue(detail?.method, finding.method),
        textValue(detail?.outbound_psm, finding.outbound_psm ?? "无"),
        textValue(detail?.outbound_method, finding.outbound_method ?? "无"),
        diffPath,
        diffValue,
        detailSuggestion(detail, finding),
        flowDiffCell(finding),
      ];
      return {
        finding_id: finding.id,
        cells: cells.map((cell, index) =>
          index === 7
            ? normalizeDiffLinkCell(String(cell))
            : normalizeCell(
                index === 5
                  ? String(cell).split("<br>").map(markdownEscape).join("<br>")
                  : markdownEscape(String(cell)),
              ),
        ),
      };
    });
  });
}

function firstMismatch(expected, rows) {
  const closest =
    rows
      .map((row) => ({
        row,
        matches: row.reduce(
          (count, cell, index) => count + (cell === expected.cells[index] ? 1 : 0),
          0,
        ),
      }))
      .sort((left, right) => right.matches - left.matches)[0]?.row ?? [];
  const columnIndex = expected.cells.findIndex((cell, index) => cell !== closest[index]);
  if (columnIndex < 0) return undefined;
  const column = EXPECTED_HEADERS[columnIndex];
  const expectedValue = expected.cells[columnIndex];
  const actualValue = closest[columnIndex] ?? "";
  return column === "Diff Value"
    ? {
        finding_id: expected.finding_id,
        column,
        expected_length: expectedValue.length,
        actual_length: actualValue.length,
      }
    : {
        finding_id: expected.finding_id,
        column,
        expected: expectedValue,
        actual: actualValue,
      };
}

function validateLocalTable(table, plan) {
  const expected = expectedRows(plan);
  const expectedRowCount = expected.length;
  if (table.rows.length !== expectedRowCount) {
    fail("Five-tuple row count does not match expanded finding/detail count.", {
      actual_rows: table.rows.length,
      expected_rows: expectedRowCount,
    });
  }
  table.rows.forEach((row, index) => {
    const [psm, method, outboundPsm, outboundMethod, diffPath, diffValue, suggestion, diffLink] =
      row.map(normalizeCell);
    if (!psm || !method || !outboundPsm || !outboundMethod || !diffPath || !diffValue) {
      fail("A five-tuple row has an empty required cell.", { row: index + 1 });
    }
    if (!ALLOWED_SUGGESTIONS.has(suggestion)) {
      fail("A five-tuple row has an invalid repair suggestion.", {
        row: index + 1,
        suggestion,
      });
    }
    const hasMarkdownLink = /\[[^\]]+\]\(\s*(?:<)?https?:\/\//u.test(row[7]);
    const hasBareUrl = /https?:\/\/\S+/u.test(row[7]);
    if (diffLink !== "链接不可用" && !hasMarkdownLink && !hasBareUrl) {
      fail("A five-tuple row has an invalid Diff link cell.", { row: index + 1 });
    }
  });
  const unmatchedRows = table.rows.map((row) =>
    row.map((cell, index) => (index === 7 ? normalizeDiffLinkCell(cell) : normalizeCell(cell))),
  );
  const missingFindings = [];
  let mismatch;
  for (const item of expected) {
    const rowIndex = unmatchedRows.findIndex((row) =>
      row.every((cell, index) => cell === item.cells[index]),
    );
    if (rowIndex < 0) {
      missingFindings.push(item.finding_id);
      mismatch ??= firstMismatch(item, unmatchedRows);
    } else {
      unmatchedRows.splice(rowIndex, 1);
    }
  }
  if (missingFindings.length > 0 || unmatchedRows.length > 0) {
    fail("Five-tuple rows do not match the expanded finding/detail content.", {
      missing_findings: missingFindings,
      unexpected_rows: unmatchedRows.length,
      ...(mismatch ? { first_mismatch: mismatch } : {}),
    });
  }
  return { expected_rows: expectedRowCount, actual_rows: table.rows.length };
}

function extractFetchedContent(value) {
  const content = value?.data?.document?.content ?? value?.document?.content;
  if (typeof content !== "string") fail("docs +fetch JSON does not contain data.document.content.");
  return content;
}

function compareReadback(localTable, fetchedTable) {
  if (localTable.rows.length !== fetchedTable.rows.length) {
    fail("Feishu readback row count differs from the local report.", {
      local_rows: localTable.rows.length,
      feishu_rows: fetchedTable.rows.length,
    });
  }
  for (let rowIndex = 0; rowIndex < localTable.rows.length; rowIndex += 1) {
    for (let columnIndex = 0; columnIndex < EXPECTED_HEADERS.length; columnIndex += 1) {
      const local = normalizeCell(localTable.rows[rowIndex][columnIndex]);
      const remote = normalizeCell(fetchedTable.rows[rowIndex][columnIndex]);
      if (local !== remote) {
        fail("Feishu readback cell differs from the local report.", {
          row: rowIndex + 1,
          column: EXPECTED_HEADERS[columnIndex],
          local_length: local.length,
          remote_length: remote.length,
        });
      }
    }
  }
  return {
    rows_compared: localTable.rows.length,
    cells_compared: localTable.rows.length * EXPECTED_HEADERS.length,
  };
}

function main() {
  const args = parseArgs(process.argv);
  const markdown = fs.readFileSync(args.markdown, "utf8");
  const plan = readJson(args.plan);
  const localTable = findTable(markdown);
  const local = validateLocalTable(localTable, plan);
  const result = {
    ok: true,
    gate: "ftf-remediation-report",
    fixed_headers: EXPECTED_HEADERS,
    local,
    feishu_readback: null,
  };
  if (args["lark-json"]) {
    const fetched = readJson(args["lark-json"]);
    const remoteTable = findTable(extractFetchedContent(fetched), { requireHeading: false });
    result.feishu_readback = compareReadback(localTable, remoteTable);
  }
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

try {
  main();
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
}

export { EXPECTED_HEADERS, compareReadback, findTable, normalizeCell, validateLocalTable };
