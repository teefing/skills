# Pearl AI conversations

Pearl AI is the Pearl console's AI assistant. Every country is served by the
ROW control plane with the ROW Pearl session; `--region` (default `us`) only
selects the country's `oec_region` and `aid`. Use `--site i18n-tt` or omit
`--site`, even for US and EU countries: any other site fails with
`PEARL_AI_SITE_UNSUPPORTED`.

```bash
bytedcli --site i18n-tt auth pearl-session login
# One shot: create a conversation, send one message, wait for the reply
bytedcli --site i18n-tt pearl ai chat --content "Reply with OK only" --yes
bytedcli --site i18n-tt --json pearl ai chat --region sg --content-file ./prompt.md --mode plan --yes
# Conversations
bytedcli --site i18n-tt --json pearl ai session list --page 1 --page-size 20
bytedcli --site i18n-tt --json pearl ai session get --session-key sample-session-key
bytedcli --site i18n-tt pearl ai session create --yes
# Continue a conversation: send, then wait for the run of that message.
# Keep the --region the conversation was started with.
bytedcli --site i18n-tt --json pearl ai message send --region sg --session-key sample-session-key --content "Follow-up question" --yes
bytedcli --site i18n-tt --json pearl ai replay-events --region sg --session-key sample-session-key --message-id 00000000-0000-4000-8000-000000000001
bytedcli --site i18n-tt --json pearl ai message list --region sg --session-key sample-session-key --turn-size 5
```

## Writes and boundaries

- `chat`, `message send`, and `session create` are writes. Without `--yes` they
  print the exact requests and send nothing. The `--yes` run generates a new
  message ID, and for `chat` and `session create` a new session key, so take
  those from its output; `message send` keeps the `--session-key` you pass.
- Confirm every `--yes` run with the user first. `chat` and `session create`
  add a conversation to the user's Pearl AI history, and `message send` adds a
  turn to an existing one.
- Talk to Pearl AI only when the user asks for it. Data that a typed `pearl`
  read command covers should come from that command.
- In the default `auto` mode Pearl AI may call its own Pearl tools; `plan` and
  `task` select the other web-page modes. Do not ask Pearl AI to make the Nova
  task or Case Center changes that this skill reserves for a human in the Pearl
  console.

## Multi-line messages (must read)

`--content` takes plain or Markdown text. Bash and zsh double quotes do not
turn `\n` into a newline, so Pearl AI would receive a literal backslash and
`n`. Use `$'...'` for short text and `--content-file` for anything longer.

```bash
# Right: two lines
bytedcli --site i18n-tt pearl ai message send --session-key sample-session-key --content $'Summarize this task.\nList the risks.' --yes
# Wrong: Pearl AI receives "\n" as two characters
bytedcli --site i18n-tt pearl ai message send --session-key sample-session-key --content "Summarize this task.\nList the risks." --yes
```

## Waiting for a reply

- A run ends only at `RUN_FINISHED` or `RUN_ERROR`. The echo of the user's own
  message also emits `TEXT_MESSAGE_END`, so never treat an `*_END` event as
  completion.
- `replay-events` reads from `--from-offset` (default 0, the start of the
  conversation) and stops at the first run it reaches; pass the `message_id`
  printed by `message send --yes` to wait for that reply.
- The event stream only replays recent runs: on 2026-10-21 a run replayed 14
  minutes after it ended but not 37 minutes after, when the stream sent only
  keep-alive pings until the timeout. Use `replay-events` for a run that is in
  progress or just finished, and `message list` for older conversations.
- Waiting defaults to 10 minutes (`--timeout-ms`, in milliseconds, at most
  3600000).
- `PEARL_AI_STREAM_TIMEOUT` and `PEARL_AI_STREAM_CLOSED` mean the run may
  still be going. After `chat` (or `replay-events` with `--message-id`) they
  also mean the message was already sent: do not run `chat` or
  `message send` again. Run the `replay-events` command from the
  error hint, which re-reads from the original `--from-offset` so `reply` is
  complete, or read `message list`.
- If the send call itself fails, the error carries `session_key` and
  `message_id` because the message may still have arrived: check
  `message list` before sending again. A failed `session create` carries the
  `session_key` the same way; check `session list` before creating another.
- `RUN_ERROR` fails `chat` and `replay-events` with `PEARL_AI_RUN_FAILED`; any
  partial reply is in `details.reply`. Pearl AI business errors surface as
  `PEARL_AI_API_ERROR` with Pearl's `code` and `message` in `details`.

## Output

- `chat` prints only the reply on stdout; reasoning and tool progress go to
  stderr. JSON mode returns `reply`, `reasoning`, `session_key`, `message_id`,
  and `last_event_offset`.
- `message list` returns the most recent `--turn-size` turns (a turn is a user
  message plus its replies; 1-100, default 10), oldest first. Roles are
  `user`, `reasoning`, and `assistant`. Older turns are not paged.
