# INTEGRATION_TODO.md

> Generated: 2026-06-18
> Plan: Einesium Integration v2
> All file-level unknowns resolved and committed. One GitHub UI/API action remains.

---

## TODO-001 - Auto-merge Branch Ruleset

| Field | Value |
|-------|-------|
| **Owner** | Human admin OR agent with `org:admin` token |
| **Priority** | HIGH |
| **Blocker** | This action cannot be completed by file commit - requires GitHub Settings API or UI |
| **Why it matters** | Without this ruleset, Dependabot PRs require manual merge approval and the `auto-merge-dependabot.yml` workflow cannot complete its merge step |

### GitHub UI Path

Navigate to:

```
https://github.com/cryptoxdog/L9-Node-Template/settings/rules
```

Click **New ruleset -> Branch ruleset** and configure:

| Setting | Value |
|---------|-------|
| Ruleset name | `main-protection` |
| Enforcement | Active |
| Target branch | `main` |
| Required status checks | `PR Pipeline Gate`, `gitleaks` |
| Require branches to be up to date | enabled |
| Required approving reviews | `1` |
| Dismiss stale reviews on push | enabled |
| Allow auto-merge (repo General settings) | enabled |

Also verify at `Settings > General > Pull Requests`:
- Allow auto-merge

---

### API Alternative (agent with org:admin token)

```bash
# Step 1 - enable auto-merge at repo level
gh api repos/cryptoxdog/L9-Node-Template \
  --method PATCH \
  --field allow_auto_merge=true

# Step 2 - create branch protection ruleset
gh api repos/cryptoxdog/L9-Node-Template/rulesets \
  --method POST \
  --field name="main-protection" \
  --field target="branch" \
  --field enforcement="active" \
  --field conditions='{"ref_name":{"include":["refs/heads/main"],"exclude":[]}}' \
  --field rules='[
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          {"context": "PR Pipeline Gate"},
          {"context": "gitleaks"}
        ]
      }
    },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
      }
    },
    {"type": "non_fast_forward"}
  ]'
```

---

### Verification Command

After applying, confirm the ruleset is active:

```bash
gh api repos/cryptoxdog/L9-Node-Template/rulesets --jq '.[].name'
# Expected: main-protection

gh api repos/cryptoxdog/L9-Node-Template --jq '.allow_auto_merge'
# Expected: true
```

---

### Done Criteria

- [ ] `gh api repos/cryptoxdog/L9-Node-Template/rulesets` returns a ruleset named `main-protection`
- [ ] Ruleset enforcement status is `active`
- [ ] `PR Pipeline Gate` is listed as a required status check
- [ ] `gitleaks` is listed as a required status check
- [ ] `allow_auto_merge` is `true` on the repo object
- [ ] Next Dependabot PR auto-merges after CI green without manual intervention
