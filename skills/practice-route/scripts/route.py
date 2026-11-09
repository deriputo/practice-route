"""Calculate practice capacity and review dates without editing the route sheet."""

import argparse
import json
from datetime import date, timedelta


WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
REVIEW_INTERVALS = (1, 3, 7, 14)


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"Expected a date in YYYY-MM-DD format: {value}") from error


def parse_minutes(entries, parse_key):
    values = {}
    for entry in entries:
        key, separator, minutes = entry.partition("=")
        if not separator or not minutes.isascii() or not minutes.isdecimal():
            raise ValueError(f"Expected KEY=MINUTES with nonnegative whole minutes: {entry}")
        key = parse_key(key)
        if key in values:
            raise ValueError(f"Duplicate schedule entry: {entry}")
        values[key] = int(minutes)
    return values


def parse_weekday(value):
    if value.lower() not in WEEKDAYS:
        raise ValueError(f"Expected a weekday from mon to sun: {value}")
    return WEEKDAYS.index(value.lower())


def available_sessions(start, end, weekly, overrides):
    for ordinal in range(start.toordinal(), end.toordinal() + 1):
        day = date.fromordinal(ordinal)
        minutes = overrides.get(day, weekly.get(day.weekday(), 0))
        if minutes:
            yield {"date": day.isoformat(), "minutes": minutes}


def capacity(args, weekly, overrides):
    start = parse_date(args.start)
    end = parse_date(args.through)
    if end < start:
        raise ValueError("--through must be on or after --from")
    sessions = list(available_sessions(start, end, weekly, overrides))
    return {
        "sessions": sessions,
        "total_minutes": sum(session["minutes"] for session in sessions),
    }


def review(args, weekly, overrides):
    attempted = parse_date(args.on)
    end = parse_date(args.through)
    if end < attempted:
        raise ValueError("--through must be on or after --on")
    has_previous = args.interval is not None and args.due is not None
    if args.outcome == "new":
        if args.interval is not None or args.due is not None:
            raise ValueError("A new review item does not take --interval or --due")
    elif not has_previous:
        raise ValueError("A review attempt requires both --interval and --due")

    interval = REVIEW_INTERVALS[0]
    if has_previous and args.outcome != "missed":
        interval = args.interval
    if has_previous:
        due = parse_date(args.due)
        if args.outcome != "missed" and attempted < due:
            target = due
        else:
            if args.outcome == "independent":
                step = REVIEW_INTERVALS.index(interval)
                interval = REVIEW_INTERVALS[min(step + 1, len(REVIEW_INTERVALS) - 1)]
            target = attempted + timedelta(days=interval)
    else:
        target = attempted + timedelta(days=interval)

    next_session = next(available_sessions(target, end, weekly, overrides), None)
    return {
        "interval_days": interval,
        "target_date": target.isoformat(),
        "next_session": next_session,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    schedule = argparse.ArgumentParser(add_help=False)
    schedule.add_argument("--through", required=True, metavar="YYYY-MM-DD",
                          help="last usable study date, inclusive")
    schedule.add_argument("--weekly", action="append", default=[], metavar="MON=MINUTES",
                          help="recurring study minutes for one weekday, repeat as needed")
    schedule.add_argument("--override", action="append", default=[], metavar="DATE=MINUTES",
                          help="replace a day's minutes, use 0 for an unavailable date")
    commands = parser.add_subparsers(dest="command", required=True)

    budget_parser = commands.add_parser("capacity", parents=[schedule],
                                        help="show dates with study time and the total")
    budget_parser.add_argument("--from", dest="start", required=True, metavar="YYYY-MM-DD")
    budget_parser.set_defaults(run=capacity)

    review_parser = commands.add_parser("review", parents=[schedule],
                                        help="find the first eligible study session for a review")
    review_parser.add_argument("--on", required=True, metavar="YYYY-MM-DD")
    review_parser.add_argument("--outcome", required=True,
                               choices=("new", "independent", "helped", "missed"))
    review_parser.add_argument("--interval", type=int, choices=REVIEW_INTERVALS,
                               help="current review interval in days")
    review_parser.add_argument("--due", metavar="YYYY-MM-DD",
                               help="previous target date, before calendar adjustment")
    review_parser.set_defaults(run=review)

    args = parser.parse_args()
    try:
        weekly = parse_minutes(args.weekly, parse_weekday)
        overrides = parse_minutes(args.override, parse_date)
        result = args.run(args, weekly, overrides)
    except (ValueError, OverflowError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
