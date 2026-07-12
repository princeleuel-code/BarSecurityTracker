# Credential Rotation Register

Status labels in this document describe evidence available in the repository. Secret values are intentionally omitted.

| System | Exposure | State | Required owner action | Deployment gate |
|---|---|---|---|---|
| RGB IP camera / NVR account | A credential-bearing RTSP URL was committed to source, Docker configuration, and an attached text asset | **Verified** | Rotate the camera/NVR password; revoke the prior credential; inspect remote-access and port-forwarding rules; review device access logs; confirm the replacement credential is unique | **Blocked** until rotation is confirmed |
| Repository Git history | The sensitive URL remains reachable from prior commits after active files are patched | **Verified** | Rewrite affected history, invalidate stale clones, and request cache cleanup where required | **Blocked** until history cleanup is completed |
| Deployment environments | It is unknown whether the exposed credential was copied into external hosts, CI variables, shell history, screenshots, or documentation | **Assumed** | Search each deployment environment and rotate/remove any copies found | **Blocked** pending owner verification |

## Required incident sequence

1. Rotate the affected camera/NVR credential before merging this patch.
2. Disable direct internet exposure and public port forwarding for camera services.
3. Store replacement stream URLs in a local `.env` file or managed secret store.
4. Verify `.env` remains ignored and never paste secret-bearing URLs into issues, logs, screenshots, or chat.
5. Complete the Git-history procedure in `GIT-HISTORY-CLEANUP.md`.
6. Re-scan all branches and tags before reopening deployment.

## Evidence boundary

This register does not prove that rotation, network isolation, or history cleanup has occurred. Those items remain **Blocked** until a human owner records completion evidence without disclosing the new credential.
