#!/usr/bin/env python3
"""
Date utility functions for converting CSV time slots to actual dates
"""

from datetime import datetime, timedelta
import json
from typing import List, Dict

def convert_slot_to_actual_date(slot_text: str) -> List[Dict]:
    """
    Convert 'Monday 9:00 AM' to actual dates for next 2 weeks
    
    Args:
        slot_text: Slot in format "Monday 9:00 AM"
    
    Returns:
        List of dictionaries with actual dates
    """
    try:
        # Parse slot format
        parts = slot_text.strip().split(' ')
        if len(parts) < 3:
            return []
        
        day_name = parts[0]
        time_part = ' '.join(parts[1:])  # "9:00 AM"
        
        # Parse time
        time_parts = time_part.split(':')
        hour = int(time_parts[0])
        minute_ampm = time_parts[1]
        
        # Separate minute and AM/PM
        minute = int(minute_ampm.split()[0])
        ampm = minute_ampm.split()[1]
        
        # Convert to 24-hour format
        if ampm.upper() == 'PM' and hour != 12:
            hour += 12
        elif ampm.upper() == 'AM' and hour == 12:
            hour = 0
        
        # Day mapping
        day_map = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 
            'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
        }
        
        if day_name not in day_map:
            return []
        
        target_weekday = day_map[day_name]
        base_date = datetime.now()
        
        # Find next occurrence of this weekday
        days_ahead = target_weekday - base_date.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        # Generate dates for next 2 weeks
        actual_dates = []
        for week in range(2):  # Next 2 weeks
            target_date = base_date + timedelta(days=days_ahead + (week * 7))
            actual_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Only add if it's in the future (at least 1 hour from now)
            if actual_datetime > datetime.now() + timedelta(hours=1):
                actual_dates.append({
                    "datetime": actual_datetime.isoformat(),
                    "formatted_date": actual_datetime.strftime("%Y-%m-%d %I:%M %p"),
                    "available": True,
                    "original_slot": slot_text
                })
        
        return actual_dates
        
    except Exception as e:
        print(f"Error converting slot '{slot_text}': {e}")
        return []

def parse_appointment_time(appointment_date: str) -> datetime:
    """
    Parse appointment date string to datetime object
    
    Args:
        appointment_date: Date string in various formats
    
    Returns:
        datetime object
    """
    try:
        # Try different date formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",  # "2024-01-15T14:30:00.123456" (ISO with microseconds)
            "%Y-%m-%dT%H:%M:%S",     # "2024-01-15T14:30:00" (ISO format)
            "%Y-%m-%d %I:%M %p",     # "2024-01-15 02:30 PM"
            "%Y-%m-%d %H:%M",        # "2024-01-15 14:30"
            "%I:%M %p",              # "2:30 PM" (assume today)
            "%H:%M"                  # "14:30" (assume today)
        ]
        
        for fmt in formats:
            try:
                if fmt in ["%I:%M %p", "%H:%M"]:
                    # For time-only formats, assume today
                    today = datetime.now().date()
                    time_str = appointment_date
                    if fmt == "%I:%M %p":
                        time_obj = datetime.strptime(time_str, fmt).time()
                    else:
                        time_obj = datetime.strptime(time_str, fmt).time()
                    return datetime.combine(today, time_obj)
                else:
                    return datetime.strptime(appointment_date, fmt)
            except ValueError:
                continue
        
        # If all formats fail, try to extract date from common patterns
        if "Monday" in appointment_date or "Tuesday" in appointment_date:
            # Convert slot format to actual date
            dates = convert_slot_to_actual_date(appointment_date)
            if dates:
                return datetime.fromisoformat(dates[0]["datetime"])
        
        # Default: assume it's a time for today
        today = datetime.now().date()
        try:
            time_obj = datetime.strptime(appointment_date, "%I:%M %p").time()
            return datetime.combine(today, time_obj)
        except:
            # Last resort: return current time + 1 hour
            return datetime.now() + timedelta(hours=1)
            
    except Exception as e:
        print(f"Error parsing appointment time '{appointment_date}': {e}")
        return datetime.now() + timedelta(hours=1)

def calculate_reminder_time(appointment_datetime: datetime, hours_before: int = 2) -> datetime:
    """
    Calculate when to send reminder
    
    Args:
        appointment_datetime: When the appointment is scheduled
        hours_before: How many hours before to send reminder
    
    Returns:
        datetime when reminder should be sent
    """
    return appointment_datetime - timedelta(hours=hours_before)

def is_slot_available(doctor_name: str, slot_datetime: str) -> bool:
    """
    Check if a slot is available (not already booked)
    
    Args:
        doctor_name: Name of the doctor
        slot_datetime: ISO format datetime string
    
    Returns:
        True if slot is available
    """
    try:
        # For now, assume all slots are available
        # In a real system, this would check against a booking database
        return True
    except Exception as e:
        print(f"Error checking slot availability: {e}")
        return True

def format_appointment_date(appointment_datetime: datetime) -> str:
    """
    Format appointment datetime for display
    
    Args:
        appointment_datetime: datetime object
    
    Returns:
        Formatted date string
    """
    return appointment_datetime.strftime("%Y-%m-%d %I:%M %p")

def get_next_available_slots(base_schedule: str, max_slots: int = 5) -> List[Dict]:
    """
    Get next available slots from base schedule
    
    Args:
        base_schedule: Comma-separated slot string from CSV
        max_slots: Maximum number of slots to return
    
    Returns:
        List of available slot dictionaries
    """
    if not base_schedule:
        return []
    
    all_slots = []
    slot_list = base_schedule.split(',')
    
    for slot in slot_list:
        slot = slot.strip()
        if slot:
            actual_dates = convert_slot_to_actual_date(slot)
            all_slots.extend(actual_dates)
    
    # Sort by datetime
    all_slots.sort(key=lambda x: x["datetime"])
    
    # Filter available slots and limit
    available_slots = []
    for slot in all_slots:
        if is_slot_available("", slot["datetime"]) and len(available_slots) < max_slots:
            available_slots.append(slot)
    
    return available_slots 