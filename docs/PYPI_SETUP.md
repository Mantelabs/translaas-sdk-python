# PyPI Setup Guide

Quick reference guide for setting up PyPI publishing for the Translaas Python SDK.

## Quick Start

### 1. PyPI Account Setup

1. **Create account**: [https://pypi.org/account/register/](https://pypi.org/account/register/)
2. **Enable 2FA**: Account settings → Security → Add 2FA
3. **Create API token**: Account settings → API tokens → Add API token
   - Name: `translaas-sdk-python`
   - Scope: Project: translaas (recommended)
   - Copy token (starts with `pypi-`)

### 2. Configure Trusted Publishing (Recommended)

**On GitHub (Create Environment):**
1. Repository → Settings → Environments → New environment
2. Environment name: `pypi`
3. Click **Configure environment**
4. Under **Deployment branches**, select:
   - ✅ **Selected branches**: Choose `main` (or your default branch)
   - Or ✅ **All branches** (for testing)
5. Click **Save protection rules**

**On PyPI:**
1. Account settings → Publishing → Add a new pending publisher
2. Fill in:
   - PyPI project name: `translaas`
   - Owner: Your GitHub username/org
   - Repository name: `translaas-sdk-python`
   - Workflow filename: `.github/workflows/release.yml`
   - Environment name: `pypi`
3. Click Add

**On GitHub (Verify Settings):**
1. Repository → Settings → Actions → General
2. Workflow permissions: ✅ Read and write permissions
3. Save

### 3. Test Publishing

**Option A: Create a GitHub Release**
1. Go to Releases → Create a new release
2. Tag: `vX.Y.Z` (must match `[project].version` in `pyproject.toml`, with a `v` prefix — e.g. `v0.3.0b1` for beta)
3. Title: `Version X.Y.Z`
4. Publish release
5. Workflow runs automatically and publishes the same build to **PyPI** and **Test PyPI** (both GitHub environments must exist and trusted publishing must be configured on each index)

**Option B: Manual Workflow Dispatch**
1. Actions → Release workflow → Run workflow
2. Check "Publish to PyPI" or "Publish to Test PyPI"
3. Run workflow

## Manual Publishing (Alternative)

If you prefer manual publishing:

### Configure Credentials

**Option 1: `~/.pypirc` file**
```ini
[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxx
```

**Option 2: Environment Variables**
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxxxxxxxxxxx
```

### Publish

```bash
# Build first
./scripts/build.sh  # or .\scripts\build.ps1 on Windows

# Publish
./scripts/publish.sh pypi  # or .\scripts\publish.ps1 pypi on Windows
```

## Verification

After publishing, verify:
- Package appears on [https://pypi.org/project/translaas/](https://pypi.org/project/translaas/)
- The same version appears on [https://test.pypi.org/project/translaas/](https://test.pypi.org/project/translaas/) when releases are published via the workflow above
- Can install: `pip install translaas`
- Test PyPI install (pulls dependencies from production PyPI):
  `pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "translaas==<version>"`
- Version matches: `python -c "import translaas; print(translaas.__version__)"`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Publisher "Pending" | Run workflow once to activate |
| 403 Forbidden | Check repository name, workflow filename, environment name (`pypi`), permissions |
| Project name mismatch | Ensure `name = "translaas"` in `pyproject.toml` |
| Environment not found | Create `pypi` environment in GitHub Settings → Environments |
| Workflow not triggering | Check YAML syntax, trigger conditions |

## Test PyPI Setup (Optional)

To also set up Test PyPI with an environment:

1. **Create GitHub Environment**: Settings → Environments → New environment
   - Name: `test-pypi`
   - Configure deployment branches
   - Save

2. **Set up Test PyPI trusted publisher** (same process as production PyPI)
   - Environment name: `test-pypi`

## Resources

- [PyPI Documentation](https://pypi.org/help/)
- [Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- Full guide: [CONTRIBUTING.md](../CONTRIBUTING.md#publishing-to-pypi)
