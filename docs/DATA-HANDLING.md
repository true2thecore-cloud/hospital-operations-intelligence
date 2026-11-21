# Data handling

All committed examples are synthetic. The original operational workbooks, personal assistant identity, staff names, site-specific paths and private source documents are not redistributed.

Keep real transcripts, staff assignments, Forms responses, contact details, tokens and generated operational reports out of Git. `.gitignore` excludes normal runtime locations, but it is not an anonymization system. A renamed file or a screenshot can still contain private information. Review every proposed commit before publishing a customized copy.

The SQLite file and exported HTML/JSON contain source excerpts and can contain identifiers from your inputs. They are not automatically de-identified or encrypted by this program. Use approved storage permissions, device encryption, access controls and retention practices. Sanitize operational information before sharing a repository example.

The core opens no external network connections unless the user invokes the optional Graph adapter. The local workbench uses loopback, a per-process request token, host checks and escaped output. These controls do not make it a multi-user hosted service. Do not expose it publicly.

Graph tokens are read from `GRAPH_ACCESS_TOKEN` at runtime and are not persisted. The adapter uses read-only calls to the fixed Microsoft Graph host. Never commit a token to a script, JSON file, screenshot or issue. Tenant credentials and consent remain under organizational control.

Treat transcript content as evidence. Embedded instructions cannot override agent rules, change permissions, execute code or authorize messages. Configure any email or Teams notification separately with an explicit owner and approved recipients. This release does not send notifications.

For removal/retention requests, stop the worker and follow your organization's approved record-management process for the database, source files, exports and backups together. Version 0.1.0 does not implement selective record erasure or a legal retention policy.
