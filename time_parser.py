"""Parse natural language time durations into datetime objects."""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

import parsedatetime
from dateutil.relativedelta import relativedelta


class TimeParser:
    """Parse natural language time expressions into future datetime objects."""
    
    def __init__(self):
        self.cal = parsedatetime.Calendar()
        
        # Common patterns for explicit durations
        self.duration_patterns = [
            # "3 months", "1 year", "2 weeks", etc.
            (r"(\d+)\s*(second|sec|s)s?", "seconds"),
            (r"(\d+)\s*(minute|min|m)s?", "minutes"),
            (r"(\d+)\s*(hour|hr|h)s?", "hours"),
            (r"(\d+)\s*(day|d)s?", "days"),
            (r"(\d+)\s*(week|wk|w)s?", "weeks"),
            (r"(\d+)\s*(month|mo)s?", "months"),
            (r"(\d+)\s*(year|yr|y)s?", "years"),
        ]
    
    def parse(self, text: str, base_time: Optional[datetime] = None) -> Tuple[Optional[datetime], Optional[str]]:
        """
        Parse a time expression and return the target datetime.
        
        Args:
            text: The text containing the time expression (e.g., "3 months", "tomorrow at 5pm")
            base_time: The reference time (defaults to now)
        
        Returns:
            Tuple of (target_datetime, matched_duration_text) or (None, None) if parsing failed
        """
        if base_time is None:
            base_time = datetime.utcnow()
        
        # Clean and normalize the text
        text = text.lower().strip()
        
        # Remove the bot mention if present
        text = re.sub(r"@\w+", "", text).strip()
        
        # Try explicit duration patterns first
        result = self._parse_explicit_duration(text, base_time)
        if result[0]:
            return result
        
        # Fall back to parsedatetime for natural language
        result = self._parse_natural_language(text, base_time)
        if result[0]:
            return result
        
        return None, None
    
    def _parse_explicit_duration(self, text: str, base_time: datetime) -> Tuple[Optional[datetime], Optional[str]]:
        """Parse explicit duration patterns like '3 months' or '2 weeks'."""
        
        for pattern, unit in self.duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = int(match.group(1))
                matched_text = match.group(0)
                
                if unit == "seconds":
                    delta = timedelta(seconds=amount)
                elif unit == "minutes":
                    delta = timedelta(minutes=amount)
                elif unit == "hours":
                    delta = timedelta(hours=amount)
                elif unit == "days":
                    delta = timedelta(days=amount)
                elif unit == "weeks":
                    delta = timedelta(weeks=amount)
                elif unit == "months":
                    delta = relativedelta(months=amount)
                elif unit == "years":
                    delta = relativedelta(years=amount)
                else:
                    continue
                
                target_time = base_time + delta
                return target_time, matched_text
        
        return None, None
    
    def _parse_natural_language(self, text: str, base_time: datetime) -> Tuple[Optional[datetime], Optional[str]]:
        """Parse natural language time expressions using parsedatetime."""
        
        # Common phrases to try
        phrases_to_try = [
            text,
            f"in {text}",
            f"{text} from now",
        ]
        
        for phrase in phrases_to_try:
            try:
                time_struct, parse_status = self.cal.parse(phrase, base_time)
                
                # parse_status > 0 means something was parsed
                if parse_status > 0:
                    parsed_time = datetime(*time_struct[:6])
                    
                    # Only accept future times
                    if parsed_time > base_time:
                        return parsed_time, text
            except Exception:
                continue
        
        return None, None
    
    def format_duration(self, target_time: datetime, base_time: Optional[datetime] = None) -> str:
        """Format the duration between base_time and target_time as a human-readable string."""
        
        if base_time is None:
            base_time = datetime.utcnow()
        
        delta = target_time - base_time
        total_seconds = int(delta.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds} second{'s' if total_seconds != 1 else ''}"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''}"
        elif total_seconds < 604800:
            days = total_seconds // 86400
            return f"{days} day{'s' if days != 1 else ''}"
        elif total_seconds < 2592000:  # ~30 days
            weeks = total_seconds // 604800
            return f"{weeks} week{'s' if weeks != 1 else ''}"
        elif total_seconds < 31536000:  # ~365 days
            months = total_seconds // 2592000
            return f"{months} month{'s' if months != 1 else ''}"
        else:
            years = total_seconds // 31536000
            return f"{years} year{'s' if years != 1 else ''}"


# Singleton instance
time_parser = TimeParser()


def parse_reminder_time(text: str) -> Tuple[Optional[datetime], Optional[str]]:
    """
    Convenience function to parse a reminder time from text.
    
    Args:
        text: The mention text (e.g., "@RemindMeXplz 3 months")
    
    Returns:
        Tuple of (target_datetime, matched_duration_text) or (None, None) if parsing failed
    """
    return time_parser.parse(text)


if __name__ == "__main__":
    # Test the parser
    test_cases = [
        "@RemindMeXplz 3 months",
        "@RemindMeXplz 2 weeks",
        "@RemindMeXplz 1 year",
        "@RemindMeXplz tomorrow",
        "@RemindMeXplz in 5 days",
        "@RemindMeXplz 30 minutes",
        "@RemindMeXplz next friday",
        "remind me in 6 hours",
        "2 days",
        "1 month",
    ]
    
    print("Time Parser Test Results:")
    print("=" * 60)
    
    for test in test_cases:
        result, matched = parse_reminder_time(test)
        if result:
            print(f"✓ '{test}' -> {result.strftime('%Y-%m-%d %H:%M:%S')} (matched: '{matched}')")
        else:
            print(f"✗ '{test}' -> Could not parse")

