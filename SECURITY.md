# SECURITY.md - Critical Profile Requirements

## ⚠️ CRITICAL CHROME PROFILE RULE (PERMANENT)

The polymarket-btc-agent **MUST ONLY EVER** use this Chrome profile:

```
Profile Name:    Polymarket Bot
Google Account:  polymarketv2@gmail.com  
Profile Dir:     Profile 1
MetaMask:        Installed, unlocked, connected to Polymarket
Network:         Polygon
```

---

## 🔒 Hard-Coded Profile (Not Configurable)

As of commit `e9dcdcf`, the Chrome profile is **hard-coded** in the source code:

```python
# From autonomous_trade_executor.py
class AutonomousTradeExecutor:
    REQUIRED_PROFILE_NAME = "Polymarket Bot"
    REQUIRED_PROFILE_EMAIL = "polymarketv2@gmail.com"
    REQUIRED_PROFILE_DIR = "Profile 1"
```

**This is intentional and must never be changed via environment variables or command-line arguments.**

---

## 🛡️ Pre-Flight Verification (Mandatory)

Before any trading begins, the system runs a **mandatory pre-flight verification**:

### Check 1: Profile Directory Exists
```
~/Library/Application Support/Google/Chrome/Profile 1
```
✅ Pass: Directory exists  
❌ Fail: Abort execution

### Check 2: Google Account Email Verification
Reads `Preferences` file and extracts account email.

✅ Pass: Email == `polymarketv2@gmail.com`  
❌ Fail: Abort execution (email mismatch)

### Check 3: MetaMask Extension Detection
Checks for MetaMask extension ID: `nkbihfbeogaeaoehlefnkodbefgpgknn`

✅ Pass: Extension found  
⚠️  Warn: Extension not detected (continues but trading may fail)

### Check 4: Final Confirmation Log
If all checks pass, system **MUST** print:

```
✅ Using Chrome profile: Polymarket Bot (polymarketv2@gmail.com) — verified
```

**If this log line is missing, execution has been aborted.**

---

## 🚫 What the System Will NEVER Do

1. ❌ **NEVER** fall back to another profile (Default, Profile 2, etc.)
2. ❌ **NEVER** silently recover by using a different profile
3. ❌ **NEVER** accept profile name from environment variables
4. ❌ **NEVER** accept profile name from command-line arguments
5. ❌ **NEVER** trade if verification fails

---

## ✅ What the System WILL Do

1. ✅ **Always** use Profile 1 (Polymarket Bot / polymarketv2@gmail.com)
2. ✅ **Always** run pre-flight verification before trading
3. ✅ **Always** abort if verification fails
4. ✅ **Always** log the mandatory confirmation line
5. ✅ **Always** log fatal errors if profile is wrong

---

## 🔍 How to Verify System is Correct

### Method 1: Check Startup Logs
```bash
tail -100 trade_executor.log | grep "Using Chrome profile"
```

Expected output:
```
✅ Using Chrome profile: Polymarket Bot (polymarketv2@gmail.com) — verified
```

### Method 2: Check Pre-Flight Section
```bash
tail -100 trade_executor.log | grep -A 15 "PRE-FLIGHT VERIFICATION"
```

Should show all verification steps passing.

### Method 3: Check for Abort
```bash
tail -100 trade_executor.log | grep "FATAL"
```

If you see FATAL errors, the system correctly aborted due to profile mismatch.

---

## 🚨 Red Flags (Indicates Problem)

🚨 **Log line missing:** "Using Chrome profile: Polymarket Bot (polymarketv2@gmail.com) — verified"  
🚨 **Wrong email in log:** Any email other than polymarketv2@gmail.com  
🚨 **Profile directory not found:** System should abort  
🚨 **Trading without verification:** Pre-flight checks were skipped  

---

## 🔧 If Profile Gets Corrupted

If the Polymarket Bot profile gets corrupted or deleted:

### DO NOT:
- ❌ Create a new profile with a different name
- ❌ Try to configure the bot to use another profile
- ❌ Skip the verification

### DO:
1. ✅ Recreate the profile with exact same name: "Polymarket Bot"
2. ✅ Sign in with: polymarketv2@gmail.com
3. ✅ Install MetaMask extension
4. ✅ Connect MetaMask to Polymarket
5. ✅ Verify profile directory is "Profile 1"
6. ✅ Test with `./start-bot.sh`

---

## 📝 Code Location of Hard-Coded Values

File: `autonomous_trade_executor.py`

Lines defining profile requirements:
```python
class AutonomousTradeExecutor:
    # HARD-CODED PROFILE REQUIREMENT
    REQUIRED_PROFILE_NAME = "Polymarket Bot"
    REQUIRED_PROFILE_EMAIL = "polymarketv2@gmail.com"
    REQUIRED_PROFILE_DIR = "Profile 1"
```

Method performing verification:
```python
def verify_chrome_profile(self) -> bool:
    """
    PRE-FLIGHT VERIFICATION (MANDATORY)
    Verify correct Chrome profile before any trading.
    """
```

Method enforcing verification:
```python
def start_browser(self) -> bool:
    # MANDATORY PRE-FLIGHT VERIFICATION
    if not self.verify_chrome_profile():
        print("\n❌ FATAL ERROR: Pre-flight verification failed!")
        return False
```

---

## 🔐 Why This is Critical

1. **Security:** Wrong profile = wrong wallet = trades with wrong funds
2. **Safety:** Prevents accidental trades from personal accounts
3. **Reliability:** No silent failures due to profile conflicts
4. **Auditability:** Clear verification trail in logs
5. **Determinism:** Same profile every time, no variability

---

## 📊 Verification Log Example (Success)

```
================================================================================
🔍 PRE-FLIGHT VERIFICATION - CHROME PROFILE CHECK
================================================================================
✓ Checking profile directory: /Users/clawd/Library/Application Support/Google/Chrome/Profile 1
   ✅ Profile directory exists
✓ Checking preferences file: /Users/clawd/Library/Application Support/Google/Chrome/Profile 1/Preferences
   Profile name: Your Chrome
   Google account: polymarketv2@gmail.com
   ✅ Profile email verified: polymarketv2@gmail.com
✓ Checking for MetaMask extension...
   ✅ MetaMask extension found: 1 version(s)

================================================================================
✅ PRE-FLIGHT VERIFICATION PASSED
   Profile: Polymarket Bot (polymarketv2@gmail.com)
   Directory: /Users/clawd/Library/Application Support/Google/Chrome/Profile 1
================================================================================

🚀 Starting Playwright with verified Chrome profile...
   Profile path: /Users/clawd/Library/Application Support/Google/Chrome/Profile 1
================================================================================
✅ Using Chrome profile: Polymarket Bot (polymarketv2@gmail.com) — verified
================================================================================
```

---

## 🚫 Verification Log Example (Failure)

```
================================================================================
🔍 PRE-FLIGHT VERIFICATION - CHROME PROFILE CHECK
================================================================================
✓ Checking profile directory: /Users/clawd/Library/Application Support/Google/Chrome/Profile 1
   ✅ Profile directory exists
✓ Checking preferences file: /Users/clawd/Library/Application Support/Google/Chrome/Profile 1/Preferences
   Profile name: Your Chrome
   Google account: wrong@email.com
   ❌ FATAL: Profile email mismatch!
   Required: polymarketv2@gmail.com
   Found: wrong@email.com

❌ FATAL ERROR: Pre-flight verification failed!
   Cannot proceed with trading.
   Chrome profile requirement not met.
```

System will **abort** and **not attempt to trade**.

---

## 🎯 Summary

| Aspect | Status |
|--------|--------|
| Profile configurable? | ❌ NO - Hard-coded |
| Can use other profiles? | ❌ NO - Will abort |
| Verification mandatory? | ✅ YES - Always runs |
| Abort on mismatch? | ✅ YES - Immediate |
| Confirmation log required? | ✅ YES - Must appear |
| Can be bypassed? | ❌ NO - Built into code |

---

**This security measure ensures the bot ONLY trades with the correct, verified profile - no exceptions.**

Last updated: 2026-01-28 (Commit: e9dcdcf)
