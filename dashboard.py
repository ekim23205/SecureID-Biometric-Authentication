import json
from pathlib import Path

import pandas as pd
import streamlit as st

# SecureID - Privacy-Focused Security Dashboard
# Reads security event logs only, not biometric data.

st.set_page_config(
    page_title="SecureID Security Dashboard",
    page_icon="🛡️",
    layout="wide"
)

LOG_FILE = (
    Path(__file__).resolve().parent
    / "data"
    / "security_events.jsonl"
)

EVENT_TYPES = [
    "DEMO_MATCH",
    "NO_MATCH",
    "TEMPORARY_LOCKOUT",
    "LOCKOUT_ENDED"
]


def load_events():
    """Load and validate local security events."""

    if not LOG_FILE.exists():
        return pd.DataFrame(
            columns=["timestamp", "event"]
        )

    records = []

    with LOG_FILE.open(
        "r", encoding="utf-8"
    ) as file:
        for line in file:
            try:
                record = json.loads(line)

                if (
                    isinstance(record, dict)
                    and record.get("event") in EVENT_TYPES
                    and isinstance(
                        record.get("timestamp"), str
                    )
                ):
                    records.append({
                        "timestamp": record["timestamp"],
                        "event": record["event"]
                    })

            except json.JSONDecodeError:
                continue

    if not records:
        return pd.DataFrame(
            columns=["timestamp", "event"]
        )

    df = pd.DataFrame(records)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        utc=True,
        errors="coerce"
    )

    df = df.dropna(subset=["timestamp"])

    return df.sort_values(
        "timestamp", ascending=False
    )


# Dashboard title
st.title("🛡️ SecureID Security Dashboard")

st.caption(
    "Local authentication monitoring | "
    "Privacy-preserving event records"
)

st.warning(
    "Demo system only. Facial matches are not "
    "validated secure logins."
)

# Load event history
df = load_events()

if df.empty:
    st.info(
        "No security events recorded yet. "
        "Run face_authentication.py and press V "
        "to generate events."
    )
    st.stop()

# Calculate security metrics
matches = (df["event"] == "DEMO_MATCH").sum()
failures = (df["event"] == "NO_MATCH").sum()

lockouts = (
    df["event"] == "TEMPORARY_LOCKOUT"
).sum()

total_events = len(df)

# Display security metrics
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Demo Matches",
    int(matches)
)

col2.metric(
    "Failed Matches",
    int(failures)
)

col3.metric(
    "Security Lockouts",
    int(lockouts)
)

col4.metric(
    "Total Events",
    total_events
)

st.divider()

# Authentication activity chart
st.subheader("Authentication Activity")

chart_data = pd.DataFrame({
    "Event Type": [
        "Demo Matches",
        "Failed Matches",
        "Lockouts"
    ],
    "Count": [
        int(matches),
        int(failures),
        int(lockouts)
    ]
})

st.bar_chart(
    chart_data.set_index("Event Type")
)

st.divider()

# Recent security events
st.subheader("Recent Security Events")

recent = df.head(20).copy()

recent["timestamp"] = (
    recent["timestamp"]
    .dt.strftime("%Y-%m-%d %H:%M:%S UTC")
)

recent.columns = [
    "Timestamp",
    "Security Event"
]

st.dataframe(
    recent,
    use_container_width=True,
    hide_index=True
)

# Alerts panel
st.divider()
st.subheader("Security Alerts")

if lockouts > 0:
    st.error(
        f"{int(lockouts)} temporary lockout "
        "event(s) recorded in the log."
    )
else:
    st.success(
        "No temporary lockouts recorded."
    )

# Privacy information
st.divider()
st.subheader("Privacy Protection")

st.write(
    "This dashboard reads local security "
    "events only. It does not load facial "
    "images, biometric samples, encryption "
    "keys, or user names."
)

st.caption(
    "Timestamps and authentication outcomes "
    "are still sensitive activity metadata. "
    "Keep event logs private."
)

# Manual refresh
if st.button("Refresh Dashboard"):
    st.rerun()