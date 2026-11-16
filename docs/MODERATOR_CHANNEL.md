# Moderator Channel Specification & Verification Protocol

## 1. Overview
The moderator channel is a dedicated Telegram channel or supergroup used for escalations, audit alerts, and critical system notifications.

---

## 2. Administrator Permissions & Group Auto-Moderation

### A. Moderator Alert Channel (Audits & Escalations)
For read-only escalation and alert broadcast channels, the bot needs minimal permissions:
- **Can post messages / Send messages:** **REQUIRED** (the only permission necessary for notification dispatch).
- Other channel admin permissions may remain disabled.

### B. Group Auto-Moderation (Autonomous Policing & Anti-Scam)
> [!IMPORTANT]
> **To enable Auto-Moderation, you must make Zoe an Administrator in your Telegram group and grant her the 'Delete Messages' and 'Ban Users' permissions.**

When granted these administrator rights:
1. **Auto-Delete Scam Links:** Zoe automatically deletes phishing URLs, fake airdrop links, and fake admin impersonation messages on detection, posting a protective warning to the group.
2. **Mute Repeat Spammers:** If a user sends more than 3 identical messages (flooding) or posts 2 scam links within 5 minutes, Zoe immediately mutes them (`restrict_chat_member`) for 1 hour.
3. **Welcome New Members:** Zoe greets every new user joining the group with a branded project welcome message.

If these administrative permissions are not granted, Zoe continues answering normal community questions and scanning tokens, but catches permission limitations gracefully without throwing errors or disrupting operation.

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
