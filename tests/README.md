# Test Suite - Silver Tier Skills

Comprehensive testing framework for Silver tier AI Employee skills.

## 📁 Test Files

### 1. `verify_setup.py` - Environment Verification
Checks if your development environment is properly configured.

**Usage:**
```bash
python tests/verify_setup.py
```

**What it checks:**
- Python 3.10+ installed
- Node.js 18+ installed
- Claude Code installed
- Required Python packages
- Playwright browsers
- PM2 process manager
- Vault directory structure
- Company Handbook exists
- Skills directory complete
- Configuration files (.env, credentials.json)

**Output:**
- ✅ Passed checks
- ⚠️ Warnings (optional items)
- ❌ Issues (must fix)
- 💡 Next steps to resolve issues

---

### 2. `test_all_skills.py` - Unit Tests
Tests each individual skill in isolation.

**Usage:**
```bash
# Test all skills
python tests/test_all_skills.py

# Test specific skill
python tests/test_all_skills.py --skill gmail
python tests/test_all_skills.py --skill email-mcp
python tests/test_all_skills.py --skill approval

# Verbose output
python tests/test_all_skills.py --verbose
```

**Available Skills:**
- `gmail` - Gmail monitoring
- `email-mcp` - Email MCP server
- `approval` - Approval workflow
- `whatsapp` - WhatsApp monitoring
- `linkedin` - LinkedIn posting
- `scheduling` - Task scheduling
- `reasoning-loop` - Reasoning loop

**What it tests:**
- Credentials and configuration
- Module existence
- Folder structure
- File format validation
- Priority detection
- Keyword matching
- File movement
- Expiration logic

---

### 3. `test_integration.py` - Integration Tests
Tests complete end-to-end workflows across multiple skills.

**Usage:**
```bash
# Test all workflows
python tests/test_integration.py

# Test specific workflow
python tests/test_integration.py --workflow email
python tests/test_integration.py --workflow file
python tests/test_integration.py --workflow approval
python tests/test_integration.py --workflow multistep
```

**Workflows Tested:**

1. **Email Workflow**
   - Email detected → Action item created
   - Action processed → Draft created
   - Draft approved → Email sent
   - Task moved to Done

2. **File Processing Workflow**
   - File dropped in Inbox
   - Watcher detects and creates action item
   - Action item processed
   - File moved to Done

3. **Approval Workflow**
   - Action requires approval
   - Approval request created
   - Human approves
   - Action executed

4. **Multi-Step Task Workflow**
   - Complex task created
   - Multiple actions required
   - All steps completed
   - Task marked done

---

### 4. `run_all_tests.py` - Master Test Runner
Runs all test suites in the correct order.

**Usage:**
```bash
# Run all tests
python tests/run_all_tests.py

# Quick mode (skip integration tests)
python tests/run_all_tests.py --quick

# Verbose output
python tests/run_all_tests.py --verbose
```

**Test Phases:**
1. **Phase 1**: Environment Verification
2. **Phase 2**: Unit Tests (Individual Skills)
3. **Phase 3**: Integration Tests (Complete Workflows)

**Output:**
- Summary of all test results
- Total duration
- Pass/fail statistics
- Next steps based on results

---

## 🚀 Quick Start

### First Time Setup
```bash
# 1. Verify environment
python tests/verify_setup.py

# 2. Fix any issues reported
# Follow the "Next Steps" suggestions

# 3. Run all tests
python tests/run_all_tests.py
```

### During Development
```bash
# Test specific skill you're working on
python tests/test_all_skills.py --skill gmail --verbose

# Test integration after completing a workflow
python tests/test_integration.py --workflow email

# Quick check before committing
python tests/run_all_tests.py --quick
```

### Before Submission
```bash
# Full test suite
python tests/run_all_tests.py

# Should see: "All tests passed!"
```

---

## 📊 Understanding Test Results

### ✅ PASSED
Test completed successfully. No action needed.

### ❌ FAILED
Test failed but didn't crash. Review the specific failure message.

**Common failures:**
- Missing files or directories
- Incorrect file format
- Configuration issues

### 💥 ERROR
Test crashed with an exception. Check the error message.

**Common errors:**
- Missing dependencies
- Permission issues
- Invalid paths

### ⏭️ SKIPPED
Test was skipped (e.g., in quick mode).

---

## 🔧 Troubleshooting

### "Python 3.10+ required"
```bash
# Check version
python --version

# Install Python 3.10+
# Visit: https://www.python.org/downloads/
```

### "Missing packages"
```bash
# Install all required packages
pip install google-auth google-auth-oauthlib google-api-python-client
pip install playwright watchdog

# Install Playwright browsers
playwright install chromium
```

### "PM2 not installed"
```bash
# Install PM2 globally
npm install -g pm2

# Verify installation
pm2 --version
```

### "Vault structure incorrect"
```bash
# The Bronze tier setup should have created this
# If missing, create manually:
cd AI_Employee_Vault
mkdir -p Inbox Needs_Action Done Plans Logs
mkdir -p Pending_Approval Approved Rejected
```

### "Skills directory not found"
```bash
# Skills should be in .claude/skills/
# Each skill has its own directory with SKILL.md
ls -la .claude/skills/
```

### "credentials.json not found"
This is optional for testing. Only needed for actual Gmail integration.

To set up:
1. Go to Google Cloud Console
2. Create project and enable Gmail API
3. Create OAuth credentials
4. Download as credentials.json

---

## 📝 Test Coverage

### Unit Tests Coverage
- ✅ Gmail monitoring (5 tests)
- ✅ Email MCP server (3 tests)
- ✅ Approval workflow (4 tests)
- ✅ WhatsApp monitoring (4 tests)
- ✅ LinkedIn posting (3 tests)
- ✅ Task scheduling (3 tests)
- ✅ Reasoning loop (3 tests)

**Total**: 25 unit tests

### Integration Tests Coverage
- ✅ Email workflow (4 steps)
- ✅ File processing workflow (3 steps)
- ✅ Approval workflow (3 steps)
- ✅ Multi-step task workflow (3 steps)

**Total**: 4 integration tests

### Environment Checks
- ✅ Python version
- ✅ Node.js version
- ✅ Claude Code installation
- ✅ Python packages
- ✅ Playwright browsers
- ✅ PM2 installation
- ✅ Vault structure
- ✅ Company Handbook
- ✅ Skills directory
- ✅ Scripts directory
- ✅ Configuration files

**Total**: 12 environment checks

---

## 🎯 Success Criteria

### Bronze Tier Complete
- ✅ All environment checks pass
- ✅ Vault structure correct
- ✅ File system watcher works
- ✅ Basic skills functional

### Silver Tier Ready
- ✅ All Bronze requirements
- ✅ Gmail API configured
- ✅ MCP server setup
- ✅ Approval workflow working
- ✅ All unit tests pass
- ✅ All integration tests pass

---

## 🔄 Continuous Testing

### Pre-Commit
```bash
# Quick check before committing
python tests/run_all_tests.py --quick
```

### Daily Development
```bash
# Full test suite
python tests/run_all_tests.py
```

### Before Submission
```bash
# Comprehensive verification
python tests/verify_setup.py
python tests/run_all_tests.py --verbose
```

---

## 📚 Additional Resources

- [Silver Tier Skills Guide](../.claude/skills/README.md)
- [Orchestrator Documentation](../scripts/orchestrator.py)
- [Hackathon Guide](../Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)

---

## 🐛 Reporting Issues

If tests fail unexpectedly:

1. Run with verbose mode: `--verbose`
2. Check specific test: `--skill <name>` or `--workflow <name>`
3. Review error messages carefully
4. Verify environment setup
5. Check file permissions
6. Review logs in `AI_Employee_Vault/Logs/`

---

## ✨ Tips

1. **Start with verify_setup.py** - Fix environment issues first
2. **Test incrementally** - Test each skill as you build it
3. **Use verbose mode** - When debugging failures
4. **Run quick tests often** - Fast feedback during development
5. **Full tests before submission** - Ensure everything works

---

**Created**: 2026-02-19
**Version**: 1.0
**Tier**: Silver
**Total Tests**: 41 (25 unit + 4 integration + 12 environment)
