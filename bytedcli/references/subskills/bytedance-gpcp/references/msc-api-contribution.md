# MSC API contribution workflow

Use this reference when adding or maintaining an MSC endpoint under `bytedcli gpcp msc`. It records MSC-specific discovery and verification decisions; do not duplicate the repository-wide TypeScript, testing, help, and review rules from `AGENTS.md`, `CONTRIBUTING.md`, or `docs/CONTRIBUTOR_PATTERNS.md`.

## 1. Establish the native contract

1. Start from the MSC thrift/IDL definition. Record the HTTP method/path, required and optional fields, wire names, integer width, pagination base/defaults, and response envelope.
2. Read the handler and downstream business/DAL code. An IDL field may be accepted but ignored, a CN handler may proxy an overseas App, and an empty result may use a different shape from a non-empty page.
3. Compare the frontend request or a safe live read. Treat page URL parameters as UI context until the backend contract proves they are API inputs.
4. Identify every App identifier explicitly: BITS App ID, MSC project `appid`, AppCloud ID, template ID, facts ID, and BPEA `msc_app_id` are not interchangeable. Expose the identifier actually consumed by the API.

Do not infer behavior from a nearby endpoint. In particular, Fact Service version packages, DS TPSDK version-facts reports, BPEA scan orders, and rule-template data are separate resources.

For BPEA certificate and release data, keep the native identity boundary. A DFID may have multiple certificate forms, so fetch form detail by certificate `id` and never collapse details by `dataflow_id`. A schema rule package is uploaded to CDN only when its record status is `online`; key-presence filters such as `need_key=true` do not establish publication status.

## 2. Decide routing and authentication per resource

MSC pages are mounted in GPCP, but the business requests go to an MSC origin. Use `mscBaseUrl`, never the GPCP shell origin.

| Resource behavior | Default/auth pattern |
| --- | --- |
| CN MSC resource | `resolveMscDeployment`; personal CN Cloud JWT via `buildMscHeaders` |
| ROW MSC resource | Resource-specific ROW resolver; personal `i18n-tt` Cloud JWT via `buildMscHeaders` |
| BPEA micro/order | ROW MSC origin plus GPCP platform-session headers via `buildMscPlatformHeaders` |
| Fact Service package list | CN default and ordinary MSC headers; CN server resolves/proxies the App region |

Keep deployment and application region separate. `--deployment` selects an origin; an app-list `region` or a package's platform/region describes data. Do not add silent CN↔ROW fallback: it hides routing defects and can mix authentication models.

Use ordinary JWT headers unless source code or a captured request proves the endpoint requires the GPCP platform session. Never log, persist, or cross-domain forward session cookies or derived tokens.

## 3. Classify the operation by effect

HTTP method does not determine mutation semantics. Several MSC queries are POSTs, including Fact Service lists and rule-history queries. Read-only POSTs do not need `--dry-run` or `--yes`.

For a real mutation, stop and define the public write boundary before implementation. Use exact request schemas, preflight when possible, preview by default, and require explicit confirmation. Do not expose broader backend branches just because they share an endpoint.

## 4. Implement through the standard layers

Keep the MSC mapping thin and predictable:

1. `src/api/gpcp/msc-types.ts`: path constant plus loose Zod schemas. Name stable operator-facing fields and preserve unknown fields.
2. `src/api/gpcp/msc-parsers.ts`: unwrap/parse only; normalize documented empty-result variants here.
3. `src/api/gpcp/msc-api.ts`: choose the correct auth helper, map camelCase options to native snake_case, and apply service defaults deliberately.
4. `src/cli/handlers/gpcp/msc.ts`: validate semantic input, select the resource default deployment, and normalize only the CLI collection envelope.
5. `src/cli/commands/gpcp/msc.ts`: register resource/action, flags, help, and placeholder-only examples.
6. Export through both GPCP indexes and add API, handler, and command tests.

Paginated JSON output must be `{items,page,page_size,total}`. Preserve each item's native nested fields, enum values, spelling, and unknown extensions. Do not parse opaque strings such as `schema_data` or `extra_info` unless the CLI contract explicitly promises that transformation.

## 5. Verify before proposing the change

Offline coverage should prove:

- exact method, path, origin, auth-header family, wire field names, and defaults;
- normal, empty, malformed, auth/business-error, and pagination behavior;
- command parsing and handler output normalization;
- preservation of unknown fields and complete artifact metadata;
- no accidental mutation export.

Then run bounded live reads against representative CN/overseas apps or platforms:

1. a normal list;
2. an exact selector such as version or ID;
3. an empty exact selector;
4. at least two pages with a small page size;
5. a safe invalid local input and, when available, a service business error.

For Fact Service specifically, verify both a Published package and an already-ingested package whose `release_stage` is empty or otherwise not Published. The command must not default to `Published`, and `detail=true` should be used when validating build/artifact fields.

When a CN MSC handler proxies an overseas Fact Service request, verify the proxy's serialized wire keys in addition to the inbound thrift mapping. Thrift JSON serialization may emit field names such as `return_number` / `page_number` even though the downstream HTTP contract requires `rn` / `pn`; compare two small pages directly against ROW before attributing a paging defect to the CLI.

Finish with formatting, typecheck/lint, targeted tests, build, generated skill-asset synchronization, and `validate:skills`. Keep real production IDs, responses, signed artifact URLs, and credentials out of committed tests and documentation.
