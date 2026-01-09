"""
Attendance/Check-in/Check-out Tracker
Manages attendance records and access control
"""

import csv
import os
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from zipfile import BadZipFile
import config
try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("[WARNING] openpyxl not installed. Run: pip install openpyxl")


class AttendanceTracker:
    """Track check-in/check-out events"""
    
    def __init__(self):
        """Initialize the attendance tracker"""
        self.attendance_file = config.ATTENDANCE_FILE
        self.status_log_file = os.path.join(config.DATA_DIR, 'status_log.csv')
        self.last_checkin = {}  # Track last check-in time per person
        self._excel_lock = threading.Lock()
        
        # Create (or recover) attendance file
        if not os.path.exists(self.attendance_file):
            self._create_attendance_file()
        else:
            # If the XLSX is corrupted (common if read/write happens concurrently),
            # rename it and recreate a fresh workbook so the app can continue.
            if EXCEL_AVAILABLE:
                try:
                    with self._excel_lock:
                        wb = load_workbook(self.attendance_file)
                        wb.close()
                except BadZipFile:
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    corrupt_path = self.attendance_file.replace('.xlsx', f'_corrupt_{ts}.xlsx')
                    try:
                        os.rename(self.attendance_file, corrupt_path)
                        print(f"[WARNING] Attendance file corrupted. Renamed to: {corrupt_path}")
                    except Exception as e:
                        print(f"[WARNING] Failed to rename corrupted attendance file: {e}")
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
        """Create a new attendance Excel file with headers"""
        try:
            if not EXCEL_AVAILABLE:
                print("[ERROR] openpyxl not installed")
                return
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Attendance"
            
            # Headers with styling
            headers = ['Name', 'Day', 'Time In', 'Time Out', 'Total', 'Status', 'Time Late', 'Time OT']
            ws.append(headers)
            
            # Style headers
            header_font = Font(bold=True, size=12)
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            for cell in ws[1]:
                cell.font = Font(bold=True, size=12, color="FFFFFF")
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Set column widths
            ws.column_dimensions['A'].width = 15  # Name
            ws.column_dimensions['B'].width = 12  # Day
            ws.column_dimensions['C'].width = 12  # Time In
            ws.column_dimensions['D'].width = 12  # Time Out
            ws.column_dimensions['E'].width = 12  # Total
            ws.column_dimensions['F'].width = 15  # Status
            ws.column_dimensions['G'].width = 12  # Time Late
            ws.column_dimensions['H'].width = 12  # Time OT
            
            wb.save(self.attendance_file)
            print(f"[INFO] Created new attendance file: {self.attendance_file}")
        except Exception as e:
            print(f"[ERROR] Failed to create attendance file: {e}")
    
    def _load_today_checkins(self):
        """Load check-in times from today to enforce cooldown"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            if not os.path.exists(self.attendance_file):
                return
            
            if not EXCEL_AVAILABLE:
                return
            
            with self._excel_lock:
                wb = load_workbook(self.attendance_file)
                ws = wb.active
            
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if len(row) < 3:
                        continue
                    name = row[0]
                    day = row[1]
                    time_in = row[2]
                    
                    if day == today and name and time_in:
                        try:
                            timestamp = datetime.strptime(f"{today} {time_in}", '%Y-%m-%d %H:%M:%S')
                            if name not in self.last_checkin or timestamp > self.last_checkin[name]:
                                self.last_checkin[name] = timestamp
                        except:
                            pass

                wb.close()
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
        Record an attendance event to Excel
        
        Args:
            name: Person's name
            event: Event type (CHECK_IN, CHECK_OUT, ACCESS_GRANTED, ACCESS_DENIED)
            confidence: Recognition confidence (0-1)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not EXCEL_AVAILABLE:
                print("[ERROR] openpyxl not installed")
                return False
            
            now = datetime.now()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H:%M:%S')
            
            # Get user status to determine punctuality (computed outside the Excel lock)
            user_status = self.get_user_status()

            with self._excel_lock:
                wb = load_workbook(self.attendance_file)
                ws = wb.active

                # Find if user already has a row for today
                # IMPORTANT: Find the LAST (most recent) row for today, not the first
                user_row = None
                for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
                    if row[0].value == name and row[1].value == date_str:
                        user_row = idx  # Keep updating - will end up with the last match

                if event == 'CHECK_IN':
                    # ONE row per person per day
                    # CHECK IN = FIRST check-in time of the day (NEVER update)
                    if user_row is not None:
                        existing_time_in = ws.cell(user_row, 3).value
                        existing_time_out = ws.cell(user_row, 4).value
                        
                        # If already has first check-in time
                        if existing_time_in:
                            # If also has checkout (user is OUT), clear checkout so status becomes IN
                            if existing_time_out:
                                print(f"[DEBUG] Clearing checkout time to toggle status to IN")
                                ws.cell(user_row, 4).value = None  # Clear Time Out
                                ws.cell(user_row, 5).value = None  # Clear Total
                                wb.save(self.attendance_file)
                                wb.close()
                                return True
                            else:
                                # Already IN, don't update
                                print(f"[DEBUG] Already IN, not updating Excel")
                                wb.close()
                                return True

                    # Determine punctuality for first check-in
                    punctuality = ''
                    time_late = ''
                    if name not in user_status or user_status[name].get('first_check_in') is None:
                        cutoff_time = datetime.strptime("08:00:00", "%H:%M:%S").time()
                        if now.time() > cutoff_time:
                            punctuality = 'LATE'
                            cutoff_dt = datetime.strptime("08:00:00", "%H:%M:%S")
                            late_duration = now - cutoff_dt.replace(year=now.year, month=now.month, day=now.day)
                            late_minutes = int(late_duration.total_seconds() // 60)
                            late_hours = late_minutes // 60
                            late_mins = late_minutes % 60
                            if late_hours > 0:
                                time_late = f"{late_hours}h {late_mins}m"
                            else:
                                time_late = f"{late_mins}m"
                        else:
                            punctuality = 'ON TIME'
                            time_late = '0m'

                    if user_row is None:
                        # New entry - first check-in of the day
                        ws.append([name, date_str, time_str, '', '', punctuality, time_late, ''])
                        new_row = ws.max_row
                        if punctuality == 'LATE':
                            ws.cell(new_row, 6).font = Font(bold=True, color="FF0000")
                            ws.cell(new_row, 7).font = Font(bold=True, color="FF0000")
                        else:
                            ws.cell(new_row, 6).font = Font(bold=True, color="00B050")
                            ws.cell(new_row, 7).font = Font(bold=True, color="00B050")
                    else:
                        # Row exists but had no Time In yet (rare). Fill it once.
                        ws.cell(user_row, 3).value = time_str
                        if punctuality:
                            ws.cell(user_row, 6).value = punctuality
                            ws.cell(user_row, 7).value = time_late
                            if punctuality == 'LATE':
                                ws.cell(user_row, 6).font = Font(bold=True, color="FF0000")
                                ws.cell(user_row, 7).font = Font(bold=True, color="FF0000")
                            else:
                                ws.cell(user_row, 6).font = Font(bold=True, color="00B050")
                                ws.cell(user_row, 7).font = Font(bold=True, color="00B050")

                elif event == 'CHECK_OUT':
                    if not user_row:
                        print(f"[DEBUG] Refusing CHECK OUT - no row found for today")
                        wb.close()
                        return False

                    # If no check-in time, can't check out.
                    if not ws.cell(user_row, 3).value:
                        print(f"[DEBUG] Refusing CHECK OUT - no check-in time")
                        wb.close()
                        return False

                    # Always UPDATE checkout time to the LAST checkout
                    ws.cell(user_row, 4).value = time_str  # Time Out (last checkout)
                    print(f"[DEBUG] Updated CHECK OUT time to {time_str}")
                    
                    # Calculate and update total time (from FIRST check-in to LAST check-out)
                    time_in = ws.cell(user_row, 3).value
                    if time_in:
                        try:
                            in_dt = datetime.strptime(time_in, "%H:%M:%S")
                            out_dt = datetime.strptime(time_str, "%H:%M:%S")
                            duration = out_dt - in_dt
                            print(f"[DEBUG] Total time calculated: {time_in} to {time_str} = {duration}")
                            hours = duration.seconds // 3600
                            minutes = (duration.seconds % 3600) // 60
                            total_str = f"{hours}h {minutes}m"
                            ws.cell(user_row, 5).value = total_str  # Total
                            
                            # Calculate overtime (after 7PM = 19:00)
                            ot_cutoff = datetime.strptime("19:00:00", "%H:%M:%S").time()
                            if now.time() > ot_cutoff:
                                ot_start = datetime.strptime("19:00:00", "%H:%M:%S")
                                ot_start = ot_start.replace(year=now.year, month=now.month, day=now.day)
                                ot_duration = now - ot_start
                                ot_minutes = int(ot_duration.total_seconds() // 60)
                                ot_hours = ot_minutes // 60
                                ot_mins = ot_minutes % 60
                                if ot_hours > 0:
                                    ot_str = f"{ot_hours}h {ot_mins}m"
                                else:
                                    ot_str = f"{ot_mins}m"
                                ws.cell(user_row, 8).value = ot_str  # Time OT
                                ws.cell(user_row, 8).font = Font(bold=True, color="FFA500")  # Orange
                            else:
                                ws.cell(user_row, 8).value = '0m'
                        except:
                            pass
            
                wb.save(self.attendance_file)
                wb.close()
            
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
        Get status of all users with their last check-in/out from Excel
        
        Returns:
            Dictionary with user status information
        """
        today = datetime.now().strftime('%Y-%m-%d')
        user_status = {}
        
        try:
            if not EXCEL_AVAILABLE or not os.path.exists(self.attendance_file):
                return user_status
            
            with self._excel_lock:
                wb = load_workbook(self.attendance_file)
                ws = wb.active
            
                # Read all rows for today
                for row in ws.iter_rows(min_row=2, values_only=True):
                    # Handle rows with different number of columns
                    if len(row) < 6:
                        continue
                        
                    name = row[0]
                    day = row[1]
                    time_in = row[2]
                    time_out = row[3] if len(row) > 3 else None
                    total = row[4] if len(row) > 4 else None
                    status_text = row[5] if len(row) > 5 else None
                    time_late = row[6] if len(row) > 6 else '0m'
                    time_ot = row[7] if len(row) > 7 else '0m'
                    
                    if day == today and name:
                        # Check if currently in OT (after 7PM and still checked in)
                        is_ot = False
                        if time_in and not time_out:
                            current_time = datetime.now().time()
                            ot_cutoff = datetime.strptime("19:00:00", "%H:%M:%S").time()
                            if current_time > ot_cutoff:
                                is_ot = True
                        
                        if name not in user_status:
                            user_status[name] = {
                                'last_event': 'CHECK_OUT' if time_out else 'CHECK_IN',
                                'last_time': time_out if time_out else time_in,
                                'status': 'OUT' if time_out else 'IN',
                                'check_in_time': time_in,
                                'check_out_time': time_out,
                                'duration': total,
                                'first_check_in': time_in,
                                'is_overtime': is_ot,
                                'time_ot': time_ot if time_ot else '0m'
                            }
                        else:
                            # Update with latest data
                            user_status[name]['check_in_time'] = time_in
                            user_status[name]['check_out_time'] = time_out
                            user_status[name]['duration'] = total
                            user_status[name]['status'] = 'OUT' if time_out else 'IN'
                            user_status[name]['last_time'] = time_out if time_out else time_in
                            user_status[name]['last_event'] = 'CHECK_OUT' if time_out else 'CHECK_IN'
                            user_status[name]['is_overtime'] = is_ot
                            user_status[name]['time_ot'] = time_ot if time_ot else '0m'

                wb.close()
        
        except BadZipFile:
            print(f"[ERROR] Failed to get user status: attendance.xlsx is corrupted (not a zip file)")
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
    
    def create_monthly_report(self):
        """Create or update monthly report sheet"""
        try:
            if not EXCEL_AVAILABLE or not os.path.exists(self.attendance_file):
                return
            
            with self._excel_lock:
                wb = load_workbook(self.attendance_file)
            
            # Get or create Monthly Report sheet
            if 'Monthly Report' in wb.sheetnames:
                ws_monthly = wb['Monthly Report']
                ws_monthly.delete_rows(2, ws_monthly.max_row)  # Keep header, delete data
            else:
                ws_monthly = wb.create_sheet('Monthly Report', 1)
                # Create headers
                headers = ['Name', 'Days Late', 'OT Days', 'Total Time Late', 'Total Time OT']
                ws_monthly.append(headers)
                
                # Style headers
                for cell in ws_monthly[1]:
                    cell.font = Font(bold=True, size=12, color="FFFFFF")
                    cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                
                # Set column widths
                ws_monthly.column_dimensions['A'].width = 15
                ws_monthly.column_dimensions['B'].width = 12
                ws_monthly.column_dimensions['C'].width = 12
                ws_monthly.column_dimensions['D'].width = 15
                ws_monthly.column_dimensions['E'].width = 15
            
            # Get daily sheet
            ws_daily = wb.active
            
            # Calculate monthly statistics
            current_year_month = datetime.now().strftime('%Y-%m')
            user_stats = {}
            
            for row in ws_daily.iter_rows(min_row=2, values_only=True):
                if len(row) < 8:
                    continue
                
                name = row[0]
                day = row[1]
                status = row[5]  # Status column
                time_late = row[6]  # Time Late column
                time_ot = row[7]  # Time OT column
                
                if not name or not day:
                    continue
                
                # Check if date is in current month
                try:
                    day_str = day if isinstance(day, str) else day.strftime('%Y-%m-%d')
                    if not day_str.startswith(current_year_month):
                        continue
                except:
                    continue
                
                if name not in user_stats:
                    user_stats[name] = {
                        'days_late': 0,
                        'ot_days': 0,
                        'total_late_minutes': 0,
                        'total_ot_minutes': 0
                    }
                
                # Count late days
                if status == 'LATE':
                    user_stats[name]['days_late'] += 1
                    # Parse time late
                    if time_late and time_late != '0m':
                        user_stats[name]['total_late_minutes'] += self._parse_time_to_minutes(time_late)
                
                # Count OT days
                if time_ot and time_ot != '0m':
                    user_stats[name]['ot_days'] += 1
                    user_stats[name]['total_ot_minutes'] += self._parse_time_to_minutes(time_ot)
            
            # Write data to monthly report
            row_num = 2
            for name in sorted(user_stats.keys()):
                stats = user_stats[name]
                total_late = self._format_time_from_minutes(stats['total_late_minutes'])
                total_ot = self._format_time_from_minutes(stats['total_ot_minutes'])
                
                ws_monthly.append([
                    name,
                    stats['days_late'],
                    stats['ot_days'],
                    total_late,
                    total_ot
                ])
                
                # Style data rows
                for cell in ws_monthly[row_num]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                
                row_num += 1
            
                wb.save(self.attendance_file)
                wb.close()
            print(f"[INFO] Monthly report updated")
        
        except BadZipFile:
            print(f"[ERROR] Failed to create monthly report: attendance.xlsx is corrupted (not a zip file)")
        except Exception as e:
            print(f"[ERROR] Failed to create monthly report: {e}")
    
    def _parse_time_to_minutes(self, time_str: str) -> int:
        """Parse time string like '1h 30m' or '30m' to total minutes"""
        try:
            time_str = time_str.strip()
            total_minutes = 0
            
            if 'h' in time_str:
                parts = time_str.split('h')
                hours = int(parts[0].strip())
                total_minutes += hours * 60
                
                if 'm' in parts[1]:
                    minutes = int(parts[1].replace('m', '').strip())
                    total_minutes += minutes
            elif 'm' in time_str:
                minutes = int(time_str.replace('m', '').strip())
                total_minutes += minutes
            
            return total_minutes
        except:
            return 0
    
    def _format_time_from_minutes(self, minutes: int) -> str:
        """Format minutes to 'Xh Ym' format"""
        if minutes == 0:
            return '0m'
        
        hours = minutes // 60
        mins = minutes % 60
        
        if hours > 0:
            return f"{hours}h {mins}m"
        else:
            return f"{mins}m"
    
    def check_in_out(self, name: str) -> str:
        """
        Toggle check-in/check-out for a person
        
        Args:
            name: Person's name
            
        Returns:
            Status message: 'CHECKED IN', 'CHECKED OUT', or 'SUCCESS' (already in)
        """
        user_status = self.get_user_status()
        current_status = user_status.get(name, {}).get('status', 'NONE')
        
        print(f"[DEBUG] check_in_out called for {name}, current status: {current_status}")
        
        # Debug log to CSV
        debug_log = os.path.join(os.path.dirname(self.attendance_file), 'debug_log.csv')
        with open(debug_log, 'a') as f:
            from datetime import datetime
            now = datetime.now()
            f.write(f"{now.strftime('%H:%M:%S')},{name},{current_status},")

        # Original toggle behavior:
        # - If currently IN -> CHECK OUT
        # - Else -> CHECK IN
        if name in user_status and user_status[name].get('status') == 'IN':
            print(f"[DEBUG] {name} is IN, attempting CHECK OUT")
            wrote = self.record_event(name, 'CHECK_OUT')
            if not wrote:
                print(f"[DEBUG] CHECK OUT refused for {name}")
                with open(debug_log, 'a') as f:
                    f.write(f"CHECKOUT_REFUSED\n")
                return 'SUCCESS'
            self.log_status_to_file()
            self.create_monthly_report()
            print(f"[DEBUG] {name} CHECKED OUT successfully")
            with open(debug_log, 'a') as f:
                f.write(f"CHECKED_OUT\n")
            return 'CHECKED OUT'

        print(f"[DEBUG] {name} not IN, attempting CHECK IN")
        wrote = self.record_event(name, 'CHECK_IN')
        if not wrote:
            print(f"[DEBUG] CHECK IN refused for {name}")
            with open(debug_log, 'a') as f:
                f.write(f"CHECKIN_REFUSED\n")
            return 'SUCCESS'
        self.log_status_to_file()
        print(f"[DEBUG] {name} CHECKED IN successfully")
        with open(debug_log, 'a') as f:
            f.write(f"CHECKED_IN\n")
        return 'CHECKED IN'
    
    def manual_checkout(self, name: str) -> str:
        """
        Manually check out a user
        
        Args:
            name: Person's name
            
        Returns:
            Status message
        """
        user_status = self.get_user_status()
        
        if name in user_status and user_status[name]['status'] == 'IN':
            self.record_event(name, 'CHECK_OUT')
            self.log_status_to_file()
            self.create_monthly_report()
            return 'CHECKED OUT'
        else:
            return 'NOT CHECKED IN'


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

