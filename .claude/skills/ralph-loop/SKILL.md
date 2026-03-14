# Ralph Loop - Autonomous Task Completion

**Type:** Automation Skill
**Purpose:** Keep Claude working on tasks until completion
**Tier:** Silver/Gold

## Overview

The Ralph Loop implements autonomous task completion by continuously re-prompting Claude until a task is fully done. Named after the "Ralph Wiggum" pattern from the hackathon spec.

## How It Works

1. **Task Detection**: Picks up a task file from `/Needs_Action`
2. **Move to Progress**: Moves task to `/In_Progress` to claim it
3. **Iteration Loop**: Runs Claude Code repeatedly with the task
4. **Completion Check**: Detects when task file moves to `/Done`
5. **Auto-Retry**: If Claude exits early, re-injects the prompt
6. **Max Iterations**: Stops after N attempts to prevent infinite loops

## Completion Strategies

### File-Based (Recommended)
Task is complete when the file moves from `/In_Progress` to `/Done`.

```bash
uv run python scripts/ralph_loop.py --task "EMAIL_urgent_client.md"
```

### Promise-Based
Claude outputs `<promise>TASK_COMPLETE</promise>` when done.

```bash
uv run python scripts/ralph_loop.py \
  --task "EMAIL_urgent_client.md" \
  --completion-promise "TASK_COMPLETE"
```

## Usage

### Basic Usage
```bash
# Process a specific task
uv run python scripts/ralph_loop.py --task "TASK_FILE.md"

# With custom iteration limit
uv run python scripts/ralph_loop.py \
  --task "TASK_FILE.md" \
  --max-iterations 20

# With custom vault path
uv run python scripts/ralph_loop.py \
  --task "TASK_FILE.md" \
  --vault "/path/to/vault"
```

### Advanced Options
```bash
uv run python scripts/ralph_loop.py \
  --task "TASK_FILE.md" \
  --max-iterations 15 \
  --completion-promise "DONE" \
  --check-interval 10 \
  --vault "AI_Employee_Vault"
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--task` | Required | Task file name in Needs_Action |
| `--vault` | AI_Employee_Vault | Path to Obsidian vault |
| `--max-iterations` | 10 | Max attempts before giving up |
| `--completion-promise` | TASK_COMPLETE | Promise string for completion |
| `--check-interval` | 5 | Seconds between iterations |

## State Tracking

Ralph Loop maintains state in `.state/ralph_loop_<task>.json`:

```json
{
  "iteration": 3,
  "started": "2026-02-26T23:30:00Z",
  "status": "running",
  "task_file": "EMAIL_urgent_client.md",
  "completion_method": null,
  "last_updated": "2026-02-26T23:35:00Z"
}
```

## Logs

Detailed logs are written to `Logs/ralph_loop_<timestamp>.md`:

```
2026-02-26 23:30:00 [INFO] 🔄 Ralph Loop Started
2026-02-26 23:30:00 [INFO] Task: EMAIL_urgent_client.md
2026-02-26 23:30:00 [INFO] Max iterations: 10
2026-02-26 23:30:05 [INFO] --- Iteration 1/10 ---
2026-02-26 23:30:05 [INFO] Running Claude Code...
2026-02-26 23:30:45 [INFO] --- Iteration 2/10 ---
2026-02-26 23:31:30 [INFO] ✓ Task file found in /Done
2026-02-26 23:31:30 [INFO] ✅ Task completed (file moved to /Done)
```

## Integration with Orchestrator

Add to your orchestrator to automatically process tasks:

```python
from scripts.ralph_loop import RalphLoop

# When new task detected
for task_file in needs_action.glob("*.md"):
    loop = RalphLoop(
        vault_path="AI_Employee_Vault",
        task_file=task_file.name,
        max_iterations=10
    )
    success = loop.run()
    if success:
        logger.info(f"✓ Task completed: {task_file.name}")
    else:
        logger.warning(f"⚠ Task incomplete: {task_file.name}")
```

## Alerts

If max iterations is reached without completion, an alert is created:

`Needs_Action/ALERT_RALPH_INCOMPLETE_<timestamp>.md`

The alert includes:
- Task file name
- Number of iterations attempted
- Link to logs
- Restart command

## Best Practices

### Task File Format
Ensure task files have clear completion criteria:

```markdown
---
type: task
priority: high
status: pending
---

## Task: Reply to Client Email

**Completion Criteria:**
- [ ] Draft reply email
- [ ] Get approval
- [ ] Send email
- [ ] Move this file to /Done

**When complete:** Move this file to AI_Employee_Vault/Done/
```

### Iteration Limits
- Simple tasks: 5-10 iterations
- Complex tasks: 15-20 iterations
- Multi-step workflows: 20-30 iterations

### Monitoring
Check Ralph Loop status:
```bash
# View active loops
ls AI_Employee_Vault/.state/ralph_loop_*.json

# View recent logs
ls -lt AI_Employee_Vault/Logs/ralph_loop_*.md | head -5

# Check for incomplete alerts
ls AI_Employee_Vault/Needs_Action/ALERT_RALPH_INCOMPLETE_*.md
```

## Troubleshooting

### Loop Never Completes
- Check if task file has clear completion criteria
- Increase max iterations
- Review logs to see where Claude is stuck
- Verify file permissions for moving files

### Claude Exits Too Early
- Task might be ambiguous
- Add explicit "move to /Done when complete" instruction
- Use promise-based completion as fallback

### High Resource Usage
- Reduce check interval
- Lower max iterations
- Run during off-peak hours

## Examples

### Example 1: Process Email
```bash
# Task file: EMAIL_urgent_client.md
uv run python scripts/ralph_loop.py --task "EMAIL_urgent_client.md"
```

### Example 2: Multi-Step Task
```bash
# Task file: TASK_invoice_generation.md
uv run python scripts/ralph_loop.py \
  --task "TASK_invoice_generation.md" \
  --max-iterations 20
```

### Example 3: Batch Processing
```bash
# Process all pending tasks
for task in AI_Employee_Vault/Needs_Action/*.md; do
  uv run python scripts/ralph_loop.py --task "$(basename $task)"
done
```

## Testing

Test the Ralph Loop with a simple task:

```bash
# Create test task
cat > AI_Employee_Vault/Needs_Action/TEST_ralph_loop.md << 'EOF'
---
type: test
priority: low
status: pending
---

## Test Task: Ralph Loop

This is a test task for the Ralph Loop system.

**Instructions:**
1. Read this file
2. Create a file: AI_Employee_Vault/Done/TEST_ralph_loop_result.txt
3. Write "Ralph Loop Test Complete" to that file
4. Move this file to AI_Employee_Vault/Done/

**Completion:** When this file is in /Done, the test passes.
EOF

# Run Ralph Loop
uv run python scripts/ralph_loop.py --task "TEST_ralph_loop.md"

# Verify completion
ls AI_Employee_Vault/Done/TEST_ralph_loop.md
cat AI_Employee_Vault/Done/TEST_ralph_loop_result.txt
```

## Performance

Typical performance metrics:
- Simple tasks: 1-3 iterations, 1-2 minutes
- Medium tasks: 3-7 iterations, 3-5 minutes
- Complex tasks: 7-15 iterations, 5-10 minutes

## Security

Ralph Loop runs with the same permissions as Claude Code:
- Can read/write vault files
- Can execute MCP actions
- Respects approval workflows
- Logs all actions

**Important:** Set appropriate max iterations to prevent runaway loops.

## Future Enhancements

Planned improvements:
- Parallel task processing
- Priority-based scheduling
- Dynamic iteration limits based on task complexity
- Integration with health monitoring
- Automatic retry with exponential backoff

---

**Status:** Implemented
**Last Updated:** 2026-02-26
**Hackathon Tier:** Silver/Gold Requirement
