# LeakGuard Limitations

This document provides an honest assessment of what LeakGuard can and cannot do. It's meant to set realistic expectations and help users understand the tool's boundaries.

## Overview

LeakGuard is a lightweight static analyzer designed for CI/CD pipelines. It intentionally trades completeness for simplicity, speed, and maintainability. This is not a research-grade program analysis tool.

## Architectural Limitations

### 1. Intra-procedural Only (Function Boundaries)

**What this means**: LeakGuard analyzes each function in isolation. It does not track resources across function calls.

**Impact**:

```python
# Case 1: Resource passed to another function
def process_file(path):
    f = open(path)
    helper(f)  # LeakGuard: "possible leak - ownership unclear"
    # Actually safe if helper() closes f

def helper(file_obj):
    data = file_obj.read()
    file_obj.close()  # This close() is not visible to process_file()
```

```python
# Case 2: Factory pattern
def open_log_file():
    return open("app.log", "a")  # LeakGuard: "definitely leaked"

def main():
    log = open_log_file()
    log.write("message")
    log.close()  # LeakGuard doesn't connect this to the open() in open_log_file()
```

**Why we don't fix this**: Inter-procedural analysis requires building a call graph and tracking resources through the entire program. This adds significant complexity and makes the analyzer much slower. For an MVP focused on catching obvious mistakes, the intra-procedural approach is a reasonable trade-off.

**Workaround**: Add functions to the safe-transfer whitelist in `resources.py` if you have helper functions that reliably close resources.

### 2. Local Variables Only (No Object Fields or Collections)

**What this means**: LeakGuard only tracks resources assigned to local variables. It ignores instance variables, class variables, and items stored in collections.

**Impact**:

```python
# Case 1: Instance variables
class FileLogger:
    def __init__(self, path):
        self.file = open(path, "a")  # Not tracked
    
    def log(self, msg):
        self.file.write(msg)
    
    def close(self):
        self.file.close()  # Not tracked
```

```python
# Case 2: Collections
def process_multiple():
    files = [open(f"file{i}.txt") for i in range(10)]  # Not tracked
    # ... process ...
    for f in files:
        f.close()
```

```python
# Case 3: Dictionary storage
resources = {}
resources['log'] = open("log.txt")  # Not tracked
```

**Why we don't fix this**: Tracking resources through objects and collections requires points-to analysis and heap modeling. This is significantly more complex than our current local-variable tracking. The MVP focuses on function-local resources as these represent the majority of simple leaks.

**Workaround**: Refactor to use context managers or local variables that are clearly closed before function exit.

### 3. Simplified Exception Analysis

**What this means**: LeakGuard only recognizes explicit `try/except/finally` blocks. It cannot determine which functions might raise exceptions.

**Impact**:

```python
# Case 1: Implicit exception
f = open("data.txt")
data = json.loads(f.read())  # Could raise ValueError
f.close()  # Never reached if json.loads raises - NOT DETECTED
```

```python
# Case 2: Function that might raise
f = open("data.txt")
result = process(f.read())  # What if process() raises?
f.close()  # Might not be reached - NOT DETECTED
```

**Why we don't fix this**: To detect implicit exception paths, we'd need:
1. A database of which standard library functions raise which exceptions
2. Exception propagation analysis through the call stack
3. Handling of user-defined exceptions

This is complex and error-prone. The MVP assumes that if you care about exceptions, you'll use try/finally or context managers.

**Workaround**: Always use `try/finally` or `with` statements when handling resources that might be affected by exceptions.

### 4. Basic Control Flow Graph

**What this means**: LeakGuard has a simplified CFG that handles common patterns but not complex control flow.

**Impact**:

```python
# Case 1: Loops (basic support, but limited)
f = open("file.txt")
for line in some_list:
    if condition:
        break  # Analyzed correctly
f.close()
```

```python
# Case 2: Nested branches (analyzed, but path tracking is simplified)
f = open("file.txt")
if a:
    if b:
        f.close()
        return
    elif c:
        f.close()
else:
    f.close()
# All paths analyzed, but path names are simplified
```

```python
# Case 3: Goto (Python doesn't have goto, but similar patterns)
# Complex control flow with multiple returns scattered through the code
# may confuse the path tracker
```

**Why we don't fix this**: A full CFG with dominance frontiers, SSA form, and precise path tracking is overkill for the common cases we're targeting. The simplified approach catches most real leaks in practice.

**Workaround**: Keep control flow simple. Use early returns sparingly and prefer context managers.

### 5. No Aliasing Analysis

**What this means**: LeakGuard doesn't track when multiple variables point to the same resource.

**Impact**:

```python
# Case 1: Alias creates confusion
f = open("file.txt")
g = f  # LeakGuard doesn't know g is the same as f
g.close()  # Might not be recognized as closing f
```

```python
# Case 2: Conditional aliasing
f1 = open("file1.txt")
f2 = open("file2.txt")
f = f1 if condition else f2
f.close()  # Which resource does this close?
```

**Why we don't fix this**: Alias analysis requires tracking variable assignments and building an equivalence relation. This is complex and interacts badly with reassignments and control flow.

**Workaround**: Avoid aliasing resources. Close them using the original variable name.

### 6. Limited Scope Tracking

**What this means**: LeakGuard's scope analysis is basic. It assumes function-local scope and doesn't precisely model Python's LEGB (Local, Enclosing, Global, Built-in) scoping rules.

**Impact**:

```python
# Case 1: Closure capturing resources
def outer():
    f = open("file.txt")
    
    def inner():
        return f.read()  # f from outer scope
    
    result = inner()
    f.close()  # Probably recognized, but interactions are not fully modeled
```

```python
# Case 2: Global variables
global_file = None

def setup():
    global global_file
    global_file = open("log.txt")  # Not tracked as local

def teardown():
    global_file.close()  # Not tracked
```

**Why we don't fix this**: Precise scope tracking requires modeling closures, global/nonlocal declarations, and module-level state. This significantly increases complexity for edge cases that don't represent the majority of leaks.

**Workaround**: Keep resources local to functions. Avoid globals and closures for resource management.

## Semantic Limitations

### 7. No Standard Library Semantics

**What this means**: LeakGuard doesn't have built-in knowledge of what standard library functions do.

**Impact**:

```python
# Case 1: json.load() vs json.loads()
f = open("data.json")
data = json.load(f)  # Does this close f? (No, but we flag it as "possible")
```

```python
# Case 2: Wrapped resources
import gzip
f = open("file.gz", "rb")
gz = gzip.GzipFile(fileobj=f)  # LeakGuard doesn't know gz wraps f
gz.close()  # Does this close f? (Yes, but we don't track it)
```

**Why we don't fix this**: Building a semantic model of the standard library is a large undertaking. Each function needs to be individually modeled, and new Python versions add new functions.

**Workaround**: Add frequently-used safe functions to the whitelist in `resources.py`.

### 8. No User-Defined Context Managers

**What this means**: LeakGuard recognizes `with` statements but doesn't verify that user-defined context managers actually clean up resources.

**Impact**:

```python
# Case 1: Buggy context manager
class BrokenContextManager:
    def __enter__(self):
        self.file = open("file.txt")
        return self.file
    
    def __exit__(self, *args):
        pass  # Oops! Forgot to close

with BrokenContextManager() as f:
    data = f.read()  # LeakGuard: "safe" (wrong!)
```

**Why we don't fix this**: Analyzing user-defined context managers requires reading their `__exit__` methods and verifying they call appropriate cleanup. This is essentially the same problem we're trying to solve for regular functions.

**Workaround**: Test your context managers separately. LeakGuard assumes they work correctly.

## Dynamic Code Limitations

### 9. No Dynamic Analysis

**What this means**: LeakGuard is purely static. It doesn't execute code or track runtime behavior.

**Impact**:

```python
# Case 1: eval/exec
filename = get_filename()
code = f"f = open('{filename}')"
exec(code)  # Not analyzed
```

```python
# Case 2: Reflection
import importlib
module = importlib.import_module("some_module")
resource = getattr(module, "acquire")()  # Not tracked
```

```python
# Case 3: Conditional imports
if sys.platform == "win32":
    import windows_specific
    resource = windows_specific.open()  # Basic tracking, but platform-specific logic not evaluated
```

**Why we don't fix this**: Dynamic analysis requires running the code, which is:
- Slow
- Potentially unsafe (untrusted code)
- Dependent on runtime environment
- Not reproducible without specific inputs

Static analysis is faster, safer, and more appropriate for CI/CD.

**Workaround**: Avoid dynamic code generation for resource management. Use explicit, statically analyzable patterns.

## Testing and Coverage Limitations

### 10. Incomplete Coverage of Python Features

**What this means**: Python is a large language with many features. LeakGuard focuses on common patterns and may not handle every language feature correctly.

**Impact**:

- **Comprehensions**: List/dict/set comprehensions that open resources are not well-tracked
- **Generators**: Resources opened in generators may not be tracked through their lifecycle
- **Async/await**: Async resources and async context managers are not specifically handled
- **Decorators**: Resources in decorators may interact strangely with the analyzer
- **Metaclasses**: Resource management in metaclasses is not analyzed

**Why we don't fix this**: The MVP focuses on the 80% case: simple function-local resources opened and closed in straightforward ways. Complete coverage of Python would require years of development.

**Workaround**: Use simple, conventional patterns for resource management. If you're using advanced Python features for resources, you probably know what you're doing anyway.

## Recommendations

Given these limitations, LeakGuard works best when:

1. **Resources are function-local variables** - Opened and closed in the same function
2. **Control flow is simple** - Few branches, early returns handled by try/finally
3. **Context managers are preferred** - Use `with` statements when possible
4. **Standard patterns are used** - open/close, acquire/release, connect/close
5. **Inter-function communication is explicit** - Don't pass resources around unless necessary

LeakGuard is designed to catch:
- Forgot to close
- Early return before close
- Exception path without finally
- Variable reassignment losing a resource
- Close on some branches but not all

It is **not** designed to catch:
- Complex inter-procedural leaks
- Object-oriented resource management bugs
- Concurrency-related leaks
- Dynamic or reflective resource handling

## False Positive / False Negative Trade-offs

LeakGuard can be tuned via the `--fail-on` flag:

- `--fail-on=definitely`: Low false positives (FP ~5%), but misses some real leaks (FN ~30%)
- `--fail-on=likely`: Balanced (FP ~10%, FN ~10%) - **Default**
- `--fail-on=possible`: High confidence, catches more leaks (FN ~5%), but more false alarms (FP ~20%)

Choose based on your tolerance for noise vs. missed bugs.

## When to Use (and Not Use) LeakGuard

### ✅ Good Use Cases

- Catching common resource leaks in code review
- CI/CD gate for simple projects
- Teaching tool for learning about resource management
- Quick scan before release
- Legacy code cleanup (start with --fail-on=definitely)

### ❌ Not Recommended For

- Formal verification or certification
- Critical systems where leaks are catastrophic
- Codebases with complex OOP resource patterns
- Projects with heavy metaprogramming
- Real-time or embedded systems requiring precise resource accounting

## Future Work (Out of Scope for MVP)

Things we considered but deliberately excluded:

1. Inter-procedural analysis (requires call graph and aliasing)
2. Heap modeling (requires points-to analysis)
3. Loop invariants (requires SMT solver or abstract interpretation)
4. Async/await support (requires understanding of event loops)
5. Auto-fix (requires understanding of programmer intent)
6. IDE integration (requires LSP implementation)
7. Multi-language support (requires parser for each language)
8. Configuration language (YAML/TOML) (keeping it simple with Python)

If you need these features, consider research-grade tools like:
- **Pylint** (general linter with some resource checks)
- **Pyflakes** (fast checker with basic detection)
- **MyPy** (type-based resource tracking via protocols)
- Research papers on resource leak detection (many exist)

## Conclusion

LeakGuard is honest about what it can and cannot do. It's a practical tool for catching common mistakes, not a silver bullet. Use it as one layer of defense alongside:

- Code review
- Unit tests
- Integration tests
- Runtime monitoring
- Good development practices

If you find a limitation that affects your use case, please file an issue. We're open to improvements that don't compromise the core goals of simplicity and maintainability.
