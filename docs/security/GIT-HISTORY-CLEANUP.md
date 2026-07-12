# Git History Cleanup Procedure

> Perform this only after the exposed camera/NVR credential has been rotated. History rewriting is disruptive and requires every collaborator to replace stale clones.

## Scope

Remove the credential-bearing RTSP URL from every branch and tag, including copies in:

- `server/video-processor.ts`
- `docker-compose.yml`
- attached text assets and generated documentation
- any other path identified by a full-history secret scan

Do not copy the secret into command history. Store the exact text temporarily in a protected local file outside the repository and securely delete it after cleanup.

## Recommended procedure

1. Create an offline backup of the repository for incident evidence and restrict access to it.
2. Notify collaborators that pushes are frozen during cleanup.
3. Use a fresh mirror clone.
4. Run `git-filter-repo` with a replacement-expression file that replaces the full compromised URL and credential fragments with `***REMOVED***`.
5. Run Gitleaks or an equivalent full-history scan over all refs.
6. Inspect tags, pull-request references, releases, artifacts, issues, Actions logs, and package/container registries for copies.
7. Force-push cleaned branches and tags only after the scan passes.
8. Ask collaborators to delete existing clones and clone again. Do not merge old branches back into the cleaned repository.
9. Contact GitHub Support when unreachable cached references or pull-request objects still expose the removed value.
10. Record the cleanup commit/time and scanner output without recording the secret.

## Example command shape

The following is intentionally incomplete so the compromised value is never copied from this document:

```bash
git clone --mirror <repository-url>
cd BarSecurityTracker.git
git filter-repo --replace-text /secure/path/replacements.txt
# Run a full-history scanner here.
git push --force --mirror
```

## Completion evidence

History cleanup remains **Blocked** until all of the following are recorded:

- credential rotation confirmation
- full-ref scan result
- force-push completion
- collaborator stale-clone notification
- review of external caches and build artifacts
