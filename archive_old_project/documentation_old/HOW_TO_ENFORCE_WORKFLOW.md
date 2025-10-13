# How to Enforce Workflow with Claude

This guide is for YOU (the human) to ensure Claude follows the workflow.

---

## 🚨 The Problem

Claude doesn't automatically remember to:
- Read CLAUDE.md
- Follow WORKFLOW.md
- Update documentation
- Check for past mistakes

**YOU need to enforce it at the start of each session.**

---

## ✅ Solution: Session Startup Protocol

### At the START of EVERY new session/conversation:

**Copy and paste this exact message to Claude:**

```
Before we do anything else, please follow the startup protocol:

1. Read and summarize:
   - CLAUDE.md (current focus)
   - Last 50 lines of CHANGELOG.md (recent work)
   - PRE_FLIGHT_CHECKLIST.md (if mid-task)

2. Tell me:
   - What is our current task?
   - What did we do last time?
   - What bugs have we recently fixed?
   - What should we do next?

3. Wait for my confirmation before proceeding.

Refer to .claude/START_SESSION.md for full protocol.
```

---

## 🔄 Mid-Session Reminders

If Claude is about to run something without verification:

```
STOP - Before running, complete the verification checklist from WORKFLOW.md:

- [ ] Correct dataset?
- [ ] Right evaluation set (train/dev/test)?
- [ ] Metadata matches what we're actually doing?
- [ ] Comparing apples to apples?
- [ ] Have we made this mistake before? (Check CHANGELOG)

Show me the checklist before proceeding.
```

---

## ✅ Session End Protocol

Before ending the session:

```
Before we end:

1. Update CHANGELOG.md with what we did today
2. Update CLAUDE.md if status changed
3. Update PRE_FLIGHT_CHECKLIST.md if mid-task
4. Clean up any debug files
5. Show me what needs to be done next time

Follow the session end protocol in .claude/START_SESSION.md
```

---

## 📋 Quick Reference Commands

Save these for easy copy-paste:

### Startup
```
Follow startup protocol in .claude/START_SESSION.md
```

### Before Running Anything
```
Complete pre-flight checklist from WORKFLOW.md before running
```

### After Completing Work
```
Update CHANGELOG.md and CLAUDE.md with what we just did
```

### Found a Bug
```
Document this bug in CHANGELOG.md immediately, and check if we've seen it before
```

---

## 🎯 Making It Easier

### Option 1: Add to Custom Instructions

If Claude Code supports custom instructions, add this:

```
At the start of each session:
1. Read CLAUDE.md to understand current status
2. Read last 50 lines of CHANGELOG.md to see recent work
3. Summarize and wait for confirmation before proceeding

Before running any code:
1. Complete verification checklist from WORKFLOW.md
2. Check CHANGELOG.md for similar past mistakes
3. Show me the checklist before proceeding

After completing work:
1. Update CHANGELOG.md immediately
2. Update CLAUDE.md if status changed
3. Follow session end protocol
```

### Option 2: Create an Alias

Add to your `.bashrc` or `.zshrc`:

```bash
alias claude-start="cat CLAUDE.md && echo '---' && tail -50 CHANGELOG.md"
```

Then run `claude-start` before starting each session and share the output with Claude.

---

## 🚫 What NOT to Do

**Don't trust Claude to remember** - Claude has no memory between sessions

**Don't skip the startup protocol** - "Just this once" becomes "every time"

**Don't let Claude run without verification** - Mistakes compound quickly

**Don't forget to update docs** - Future you will thank present you

---

## ✅ Success Looks Like

1. **Every session starts** with Claude reading CLAUDE.md and CHANGELOG.md
2. **Every task begins** with documentation and verification
3. **Every run includes** pre-flight checklist review
4. **Every completion** updates CHANGELOG.md and CLAUDE.md
5. **No repeated mistakes** because we check CHANGELOG first

---

## 🎯 Your Responsibility

As the human, YOU must:

1. ✅ Send startup protocol message at beginning of session
2. ✅ Stop Claude if it skips verification
3. ✅ Remind Claude to update docs after completing work
4. ✅ Review the checklist when Claude shows it to you
5. ✅ Enforce the session end protocol

**This is not automated - you need to actively enforce it.**

---

## 📝 Session Template

Here's a full template for a complete session:

```
# SESSION START
Follow startup protocol in .claude/START_SESSION.md

[Claude reads docs and summarizes]

# CONFIRM OR CORRECT
[You verify Claude understood correctly]

# DO WORK
[With verification checklist at each step]

# SESSION END
Follow session end protocol in .claude/START_SESSION.md

[Claude updates docs and shows next steps]
```

---

## 💡 Pro Tip

Keep this file open in a browser tab so you can quickly copy-paste the enforcement messages.

---

**Remember: The workflow only works if YOU enforce it!**
