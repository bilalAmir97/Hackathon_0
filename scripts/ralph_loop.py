#!/usr/bin/env python3
"""
Ralph Loop - Autonomous Task Completion System

Keeps Claude Code working on a task until completion is detected.
Implements the "Ralph Wiggum" pattern from the hackathon spec.

Two completion strategies:
1. File-based: Task file moves from /Needs_Action to /Done
2. Promise-based: Claude outputs <promise>TASK_COMPLETE</promise>
"""

import sys
import time
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class RalphLoop:
    """Autonomous task completion loop for Claude Code."""

    def __init__(
        self,
        vault_path: str,
        task_file: str,
        max_iterations: int = 10,
        completion_promise: str = "TASK_COMPLETE",
        check_interval: int = 5
    ):
        self.vault_path = Path(vault_path)
        self.task_file = Path(task_file)
        self.max_iterations = max_iterations
        self.completion_promise = completion_promise
        self.check_interval = check_interval

        # Vault folders
        self.needs_action = self.vault_path / "Needs_Action"
        self.done = self.vault_path / "Done"
        self.in_progress = self.vault_path / "In_Progress"

        # State tracking
        self.state_file = self.vault_path / ".state" / f"ralph_loop_{self.task_file.stem}.json"
        self.state_file.parent.mkdir(exist_ok=True)

        # Logs
        self.log_file = self.vault_path / "Logs" / f"ralph_loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self.log_file.parent.mkdir(exist_ok=True)

    def load_state(self) -> Dict[str, Any]:
        """Load loop state from disk."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            "iteration": 0,
            "started": datetime.now().isoformat(),
            "status": "running",
            "task_file": str(self.task_file),
            "completion_method": None
        }

    def save_state(self, state: Dict[str, Any]):
        """Save loop state to disk."""
        state["last_updated"] = datetime.now().isoformat()
        self.state_file.write_text(json.dumps(state, indent=2))

    def log(self, message: str, level: str = "INFO"):
        """Append to log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} [{level}] {message}\n"

        with open(self.log_file, "a") as f:
            f.write(log_entry)

        print(f"[{level}] {message}")

    def check_file_completion(self) -> bool:
        """Check if task file has moved to /Done."""
        # Check if file exists in Done folder
        done_file = self.done / self.task_file.name
        if done_file.exists():
            self.log(f"✓ Task file found in /Done: {done_file.name}")
            return True

        # Check if file no longer exists in Needs_Action or In_Progress
        needs_action_file = self.needs_action / self.task_file.name
        in_progress_file = self.in_progress / self.task_file.name

        if not needs_action_file.exists() and not in_progress_file.exists():
            # File might have been moved to Done with different name
            # Check if any file in Done was modified recently
            recent_files = [
                f for f in self.done.glob("*.md")
                if (time.time() - f.stat().st_mtime) < 60  # Modified in last minute
            ]
            if recent_files:
                self.log(f"✓ Recent file in /Done detected: {recent_files[0].name}")
                return True

        return False

    def check_promise_completion(self, output: str) -> bool:
        """Check if Claude output contains completion promise."""
        promise_tag = f"<promise>{self.completion_promise}</promise>"
        if promise_tag in output:
            self.log(f"✓ Completion promise detected: {self.completion_promise}")
            return True
        return False

    def move_to_in_progress(self):
        """Move task file to In_Progress folder."""
        source = self.needs_action / self.task_file.name
        if source.exists():
            dest = self.in_progress / self.task_file.name
            source.rename(dest)
            self.log(f"Moved task to /In_Progress: {self.task_file.name}")

    def create_prompt(self, iteration: int) -> str:
        """Generate prompt for Claude Code."""
        task_path = self.in_progress / self.task_file.name
        if not task_path.exists():
            task_path = self.needs_action / self.task_file.name

        prompt = f"""You are working on an autonomous task. This is iteration {iteration + 1} of {self.max_iterations}.

TASK FILE: {task_path}

INSTRUCTIONS:
1. Read the task file to understand what needs to be done
2. Complete ALL steps required for this task
3. When FULLY complete, move the task file to AI_Employee_Vault/Done/
4. Output <promise>{self.completion_promise}</promise> when done

IMPORTANT:
- Do not exit until the task is FULLY complete
- If you encounter errors, fix them and continue
- Check your work before marking complete
- The task file MUST be in /Done when finished

Begin working on the task now.
"""
        return prompt

    def run_claude_iteration(self, prompt: str) -> tuple[bool, str]:
        """Run one iteration of Claude Code."""
        try:
            # Run Claude Code with the prompt (using --print for non-interactive mode)
            result = subprocess.run(
                ["claude", "--print", prompt],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per iteration
                cwd=str(self.vault_path.parent)
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0

            return success, output

        except subprocess.TimeoutExpired:
            self.log("⚠ Claude iteration timed out", "WARNING")
            return False, "Timeout"
        except Exception as e:
            self.log(f"✗ Error running Claude: {e}", "ERROR")
            return False, str(e)

    def run(self) -> bool:
        """Run the Ralph Loop until completion or max iterations."""
        state = self.load_state()

        self.log("=" * 60)
        self.log("🔄 Ralph Loop Started")
        self.log(f"Task: {self.task_file.name}")
        self.log(f"Max iterations: {self.max_iterations}")
        self.log("=" * 60)

        # Move task to In_Progress
        self.move_to_in_progress()

        for iteration in range(self.max_iterations):
            state["iteration"] = iteration + 1
            self.save_state(state)

            self.log(f"\n--- Iteration {iteration + 1}/{self.max_iterations} ---")

            # Check file-based completion first
            if self.check_file_completion():
                state["status"] = "completed"
                state["completion_method"] = "file_movement"
                self.save_state(state)
                self.log("✅ Task completed (file moved to /Done)")
                return True

            # Generate prompt for this iteration
            prompt = self.create_prompt(iteration)

            # Run Claude Code
            self.log("Running Claude Code...")
            success, output = self.run_claude_iteration(prompt)

            if not success:
                self.log(f"⚠ Iteration failed: {output[:200]}", "WARNING")

            # Check promise-based completion
            if self.check_promise_completion(output):
                # Verify file was actually moved
                if self.check_file_completion():
                    state["status"] = "completed"
                    state["completion_method"] = "promise"
                    self.save_state(state)
                    self.log("✅ Task completed (promise + file verification)")
                    return True
                else:
                    self.log("⚠ Promise detected but file not in /Done", "WARNING")

            # Wait before next iteration
            if iteration < self.max_iterations - 1:
                self.log(f"Waiting {self.check_interval}s before next iteration...")
                time.sleep(self.check_interval)

        # Max iterations reached
        state["status"] = "max_iterations_reached"
        self.save_state(state)
        self.log("⚠ Max iterations reached without completion", "WARNING")

        # Create alert
        self.create_incomplete_alert(state)

        return False

    def create_incomplete_alert(self, state: Dict[str, Any]):
        """Create alert for incomplete task."""
        alert_file = self.vault_path / "Needs_Action" / f"ALERT_RALPH_INCOMPLETE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        content = f"""---
type: alert
priority: high
status: pending
created: {datetime.now().isoformat()}
---

## Ralph Loop Incomplete

The autonomous task completion loop reached maximum iterations without completing the task.

**Task File:** {self.task_file.name}
**Iterations:** {state['iteration']}/{self.max_iterations}
**Started:** {state['started']}
**Status:** {state['status']}

**Action Required:**
1. Review the task file: {self.in_progress / self.task_file.name}
2. Check logs: {self.log_file}
3. Complete manually or restart loop with higher iteration limit

**Restart Command:**
```bash
uv run python scripts/ralph_loop.py \\
  --task "{self.task_file.name}" \\
  --max-iterations 20
```
"""
        alert_file.write_text(content)
        self.log(f"⚠ Alert created: {alert_file.name}")


def main():
    parser = argparse.ArgumentParser(
        description='Ralph Loop - Autonomous task completion for Claude Code'
    )
    parser.add_argument(
        '--task',
        required=True,
        help='Task file name (in Needs_Action folder)'
    )
    parser.add_argument(
        '--vault',
        default='AI_Employee_Vault',
        help='Path to Obsidian vault'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum iterations before giving up'
    )
    parser.add_argument(
        '--completion-promise',
        default='TASK_COMPLETE',
        help='Promise string to detect completion'
    )
    parser.add_argument(
        '--check-interval',
        type=int,
        default=5,
        help='Seconds to wait between iterations'
    )

    args = parser.parse_args()

    loop = RalphLoop(
        vault_path=args.vault,
        task_file=args.task,
        max_iterations=args.max_iterations,
        completion_promise=args.completion_promise,
        check_interval=args.check_interval
    )

    success = loop.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
