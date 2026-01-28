"""Kairos Voice Scheduling Assistant Agent - Natural Conversational AI"""

import logging
import json
import asyncio
from livekit.agents import Agent
from livekit.agents.llm import function_tool
from typing import Annotated, Optional
from pydantic import Field
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta

load_dotenv()

logger = logging.getLogger("kairos-agent")


def format_phone_for_speech(phone: str) -> str:
    """Convert phone number to natural speech format."""
    digits_only = ''.join(c for c in phone if c.isdigit())
    
    digit_words = {
        '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
    }
    
    if len(digits_only) == 10:
        part1 = ' '.join(digit_words[d] for d in digits_only[:3])
        part2 = ' '.join(digit_words[d] for d in digits_only[3:6])
        part3 = ' '.join(digit_words[d] for d in digits_only[6:])
        return f"{part1}, {part2}, {part3}"
    elif len(digits_only) == 11 and digits_only[0] == '1':
        part1 = ' '.join(digit_words[d] for d in digits_only[1:4])
        part2 = ' '.join(digit_words[d] for d in digits_only[4:7])
        part3 = ' '.join(digit_words[d] for d in digits_only[7:])
        return f"one, {part1}, {part2}, {part3}"
    else:
        return ' '.join(digit_words.get(d, d) for d in digits_only)


def format_date_for_speech(date_str: str) -> str:
    """Convert YYYY-MM-DD to natural speech like 'January twenty-sixth'."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '').split('T')[0])
        day = dt.day
        
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        
        day_words = {
            1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
            6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth",
            11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth",
            15: "fifteenth", 16: "sixteenth", 17: "seventeenth", 18: "eighteenth",
            19: "nineteenth", 20: "twentieth", 21: "twenty-first", 22: "twenty-second",
            23: "twenty-third", 24: "twenty-fourth", 25: "twenty-fifth",
            26: "twenty-sixth", 27: "twenty-seventh", 28: "twenty-eighth",
            29: "twenty-ninth", 30: "thirtieth", 31: "thirty-first"
        }
        
        day_word = day_words.get(day, f"{day}{suffix}")
        month_name = dt.strftime("%B")
        
        return f"{month_name} {day_word}"
    except:
        return date_str


def format_time_for_speech(time_str: str) -> str:
    """Convert HH:MM to natural speech like 'two thirty PM'."""
    try:
        if 'T' in time_str:
            time_part = time_str.split('T')[1][:5]
        else:
            time_part = time_str[:5]
        
        hour, minute = map(int, time_part.split(':'))
        
        period = "AM" if hour < 12 else "PM"
        if hour == 0:
            hour = 12
        elif hour > 12:
            hour -= 12
        
        hour_words = {
            1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
            7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"
        }
        
        hour_word = hour_words.get(hour, str(hour))
        
        if minute == 0:
            return f"{hour_word} {period}"
        elif minute == 30:
            return f"{hour_word} thirty {period}"
        else:
            return f"{hour_word} {minute:02d} {period}"
    except:
        return time_str


class KairosAgent(Agent):
    """Natural voice scheduling assistant with human-like conversation skills"""
    
    def __init__(self, room=None, participant_name=None):
        super().__init__(
            instructions="""You are Kairos, a friendly receptionist at a medical office. Speak naturally like a real person on the phone.

IMPORTANT RULES:
1. Never mention any technical terms. The caller doesn't know you're an AI.
2. Say "Let me check..." then give the answer naturally.
3. Keep responses short - one or two sentences.
4. Be warm: "Great!", "Perfect!", "Sure thing!"
5. Always end with: "Anything else I can help with?"

WHEN CHECKING AVAILABILITY:
Say: "Let me check... I have openings at ten AM, two PM, and four thirty PM."

WHEN BOOKING:
Say: "Perfect, booking that for you... All set! You're confirmed for [date] at [time]."

WHEN CHECKING APPOINTMENTS:
Say: "Let me look... You have an appointment on [date] at [time]."

SPEAKING STYLE:
- Phone numbers: say each digit separately ("eight seven seven...")
- Dates: "January twenty-ninth" 
- Times: "two PM" or "ten thirty AM"
- Use filler words: "Hmm", "Let me see", "One sec"

You're a helpful receptionist. Just answer naturally!
""",
        )
        
        # Store room for data channel publishing
        self.room = room
        self.participant_name = participant_name  # Name from frontend input
        
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("[KairosAgent] Supabase client initialized")
        else:
            self.supabase = None
            logger.warning("[KairosAgent] Supabase credentials not set")
        
        # Store conversation context
        self.current_user_phone = None
        self.current_user_id = None
        self.current_user_name = participant_name  # Initialize with frontend name
        self.actions_taken = []  # Track actions for summary
        
        logger.info(f"[KairosAgent] Initialized with participant: {participant_name}")
    
    async def publish_tool_update(self, tool_name: str, data: dict):
        """Publish tool call update to frontend via data channel."""
        if self.room:
            try:
                message = json.dumps({
                    "type": "TOOL_UPDATE",
                    "tool": tool_name,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
                await self.room.local_participant.publish_data(
                    message.encode(),
                    topic="ui_state"
                )
                logger.info(f"[KairosAgent] Published tool update: {tool_name}")
            except Exception as e:
                logger.error(f"[KairosAgent] Failed to publish tool update: {e}")
    
    @function_tool()
    async def identify_user(
        self, 
        phone_number: Annotated[str, Field(description="User's phone number - must be 10 digits")]
    ) -> str:
        """Look up user by phone number. Requires a valid 10-digit phone number."""
        logger.info(f"[KairosAgent] identify_user called with: {phone_number}")
        
        # Extract digits only
        digits_only = ''.join(c for c in phone_number if c.isdigit())
        
        # Validate phone number length
        if len(digits_only) < 10:
            logger.warning(f"[KairosAgent] Invalid phone: {digits_only} ({len(digits_only)} digits)")
            return f"Hmm, that doesn't seem like a complete phone number. Could you give me all 10 digits please?"
        
        # Publish to UI with actual name
        display_name = self.participant_name or "User"
        await self.publish_tool_update("identify_user", {"name": display_name, "phone": digits_only[-10:]})
        
        self.current_user_phone = digits_only[-10:]  # Take last 10 digits
        
        if not self.supabase:
            return "Got it! How can I help you today?"
        
        try:
            response = self.supabase.table("users").select("*").eq(
                "phone_number", self.current_user_phone
            ).execute()
            
            if response.data:
                user = response.data[0]
                self.current_user_id = user.get("id")
                self.current_user_name = user.get("full_name", "there")
                logger.info(f"[KairosAgent] Found user: {self.current_user_name}")
                self.actions_taken.append(f"Identified user: {self.current_user_name}")
                return f"Hey {self.current_user_name}! Great to hear from you. How can I help you today?"
            else:
                logger.info(f"[KairosAgent] New user: {self.current_user_phone}")
                return "I don't have your number on file yet, but no problem! I can still help you. What would you like to do?"
        
        except Exception as e:
            logger.error(f"[KairosAgent] Error in identify_user: {e}")
            return "Got it! What can I help you with today?"
    
    @function_tool()
    async def fetch_slots(
        self,
        date_preference: Annotated[str, Field(description="Date like 'today', 'tomorrow', or YYYY-MM-DD")] = "tomorrow"
    ) -> str:
        """Get available appointment slots for a given date."""
        logger.info(f"[KairosAgent] fetch_slots called for: {date_preference}")
        
        await self.publish_tool_update("fetch_slots", {"date": date_preference})
        
        now = datetime.now()
        
        # Determine the target date
        if date_preference.lower() == "today":
            target_date = now
            # For today, only show future times
            current_hour = now.hour
            available_slots = []
            if current_hour < 10:
                available_slots.append("ten AM")
            if current_hour < 14:
                available_slots.append("two PM")
            if current_hour < 16:
                available_slots.append("four thirty PM")
            
            if not available_slots:
                return "Unfortunately, all slots for today have passed. Would you like to check tomorrow instead?"
            
            spoken_date = format_date_for_speech(now.strftime("%Y-%m-%d"))
            slots_text = ", ".join(available_slots[:-1]) + f", and {available_slots[-1]}" if len(available_slots) > 1 else available_slots[0]
            return f"For today, {spoken_date}, I have openings at {slots_text}. Which works for you?"
        else:
            # Tomorrow or specific date
            tomorrow = now + timedelta(days=1)
            spoken_date = format_date_for_speech(tomorrow.strftime("%Y-%m-%d"))
            return f"For tomorrow, {spoken_date}, I have openings at ten AM, two PM, and four thirty PM. Which works for you?"
    
    @function_tool()
    async def book_appointment(
        self,
        phone_number: Annotated[str, Field(description="User's 10-digit phone number")],
        date: Annotated[str, Field(description="Date in YYYY-MM-DD format")],
        time: Annotated[str, Field(description="Time in HH:MM 24-hour format")]
    ) -> str:
        """Book an appointment. Validates that the time is in the future."""
        logger.info(f"[KairosAgent] book_appointment called: {phone_number}, {date}, {time}")
        
        spoken_date = format_date_for_speech(date)
        spoken_time = format_time_for_speech(time)
        
        # Validate phone number
        digits_only = ''.join(c for c in phone_number if c.isdigit())
        if len(digits_only) < 10:
            return "I need your full 10-digit phone number first. What's your number?"
        
        # Validate the appointment is in the future
        try:
            appointment_dt = datetime.fromisoformat(f"{date}T{time}:00")
            now = datetime.now()
            
            if appointment_dt <= now:
                logger.warning(f"[KairosAgent] Past time requested: {appointment_dt} vs now {now}")
                return f"Oops, {spoken_time} has already passed today. Would you like to book for a later time, or maybe tomorrow?"
        except ValueError as e:
            logger.error(f"[KairosAgent] Invalid date/time format: {e}")
            return "I didn't catch that time correctly. Could you tell me again what time works for you?"
        
        await self.publish_tool_update("book_appointment", {
            "phone": digits_only[-10:],
            "date": date,
            "time": time
        })
        
        if not self.supabase:
            self.actions_taken.append(f"Booked appointment: {spoken_date} at {spoken_time}")
            return f"You're all set for {spoken_date} at {spoken_time}. Anything else?"
        
        try:
            normalized_phone = digits_only[-10:]  # Use validated phone
            
            # Find or create user
            user_res = self.supabase.table("users").select("id, full_name").eq("phone_number", normalized_phone).execute()
            
            if not user_res.data:
                # Use participant name from frontend, fallback to "Guest"
                user_name = self.participant_name or self.current_user_name or "Guest"
                insert_res = self.supabase.table("users").insert({
                    "phone_number": normalized_phone,
                    "full_name": user_name
                }).execute()
                
                if insert_res.data:
                    user_id = insert_res.data[0]["id"]
                else:
                    user_res = self.supabase.table("users").select("id").eq("phone_number", normalized_phone).execute()
                    user_id = user_res.data[0]["id"]
            else:
                user_id = user_res.data[0]["id"]
            
            # Check for double-booking
            start_dt = datetime.fromisoformat(f"{date}T{time}:00")
            end_dt = start_dt + timedelta(hours=1)
            
            existing = self.supabase.table("appointments").select("id").eq(
                "status", "booked"
            ).gte("start_time", start_dt.isoformat()).lt(
                "start_time", end_dt.isoformat()
            ).execute()
            
            if existing.data:
                return f"Oh, that slot at {spoken_time} is already taken. Would you like to try a different time? I have openings at ten AM and four thirty PM."
            
            # Create appointment
            appt_response = self.supabase.table("appointments").insert({
                "user_id": user_id,
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "status": "booked",
                "description": "Voice Booking"
            }).execute()
            
            if appt_response.data:
                logger.info("[KairosAgent] Appointment booked successfully")
                self.actions_taken.append(f"Booked: {spoken_date} at {spoken_time}")
                return f"You're all set for {spoken_date} at {spoken_time}. Anything else I can help with?"
            else:
                return "I couldn't book that slot. Want to try a different time?"
                
        except Exception as e:
            logger.error(f"[KairosAgent] Error in book_appointment: {e}")
            return "I'm having trouble booking that. Can we try again?"

    @function_tool()
    async def retrieve_appointments(
        self,
        phone_number: Annotated[str, Field(description="User's phone number")]
    ) -> str:
        """Check for upcoming appointments."""
        logger.info(f"[KairosAgent] retrieve_appointments called for: {phone_number}")
        
        await self.publish_tool_update("retrieve_appointments", {"phone": phone_number})
        
        if not self.supabase:
            return "You don't have any upcoming appointments. Would you like to book one?"
        
        try:
            normalized_phone = ''.join(c for c in phone_number if c.isdigit())
            
            user_res = self.supabase.table("users").select("id").eq("phone_number", normalized_phone).execute()
            if not user_res.data:
                return "I couldn't find any appointments. Would you like to book one?"
            
            user_id = user_res.data[0]["id"]
            
            now_iso = datetime.now().isoformat()
            appt_res = self.supabase.table("appointments").select("*").eq(
                "user_id", user_id
            ).eq("status", "booked").gt("start_time", now_iso).order("start_time").execute()
            
            if appt_res.data:
                appointments = []
                for appt in appt_res.data[:3]:
                    raw_start = appt.get("start_time", "")
                    if raw_start.endswith('Z'):
                        raw_start = raw_start[:-1]
                    
                    spoken_date = format_date_for_speech(raw_start)
                    spoken_time = format_time_for_speech(raw_start)
                    appointments.append(f"{spoken_date} at {spoken_time}")
                
                logger.info(f"[KairosAgent] Found {len(appointments)} appointments")
                self.actions_taken.append(f"Retrieved {len(appointments)} appointments")
                
                if len(appointments) == 1:
                    return f"You have one appointment: {appointments[0]}. Need to change it?"
                else:
                    return f"You have {len(appointments)} appointments: {', '.join(appointments)}. Anything you'd like to change?"
            else:
                return "You don't have any upcoming appointments. Want to book one?"

        except Exception as e:
            logger.error(f"[KairosAgent] Error in retrieve_appointments: {e}")
            return "I'm having trouble checking. Can you try again?"

    @function_tool()
    async def modify_appointment(
        self,
        phone_number: Annotated[str, Field(description="User's phone number")],
        original_date: Annotated[str, Field(description="Original date YYYY-MM-DD")],
        new_date: Annotated[str, Field(description="New date YYYY-MM-DD")],
        new_time: Annotated[str, Field(description="New time HH:MM")]
    ) -> str:
        """Reschedule an appointment."""
        logger.info(f"[KairosAgent] modify_appointment: {original_date} -> {new_date} {new_time}")
        
        await self.publish_tool_update("modify_appointment", {
            "original_date": original_date,
            "new_date": new_date,
            "new_time": new_time
        })
        
        spoken_new_date = format_date_for_speech(new_date)
        spoken_new_time = format_time_for_speech(new_time)
        
        if not self.supabase:
            self.actions_taken.append(f"Rescheduled to: {spoken_new_date} at {spoken_new_time}")
            return f"Done! Moved to {spoken_new_date} at {spoken_new_time}. Anything else?"
        
        try:
            normalized_phone = ''.join(c for c in phone_number if c.isdigit())
            
            user_res = self.supabase.table("users").select("id").eq("phone_number", normalized_phone).execute()
            if not user_res.data:
                return "I couldn't find your account. Can you confirm your phone number?"
            
            user_id = user_res.data[0]["id"]
            
            start_of_day = f"{original_date}T00:00:00"
            end_of_day = f"{original_date}T23:59:59"
            
            appt_res = self.supabase.table("appointments").select("id").eq(
                "user_id", user_id
            ).eq("status", "booked").gte("start_time", start_of_day).lte("start_time", end_of_day).execute()
            
            if not appt_res.data:
                return "I couldn't find that appointment. Want me to check your schedule?"
            
            appt_id = appt_res.data[0]["id"]
            
            new_start = datetime.fromisoformat(f"{new_date}T{new_time}:00")
            new_end = new_start + timedelta(hours=1)
            
            update_res = self.supabase.table("appointments").update({
                "start_time": new_start.isoformat(),
                "end_time": new_end.isoformat()
            }).eq("id", appt_id).execute()
            
            if update_res.data:
                logger.info("[KairosAgent] Appointment rescheduled")
                self.actions_taken.append(f"Rescheduled to: {spoken_new_date} at {spoken_new_time}")
                return f"Done! Moved to {spoken_new_date} at {spoken_new_time}. Anything else?"
            else:
                return "That slot might not be available. Try a different time?"
                
        except Exception as e:
            logger.error(f"[KairosAgent] Error in modify_appointment: {e}")
            return "I'm having trouble with that. What time works for you?"

    @function_tool()
    async def cancel_appointment(
        self,
        phone_number: Annotated[str, Field(description="User's phone number")],
        date: Annotated[str, Field(description="Date to cancel YYYY-MM-DD")]
    ) -> str:
        """Cancel an appointment."""
        logger.info(f"[KairosAgent] cancel_appointment: {date}")
        
        await self.publish_tool_update("cancel_appointment", {"date": date})
        
        spoken_date = format_date_for_speech(date)
        
        if not self.supabase:
            self.actions_taken.append(f"Cancelled appointment on {spoken_date}")
            return f"Cancelled your appointment for {spoken_date}. Anything else?"
        
        try:
            normalized_phone = ''.join(c for c in phone_number if c.isdigit())
            
            user_res = self.supabase.table("users").select("id").eq("phone_number", normalized_phone).execute()
            if not user_res.data:
                return "I couldn't find that. Can you confirm the date?"
            
            user_id = user_res.data[0]["id"]
            
            start_of_day = f"{date}T00:00:00"
            end_of_day = f"{date}T23:59:59"
            
            update_res = self.supabase.table("appointments").update({
                "status": "cancelled"
            }).eq("user_id", user_id).gte("start_time", start_of_day).lte("start_time", end_of_day).execute()
            
            if update_res.data:
                logger.info("[KairosAgent] Appointment cancelled")
                self.actions_taken.append(f"Cancelled: {spoken_date}")
                return f"Done! Cancelled your {spoken_date} appointment. Need anything else?"
            else:
                return "I couldn't find an appointment on that date. Want me to check your schedule?"

        except Exception as e:
            logger.error(f"[KairosAgent] Error in cancel_appointment: {e}")
            return "I'm having trouble with that. What's the date again?"

    @function_tool()
    async def end_conversation(
        self,
        phone_number: Annotated[str, Field(description="User's phone number")],
        summary: Annotated[str, Field(description="Brief summary of what was done")]
    ) -> str:
        """End the call gracefully with a summary."""
        logger.info("[KairosAgent] Ending conversation")
        
        # Build summary from actions taken
        full_summary = summary
        if self.actions_taken:
            full_summary = f"{summary}. Actions: {'; '.join(self.actions_taken)}"
        
        # Save to database
        if self.supabase:
            try:
                normalized_phone = ''.join(c for c in phone_number if c.isdigit())
                user_res = self.supabase.table("users").select("id").eq("phone_number", normalized_phone).execute()
                
                log_entry = {"summary": full_summary}
                if user_res.data:
                    log_entry["user_id"] = user_res.data[0]["id"]
                
                self.supabase.table("conversation_logs").insert(log_entry).execute()
                logger.info("[KairosAgent] Summary saved to database")
            except Exception as e:
                logger.error(f"[KairosAgent] Error saving summary: {e}")
        
        # Publish summary to UI
        await self.publish_tool_update("end_conversation", {
            "summary": full_summary,
            "actions": self.actions_taken
        })
        
        # Build spoken summary
        if self.actions_taken:
            spoken_summary = "Just to recap what we did today: " + ", ".join(self.actions_taken) + "."
            return f"{spoken_summary} It was great helping you! Have a wonderful day!"
        else:
            return "It was great chatting with you! Have a wonderful day, and call back anytime!"
