# Archived-project errors in SDK 0.6.0

SDK 0.6.0 adds `PolygresProjectArchivedError` for any Runtime API method that
receives `PROJECT_ARCHIVED`. It subclasses `PolygresAPIError`; existing handlers
for that base class continue to catch it.

With the accompanying backend update, authenticated access to an archiving,
archived, or restoring project returns HTTP 409 with `PROJECT_ARCHIVED` and
`details["archive_state"]`. Previously it returned HTTP 404 with
`RUNTIME_PROJECT_NOT_FOUND`, mapped to `PolygresNotFoundError`.

The server response change also affects SDK 0.5.0 and earlier: those clients
raise the generic `PolygresAPIError` for the new 409 response. Older backends
continue to produce `PolygresNotFoundError`, including with SDK 0.6.0.

## Caller action

Upgrade to SDK 0.6.0 and handle `PolygresProjectArchivedError` separately from
`PolygresNotFoundError`. Keep the not-found handler for missing projects and
older backends. If already catching `PolygresAPIError`, no catch change is
required; inspect `code` to distinguish archive failures.

Before, callers could classify archived projects as missing:

```python
except PolygresNotFoundError:
    print("Project not found.")
```

After importing `PolygresProjectArchivedError` from `polygres`, handle the
archive condition explicitly:

```python
except PolygresProjectArchivedError as error:
    print(str(error))
except PolygresNotFoundError:
    print("Project not found.")
```

The archive message explains whether archiving is in progress, restoration is
needed in the dashboard, or restoration is in progress. Requests do not retry
or restore projects automatically.

There is no SDK deprecation warning or scheduled API removal. The response
change takes effect when the updated backend is deployed.
