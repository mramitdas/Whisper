def welcome(name: str) -> str:
    return (
        f"Hey {name}!\n"
        "Talk to a stranger anonymously. No names, no usernames — just words.\n\n"
        "Tap Find partner to start."
    )


RULES = (
    "Be respectful. No spam, no links, no 18+ content with minors. "
    "Report bad behavior with /report."
)
PRIVACY = (
    "We never store message content. Sessions auto-expire. "
    "Your partner never sees your username, name, or ID."
)
HELP = (
    "Commands:\n"
    "/search - find a partner\n"
    "/next - skip current partner\n"
    "/stop - leave chat\n"
    "/report [reason] - report partner\n"
    "/block - block partner forever\n"
    "/rules - community rules\n"
    "/privacy - privacy notice\n"
    "/help - this message"
)
BANNED = "Your access is suspended. Contact the admin if you think this is a mistake."
SLOW_DOWN = "Slow down a bit."
SEARCHING = "Looking for someone… (position {pos})"
NO_PARTNER = "No one's free right now. Try again in a bit."
CANCELLED = "Search cancelled."
ALREADY_CHATTING = "You already have a partner. Use /next or /stop first."
MATCHED_ME = "Partner found! Say hi.\n/next - skip partner\n/stop - end chat"
MATCHED_PARTNER = "Partner found! Say hi.\n/next - skip partner\n/stop - end chat"
STOPPED_ME = "You stopped the dialog. Type /search for a new one."
STOPPED_PARTNER = "Your partner left. Type /search for a new one."
INVALID_STOP = "You have no partner. Type /search to find one."
RELAY_NO_PARTNER = "You have no partner. Type /search to find one."
LINK_BLOCKED = "That message was blocked: links and @usernames are not allowed."
FORBIDDEN_BLOCKED = "That message was blocked by the word filter."
REPORT_RECEIVED = "Report received. Thanks for keeping this safe."
REPORT_NO_TARGET = "No recent partner to report."
BLOCKED_PARTNER = "Partner blocked. You'll never be matched again."
BLOCKED_BY_PARTNER = "Your partner ended the chat."
IDLE_TIMEOUT = "Chat ended after 30 minutes of inactivity. Type /search for a new one."
ERROR_GENERIC = "Something went wrong. Send /start to continue."
ALREADY_SEARCHING = "You're already in the queue."
ADMIN_ONLY = "Not allowed."
ADMIN_BANNED = "Banned: {uid}"
ADMIN_UNBANNED = "Unbanned: {uid}"
ADMIN_NO_BAN = "No active ban for {uid}."


def admin_stats(users: int, matches: int, reports: int, queue: int, bans: int) -> str:
    return (
        f"Users: {users}\nMatches: {matches}\nReports: {reports}\n"
        f"Queue: {queue}\nActive bans: {bans}"
    )
