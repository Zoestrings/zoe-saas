# Moderator Channel Specification & Verification Protocol

## 1. Overview
The moderator channel is a dedicated Telegram channel or supergroup used for escalations, audit alerts, and critical system notifications.

---

## 2. Minimum Admin Permissions
The bot must be added to the channel as an Administrator with the minimal necessary permission set:
- **Can post messages / Send messages:** **REQUIRED** (the only permission necessary for notification dispatch).
- All other administrative permissions (Change channel info, Delete messages, Edit messages, Ban users, Add subscribers, Add new admins) should remain **DISABLED**.

---

## 3. Automated API-Level Verification (Stage 2)
In Stage 2, `verify_moderator_channel()` performs automated API-level verification:
- Confirms the bot is recognized as an active member.
- Verifies that the bot's status is `administrator` or `creator`.
- **Note:** `verify_moderator_channel()` does **not** send any preflight messages or broadcast into the channel.

---

## 4. Manual Preflight Verification Procedure
Prior to enabling live notifications in production or pilot mode, the operator performs a one-time manual preflight check:

1. **Preflight Dispatch:** From the operator control console, send a single synthetic verification message:
   ```text
   [PREFLIGHT TEST] Zoe channel verification
   ```
2. **Confirmation:** Confirm the message arrives in the designated channel.
3. **Record ID:** Record the returned Telegram `message_id` and timestamp in the operator audit log.
4. **No Ongoing Preflight:** The automated runtime never periodically spams or sends synthetic test pings into the channel.
