# 🚀 LeakGuard CI/CD Demonstration Guide

## Installation for Enhanced Visuals

```bash
# Install LeakGuard with visual enhancements
pip install -e ".[visual]"

# Or just the core (works without visuals too)
pip install -e .
```

## Running the Professional Demo

### Quick Demo (30 seconds)
```powershell
.\demo.ps1
```

This will show:
- ✅ Colored output with panels
- ✅ Progress bars
- ✅ Beautiful tables
- ✅ Build blocking in action

### Manual Demo Commands

**1. Detect a leak (blocks build):**
```bash
python -m leakguard.cli scan tests/fixtures/leaky/01_simple_file_leak.py
```
**Result:** ❌ Exit code 1 (build fails)

**2. Clean file (passes):**
```bash
python -m leakguard.cli scan tests/fixtures/clean/01_with_statement.py
```
**Result:** ✅ Exit code 0 (build passes)

## CI/CD Integration Proof

### GitHub Actions (Live Demo)

1. **Push a leaky file** to trigger the workflow
2. **Action runs automatically** (see `.github/workflows/leakguard.yml`)
3. **Build BLOCKS** if leaks detected
4. **Pull request cannot merge** until fixed

### Pre-commit Hook (Live Demo)

```bash
# Install the hook
pip install pre-commit
pre-commit install

# Try to commit a leaky file
echo "f = open('test.txt')" > bad_code.py
git add bad_code.py
git commit -m "test"  # ❌ BLOCKED!
```

## Visual Features

### With `rich` installed:
- 🎨 Color-coded severity levels (RED=definitely, YELLOW=likely, BLUE=possible)
- 📊 Beautiful ASCII tables
- 📈 Animated progress bars
- 🎯 Styled panels and borders
- ✅ Professional output

### Without `rich`:
- Still works perfectly!
- Plain text output
- Same detection accuracy
- All features functional

## Exit Codes (CI Integration)

- `0` = No leaks found → ✅ Build passes
- `1` = Leaks detected → ❌ Build fails

This is exactly what CI/CD systems need!

## Judge Demo Script

**Say this while demonstrating:**

"Let me show you how LeakGuard blocks real CI builds. Watch the screen..."

**[Run demo.ps1]**

"See that? Beautiful colored output showing exactly what's wrong. The red panel means the build is BLOCKED. In a real CI pipeline, this pull request cannot merge until the developer fixes the leak."

"Now let me show you a clean file..."

**[Show clean file result]**

"Green panel - build passes! That's production-ready code."

---

**This is not a toy demo - this is production CI/CD integration!** 🚀
