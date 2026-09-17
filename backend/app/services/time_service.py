from datetime import date, timedelta
from zoneinfo import ZoneInfo
from datetime import datetime


INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")


def today_india() -> date:
    """
    Get today's date in India.
    """
    return datetime.now(INDIA_TIMEZONE).date()


def resolve_date(time_value: str) -> date | None:
    """
    Convert a recognized time value into a calendar date.
    """

    today = today_india()

    if time_value in ("now", "today"):
        return today

    if time_value in (
        "tomorrow",
        "tomorrow_morning",
        "tomorrow_afternoon",
        "tomorrow_evening",
    ):
        return today + timedelta(days=1)

    if time_value == "day_after_tomorrow":
        return today + timedelta(days=2)

    if time_value == "day_after_tomorrow_morning":
        return today + timedelta(days=2)

    if time_value == "yesterday":
        return today - timedelta(days=1)

    weekday_map = {
        "this_saturday": 5,
        "this_sunday": 6,
        "next_monday": 0,
        "next_tuesday": 1,
        "next_wednesday": 2,
        "next_thursday": 3,
        "next_friday": 4,
        "next_saturday": 5,
        "next_sunday": 6,
    }

    if time_value in weekday_map:

        target_weekday = weekday_map[time_value]
        current_weekday = today.weekday()

        days_ahead = (target_weekday - current_weekday) % 7

        # "next X" should mean the next occurrence,
        # not today.
        if days_ahead == 0:
            days_ahead = 7

        return today + timedelta(days=days_ahead)

    return None


def get_time_range(time_value: str) -> tuple[int, int]:
    """
    Return an hourly range as (start_hour, end_hour).
    """

    if time_value in ("next_3_hours", "next_three_hours", "next_few_hours"):
        current_hour = datetime.now(INDIA_TIMEZONE).hour
        return current_hour, min(23, current_hour + 3)

    if time_value == "tonight":
        return 18, 23

    if time_value == "tomorrow_morning":
        return 6, 12

    if time_value == "tomorrow_afternoon":
        return 12, 18

    if time_value == "tomorrow_evening":
        return 18, 23

    if time_value == "day_after_tomorrow_morning":
        return 6, 12

    return 0, 23

def filter_hourly_forecast(hourly_forecast: list, time_value: str) -> list:
    """
    Filter hourly forecast according to the requested time period.
    """

    today = today_india()

    # --------------------------------------------------------
    # Next 3 hours
    # --------------------------------------------------------

    if time_value in ("next_3_hours", "next_three_hours", "next_few_hours"):
        now_hour_iso = datetime.now(INDIA_TIMEZONE).strftime("%Y-%m-%dT%H:00")
        future_hours = [
            hour
            for hour in hourly_forecast
            if hour.get("time", "") >= now_hour_iso
        ]
        if not future_hours:
            future_hours = hourly_forecast
        return future_hours[:3]

    # --------------------------------------------------------
    # Next 24 hours
    # --------------------------------------------------------

    if time_value == "next_24_hours":
        return hourly_forecast[:24]

    # --------------------------------------------------------
    # Next 48 hours
    # --------------------------------------------------------

    if time_value == "next_48_hours":
        return hourly_forecast[:48]

    # --------------------------------------------------------
    # Tonight
    # --------------------------------------------------------

    if time_value == "tonight":

        target_date = today.isoformat()

        return [
            hour
            for hour in hourly_forecast
            if hour["time"].startswith(target_date)
            and 18 <= int(hour["time"][11:13]) <= 23
        ]

    # --------------------------------------------------------
    # Tomorrow morning
    # --------------------------------------------------------

    if time_value == "tomorrow_morning":

        target_date = (
            today + timedelta(days=1)
        ).isoformat()

        return [
            hour
            for hour in hourly_forecast
            if hour["time"].startswith(target_date)
            and 6 <= int(hour["time"][11:13]) < 12
        ]

    # --------------------------------------------------------
    # Tomorrow afternoon
    # --------------------------------------------------------

    if time_value == "tomorrow_afternoon":

        target_date = (
            today + timedelta(days=1)
        ).isoformat()

        return [
            hour
            for hour in hourly_forecast
            if hour["time"].startswith(target_date)
            and 12 <= int(hour["time"][11:13]) < 18
        ]

    # --------------------------------------------------------
    # Tomorrow evening
    # --------------------------------------------------------

    if time_value == "tomorrow_evening":

        target_date = (
            today + timedelta(days=1)
        ).isoformat()

        return [
            hour
            for hour in hourly_forecast
            if hour["time"].startswith(target_date)
            and 18 <= int(hour["time"][11:13]) <= 23
        ]

    # --------------------------------------------------------
    # Day after tomorrow morning
    # --------------------------------------------------------

    if time_value == "day_after_tomorrow_morning":

        target_date = (
            today + timedelta(days=2)
        ).isoformat()

        return [
            hour
            for hour in hourly_forecast
            if hour["time"].startswith(target_date)
            and 6 <= int(hour["time"][11:13]) < 12
        ]

    return []