# Model records, configuration, schedules and serving

`bytedcli byterec model` provides atomic operations for the model-cloning workflow. For a copying workflow, read a source variant, then explicitly pass the required fields to create or edit its matching target variant. Creation itself does not query a source model. A model ID identifies one exact corpus/model_name/opname/version combination. Do not infer an opname × version cross product or copy one variant's configuration or launch settings onto another variant.

## Command map

| Command                                                | Purpose                                                                    |
| ------------------------------------------------------ | -------------------------------------------------------------------------- |
| `model list`                                           | Search by namespace/keyword; one page per invocation                       |
| `model get --model-id`                                 | Read one variant, including metadata, configuration set and build schedule |
| `model create`                                         | Create a model record from explicit metadata and initialization JSON       |
| `model config list --model-id`                         | List attached private files and shared references                          |
| `model config get --model-id --conf-id`                | Read metadata, base64 text and `decoded_text`                              |
| `model config create --model-id --name --text-file`    | Create a private configuration file                                        |
| `model config update --model-id --conf-id --text-file` | Replace a private configuration file                                       |
| `model config delete --model-id --conf-id`             | Delete an attached private file                                            |
| `model config bind/unbind --model-id --conf-id`        | Add/remove an existing shared configuration reference                      |
| `model config deploy --model-id`                       | Synchronize model configuration to ByteKV                                  |
| `model schedule get/update --model-id`                 | Read scheduling objects or replace them from JSON files                    |
| `model serving list`                                   | Read launch information by model ID or service PSM + namespace             |
| `model serving create --model-id`                      | Submit a variant to a Viking service                                       |

All writes default to dry-run and return a complete `plan` with method, path, body and target. Inspect that plan; append `--yes` only when the user has authorized that specific write. Mutation requests do not retry automatically. An uncertain request or failed readback must be investigated with the read commands before retrying.

Model configuration and Viking **service** configuration are different resources. These commands operate on `model_conf_set`; `byterec viking service-config` operates on the service's flags and deployment configuration.

## Read and create model records

```bash
# A copying workflow can first inspect the exact requested source variant.
bytedcli --site i18n-tt --json byterec model list \
  --namespace demo_namespace --keyword demo_source --no-only-brief
bytedcli --site i18n-tt --json byterec model get --model-id 1001 > source-model.json

# Prepare the platform initialization JSON explicitly. In the clone SOP this
# object identifies the source variant; its model_name differs from the target.
cat > initialization.json <<'JSON'
{"corpus":"demo_corpus","model_name":"demo_source","opname":"hnsw","version":"2"}
JSON

# Preview one record creation from explicit fields. No source model is queried.
bytedcli --site i18n-tt --json byterec model create \
  --namespace demo_namespace --model-name demo_target --created-by demo.user \
  --corpus demo_corpus --opname hnsw --version 2 --regions sg \
  --model-schema-type fermi_dsl --model-config-file initialization.json

# After an authorized submission, use the returned model ID (2001 in this example).
bytedcli --site i18n-tt --json byterec model get --model-id 2001
```

Required creation inputs:

| Option                              | Value / source when copying an existing variant                          |
| ----------------------------------- | ------------------------------------------------------------------------ |
| `--namespace`                       | Explicit namespace; available as `model get` → `namespace`               |
| `--model-name`                      | New model name                                                           |
| `--created-by`                      | Creator username                                                         |
| `--corpus`, `--opname`, `--version` | Explicit variant fields; available under `model_meta`                    |
| `--regions`                         | Repeatable or comma-separated regions; available as `model_meta.regions` |
| `--model-schema-type`               | Explicit schema type; available as `model_schema_type`                   |
| `--model-config-file`               | UTF-8 JSON object containing the platform initialization configuration   |

Optional fields are `--model-key` (defaults to model-name), `--model-level` (temp), `--custom-tag` (empty), `--description` (empty), `--test-lane` / `--no-test-lane` (false), `--pooled-build` / `--no-pooled-build` (true), and `--template-id` (0). In a copying workflow, inspect and pass any source settings that must be preserved; none are inherited implicitly. These settings are available as `model_key`, `model_level`, `custom_tag`, `model_desc`, and `model_meta.test_lane/pooled_build` in the get result.

`create` performs one POST followed by a GET of the returned new model ID. Dry-run only validates the explicit inputs and returns a plan, without any model GET or POST. There is no `--source-model-id` option and no `model clone` command.

The initialization file is sent as a JSON **string** in `model_config`, retaining its object fields. In the cloning SOP, the inner `model_name` identifies the source while the outer `--model-name` names the new record; the CLI does not infer or force these names to match. `model get` also preserves the platform's base64 `model_config` field, which a script can decode to prepare an initialization file. Creation readback verifies namespace, corpus, model_name, opname and version against the explicit target fields.

The platform initializes `fermi.py` according to the supplied initialization configuration. Other private files, shared references, scheduling, ByteKV synchronization and Viking launch remain independent operations.

## Read and edit configuration

```bash
# Inspect source and target files. Copy each matching variant separately.
bytedcli --site i18n-tt --json byterec model config list --model-id 1001
bytedcli --site i18n-tt --json byterec model config list --model-id 2001

# Save decoded source content without adding a trailing newline.
bytedcli --site i18n-tt --json byterec model config get \
  --model-id 1001 --conf-id 10 | jq -j '.data.decoded_text' > source-fermi.py

# Prepare target-fermi.py locally, replacing the source model_name with the target.
# Preserve the other source settings and the original file's newline state.
# Replace an existing target private file; this is a dry-run.
bytedcli --site i18n-tt --json byterec model config update \
  --model-id 2001 --conf-id 11 --text-file target-fermi.py

# Create a private file that is absent from the target.
bytedcli --site i18n-tt --json byterec model config create \
  --model-id 2001 --name fermi.flags --text-file source-fermi.flags

# Shared configurations are referenced by ID; do not copy or overwrite their contents.
bytedcli --site i18n-tt --json byterec model config bind \
  --model-id 2001 --conf-id 20

# Explicitly remove an unwanted private file or shared reference.
bytedcli --site i18n-tt --json byterec model config delete \
  --model-id 2001 --conf-id 22
bytedcli --site i18n-tt --json byterec model config unbind \
  --model-id 2001 --conf-id 24

# Publish configuration separately after completing and checking the target files.
bytedcli --site i18n-tt --json byterec model config deploy --model-id 2001
```

- `--text-file` is UTF-8, including empty files; the client encodes it to base64. Invalid UTF-8 is rejected. Updating replaces the complete file content.
- `--directory` defaults to `fermat_config` for creation. A duplicate filename within the same directory is rejected.
- `--description` accepts plain text, which is sent as plain text. The backend returns descriptions as base64; updates decode the existing description once before sending it when this option is omitted. To copy a description from `config get`, decode `config.raw.desc` once and pass that text. Readback verifies both content and description. `--is-lua` / `--no-is-lua` explicitly set the Lua flag; omission preserves it on updates.
- A file selected for get/update/delete must belong to the selected model. Shared files (`app_name=fermat_model` or the matching full-key segment) cannot be updated/deleted through these commands; use bind/unbind. Shared references must belong to the target namespace.
- Readback checks file contents or reference membership after writes. `config deploy` defaults to `need_order=true`; `--no-need-order` explicitly disables it. A successful synchronization request and model readback do not prove asynchronous publication is complete.

## Read and edit build scheduling

```bash
bytedcli --site i18n-tt --json byterec model schedule get \
  --model-id 1001 | jq '.data.schedule_config' > source-schedule.json

# Replace the target's schedule with the exact matching source variant's settings.
bytedcli --site i18n-tt --json byterec model schedule update \
  --model-id 2001 --schedule-file source-schedule.json

# Read back the target after submission.
bytedcli --site i18n-tt --json byterec model schedule get --model-id 2001
```

`--schedule-file` must contain a JSON object. `--build-file` optionally supplies a complete replacement `build_config`; otherwise the target's current build settings are preserved. Both fields are sent as JSON **strings**, matching the platform contract. Readback compares nested values semantically and allows backend-derived `schedule_pool_info` / `test_schedule_pool_info` to be recomputed. Preserve the source variant's pool, interval, shard count and switches; do not hardcode common values.

## Read and create launch information

```bash
# Read the source's launch information; inspect each task's shard_policy.
bytedcli --site i18n-tt --json byterec model serving list --model-id 1001

# Use the matching source variant's PSM, M/N, policy, threshold and slot mapping.
# This illustrative mapping has M=4, N=2; it is not a default.
bytedcli --site i18n-tt --json byterec model serving create \
  --model-id 2001 --serving-psm example.viking.recall \
  --m-shard 4 --n-shard 2 --policy shard-slot \
  --shard-slots '0;1;0;1' --ready-threshold 0.9

# Query the current state after submission.
bytedcli --site i18n-tt --json byterec model serving list --model-id 2001

```

`--policy mod` maps to backend `policy_type=0`; `--policy shard-slot` maps to `2` and requires one semicolon-separated slot per model shard, each in `[0, n-shard)`. Read the source `shard_policy.policy_type`, `m_shard_num`, `n_shard_num`, `ready_threshold` and `shard_slots_policy`; translate the actual source mapping, without inventing a policy or selecting the first task when multiple services are attached. Launch creation does not modify an existing policy or offline a model.

`serving list` returns a complete current snapshot with `current_count` and `has_more=false`; there are no pagination flags. Submission returns the backend response and current readback, which may be empty or LOADING. Inspect status/status_desc until the platform reports READY; command success does not mean the model is ready for traffic.
