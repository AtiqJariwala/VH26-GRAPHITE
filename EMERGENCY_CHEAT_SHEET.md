# 🚨 LEAKGUARD - EMERGENCY CHEAT SHEET 🚨
## Last-Minute Prep for Judge Presentation

---

## 🎯 30-SECOND PITCH (MEMORIZE THIS!)

"LeakGuard catches resource leaks in Python code before they reach production. 
It uses AST analysis and control-flow tracking to detect when files, sockets, 
databases, or locks are opened but never closed. It runs automatically in CI/CD 
pipelines with 90% accuracy and zero dependencies."

---

## ⚡ TOP 5 THINGS JUDGES MUST HEAR

1. **"90% accuracy with 10% false positive rate"** (we tested on 20 fixtures)
2. **"Zero external dependencies"** (pure Python stdlib)
3. **"AST-based, not regex"** (understands code structure, not text matching)
4. **"Control-flow aware"** (tracks early returns, exceptions, branches)
5. **"CI/CD ready"** (pre-commit hooks + GitHub Actions included)

---

## 🎬 DEMO SCRIPT (5 MINUTES)

### STEP 1: Show the Bug (30 sec)
Open `demo_leak.py`:
```python
def process_file(filename):
    f = open(filename)
    if not valid(filename):
        return None  # BUG: file never closed!
    data = f.read()
    f.close()
    return data
```

Say: "See the bug? Early return at line 4 skips the close(). Easy to miss in code review."

### STEP 2: Run LeakGuard (30 sec)
```bash
python -m leakguard.cli scan demo_leak.py
```

Say: "LeakGuard caught it! Shows exact line number and explains the problem."

### STEP 3: Show the Fix (30 sec)
```python
def process_file(filename):
    with open(filename) as f:
        if not valid(filename):
            return None
        return f.read()
```

Run again: "Now it's clean. Context manager handles closing automatically."

### STEP 4: Show CI Integration (1 min)
Open `.github/workflows/leakguard.yml`

Say: "This runs on every push and PR. Blocks builds if leaks found. Zero manual effort."

### STEP 5: Show Test Results (1 min)
Open README, scroll to test table.

Say: "We tested on 20 fixtures. 90% detection rate. We're honest about the 10% we miss."

### STEP 6: Architecture (1 min)
Show README architecture diagram.

Say: "6 components: CLI → AST Parser → Analyzer → Control Flow → Confidence Scorer → Report."

---

## 🔥 MUST-KNOW FACTS

**What We Track:**
- Files: `open()` → `.close()`
- Sockets: `socket.socket()` → `.close()`
- Databases: `sqlite3.connect()` → `.close()`
- Locks: `.acquire()` → `.release()`

**Confidence Levels:**
- DEFINITELY: No close() anywhere (always fail build)
- LIKELY: Close() on some paths, not all (fail by default)
- POSSIBLE: Ownership unclear (warn only)

**Key Files:**
- `analyzer.py` = The brain (AST walking)
- `cfg.py` = Control flow tracking
- `resources.py` = Resource definitions
- `cli.py` = Command-line interface

---

## 💬 TOP 10 JUDGE QUESTIONS & ANSWERS

**Q1: How is this different from Pylint?**
A: "Pylint is generic. We're resource-specific. We understand open/close semantics and track ALL execution paths including exceptions."

**Q2: False positive rate?**
A: "10% on our fixtures. Mostly resources passed to functions where ownership is unclear. We mark these as 'possible' so teams can tune thresholds."

**Q3: What about inter-procedural analysis?**
A: "Currently we don't track across functions - that's our main limitation. We focus on local variables. Catches 90% of real-world leaks."

**Q4: How do you handle complex control flow?**
A: "We build a lightweight CFG. Track all paths - normal flow, early returns, exceptions, branches. Must see close() on EVERY path."

**Q5: Performance impact on CI?**
A: "Fast. Pure Python parsing. 1000 files in maybe 30 seconds. No runtime overhead - it's static analysis."

**Q6: How would companies adopt this?**
A: "Three commands: pip install, pre-commit install, add to CI. Works with existing workflows. 10-minute setup."

**Q7: What's your biggest limitation?**
A: "No inter-procedural analysis. We can't track resources passed to other functions. Workaround is a whitelist of safe functions."

**Q8: Why not machine learning?**
A: "Deterministic is better here. We guarantee checking every path. ML needs training data and can't explain decisions. Ours is transparent."

**Q9: Real-world applications?**
A: "E-commerce preventing database connection leaks during sales. Healthcare ensuring file handles close for HIPAA compliance. Anywhere Python runs backend services."

**Q10: Open source?**
A: "Yes! MIT licensed on GitHub. Zero dependencies makes it easy to contribute."

---

## 🏗️ ARCHITECTURE (Know This!)

```
User Code
    ↓
CLI (cli.py) - Entry point
    ↓
AST Parser (Python's ast module) - Convert code to tree
    ↓
Resource Analyzer (analyzer.py) - Find open(), connect(), etc.
    ↓
Control Flow Tracker (cfg.py) - Track all execution paths
    ↓
Confidence Scorer (confidence.py) - Rank findings
    ↓
Report Generator (report.py) - Format output
```

**One-liner:** "We parse Python to AST, walk the tree finding resource acquisitions, simulate all execution paths, and verify close() on every path."

---

## 🎯 WHAT MAKES US UNIQUE

1. **Resource-Specific:** Not generic linting - we know `open()` needs `.close()`
2. **Path-Sensitive:** Track ALL paths (returns, exceptions, branches)
3. **Zero Deps:** Pure stdlib - runs anywhere
4. **CI-First:** Built for automation from day 1
5. **Honest:** We document our 10% FP/FN rate

---

## 🚀 STRETCH GOALS ACHIEVED

✅ Multiple resource types (files, sockets, DB, locks)
✅ Context manager detection (with statements)
✅ CI/CD integration (hooks + GitHub Actions)
✅ Confidence scoring (3 levels)
✅ Comprehensive testing (20 fixtures, documented accuracy)

---

## 🎓 ROLE ASSIGNMENTS (DECIDE NOW!)

**Person 1:** Problem + Demo
- Explain resource leaks
- Run live demo
- Show the fix

**Person 2:** Technical
- Explain AST vs regex
- Walk through architecture
- Show analyzer.py code

**Person 3:** CI/CD + Real-World
- Demo GitHub Actions
- Discuss real applications
- Show test results

**Person 4:** Q&A
- Field judge questions
- Discuss limitations honestly
- Talk extensibility

---

## ⚠️ COMMON MISTAKES TO AVOID

❌ Don't say "100% accurate" - we're 90%
❌ Don't hide limitations - judges respect honesty
❌ Don't use jargon without explaining it
❌ Don't talk over teammates - coordinate!
❌ Don't panic if you don't know something - say "great question, let me think..."

✅ DO show enthusiasm - this is genuinely useful!
✅ DO reference the 90% accuracy stat
✅ DO mention zero dependencies
✅ DO show the README and test results

---

## 🔑 KEY TERMS EXPLAINED (In Case Judge Asks)

**AST (Abstract Syntax Tree):** Tree representation of code structure. Each node is a code construct (function, call, etc.)

**Control Flow Graph (CFG):** Model of all possible execution paths through code

**Static Analysis:** Analyzing code without running it (vs dynamic = runtime analysis)

**Context Manager:** Python's `with` statement - automatically handles setup/cleanup

**False Positive:** Flagging clean code as leaky (our rate: 10%)

**False Negative:** Missing actual leaks (our rate: 10%)

---

## 🎯 IF YOU ONLY REMEMBER 3 THINGS

1. **"90% accurate, AST-based, zero dependencies"**
2. **"Catches resource leaks before production"**
3. **"CI/CD ready with pre-commit hooks and GitHub Actions"**

---

## 🚨 EMERGENCY PREP (30 MINUTES BEFORE)

**10 min:** Each person practice their section
**10 min:** Run through demo together ONCE
**5 min:** Quiz each other on Q&A
**5 min:** Deep breath, review this cheat sheet

---

## 📱 KEEP THIS OPEN DURING PRESENTATION

Have this file open on a laptop/phone for quick reference during Q&A.

---

## 💪 CONFIDENCE BOOSTERS

- You built something that actually works
- 90% accuracy is genuinely good for an MVP
- Zero dependencies is impressive
- CI/CD integration is production-ready
- Your honesty about limitations shows maturity

**You've got this! 🚀**

---

## 🎬 OPENING LINE (STRONG START!)

"Hi judges! We're team VH26-GRAPHITE and we built LeakGuard - a tool that prevents production outages by catching resource leaks in Python code before they ship. Let me show you how it works..."

---

## 🏁 CLOSING LINE (STRONG FINISH!)

"To summarize: LeakGuard achieves 90% accuracy using pure Python stdlib, integrates seamlessly into CI/CD pipelines, and is open-source and ready for production use. We'd love to answer your questions!"

---

**GOOD LUCK TEAM! 🎉**

Remember: You know more than you think you do. Be confident!
