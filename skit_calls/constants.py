AUTHORIZATION = "authorization"
ROUTE__CALL = "/call_report/calls/"
ROUTE__TURN = "/call_report/calls/{}/"
LIVE = "live"

# --- Tagged calls are one of the following ----
REPORTED = "reported"
RESOLVED = "resolved"
# but if there are no preferences, we can get
# all calls.
ALL = "all"
# -----------------------------------------------

# ------------- Get call params -----------------
START_DATE = "start"
END_DATE = "end"
LANG_CODE = "lang_code"
PAGE_SIZE = "page_size"
CALL_TYPE = "call_type"
IGNORED_CALLER_NUMBERS = "ignored_caller_numbers"
TAB = "tab"
PAGE = "page"
CUSTOM_SEARCH_KEY = "custom_search_key"
CUSTOM_SEARCH_VALUE = "custom_search_value"

# These are system generated pings and are never required
DEFAULT_IGNORE_CALLERS_LIST = ["ev-connect", "0000000000"]
# ------------------------------------------------

TOTAL_PAGES = "total_pages"
TOTAL_ITEMS = "total_items"
ITEMS = "items"
UUID = "uuid"
CONV_UUID = "conversation_uuid"
CALL_UUID = "call_uuid"
TURNS = "turns"
CONVERSATIONS = "conversations"
PREDICTION = "prediction"
METADATA = "metadata"
CREATED_AT = "created_at"
UPDATED_AT = "updated_at"

FILES = "files"
IN_MEMORY = "in-memory"
MEMORY_LIMIT = 10000
