---
name: bytedance-shortlink
description: "Manage IT ShortLink go links through bytedcli: list my links, inspect exact suffixes and owners, check anonymous redirects, create links, update targets and notes, and delete owned links. Use for IT 短链管家, go 短链, shortlink, and custom internal URL suffixes."
---

# bytedcli Shortlink

Platform: [IT ShortLink 短链管家](https://shortlink.bytedance.net). [Platform help](https://bytedance.larkoffice.com/docx/MTqFdZP8iooCH7xK71Qco3XDnng). This CLI supports the CN SSO platform; i18n sites are not supported.

Use `bytedcli shortlink` for IT ShortLink links. Authenticated commands use the saved CN SSO browser session and exchange it for a platform token in memory. The commands never print that token or open a browser automatically.

```bash
# Complete authentication yourself when the saved SSO browser session is unavailable.
bytedcli auth login --session

# List my links; --suffix filters suffixes locally by startsWith.
bytedcli --json shortlink list --suffix demo/

# Exact lookup includes ownership. Missing links return link:null.
bytedcli --json shortlink get --suffix demo/team

# Anonymous check: no login, no following the destination.
bytedcli --json shortlink check --suffix demo/team

# Every write previews by default; --dry-run wins even when --yes is also present.
bytedcli --json shortlink create --suffix demo/team --target https://example.com/start --note 'Demo link' --dry-run
bytedcli --json shortlink create --suffix demo/team --target https://example.com/start --note 'Demo link' --yes

# Omitted fields are preserved. An empty note clears the remark.
bytedcli --json shortlink update --suffix demo/team --target https://example.com/updated --dry-run
bytedcli --json shortlink update --suffix demo/team --note '' --yes

# Delete resolves one exact owned record and requires --yes to submit.
bytedcli --json shortlink delete --suffix demo/team --dry-run
bytedcli --json shortlink delete --suffix demo/team --yes
```

`create` and `update` submit one approval and query its state once. The platform completes robot approval and registration asynchronously. `submitted:true` with `approval_complete:false` is a normal pending result; wait and read back with `get` and `check`. The command never calls manual approval or registration endpoints, and never automatically retries a write. Preview output includes the create payload and subsequent read-only approval query with references to the returned IDs.

`check` reports registered for a 301 redirect with an HTTP(S) destination, and unregistered for a 302 to the platform creation page. Other responses produce `SHORTLINK_CHECK_UNKNOWN`. Browser redirects may remain cached for ten minutes; the CLI performs a fresh request.

## Agent guidance

- Pass an exact `--suffix` for get/check/create/update/delete; list accepts `--suffix` as an optional prefix filter. Use a suffix, such as `demo/team`, without a URL prefix. Slash-separated paths, Unicode, and emoji are supported by the CLI; the platform still validates availability and naming.
- List/get use the current user's platform identity. Update/delete require exactly one record owned by that same identity; no owner or numeric ID override exists.
- List returns the complete backend result with local prefix filtering as one page: `page:1`, `page_size` and `returned_count` are the filtered item count (zero for an empty result). `total` is included only when provided by the backend and remains unfiltered.
- The platform UI uses `expire_days:3650` for create/update; the CLI follows that contract.
- `SHORTLINK_APPROVAL_INCOMPLETE` means an approval was submitted but its read-only status check failed or returned an unexpected result. Inspect its ID, wait for asynchronous processing, and read back the link. Do not repeat create/update or try another write path.
- `SHORTLINK_APPROVAL_REJECTED` reports a rejected or closed approval separately, with `approval_status` and `approval_node`. Inspect the approval and read back the link before correcting and resubmitting a rejected request.
- Authentication failure requires the user to complete `bytedcli auth login --session`. ByteCloud JWTs and captured browser tokens are not substitutes for the platform token exchange.
- Network errors, business failures, and uncertain write outcomes require readback before any retry. Platform configuration, owner reassignment, and manual approval overrides are outside these commands.
- Keep cookies, authorization headers, SSO codes/state, and access tokens out of reports and committed fixtures.
