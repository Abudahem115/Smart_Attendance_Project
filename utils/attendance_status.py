# File: utils/attendance_status.py
"""
Shared attendance status determination logic.
Used by both the hardware face recognizer and the attendance logger
to prevent code duplication.
"""


def determine_attendance_status(hour: int) -> str:
    """
    Determine the attendance status label based on the current hour.

    Args:
        hour: The current hour (0-23).

    Returns:
        A status string describing the attendance type.
    """
    if 5 <= hour < 12:
        return "Morning Check-In"
    elif 12 <= hour < 13:
        return "Morning Check-Out"
    elif 13 <= hour < 16:
        return "Afternoon Check-In"
    elif 16 <= hour < 22:
        return "Afternoon Check-Out"
    else:
        return "Check-In/Out"
