# LeakGuard - Complete Team Knowledge Guide
## VH26-GRAPHITE Hackathon Project

---

## 📋 TABLE OF CONTENTS

1. [Problem Statement Summary](#problem-statement)
2. [What is LeakGuard? (Elevator Pitch)](#what-is-leakguard)
3. [The Problem We're Solving](#the-problem)
4. [Our Solution Explained](#our-solution)
5. [How It Works (Technical Deep Dive)](#how-it-works)
6. [What Makes Us Unique](#uniqueness)
7. [Real-World Applications](#real-world-applications)
8. [Code Knowledge You Need](#essential-code-knowledge)
9. [Stretch Goals Achieved](#stretch-goals)
10. [Demo Script for Judges](#demo-script)
11. [Q&A: Common Judge Questions](#qa-section)

---

## 1. PROBLEM STATEMENT SUMMARY

**Challenge:** Build a static analysis tool for Python that detects resource leaks

**What are Resource Leaks?**
When you open a file, connect to a database, or acquire a lock but forget to close/release it, that's a resource leak. Over time, these leaks cause:
- Memory exhaustion
- File descriptor limits hit
- Database connection pool exhaustion
- Application crashes in production

**Why It Matters:**
- Hard to catch in code review (hidden in complex control flow)
- Only shows up in production under load
- Costs companies money (downtime, debugging time)
- Junior developers make these mistakes frequently

**The Goal:**
Create a tool that automatically finds these leaks BEFORE code reaches production, integrated into CI/CD pipelines.

---

## 2. WHAT IS LEAKGUARD? (ELEVATOR PITCH)

**30-Second Version:**
"LeakGuard is a Python static analysis tool that finds resource leaks in your code before they reach production. It uses AST analysis and control-flow tracking to detect when files, sockets, database connections, or locks are opened but never closed. It integrates directly into CI/CD pipelines to automatically block leaky code."

**Key Points to Memorize:**
- ✅ Python-only (uses only standard library)
- ✅ AST-based (no regex, understands actual code structure)
- ✅ Control-flow aware (handles early returns, exceptions, branches)
- ✅ CI/CD ready (pre-commit hooks + GitHub Actions)
- ✅ Confidence scoring (definitely/likely/possible)
- ✅ 90% accuracy with 10% false positive rate

---

## 3. THE PROBLEM WE'RE SOLVING

### Real-World Scenario:

**Before LeakGuard:**
```python
def process_user_data(user_id):
    db = sqlite3.connect('users.db')
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        return None  # 🐛 BUG: db connection never closed!
    
    cursor.close()
    db.close()
    return user
```

**What Happens:**
- Works fine in testing (small number of requests)
- In production: 1000 requests/second
- Each failed lookup leaks a DB connection
- After 100 connections, database refuses new connections
- **Application crashes** 💥

**Manual Code Review Missed It Because:**
- The close() calls ARE there (at the bottom)
- The early return is easy to overlook
- Reviewer focused on business logic, not resource management

---

## 4. OUR SOLUTION EXPLAINED

### How LeakGuard Catches It:

```bash
$ leakguard scan my_code.py

[LIKELY LEAK] my_code.py:8
  Resource: database (sqlite3.connect('users.db'))
  Resource opened but not closed on early return path at line 9

Build failed: found leaks at 'likely' confidence level
```

### What Makes It Smart:

1. **Understands Code Structure:** Parses Python into AST (Abstract Syntax Tree), not just text matching
2. **Tracks All Paths:** Follows every possible execution path (normal flow, early returns, exceptions)
3. **Proves Safety:** Must see a close() on EVERY path, or it's flagged
4. **Recognizes Safe Patterns:** Knows that `with` statements automatically close resources
5. **Gives Confidence Levels:** Not all findings are equal - ranks them by certainty

---

## 5. HOW IT WORKS (TECHNICAL DEEP DIVE)

### Architecture (6 Components):

```
User Code (Python file)
    ↓
1. CLI Interface
    ↓
2. AST Parser (Python's ast module)
    ↓
3. Resource Analyzer
    ↓
4. Control Flow Tracker (CFG-lite)
    ↓
5. Confidence Scorer
    ↓
6. Report Generator
```

### Step-by-Step Breakdown:

#### **Step 1: CLI Interface** (`cli.py`)
- Entry point: `leakguard scan <path>`
- Accepts flags: `--fail-on=definitely|likely|possible`
- Finds all .py files recursively
- Calls analyzer on each file

**Code to Know:**
```python
# Main command structure
def scan_command(args):
    files = find_python_files(path)
    for py_file in files:
        file_findings = analyze_file(py_file)
        report.add(finding)
    report.print_summary()
```

---

#### **Step 2: AST Parser** (Python's `ast` module)
- Converts Python code into a tree structure
- Each code construct becomes a node (FunctionDef, Call, With, etc.)
- We walk this tree looking for patterns

**Example AST Structure:**
```python
# Code:
f = open("file.txt")

# Becomes AST:
Assign(
    targets=[Name(id='f')],
    value=Call(
        func=Name(id='open'),
        args=[Constant(value='file.txt')]
    )
)
```

**Why AST vs Regex?**
- Regex: `open\(.*\)` — catches comments, strings, false matches
- AST: Only catches actual function calls in executable code
- AST understands scope, nesting, control flow

---

#### **Step 3: Resource Analyzer** (`analyzer.py`)
- Walks the AST using visitor pattern
- Identifies resource acquisitions: `open()`, `socket.socket()`, `sqlite3.connect()`, etc.
- Tracks variable assignments: "variable `f` now holds a file"
- Identifies release calls: `.close()`, `.release()`

**What It Tracks** (defined in `resources.py`):
```python
RESOURCE_PATTERNS = [
    ResourcePattern(
        name="file",
        acquisitions=[(None, "open"), ("io", "open")],
        release_methods=["close"],
    ),
    ResourcePattern(
        name="socket",
        acquisitions=[("socket", "socket")],
        release_methods=["close"],
    ),
    # ... database, locks, etc.
]
```

**Code to Know:**
```python
class ResourceAnalyzer(ast.NodeVisitor):
    def visit_Assign(self, node):
        # Track: f = open("file.txt")
        
    def visit_Call(self, node):
        # Check if it's open(), connect(), etc.
        
    def visit_With(self, node):
        # Context manager = automatically safe
```

---

#### **Step 4: Control Flow Tracker** (`cfg.py`)
- Simulates execution paths through the code
- Tracks what happens to each resource on each path

**Path Examples:**

**Simple Path:**
```python
f = open("file.txt")  # Acquire
f.close()             # Release
# ✅ Safe: single path, resource closed
```

**Branching Paths:**
```python
f = open("file.txt")   # Acquire
if condition:
    return data        # Path 1: early exit
f.close()              # Path 2: normal flow
# ❌ Leak: Path 1 never closes
```

**Exception Paths:**
```python
f = open("file.txt")    # Acquire
try:
    process(f)
finally:
    f.close()           # Runs on ALL paths (normal + exception)
# ✅ Safe: finally guarantees close
```

**How We Track Paths:**
```python
class PathState:
    def __init__(self):
        self.resources = {}  # var_name -> resource_info
        
    def acquire(self, var_name, resource_type):
        self.resources[var_name] = {"type": resource_type, "closed": False}
        
    def release(self, var_name):
        if var_name in self.resources:
            self.resources[var_name]["closed"] = True
            
    def has_leaks(self):
        return any(not r["closed"] for r in self.resources.values())
```

---

#### **Step 5: Confidence Scorer** (`confidence.py`)
Not all leaks are equal. We classify them:

**DEFINITELY (Highest Confidence):**
- Resource opened, no close() anywhere in function
- Example: `f = open("x.txt"); return data`
- **Action:** Always fail the build

**LIKELY (Medium Confidence):**
- Resource closed on some paths but not all
- Example: Early return before close()
- **Action:** Fail by default (but configurable)

**POSSIBLE (Lowest Confidence):**
- Resource passed to unknown function (ownership unclear)
- Variable reassigned (first resource might be lost)
- Example: `helper(f)` — does helper close it? We don't know
- **Action:** Warn only (configurable to fail)

**Code:**
```python
class Confidence(Enum):
    DEFINITELY = "definitely"
    LIKELY = "likely"
    POSSIBLE = "possible"
    
    def should_fail(self, threshold):
        levels = {DEFINITELY: 3, LIKELY: 2, POSSIBLE: 1}
        return levels[self] >= levels[threshold]
```

---

#### **Step 6: Report Generator** (`report.py`)
Formats findings for humans and CI systems

**Output Format:**
```
[LIKELY LEAK] file.py:42
  Resource: file (open('data.txt'))
  Resource opened but not closed on early return path at line 45

Summary:
  Definitely leaked: 1
  Likely leaked: 2
  Possibly leaked: 1
```

**Exit Codes for CI:**
- `0` = No leaks (build passes)
- `1` = Leaks found at/above threshold (build fails)

---

## 6. WHAT MAKES US UNIQUE

### Comparison with Alternatives:

| Approach | How It Works | Limitations |
|----------|--------------|-------------|
| **Manual Code Review** | Human reads code | Slow, inconsistent, misses edge cases |
| **Regex/Grep** | Text search: `grep -E 'open\('` | No understanding of context, high false positives |
| **Pylint** | Generic linter | Not resource-specific, shallow analysis |
| **LeakGuard (Us)** | AST + CFG + resource-specific rules | Limited to local variables, no inter-procedural |

### Our Unique Advantages:

1. **Resource-Specific Knowledge**
   - We know `open()` needs `.close()`
   - We know `with` statements are safe
   - Generic linters don't have this domain knowledge

2. **Path-Sensitive Analysis**
   - We track ALL execution paths (early returns, exceptions, branches)
   - Regex can't do this
   - Most linters don't go this deep

3. **Zero Dependencies**
   - Uses only Python standard library
   - No external tools to install
   - Runs anywhere Python runs

4. **CI/CD First**
   - Built for automation from day 1
   - Pre-commit hooks + GitHub Actions included
   - Exit codes designed for pipelines

5. **Honest About Limitations**
   - We document our 10% FP/FN rates
   - We explain what we CAN'T detect
   - We provide workarounds
   - **Judges love honesty over hype**

---

## 7. REAL-WORLD APPLICATIONS

### Where LeakGuard Would Be Used:

#### **1. E-Commerce Platform (High Traffic)**
**Scenario:** Payment processing service
**Problem:** Database connection leak during payment failures
**Impact:** During Black Friday sale, connections exhausted after 2 hours
**LeakGuard's Role:** Catches leak in CI before deployment
**Value:** Prevented potential $100K+ in lost sales

#### **2. Financial Services (Compliance)**
**Scenario:** Trading platform
**Problem:** File handles leaked when processing transaction logs
**Impact:** System runs out of file descriptors, crashes during market hours
**LeakGuard's Role:** Daily scans in CI catch leaks before production
**Value:** Regulatory compliance, avoided SEC fines

#### **3. Healthcare (Data Security)**
**Scenario:** Patient records system
**Problem:** Encryption key files left open
**Impact:** Security audit failure, potential HIPAA violation
**LeakGuard's Role:** Pre-commit hook blocks commits with file leaks
**Value:** HIPAA compliance, patient data protection

#### **4. SaaS Startup (Developer Experience)**
**Scenario:** Small team, junior developers
**Problem:** New devs frequently forget to close resources
**Impact:** Customer complaints about "app feels slow"
**LeakGuard's Role:** Automated code review, teaches best practices
**Value:** Faster onboarding, fewer production bugs

#### **5. Open Source Project (Code Quality)**
**Scenario:** Popular Python library
**Problem:** Contributors from around the world, varying skill levels
**Impact:** Resource leaks reported in issues, maintainer burnout
**LeakGuard's Role:** GitHub Action blocks PRs with leaks
**Value:** Maintains project quality, reduces maintainer burden

---

## 8. ESSENTIAL CODE KNOWLEDGE

### Files You Should Understand:

#### **1. `resources.py` (Easiest - Start Here)**
**What it does:** Defines what resources we track

**Key concept:**
```python
ResourcePattern(
    name="file",
    acquisitions=[(None, "open")],  # How to acquire
    release_methods=["close"],      # How to release
)
```

**Judge Question:** "What resources do you track?"
**Answer:** "Files, sockets, databases, and locks. It's defined in a single config file, making it easy to add new resource types."

---

#### **2. `confidence.py` (Simple - 50 lines)**
**What it does:** Scores findings as definitely/likely/possible

**Key concept:**
```python
class Confidence(Enum):
    DEFINITELY = "definitely"
    LIKELY = "likely"
    POSSIBLE = "possible"
```

**Judge Question:** "How do you avoid false positives?"
**Answer:** "We use confidence scoring. 'Definitely' means no close() anywhere. 'Likely' means close() exists but not on all paths. 'Possible' means ownership is unclear. Teams can tune the threshold."

---

#### **3. `cli.py` (Entry Point)**
**What it does:** Command-line interface

**Key functions:**
- `scan_command(args)` - Main scan logic
- `find_python_files(path)` - Recursively find .py files
- `--fail-on` flag handling

**Judge Question:** "How would a developer use this?"
**Answer:** "Just run `leakguard scan .` in their project. It scans all Python files and reports leaks. In CI, we use `--fail-on=likely` to block builds."

---

#### **4. `analyzer.py` (Core Logic - Most Important)**
**What it does:** The brain - finds acquisitions and releases

**Key concepts:**
```python
class ResourceAnalyzer(ast.NodeVisitor):
    # Walks the AST tree
    
    def visit_Call(self, node):
        # Is this open(), connect(), etc?
        
    def visit_With(self, node):
        # Context manager = safe
        
    def visit_Return(self, node):
        # Early return = check if resources closed
```

**Judge Question:** "How does it actually work?"
**Answer:** "We parse Python code into an AST - a tree structure. We walk the tree looking for resource acquisitions like open(). Then we track all execution paths to ensure every path closes the resource."

---

#### **5. `cfg.py` (Advanced - Understand Conceptually)**
**What it does:** Control flow tracking

**Key concept:** Simulates execution paths
- Normal path: line by line
- Branch paths: if/else splits into 2 paths
- Exception paths: try/except creates alternate paths
- Must check ALL paths for close()

**Judge Question:** "What about complex control flow?"
**Answer:** "We build a lightweight control flow graph. When we hit an if/else, we track both branches independently. A leak is only reported if at least one path doesn't close the resource."

---

#### **6. `report.py` (Simple - Output Formatting)**
**What it does:** Formats findings for humans

**Key concepts:**
```python
class LeakFinding:
    file_path: str
    acquisition_line: int
    resource_type: str
    confidence: Confidence
    explanation: str
```

---

### Key Algorithms to Know:

#### **Algorithm 1: AST Visitor Pattern**
```python
# We inherit from ast.NodeVisitor
# Override visit_* methods for nodes we care about

def visit_Call(self, node):
    # Called for every function call
    if is_resource_acquisition(node):
        self.track_resource()
    self.generic_visit(node)  # Continue walking
```

**Why?** Python's AST module does the hard work of parsing. We just define what to do at each node.

---

#### **Algorithm 2: Path Tracking**
```
1. Start with empty path state
2. For each statement:
   a. If resource acquisition: mark as open
   b. If resource release: mark as closed
   c. If branch (if/else): split into 2 paths
   d. If early exit (return): check current state
3. At function end: check if any paths have open resources
```

---

## 9. STRETCH GOALS ACHIEVED

### From Original Problem Statement:

**Stretch Goal 1: ✅ Support Multiple Resource Types**
- ✅ Files (open, pathlib.Path.open, io.open)
- ✅ Sockets (socket.socket, socket.create_connection)
- ✅ Databases (sqlite3.connect)
- ✅ Locks (threading.Lock().acquire)

**Stretch Goal 2: ✅ Context Manager Detection**
- ✅ Recognizes `with` statements as safe
- ✅ Doesn't flag false positives for proper usage

**Stretch Goal 3: ✅ CI/CD Integration**
- ✅ Pre-commit hook configuration
- ✅ GitHub Actions workflow
- ✅ Proper exit codes for automation

**Stretch Goal 4: ✅ Confidence Scoring**
- ✅ Three-tier system (definitely/likely/possible)
- ✅ Configurable thresholds via CLI

**Stretch Goal 5: ✅ Comprehensive Testing**
- ✅ 20 test fixtures (10 clean, 10 leaky)
- ✅ Documented accuracy (90% with 10% FP/FN)
- ✅ Honest limitations documentation

**Bonus Achievements:**
- ✅ Zero external dependencies
- ✅ Professional documentation
- ✅ Extensibility (easy to add new resources)
- ✅ Human-readable explanations for each finding

---

## 10. DEMO SCRIPT FOR JUDGES

### **Demo Flow (5-7 minutes):**

#### **1. Problem Introduction (1 min)**
"Resource leaks are silent killers. They work fine in testing but crash production systems under load. We built LeakGuard to catch them automatically."

#### **2. Show a Real Leak (1 min)**
```python
# demo_leak.py
def process_file(filename):
    f = open(filename)
    if not validate(filename):
        return None  # BUG!
    data = f.read()
    f.close()
    return data
```

"See the bug? The file is never closed if validation fails. Manual review missed it. Watch LeakGuard catch it:"

#### **3. Run LeakGuard (30 sec)**
```bash
$ leakguard scan demo_leak.py

[LIKELY LEAK] demo_leak.py:2
  Resource: file (open(filename))
  Resource opened but not closed on early return path at line 4

Summary:
  Definitely leaked: 0
  Likely leaked: 1
  Possibly leaked: 0
```

"Caught it! Line 2 opens the file, line 4's early return skips the close."

#### **4. Show the Fix (30 sec)**
```python
def process_file(filename):
    with open(filename) as f:  # Safe!
        if not validate(filename):
            return None
        return f.read()
```

"Using a context manager. Now watch:"

```bash
$ leakguard scan demo_leak.py

No resource leaks detected ✅
```

#### **5. Show CI Integration (1 min)**
"This runs automatically in your pipeline. Show `.github/workflows/leakguard.yml`."

"Every commit, every PR - LeakGuard checks for leaks. Blocks merges until fixed."

#### **6. Show Test Results (1 min)**
"We tested on 20 fixtures - 90% accuracy. Show the test results table from README."

"We're honest about limitations. Show docs/limitations.md."

#### **7. Architecture (1 min)**
"Show the architecture diagram from README."

"Six components: CLI → AST Parser → Analyzer → CFG Tracker → Confidence Scorer → Report."

#### **8. Closing (30 sec)**
"Real-world ready. Zero dependencies. Extensible. Open source."

---

## 11. Q&A: COMMON JUDGE QUESTIONS

### **Technical Questions:**

**Q: How is this different from Pylint?**
A: "Pylint is a general linter. We're resource-specific. Pylint might say 'unused variable' but won't track whether a file was closed on all execution paths. We understand open/close semantics specifically."

**Q: What if someone uses a custom close method?**
A: "Great question! It's configurable in resources.py. You can add custom acquisition/release patterns. We also have a whitelist for safe transfer functions."

**Q: How do you handle inter-procedural analysis (functions calling functions)?**
A: "Currently we don't - that's a known limitation documented in docs/limitations.md. We track local variables within a function. For MVP, this catches 90% of leaks. Future work would add inter-procedural tracking."

**Q: False positive rate?**
A: "10% on our test fixtures. Most false positives are resources passed to helper functions where ownership is unclear. We mark these as 'possible' so teams can tune the threshold."

**Q: What about async code?**
A: "Not yet supported. Our MVP focuses on synchronous code. Async would require tracking across await boundaries - feasible future work."

**Q: Can it fix the leaks automatically?**
A: "No, we only detect. Auto-fix is risky - we might break business logic. We give clear line numbers and explanations so developers can fix correctly."

---

### **Practical Questions:**

**Q: How would a company adopt this?**
A: "Three steps: 1) Install as dev dependency, 2) Add pre-commit hook, 3) Add to CI pipeline. Takes 10 minutes. Works with existing workflows."

**Q: Performance? Will it slow down CI?**
A: "It's fast - pure Python parsing. Our test suite (20 files) runs in under 1 second. A typical project (1000 files) would take maybe 10-30 seconds."

**Q: What about legacy codebases with existing leaks?**
A: "Start with --fail-on=definitely to catch only the worst leaks. Gradually tighten to 'likely'. Or use a baseline feature (future work) to track new leaks only."

**Q: Open source?**
A: "Yes! MIT licensed. Available on GitHub. Contributions welcome."

---

### **Business Questions:**

**Q: Who would use this?**
A: "Any company with Python backend services. Especially fintech, healthcare, e-commerce where leaks cause customer impact. Also valuable for training junior developers."

**Q: What's the ROI?**
A: "One production outage from a resource leak can cost thousands in lost revenue plus engineering time. This catches it in development. ROI is positive after preventing just one incident."

**Q: Competitive landscape?**
A: "No Python-specific resource leak detector exists in open source. Pylint does generic linting. Our niche is resource management specifically, with CI/CD focus."

---

### **Stretch/Tough Questions:**

**Q: What's your biggest limitation?**
A: "Honest answer: We don't track resources across function boundaries. If you pass a file to another function, we can't tell if that function closes it. Workaround is a whitelist. Full solution needs inter-procedural analysis."

**Q: Why not use machine learning?**
A: "Static analysis is deterministic and explainable. ML would need huge training data and still might miss edge cases. Our approach guarantees we check every path. Plus, no training data needed."

**Q: What if I disagree with a finding?**
A: "Two options: 1) Use confidence thresholds to filter, 2) Add the pattern to a whitelist. We're practical - not trying to be 100% strict."

**Q: How do you prevent false negatives?**
A: "We can't catch everything - that's why we document our 10% FN rate. We prioritize low false positives (don't annoy developers) over catching every possible leak. Better to catch 90% reliably than 95% with noise."

---

## 12. TEAM MEMBER RESPONSIBILITIES

### **For the Presentation:**

**Person 1 - Problem & Demo:**
- Explain resource leaks and their impact
- Show live demo of catching a leak
- Show the fix

**Person 2 - Technical Architecture:**
- Explain AST parsing and CFG tracking
- Walk through the 6 components
- Show code snippets from analyzer.py

**Person 3 - CI/CD & Real-World:**
- Demonstrate GitHub Actions integration
- Discuss real-world applications
- Show test results and accuracy

**Person 4 - Q&A Specialist:**
- Answer judge questions
- Discuss limitations honestly
- Talk about future work and extensibility

**All - Rotate These:**
- Show enthusiasm (this is genuinely useful!)
- Reference the 90% accuracy explicitly
- Mention zero dependencies
- Emphasize CI/CD first design

---

## 13. KEY TALKING POINTS (MEMORIZE THESE)

### **The Elevator Pitch (30 seconds):**
"LeakGuard is a Python static analysis tool that catches resource leaks before production. It uses AST parsing and control-flow analysis to ensure files, sockets, databases, and locks are properly closed on all execution paths. It integrates directly into CI/CD pipelines with 90% accuracy and zero external dependencies."

### **The Technical Highlight:**
"Unlike regex-based tools or generic linters, LeakGuard understands Python code structure through AST analysis and tracks all execution paths including early returns and exception handlers. This gives us resource-specific accuracy that other tools can't match."

### **The Business Value:**
"One resource leak in production can cause cascading failures costing thousands in downtime. LeakGuard catches these in development, automated through pre-commit hooks and GitHub Actions. The ROI is clear: prevent one outage and you've saved more than this tool costs to run."

### **The Honest Limitation:**
"We're transparent about our limits: 10% false positive rate, no inter-procedural analysis, local variables only. But we've documented workarounds and made it extensible. We'd rather be honest and useful than overpromise."

### **The Differentiator:**
"Zero dependencies. Pure Python stdlib. Runs anywhere. Extensible resource definitions. CI/CD first. Open source. We built this to actually be adopted, not just to win a hackathon."

---

## 14. FINAL CHECKLIST BEFORE JUDGES

**Technical Prep:**
- [ ] Can explain AST vs regex
- [ ] Can walk through analyzer.py code
- [ ] Can explain confidence scoring
- [ ] Know the 6 architecture components
- [ ] Can demo live leak detection

**Project Knowledge:**
- [ ] Know our 90% accuracy rate
- [ ] Know our 10% FP/FN rates
- [ ] Can list 4 resource types we track
- [ ] Can name 3 stretch goals achieved
- [ ] Know our key limitation (no inter-procedural)

**Presentation Prep:**
- [ ] Demo script practiced
- [ ] Backup demo files ready
- [ ] README.md open for reference
- [ ] GitHub repo looking professional
- [ ] Everyone can answer at least 5 judge questions

**Soft Skills:**
- [ ] Enthusiasm! (This is genuinely cool)
- [ ] Honesty about limitations
- [ ] Clear explanations (avoid jargon)
- [ ] Team coordination (who answers what)
- [ ] Confidence without arrogance

---

## 15. BONUS: ONE-LINERS FOR IMPACT

Use these for impact during presentation:

- "We catch bugs before your customers do."
- "Static analysis with zero runtime overhead."
- "One command, all your leaks found."
- "Built for CI/CD, not just code review."
- "90% accurate, 100% honest about the 10%."
- "Zero dependencies means zero friction to adopt."
- "Open source, MIT licensed, contribution-ready."
- "Prevents production fires before they start."

---

## STUDY PLAN FOR YOUR TEAM

**Day 1 (2 hours):**
- Read sections 1-3 (Problem, Solution, How It Works)
- Run the demo yourself
- Understand AST basics

**Day 2 (2 hours):**
- Read sections 4-7 (Uniqueness, Real-World, Code Knowledge)
- Browse analyzer.py and resources.py
- Practice explaining to each other

**Day 3 (2 hours):**
- Read sections 8-11 (Stretch Goals, Demo Script, Q&A)
- Practice the demo presentation
- Drill Q&A questions

**Day 4 (1 hour):**
- Final review of Key Talking Points
- Team practice presentation
- Assign roles (who presents what)

---

## RESOURCES TO KEEP HANDY

- **GitHub Repo:** https://github.com/siddhantpawar1221-dev/VH26-GRAPHITE
- **This Guide:** Share with all teammates
- **README.md:** Reference during Q&A
- **docs/limitations.md:** Honesty wins judges
- **Test fixtures:** Show real examples

---

**REMEMBER:** You built something genuinely useful. Be proud, be honest, and show enthusiasm. Judges love teams who understand their trade-offs and can explain complex ideas simply.

**Good luck! 🚀**

---

Generated for VH26-GRAPHITE Team
LeakGuard Project Documentation
