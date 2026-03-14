# Claude Reasoning Loop (Ralph Loop Pattern)

Enable Claude Code to work autonomously on multi-step tasks until completion using the Ralph Loop implementation.

## What this skill does

Implements a continuous reasoning loop that keeps Claude working on a task until it's fully complete. Uses file-based and promise-based completion detection to ensure tasks are finished before moving on.

## Prerequisites

- Claude Code installed and configured
- Task files in Needs_Action/ folder
- Company_Handbook.md with task completion rules
- Python 3.12+
- Ralph Loop script implemented

## Concept

**The Problem**: Claude Code processes one prompt at a time. For autonomous operation, we need Claude to keep working until a task is complete.

**The Solution**: Ralph Loop pattern:
1. Creates a task prompt
2. Runs Claude iteration
3. Checks if task is complete (file in Done/ or promise detected)
4. If incomplete: runs another iteration
5. If complete: exits successfully
6. Repeats until task done or max iterations reached

## Setup

### Ralph Loop Implementation

**File**: `scripts/ralph_loop.py` (352 lines)

Key features:
- File-based completion detection
- Promise-based completion detection
- Max iteration limits
- State persistence
- Comprehensive logging

## Usage

```bash
# Run Ralph Loop on specific task
uv run python scripts/ralph_loop.py --task-file AI_Employee_Vault/Needs_Action/EMAIL_client.md

# Run with custom max iterations
uv run python scripts/ralph_loop.py --task-file task.md --max-iterations 15

# Run with promise-based completion
uv run python scripts/ralph_loop.py --task-file task.md --completion-promise "TASK_COMPLETE"
```

Or via Claude Code:
```
Please use the Ralph Loop to process all pending tasks in Needs_Action until complete.
```

## Implementation

**File**: `scripts/ralph_loop.py` (352 lines)

```python
class RalphLoop:
    def __init__(self, task_file: Path, max_iterations: int = 10):
        self.task_file = task_file
        self.max_iterations = max_iterations
        self.vault_path = Path('AI_Employee_Vault')
        self.done_path = self.vault_path / 'Done'

    def run(self) -> bool:
        """Run loop until task complete or max iterations"""
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n{'='*60}")
            print(f"Iteration {iteration}/{self.max_iterations}")
            print(f"{'='*60}\n")

            # Check file-based completion
            if self.check_file_completion():
                print(f"✓ Task complete: File moved to Done/")
                return True

            # Run Claude iteration
            prompt = self.create_prompt(iteration)
            success, output = self.run_claude_iteration(prompt)

            # Check promise-based completion
            if self.check_promise_completion(output):
                print(f"✓ Task complete: Promise detected")
                return True

            # Continue loop
            print(f"⟳ Task incomplete, continuing...")

        print(f"⚠ Max iterations reached")
        return False

    def check_file_completion(self) -> bool:
        """Check if task file moved to Done/"""
        done_file = self.done_path / self.task_file.name
        return done_file.exists()

    def check_promise_completion(self, output: str) -> bool:
        """Check for completion promise in output"""
        return '<promise>TASK_COMPLETE</promise>' in output
```

## Performance Metrics

**Your Actual Results:**
- Implementation: 352 lines of Python
- Max Iterations: 10 (configurable)
- Completion Detection: File-based + Promise-based
- State Tracking: Comprehensive logging
- Status: Implemented and tested ✅

## Workflow

```
1. Orchestrator starts
   ├── Reads task from Needs_Action/
   ├── Generates prompt
   └── Starts iteration loop

2. Iteration N begins
   ├── Run Claude with prompt
   ├── Claude reads task
   ├── Claude performs actions
   ├── Claude attempts to exit
   └── Stop hook intercepts

3. Stop hook checks
   ├── Is file in Done/?
   │   ├── YES → Allow exit (complete)
   │   └── NO → Block exit (continue)
   ├── Max iterations reached?
   │   ├── YES → Allow exit (timeout)
   │   └── NO → Continue loop
   └── Re-inject prompt

4. Loop continues until:
   ├── Task file moved to Done/ (success)
   ├── Completion promise detected (success)
   └── Max iterations reached (timeout)
```

## Completion Strategies

### Strategy 1: File Movement (Recommended)

Task is complete when file moves to Done/:
```python
# Claude's final action
shutil.move(
    'Needs_Action/EMAIL_client.md',
    'Done/EMAIL_client.md'
)
```

**Pros**: Natural workflow, reliable detection
**Cons**: Requires file system operations

### Strategy 2: Completion Promise

Claude outputs special tag:
```python
# Claude's final output
print("<promise>TASK_COMPLETE</promise>")
```

**Pros**: Simple, no file operations needed
**Cons**: Claude might forget to output promise

### Strategy 3: Status Field

Update task file metadata:
```markdown
---
status: completed
---
```

**Pros**: Trackable, auditable
**Cons**: Requires parsing, less reliable

## Example Task Processing

**Task File**: `Needs_Action/EMAIL_client_inquiry.md`

```markdown
---
type: email
from: client@example.com
priority: high
status: pending
---

## Email Content
Client asking about pricing for website project.

## Required Actions
- [ ] Draft response with pricing
- [ ] Create approval request
- [ ] Update Dashboard
```

**Iteration 1**:
```
Claude reads task
Claude drafts response
Claude creates: Pending_Approval/EMAIL_response.md
Claude updates Dashboard
Claude attempts exit
Stop hook: File still in Needs_Action/ → Continue
```

**Iteration 2**:
```
Claude sees task still pending
Claude checks Pending_Approval/
Claude realizes waiting for human approval
Claude adds note to task file
Claude attempts exit
Stop hook: File still in Needs_Action/ → Continue
```

**Iteration 3**:
```
Claude checks approval status
Human has approved (file in Approved/)
Claude triggers email send
Claude logs result
Claude moves task to Done/
Stop hook: File in Done/ → Exit (Success!)
```

## Advanced Features

### 1. Multi-Task Processing

```python
def process_all_pending(self):
    """Process all tasks in Needs_Action/"""
    tasks = list(self.needs_action.glob('*.md'))

    for task in sorted(tasks, key=self.get_priority):
        print(f"\nProcessing: {task.name}")
        success = self.run_task_loop(task.name)

        if not success:
            print(f"⚠ Task {task.name} did not complete")
            # Continue with next task or stop?
```

### 2. Priority-Based Processing

```python
def get_priority(self, task_path):
    """Extract priority from task metadata"""
    content = task_path.read_text()
    if 'priority: high' in content:
        return 0
    elif 'priority: medium' in content:
        return 1
    else:
        return 2
```

### 3. Dependency Handling

```python
def check_dependencies(self, task_path):
    """Check if task dependencies are met"""
    metadata = parse_metadata(task_path)
    depends_on = metadata.get('depends_on', [])

    for dep in depends_on:
        dep_path = self.done / dep
        if not dep_path.exists():
            return False  # Dependency not complete

    return True  # All dependencies met
```

### 4. Error Recovery

```python
def run_task_loop_with_recovery(self, task_file):
    """Run task loop with error recovery"""
    try:
        return self.run_task_loop(task_file)
    except Exception as e:
        print(f"Error processing {task_file}: {e}")

        # Create error report
        error_file = self.vault_path / 'Errors' / f'ERROR_{task_file}'
        error_file.write_text(f"""
---
task: {task_file}
error: {str(e)}
timestamp: {time.time()}
---

Task failed with error. Manual intervention required.
""")

        return False
```

## Safety Features

### 1. Max Iterations Limit

Prevents infinite loops:
```python
MAX_ITERATIONS = 10  # Stop after 10 attempts
```

### 2. Timeout Protection

```python
MAX_RUNTIME = 600  # 10 minutes max per task

if time.time() - state['started'] > MAX_RUNTIME:
    print("⚠ Task timeout - exceeded max runtime")
    return False
```

### 3. Stuck Detection

```python
def detect_stuck(self, task_file, iterations):
    """Detect if task is stuck in loop"""
    if iterations > 5:
        # Check if any progress made
        logs = self.get_task_logs(task_file)
        if len(set(logs)) == 1:  # Same action repeated
            print("⚠ Task appears stuck")
            return True
    return False
```

## Troubleshooting

**"Loop exits immediately"**
- Check task file exists in Needs_Action/
- Verify file paths are correct
- Test with simple task first

**"Infinite loop detected"**
- Reduce MAX_ITERATIONS
- Check task completion logic
- Verify file movement works
- Add more logging

**"Task never completes"**
- Review task requirements (may be too complex)
- Check for missing dependencies
- Simplify task if needed
- Verify Claude has necessary permissions

**"Module import errors"**
- Add project root to sys.path
- Verify all dependencies installed
- Check Python version (3.12+)

## Best Practices

1. **Clear Task Definitions** - Specify exact completion criteria
2. **Reasonable Iterations** - 10 is usually enough for most tasks
3. **Progress Logging** - Log each iteration's actions
4. **Error Handling** - Catch and report failures
5. **Human Oversight** - Review loop results regularly

## Performance Considerations

- Each iteration adds ~5-10 seconds
- Complex tasks may need 5-8 iterations
- Simple tasks complete in 1-2 iterations
- Monitor API usage (costs per iteration)

## Security Considerations

1. **Prevent Runaway** - Always set max iterations
2. **Validate Actions** - Check actions before execution
3. **Audit Trail** - Log all loop activity
4. **Resource Limits** - Monitor CPU/memory usage

## Next Steps

After setup:
1. Test with simple task (1-2 steps)
2. Try complex multi-step task
3. Monitor iteration counts
4. Adjust max iterations if needed
5. Integrate with other skills

## Related Skills

- `/schedule-tasks` - Run reasoning loops automatically
- `/approve-actions` - Handle approvals within loops
- `/monitor-gmail` - Trigger loops on new emails

---
**Phase**: 3 - Automation
**Tier**: Silver ✅ COMPLETE
**Estimated Setup Time**: 3-4 hours
**Dependencies**: Claude Code, Python 3.12+
**Status**: Implemented (352 lines)
**Implementation**: scripts/ralph_loop.py
**Reference**: https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
