#!/usr/bin/env python3
"""
Task Orchestrator - Ralph Wiggum Pattern Implementation

Manages autonomous task completion using Claude Code with continuous
reasoning loops until tasks are fully complete.

Usage:
    python scripts/orchestrator.py --task EMAIL_client.md
    python scripts/orchestrator.py --all
    python scripts/orchestrator.py --task PROJECT_analysis.md --max-iterations 15
"""

import subprocess
import json
import argparse
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


class TaskOrchestrator:
    """Orchestrates autonomous task completion with Claude Code"""

    def __init__(self, vault_path: str, max_iterations: int = 10):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'
        self.max_iterations = max_iterations

        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.done.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

    def run_task_loop(self, task_file: str, prompt: Optional[str] = None) -> bool:
        """
        Run Claude in a loop until task is complete

        Args:
            task_file: Name of task file in Needs_Action/
            prompt: Optional custom prompt (auto-generated if not provided)

        Returns:
            True if task completed successfully, False otherwise
        """
        task_path = self.needs_action / task_file

        if not task_path.exists():
            print(f"❌ Task file not found: {task_file}")
            return False

        # Generate prompt if not provided
        if not prompt:
            prompt = self.generate_prompt(task_path)

        # Create state for tracking
        state = {
            'task_file': task_file,
            'task_path': str(task_path),
            'max_iterations': self.max_iterations,
            'current_iteration': 0,
            'started': datetime.now().isoformat(),
            'status': 'running'
        }

        print(f"\n{'='*70}")
        print(f"🚀 Starting Task Loop: {task_file}")
        print(f"{'='*70}\n")

        iteration = 0
        start_time = time.time()

        while iteration < self.max_iterations:
            iteration += 1
            state['current_iteration'] = iteration

            print(f"\n{'─'*70}")
            print(f"⟳ Iteration {iteration}/{self.max_iterations}")
            print(f"{'─'*70}")

            # Run Claude with prompt
            iteration_start = time.time()
            result = self.run_claude(prompt, state)
            iteration_time = time.time() - iteration_start

            print(f"\n⏱️  Iteration completed in {iteration_time:.1f}s")

            # Check if task is complete (file moved to Done/)
            done_path = self.done / task_file
            if done_path.exists():
                total_time = time.time() - start_time
                print(f"\n{'='*70}")
                print(f"✅ Task Complete: {task_file}")
                print(f"📊 Iterations: {iteration}/{self.max_iterations}")
                print(f"⏱️  Total time: {total_time:.1f}s")
                print(f"{'='*70}\n")

                state['status'] = 'completed'
                state['iterations_used'] = iteration
                state['total_time'] = total_time
                self.log_completion(state)
                return True

            # Check if Claude indicated completion via promise
            if self.check_completion_promise(result):
                print(f"\n✅ Task complete (completion promise detected)")
                state['status'] = 'completed_promise'
                state['iterations_used'] = iteration
                self.log_completion(state)
                return True

            # Check if task appears stuck
            if iteration > 3 and self.detect_stuck(task_file, iteration):
                print(f"\n⚠️  Task appears stuck - same actions repeating")
                state['status'] = 'stuck'
                state['iterations_used'] = iteration
                self.log_timeout(state)
                return False

            # Continue loop
            print(f"\n⟳ Task incomplete, continuing...")
            time.sleep(1)  # Brief pause between iterations

        # Max iterations reached
        total_time = time.time() - start_time
        print(f"\n{'='*70}")
        print(f"⚠️  Max Iterations Reached: {task_file}")
        print(f"📊 Iterations: {iteration}/{self.max_iterations}")
        print(f"⏱️  Total time: {total_time:.1f}s")
        print(f"{'='*70}\n")

        state['status'] = 'timeout'
        state['iterations_used'] = iteration
        state['total_time'] = total_time
        self.log_timeout(state)
        return False

    def run_claude(self, prompt: str, state: Dict) -> str:
        """
        Execute Claude Code with prompt

        Args:
            prompt: The prompt to send to Claude
            state: Current state dictionary

        Returns:
            Claude's output as string
        """
        # For now, this is a placeholder that would call Claude Code
        # In production, this would use subprocess to call claude CLI
        # or use the Claude API directly

        print(f"📝 Prompt: {prompt[:100]}...")

        # Placeholder - in real implementation:
        # cmd = ['claude', '--non-interactive', '--prompt', prompt]
        # result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.vault_path)
        # return result.stdout

        # For testing, simulate Claude processing
        print(f"🤖 Claude processing task...")
        time.sleep(2)  # Simulate processing time

        return "Task processed (simulated)"

    def generate_prompt(self, task_path: Path) -> str:
        """
        Generate prompt from task file

        Args:
            task_path: Path to task file

        Returns:
            Generated prompt string
        """
        content = task_path.read_text()
        task_name = task_path.name

        # Read Company Handbook for context
        handbook_path = self.vault_path / 'Company_Handbook.md'
        handbook_context = ""
        if handbook_path.exists():
            handbook_context = "\n\nRefer to Company_Handbook.md for rules and guidelines."

        prompt = f"""
Process the following task completely and autonomously.

Task File: {task_name}

Task Content:
{content}

Instructions:
1. Read and understand the task requirements
2. Check Company_Handbook.md for relevant rules{handbook_context}
3. Complete all required actions step by step
4. Update Dashboard.md with progress
5. Create any necessary approval requests in Pending_Approval/
6. When ALL actions are complete, move the task file to Done/ folder

IMPORTANT:
- The task is ONLY complete when the file is moved to Done/
- Do not exit until the task is fully complete
- If waiting for approval, note this in the task file but continue monitoring
- Log all actions taken

Complete this task now.
"""
        return prompt

    def check_completion_promise(self, output: str) -> bool:
        """
        Check if Claude output contains completion promise

        Args:
            output: Claude's output text

        Returns:
            True if completion promise found
        """
        return '<promise>TASK_COMPLETE</promise>' in output

    def detect_stuck(self, task_file: str, iteration: int) -> bool:
        """
        Detect if task is stuck in a loop

        Args:
            task_file: Name of task file
            iteration: Current iteration number

        Returns:
            True if task appears stuck
        """
        # Check recent logs for repeated actions
        log_file = self.logs / 'reasoning_loop.json'
        if not log_file.exists():
            return False

        try:
            logs = json.loads(log_file.read_text())
            recent_logs = [l for l in logs if l.get('task') == task_file][-3:]

            if len(recent_logs) >= 3:
                # Check if all recent logs show same status
                statuses = [l.get('status') for l in recent_logs]
                if len(set(statuses)) == 1 and statuses[0] == 'running':
                    return True
        except Exception:
            pass

        return False

    def process_all_pending(self) -> Dict[str, bool]:
        """
        Process all tasks in Needs_Action/ folder

        Returns:
            Dictionary mapping task names to completion status
        """
        tasks = list(self.needs_action.glob('*.md'))

        if not tasks:
            print("📭 No pending tasks found in Needs_Action/")
            return {}

        print(f"\n📋 Found {len(tasks)} pending tasks")
        print(f"{'='*70}\n")

        # Sort by priority
        tasks = sorted(tasks, key=self.get_priority)

        results = {}
        for i, task in enumerate(tasks, 1):
            print(f"\n[{i}/{len(tasks)}] Processing: {task.name}")
            success = self.run_task_loop(task.name)
            results[task.name] = success

            if not success:
                print(f"⚠️  Task {task.name} did not complete")
                # Continue with next task

        # Print summary
        print(f"\n{'='*70}")
        print(f"📊 Processing Summary")
        print(f"{'='*70}")
        print(f"✅ Completed: {sum(results.values())}/{len(results)}")
        print(f"❌ Failed: {len(results) - sum(results.values())}/{len(results)}")
        print(f"{'='*70}\n")

        return results

    def get_priority(self, task_path: Path) -> int:
        """
        Extract priority from task metadata

        Args:
            task_path: Path to task file

        Returns:
            Priority value (0=high, 1=medium, 2=low)
        """
        try:
            content = task_path.read_text()
            if 'priority: high' in content.lower():
                return 0
            elif 'priority: medium' in content.lower():
                return 1
            else:
                return 2
        except Exception:
            return 2  # Default to low priority

    def log_completion(self, state: Dict):
        """Log successful completion"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task': state['task_file'],
            'status': state['status'],
            'iterations': state.get('iterations_used', 0),
            'total_time': state.get('total_time', 0),
            'started': state['started']
        }
        self.append_log(log_entry)

    def log_timeout(self, state: Dict):
        """Log timeout or failure"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task': state['task_file'],
            'status': state['status'],
            'iterations': state.get('iterations_used', 0),
            'total_time': state.get('total_time', 0),
            'started': state['started']
        }
        self.append_log(log_entry)

    def append_log(self, entry: Dict):
        """Append entry to reasoning loop log"""
        log_file = self.logs / 'reasoning_loop.json'
        logs = []

        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except Exception:
                logs = []

        logs.append(entry)
        log_file.write_text(json.dumps(logs, indent=2))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Task Orchestrator - Autonomous task completion with Claude Code'
    )
    parser.add_argument(
        '--task',
        type=str,
        help='Specific task file to process (e.g., EMAIL_client.md)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all pending tasks in Needs_Action/'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        help='Custom prompt (optional, auto-generated if not provided)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum iterations before timeout (default: 10)'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        default='./AI_Employee_Vault',
        help='Path to Obsidian vault (default: ./AI_Employee_Vault)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.task and not args.all:
        parser.error('Either --task or --all must be specified')

    # Create orchestrator
    orchestrator = TaskOrchestrator(
        vault_path=args.vault_path,
        max_iterations=args.max_iterations
    )

    # Process tasks
    if args.all:
        results = orchestrator.process_all_pending()
        success = all(results.values())
        sys.exit(0 if success else 1)
    else:
        success = orchestrator.run_task_loop(args.task, args.prompt)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
