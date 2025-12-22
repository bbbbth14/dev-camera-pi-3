"""
Attendance/Check-in/Check-out Tracker
Manages attendance records and access control
"""

import csv
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import config


class AttendanceTracker:
    """Track check-in/check-out events"""
    
    def __init__(self):
        """Initialize the attendance tracker"""
        self.attendance_file = config.ATTENDANCE_FILE
        self.status_log_file = os.path.join(config.DATA_DIR, 'status_log.csv')
        self.last_checkin = {}  # Track last check-in time per person
        
        # Create attendance file if it doesn't exist
        if not os.path.exists(self.attendance_file):
            self._create_attendance_file()
        
        # Create status log file if it doesn't exist
        if not os.path.exists(self.status_log_file):
            self._create_status_log_file()
        
        # Load last check-ins from today
        self._load_today_checkins()
        
        print("[INFO] Attendance tracker initialized")
    
    def _create_status_log_file(self):
        """Create a new status log CSV file with headers"""
        try:
            with open(self.status_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Name', 'Status', 'Check_In_Time', 'Check_Out_Time', 'Duration'])
            print(f"[INFO] Created new status log file: {self.status_log_file}")
        except Exception as e:
            print(f"[ERROR] Failed to create status log file: {e}")
    
    def _create_attendance_file(self):
        """Create a new attendance CSV file with headers"""
        try:
            with open(self.attendance_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Name', 'Date', 'Time', 'Event', 'Confidence'])
            print(f"[INFO] Created new attendance file: {self.attendance_file}")
        except Exception as e:
            print(f"[ERROR] Failed to create attendance file: {e}")
    
    def _load_today_checkins(self):
        """Load check-in times from today to enforce cooldown"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            if os.path.exists(self.attendance_file):
                with open(self.attendance_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['Date'] == today and row['Event'] in ['CHECK_IN', 'ACCESS_GRANTED']:
                            name = row['Name']
                            time_str = row['Time']
                            timestamp = datetime.strptime(f"{today} {time_str}", '%Y-%m-%d %H:%M:%S')
                            
                            # Keep the most recent check-in
                            if name not in self.last_checkin or timestamp > self.last_checkin[name]:
                                self.last_checkin[name] = timestamp
        except Exception as e:
            print(f"[WARNING] Failed to load today's check-ins: {e}")
    
    def can_checkin(self, name: str) -> bool:
        """
        Check if person can check in (cooldown period)
        
        Args:
            name: Person's name
            
        Returns:
            True if can check in, False if in cooldown period
        """
        if name not in self.last_checkin:
            return True
        
        time_since_last = datetime.now() - self.last_checkin[name]
        cooldown = timedelta(seconds=config.CHECK_IN_COOLDOWN)
        
        return time_since_last >= cooldown
    
    def get_cooldown_remaining(self, name: str) -> int:
        """
        Get remaining cooldown time in seconds
        
        Args:
            name: Person's name
            
        Returns:
            Remaining seconds, or 0 if no cooldown
        """
        if name not in self.last_checkin:
            return 0
        
        time_since_last = datetime.now() - self.last_checkin[name]
        cooldown = timedelta(seconds=config.CHECK_IN_COOLDOWN)
        remaining = cooldown - time_since_last
        
        return max(0, int(remaining.total_seconds()))
    
    def record_event(self, name: str, event: str, confidence: float = 1.0) -> bool:
        """
        Record an attendance event
        
        Args:
            name: Person's name
            event: Event type (CHECK_IN, CHECK_OUT, ACCESS_GRANTED, ACCESS_DENIED)
            confidence: Recognition confidence (0-1)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            now = datetime.now()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H:%M:%S')
            
            with open(self.attendance_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([name, date_str, time_str, event, f"{confidence:.2f}"])
            
            # Update last check-in time
            if event in ['CHECK_IN', 'ACCESS_GRANTED']:
                self.last_checkin[name] = now
            
            print(f"[INFO] Recorded: {name} - {event} at {time_str}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to record event: {e}")
            return False
    
    def get_today_attendance(self) -> List[Dict[str, str]]:
        """
        Get all attendance records for today
        
        Returns:
            List of attendance records
        """
        today = datetime.now().strftime('%Y-%m-%d')
        records = []
        
        try:
            if os.path.exists(self.attendance_file):
                with open(self.attendance_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['Date'] == today:
                            records.append(row)
        except Exception as e:
            print(f"[ERROR] Failed to read attendance: {e}")
        
        return records
    
    def get_attendance_summary(self) -> Dict[str, int]:
        """
        Get summary of today's attendance
        
        Returns:
            Dictionary with counts of different events
        """
        records = self.get_today_attendance()
        summary = {
            'total_checkins': 0,
            'total_checkouts': 0,
            'total_access_granted': 0,
            'total_access_denied': 0,
            'unique_people': set()
        }
        
        for record in records:
            event = record['Event']
            name = record['Name']
            
            if event == 'CHECK_IN':
                summary['total_checkins'] += 1
                summary['unique_people'].add(name)
            elif event == 'CHECK_OUT':
                summary['total_checkouts'] += 1
            elif event == 'ACCESS_GRANTED':
                summary['total_access_granted'] += 1
                summary['unique_people'].add(name)
            elif event == 'ACCESS_DENIED':
                summary['total_access_denied'] += 1
        
        summary['unique_people'] = len(summary['unique_people'])
        
        return summary
    
    def export_report(self, output_file: str, start_date: Optional[str] = None, 
                     end_date: Optional[str] = None):
        """
        Export attendance report to a file
        
        Args:
            output_file: Output file path
            start_date: Start date (YYYY-MM-DD), optional
            end_date: End date (YYYY-MM-DD), optional
        """
        try:
            records = []
            
            with open(self.attendance_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    date = row['Date']
                    
                    # Filter by date range if specified
                    if start_date and date < start_date:
                        continue
                    if end_date and date > end_date:
                        continue
                    
                    records.append(row)
            
            # Write filtered records
            with open(output_file, 'w', newline='') as f:
                if records:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)
            
            print(f"[INFO] Exported {len(records)} records to {output_file}")
            
        except Exception as e:
            print(f"[ERROR] Failed to export report: {e}")
    
    def get_user_status(self) -> Dict[str, Dict]:
        """
        Get status of all users with their last check-in/out
        
        Returns:
            Dictionary with user status information
        """
        today = datetime.now().strftime('%Y-%m-%d')
        user_status = {}
        
        try:
            if os.path.exists(self.attendance_file):
                with open(self.attendance_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['Date'] == today and row['Event'] in ['CHECK_IN', 'CHECK_OUT']:
                            name = row['Name']
                            event = row['Event']
                            time_str = row['Time']
                            
                            if name not in user_status:
                                user_status[name] = {
                                    'last_event': event,
                                    'last_time': time_str,
                                    'status': 'OUT',
                                    'check_in_time': None,
                                    'check_out_time': None,
                                    'duration': None,
                                    'first_check_in': None
                                }
                            
                            # Update last event
                            user_status[name]['last_event'] = event
                            user_status[name]['last_time'] = time_str
                            
                            # Track first check-in and last check-out
                            if event == 'CHECK_IN':
                                user_status[name]['status'] = 'IN'
                                user_status[name]['check_out_time'] = None  # Reset checkout
                                
                                # Set first check-in if not set
                                if user_status[name]['first_check_in'] is None:
                                    user_status[name]['first_check_in'] = time_str
                                    user_status[name]['check_in_time'] = time_str
                                
                            elif event == 'CHECK_OUT':
                                user_status[name]['status'] = 'OUT'
                                user_status[name]['check_out_time'] = time_str
                                
                                # Calculate duration from FIRST check-in to LAST check-out
                                if user_status[name]['first_check_in']:
                                    check_in = datetime.strptime(
                                        f"{today} {user_status[name]['first_check_in']}", 
                                        '%Y-%m-%d %H:%M:%S'
                                    )
                                    check_out = datetime.strptime(
                                        f"{today} {time_str}", 
                                        '%Y-%m-%d %H:%M:%S'
                                    )
                                    duration = check_out - check_in
                                    hours = int(duration.total_seconds() // 3600)
                                    minutes = int((duration.total_seconds() % 3600) // 60)
                                    user_status[name]['duration'] = f"{hours}h {minutes}m"
        
        except Exception as e:
            print(f"[ERROR] Failed to get user status: {e}")
        
        return user_status
    
    def log_status_to_file(self):
        """Log current status of all users to file"""
        try:
            user_status = self.get_user_status()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.status_log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                for name, status in user_status.items():
                    writer.writerow([
                        timestamp,
                        name,
                        status['status'],
                        status.get('check_in_time', 'N/A'),
                        status.get('check_out_time', 'N/A'),
                        status.get('duration', 'N/A')
                    ])
            
            print(f"[INFO] Logged status for {len(user_status)} users")
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to log status: {e}")
            return False
    
    def check_in_out(self, name: str) -> str:
        """
        Toggle check-in/check-out for a person
        
        Args:
            name: Person's name
            
        Returns:
            Status message
        """
        # Get current status
        user_status = self.get_user_status()
        
        # Check current status - if IN, then CHECK OUT; otherwise CHECK IN
        if name in user_status and user_status[name]['status'] == 'IN':
            # User is IN, so CHECK OUT
            self.record_event(name, 'CHECK_OUT')
            # Log status after check-out
            self.log_status_to_file()
            return 'CHECKED OUT'
        else:
            # User is OUT or not checked in, so CHECK IN
            self.record_event(name, 'CHECK_IN')
            # Log status after check-in
            self.log_status_to_file()
            return 'CHECKED IN'


if __name__ == "__main__":
    """Test the attendance tracker"""
    print("[INFO] Testing attendance tracker...")
    
    tracker = AttendanceTracker()
    
    # Test recording events
    tracker.record_event("Test User", "CHECK_IN", 0.95)
    tracker.record_event("Test User", "CHECK_OUT", 0.92)
    
    # Get summary
    summary = tracker.get_attendance_summary()
    print(f"\n[INFO] Today's Summary:")
    print(f"  Check-ins: {summary['total_checkins']}")
    print(f"  Check-outs: {summary['total_checkouts']}")
    print(f"  Access Granted: {summary['total_access_granted']}")
    print(f"  Access Denied: {summary['total_access_denied']}")
    print(f"  Unique People: {summary['unique_people']}")
    
    # Show today's records
    records = tracker.get_today_attendance()
    print(f"\n[INFO] Today's Records ({len(records)} total):")
    for record in records[-5:]:  # Show last 5
        print(f"  {record['Name']} - {record['Event']} at {record['Time']}")

