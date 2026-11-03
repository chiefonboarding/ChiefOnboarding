# Mock integrations

Integration manifests that talk to the built-in `/test-integrations/` mock
endpoint instead of a real third-party API. Use them to try out integration
flows (provisioning, revoking, syncing, failures) locally.

## Setup

1. Set `TEST_INTEGRATIONS_ENDPOINT=True` and restart the server.
2. The manifests point at `http://localhost:8000`, which is where the dev server
   runs. If yours runs elsewhere, find and replace that in the files.
3. Go to **Settings → Integrations → Add new integration**, choose the manifest
   type from the table below, and paste in the contents of the JSON file.

## Manifests

| File | Manifest type | What happens |
|---|---|---|
| `provision_user.json` | Provision user accounts | Happy path. A team dropdown is filled from the mock, the user is not found, so they get created (the returned `id` is saved as `MOCK_USER_ID`). Then they get added to the chosen team, with the request echoed back so you can see the payload in the tracker. Revoking returns a `204`. |
| `provision_user_already_exists.json` | Provision user accounts | The exists check finds the user and saves their id as `MOCK_USER_ID` on the new hire. |
| `provision_user_server_error.json` | Provision user accounts | Creating the user returns a `502` with an HTML body, so the integration fails, sends a notification and, if triggered from a sequence, retries in an hour. |
| `provision_user_slow.json` | Provision user accounts | Every request is slow: 3s for the exists check and 8s for each of the two execute steps. Useful for loading states and timing. |
| `provision_user_blocked.json` | Provision user accounts | The first step returns `"status": "pending_approval"` but `continue_if` wants `"active"`, so the integration is blocked and the second step never runs. |
| `provision_user_polling_timeout.json` | Provision user accounts | Polls 3 times, 2s apart, waiting for `"state": "ready"`. It never arrives, so it fails with "Polling timed out". |
| `revoke_user_failure.json` | Provision user accounts | The user exists, but revoking returns a `403`, so the revoke fails. |
| `sync_users.json` | Sync users | Imports two users (Ada Lovelace and Alan Turing) from a nested response (`data.users`, `name.first`, `name.last`). |

## Writing your own

The mock's response is controlled by query params in the URL: `status`,
`delay` (max 10s), `body`, `content_type` and `echo`. Some notes:

- Status codes in `status_code` lists must be strings (`["201"]`, not `[201]`).
- URLs are rendered as Django templates, so `{{ email }}` and other new hire
  fields work inside `body`. Avoid `{%` and `{#` in a body, since Django
  treats those as template tags.
- Keep `&`, `#`, `+` and `%` out of `body` values, or percent-encode them.
- Every value saved in the integration's setup form is masked in the tracker,
  which is why the base URL is hardcoded rather than made a setup field.
