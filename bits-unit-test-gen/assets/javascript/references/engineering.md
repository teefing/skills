# Engineering Environment Quick Reference

Read this only when package manager, monorepo layout, test config, or TypeScript config is unclear.

## Identification Order

1. Workspace orchestrators: `rush.json`, `eden.monorepo.json`, `pnpm-workspace.yaml`, `turbo.json`, `package.json#workspaces`
2. Lockfiles: `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `bun.lockb`
3. Test config: `jest.config.*`, `vitest.config.*`, `rstest.config.*`, `package.json#scripts`
4. TypeScript config: `tsconfig.json`, `compilerOptions.paths`, `types`

`rush.json` and `eden.monorepo.json` override the lockfile signal. A Rush repo may contain `pnpm-lock.yaml` and `pnpmVersion`; pnpm is still Rush's implementation detail, not the command surface to use directly.

## Rush Tool Preflight

Before any Rush install/add/test command:

1. Read project requirements from `rush.json`:

   ```bash
   node -e "const r=require('./rush.json'); console.log(JSON.stringify({rushVersion:r.rushVersion,nodeSupportedVersionRange:r.nodeSupportedVersionRange,pnpmVersion:r.pnpmVersion}, null, 2))"
   node -p "process.version"
   ```

2. If the current Node clearly does not satisfy `nodeSupportedVersionRange`, switch Node first. Do not start `rush install` and hope it succeeds.
3. Check whether a global Rush CLI exists and matches `rushVersion`. Run the version probe outside the repo to avoid project plugins/autoinstallers:

   ```bash
   command -v rush
   tmp="$(mktemp -d)" && (cd "$tmp" && rush --help | sed -n '1,3p')
   ```

4. Check which repo launchers exist:

   ```bash
   test -f common/scripts/install-run-rush.js && echo has-install-run-rush
   test -f common/scripts/install-run-rushx.js && echo has-install-run-rushx
   test -f common/scripts/install-run-rush-pnpm.js && echo has-install-run-rush-pnpm
   test -f common/scripts/install-run.js && echo has-install-run
   ```

   Standard Rush repos normally commit these generated scripts, but stale or customized repos may be missing them. Do not assume.

5. If global Rush is missing or the displayed version does not match `rush.json#rushVersion`, prefer the repo launcher when it exists:

   ```bash
   node common/scripts/install-run-rush.js <rush-command> [args...]
   ```

   `install-run-rush.js` installs and runs the Rush version requested by `rush.json`. Use it from the repo root. `install-run.js` is for arbitrary NPM package binaries, not the first-choice Rush CLI launcher.

6. Only after the Node and Rush preflight passes, run the install/add/test command. If neither matching global Rush nor `install-run-rush.js` is available, record the missing Rush launcher/tooling failure or follow explicit project docs; do not fall back to raw `pnpm`.

## Package Manager Commands

| Environment | Install | Add missing test deps | Test script | Single test file |
|---|---|---|---|---|
| Rush | After Rush Tool Preflight, from repo root: `rush install`; if scoped install is supported, prefer `rush install --to .` from the package. If `common/scripts/install-run-rush.js` exists and global Rush is missing or mismatched, run `node common/scripts/install-run-rush.js install` from the repo root. | From package dir with matching Rush: `rush add --package <dep> --dev --skip-update`, then one `rush update`. With launcher: run `node common/scripts/install-run-rush.js add --package <dep> --dev --skip-update` from the package if supported, otherwise use the project-documented Rush add flow. | From package dir: `rushx test -- ...`; if needed use `node ../../common/scripts/install-run-rushx.js test -- ...` with the correct relative path to the repo script. | From package dir: `rushx test -- <test-file>` or repo launcher equivalent |
| Eden/EMO | `emo install` from repo root or project-documented install command | Project-documented `emo`/package update flow; do not raw-install into a managed repo by default | `emo run test --filter <pkg>` or package-local `emox test ...` | Use the nearest existing EMO/package test command |
| npm | `npm install` | `npm install -D <deps>` | `npm test -- ...` | `npm test -- <test-file>` |
| pnpm | `pnpm install` | `pnpm add -D <deps>` | `pnpm test -- ...` | `pnpm test -- <test-file>` |
| yarn classic | `yarn install` | `yarn add -D <deps>` | `yarn test ...` | `yarn test <test-file>` |
| yarn berry | `yarn install --immutable` | `yarn add -D <deps>` | `yarn test ...` | `yarn test <test-file>` |
| bun | `bun install` | `bun add -d <deps>` | `bun test` | `bun test <test-file>` |

Prefer existing project scripts. Do not assume direct `jest` / `vitest` / `rstest` binaries are available.

## Dependency Setup

Install if package dependencies or the selected framework cannot resolve from the package root.

Framework resolution examples: `npm exec -- vitest --version`, `pnpm exec jest --version`, `yarn vitest --version`, `bunx jest --version`.

Rush framework resolution examples: use `rush-pnpm exec vitest --version` / `rush-pnpm exec jest --version` from the package when an ad hoc binary check is needed. `rush-pnpm` is for diagnostics and compatible pnpm subcommands inside Rush, not a replacement for `rush install`, `rush add`, or `rushx`.

When no framework is declared, add only the chosen fallback devDependency (`vitest` or `jest`). Add `jsdom` only for DOM tests, and add `package.json#scripts.test` only when missing.

Registry and scripts:

- Use the repository's checked-in registry config first. Internal packages generally require the internal registry; public registry fallback is only for public packages in repos without private registry configuration.
- For npm/pnpm/yarn/bun repos, if an unrelated lifecycle script blocks test setup, retry with the package-manager supported script-skip option such as `--ignore-scripts` or a checked-in `.npmrc` setting.
- For Rush/EMO repos, do not bypass the orchestrator to use raw pnpm. Use project-documented Rush/EMO configuration for script skipping, or record the environment failure if no supported path exists.

## Monorepo Package Selection

| Type | Marker | Common command |
|---|---|---|
| pnpm workspace | `pnpm-workspace.yaml` | `pnpm --filter <pkg> test -- <file>` |
| Yarn workspace | `package.json#workspaces` | `yarn workspace <pkg> test <file>` |
| Rush | `rush.json` | Run `rushx test -- <file>` inside the package |
| Turborepo | `turbo.json` | Prefer package script; fallback `turbo run test --filter=<pkg>` |
| Eden/EMO | `eden.monorepo.json` | `emo test --filter <pkg>` or package-local `emox test` |

Find the package by walking upward from the target source file to the nearest `package.json`.

## Test Config Notes

### Jest

- File matching: `testMatch`, `testRegex`, `testPathIgnorePatterns`
- TS transform: `ts-jest`, `babel-jest`, `@swc/jest`
- DOM environment: `testEnvironment: 'jsdom'` or `/** @jest-environment jsdom */`
- Path aliases: `moduleNameMapper` should match `tsconfig.paths`

### Vitest

- File matching: `test.include`, `test.exclude`
- DOM environment: `environment: 'jsdom'` or `// @vitest-environment jsdom`
- Path aliases: `resolve.alias` must be absolute, or use `vite-tsconfig-paths`
- Global APIs: if `globals: true` is not configured, import from `vitest`

### Rstest

- File matching: `include`, `exclude`
- DOM environment: `testEnvironment: 'jsdom'` or `// @rstest-environment jsdom`
- Global APIs: if globals are disabled, import from `@rstest/core`
- Build config is often reused via `@rstest/adapter-rsbuild` / `@rstest/adapter-rspack`

## TypeScript Config

- Path aliases come from `compilerOptions.paths`; test framework aliases must match.
- JSX tests need `.tsx`; do not put JSX in `.ts` tests.
- In strict mode, reuse exported source types first.
- Source-file type errors are not fixed by changing production code; fix test-file-related errors or language-authorized test infrastructure only.

## Troubleshooting Priority

1. `No tests found`: check test file path against framework config.
2. `Cannot find module`: check alias / moduleNameMapper / resolve.alias.
3. `document is not defined`: use jsdom/happy-dom.
4. `SyntaxError`: check Babel/SWC/TS transform; mock hard-to-transform dependencies if needed.
5. timeout: mock network, timers, WebSocket, subscriptions, and external services.
