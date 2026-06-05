# Modernize Admin Config Permission UI Design

## Goal

Upgrade `/admin/config-ui` from a YAML-first form into a permission workspace for Parquet Gateway admins. The UI should make it clear which Feishu users have which roles, which roles can access each dataset, which columns are visible to each role, and how row policies use user attributes.

The saved configuration format stays compatible with the existing gateway:

```yaml
auth:
  feishu_users:
    - name: "郭晶晶(星艾舍)"
      roles: [analyst]
      attributes:
        regions: [US, EU]

datasets:
  orders:
    roles: [analyst, admin]
    columns:
      analyst: [order_id, region, amount]
      admin: [order_id, region, amount, margin]
    row_policy:
      field: region
      source: attributes.regions
```

## Current Problem

The current admin UI exposes the configuration as cards and textareas. Dataset column permissions are edited as comma-separated column lists per role. This works for a small demo, but it becomes hard to audit when datasets have many fields or several roles.

Admins need a visual answer to these questions:

- Which columns can this role see?
- Which roles can access this dataset?
- Which users belong to those roles?
- Is row-level filtering configured correctly?
- What YAML will be saved?

## First-Version Scope

- Keep the existing backend API: `GET /admin/config`, `POST /admin/config`, and `GET /admin/config/discover-datasets`.
- Keep the existing YAML schema and permission enforcement model.
- Replace textarea-based column editing with a matrix-style editor.
- Add structured editing for Feishu users, pending Feishu users, roles, and user attributes.
- Add a row policy editor that maps a dataset field to a user attribute source.
- Keep YAML available as an advanced preview and fallback editor.
- Add an explicit "apply YAML to form" action for admins who manually edit YAML.
- Add save-time validation before sending YAML to the backend.

## Out Of Scope

- Changing the gateway permission model.
- Adding a database-backed config store.
- Multi-admin drafts, review workflows, or approvals beyond the existing pending Feishu user flow.
- Full version history UI. The server-side backup path returned by save remains the recovery mechanism.
- Query execution from the admin UI.

## Information Architecture

The UI should shift from two raw panels to a workspace layout:

```text
┌────────────────────────────────────────────────────────────┐
│ Parquet Gateway Admin                  [Load] [Save] [Diff] │
├───────────────┬────────────────────────────────────────────┤
│ Datasets       │ Dataset detail                              │
│ Users          │ - Field permission matrix                   │
│ Pending users  │ - Row policy editor                         │
│ Settings       │ - YAML preview                              │
│ Advanced YAML  │                                            │
└───────────────┴────────────────────────────────────────────┘
```

The left navigation is for choosing the object being edited. The right side is the focused editor for that object.

## Dataset Permission Matrix

Each dataset should show roles as columns and fields as rows:

```text
Dataset: orders
Path: orders/*

┌──────────────┬─────────┬───────┬───────────┐
│ Field        │ analyst │ admin │ promotion │
├──────────────┼─────────┼───────┼───────────┤
│ order_id     │    ✓    │   ✓   │     ✓     │
│ region       │    ✓    │   ✓   │     ✓     │
│ amount       │    ✓    │   ✓   │           │
│ margin       │         │   ✓   │           │
└──────────────┴─────────┴───────┴───────────┘
```

Matrix interactions:

- Search fields by name.
- Toggle one field-role cell.
- Toggle a whole field row.
- Toggle a whole role column.
- Select all visible fields for a role.
- Clear all visible fields for a role.
- Copy one role's field permissions to another role.

The matrix writes back to:

```yaml
datasets.<dataset_id>.columns.<role>
```

Dataset roles write back to:

```yaml
datasets.<dataset_id>.roles
```

## Row Policy Editor

The row policy editor should avoid free-form JSON for common cases:

```text
Row policy

Dataset field: [region v]
User attribute source: [attributes.regions v]

Meaning:
region IN current_user.attributes.regions
```

The editor writes back to:

```yaml
datasets.<dataset_id>.row_policy.field
datasets.<dataset_id>.row_policy.source
```

The UI should warn when:

- The row policy field is not in the discovered or configured field list.
- The selected row policy field is not visible to a dataset role.
- No Feishu user has the selected attribute key.

## Feishu User Workspace

Feishu users should be edited in a compact table instead of stacked cards:

```text
┌───────────────┬─────────────┬────────────────────┬──────────────┐
│ Name          │ ID          │ Open ID            │ Roles        │
├───────────────┼─────────────┼────────────────────┼──────────────┤
│ 郭晶晶(星艾舍) │ guojingjing │ ou_f6c...          │ analyst      │
│ 刘文欣(星宁馨) │ 宁馨        │                    │ admin,analyst│
└───────────────┴─────────────┴────────────────────┴──────────────┘
```

User attributes should be structured inputs derived from row policy sources:

```text
attributes.regions: US, EU
attributes.departments: retail, finance
```

The advanced JSON textarea can remain behind a disclosure for unusual attributes.

## Pending Feishu Users

Pending users should be localized and treated as a guided approval flow:

```text
待审批飞书用户

郭晶晶(星艾舍)
ou_f6c0023f38720da65eeb2773874f301a
[批准为 analyst] [编辑后批准] [忽略]
```

Approval should:

- Move the user from `auth.pending_feishu_users` to `auth.feishu_users`.
- Default the role to `analyst`.
- Preserve `name` and `open_id`.
- Use a readable ASCII internal `id` when one can be generated or entered, and fall back to `open_id` only when no readable id is available.
- Let the admin adjust `id`, roles, and attributes before saving.

## YAML Preview And Diff

YAML should remain visible, but as an advanced representation of the visual state. The workspace should support:

- Preview current YAML.
- Show changed sections before save.
- Copy YAML.
- Fall back to manual YAML editing for advanced cases.
- Apply manually edited YAML back into the visual workspace through an explicit action.

The visual workspace is the primary source of truth for normal operations. YAML is an advanced fallback. If an admin manually edits YAML, the visual workspace must not re-render automatically while the textarea may contain partial or invalid YAML. Instead, the admin must click "apply YAML to form"; if parsing or validation fails, the UI should show the error and keep the current visual state unchanged.

## Validation

Before save, the UI should validate:

- Every dataset has at least one role.
- Every dataset role has at least one visible column.
- Every role listed in `datasets.<id>.columns` is listed in `datasets.<id>.roles`.
- Every row policy field exists in the dataset field list.
- Every Feishu user has at least one role.
- Every pending-user approval creates a non-empty `id`.
- User attributes referenced by row policies are highlighted if missing.

Validation should warn before save, but should not silently repair missing user attributes, empty roles, or empty field permissions. The backend remains the final validator through Pydantic and `save_admin_config_yaml()`.

## Data Flow

```text
GET /admin/config
  -> parse YAML into config object
  -> render workspace state
  -> admin edits matrix/users/row policy
  -> generate updated YAML
  -> local validation
  -> POST /admin/config
  -> backend validates and writes backup + config
  -> reload UI from server response
```

Dataset discovery remains:

```text
GET /admin/config/discover-datasets
  -> show discovered datasets and fields
  -> add selected dataset to config
  -> initialize roles and columns from defaults
```

## Testing Strategy

Backend tests should keep checking that `/admin/config-ui` serves the expected UI script and that `/admin/config` still saves with `POST`.

UI behavior can initially be covered by HTML/source assertions, matching the current test style. If the UI grows more complex, add a browser-level smoke test that verifies:

- Loading config with an admin token.
- Approving a pending Feishu user.
- Toggling a matrix cell.
- Generating expected YAML.
- Saving and reloading.

## Rollout Plan

1. Build the visual controls while keeping YAML preview and save behavior compatible.
2. Deploy to `intranet-184`.
3. Verify `/health`, `/admin/config-ui`, and `/admin/config`.
4. Manually test one dataset permission edit and one Feishu user edit on a safe config backup.
5. Keep the previous server-side config backup path for rollback.

## Decisions

- Role sources: keep the current fixed default roles and also discover custom roles from existing config.
- Pending Feishu approval: default the approved user to role `analyst`; prefer a readable ASCII internal `id`, falling back to `open_id` only when necessary.
- YAML synchronization: manual YAML edits require an explicit "apply YAML to form" action before the visual workspace is re-rendered.
- Permission simulator: exclude it from the first version and track it as future work.

## Future Work

A permission simulator should be a second change after the matrix editor and user workspace are stable. It should let an admin choose a user and dataset, then show:

- Whether the user can access the dataset.
- Which roles are active for that dataset.
- Which columns are visible.
- Which row policy is applied, including the current user attribute values.

This simulator is intentionally not part of the first-version implementation.
