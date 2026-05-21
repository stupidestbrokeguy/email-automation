import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import os
from datetime import datetime
import time
import json
import sys

class EmailSender:
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        self.SMTP_SERVER = smtp_server
        self.SMTP_PORT = smtp_port
        self.SENDER_EMAIL = "vheremu007@gmail.com"
        self.SENDER_PASSWORD = "tmpqirdlhfyrqmqx"
        self.server = None
        self.max_retries = 3

    def connect(self):
        """Establish connection to SMTP server"""
        try:
            self.server = smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT, timeout=30)
            self.server.starttls()
            self.server.login(self.SENDER_EMAIL, self.SENDER_PASSWORD)
            print("✅ Successfully connected to SMTP server")
            return True
        except Exception as e:
            print(f"❌ Error connecting to SMTP server: {e}")
            return False

    def reconnect(self):
        """Reconnect to SMTP server"""
        if self.server:
            try:
                self.server.quit()
            except:
                pass
        time.sleep(5)
        return self.connect()

    def send_email(self, msg, recipients, retry_count=0):
        """Send email with retry logic"""
        try:
            if not self.server:
                if not self.connect():
                    return False

            self.server.sendmail(self.SENDER_EMAIL, recipients, msg.as_string())
            return True

        except (smtplib.SMTPServerDisconnected, ConnectionError, TimeoutError) as e:
            print(f"⚠️ Connection lost: {e}")
            if retry_count < self.max_retries:
                print(f"🔄 Attempting to reconnect (attempt {retry_count + 1}/{self.max_retries})...")
                if self.reconnect():
                    return self.send_email(msg, recipients, retry_count + 1)
            return False

        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

    def quit(self):
        """Safely close the connection"""
        if self.server:
            try:
                self.server.quit()
                print("✅ SMTP connection closed")
            except:
                pass

# ============ BATCH TRACKING FUNCTIONS ============
def get_current_batch(progress_file):
    """Read the last sent index from progress file"""
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            try:
                progress = json.load(f)
                return progress.get('last_index', 0)
            except:
                return int(f.read().strip())
    else:
        return 0

def save_progress(progress_file, last_index, batch_size, total_sent_today=0, completed_cycles=0):
    """Save the current progress with timestamp"""
    progress = {
        'last_index': last_index,
        'last_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_sent': last_index,
        'batch_size': batch_size,
        'last_batch_count': total_sent_today,
        'completed_cycles': completed_cycles
    }
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=4)

    # Also create a simple log file
    with open("email_sending_log.txt", "a") as log:
        log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Sent batch up to index {last_index} ({total_sent_today} emails) - Cycle {completed_cycles}\n")

def auto_reset_progress(progress_file, total_emails, batch_size):
    """Automatically reset progress when all emails are sent without asking"""
    current_index = get_current_batch(progress_file)

    if current_index >= total_emails and total_emails > 0:
        # Get current completed cycles
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r') as f:
                    progress = json.load(f)
                    completed_cycles = progress.get('completed_cycles', 0) + 1
            except:
                completed_cycles = 1
        else:
            completed_cycles = 1

        # Reset progress
        progress = {
            'last_index': 0,
            'last_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_sent': 0,
            'batch_size': batch_size,
            'last_batch_count': 0,
            'completed_cycles': completed_cycles,
            'last_reset': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=4)

        with open("email_sending_log.txt", "a") as log:
            log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 🔄 AUTO-RESET: Starting cycle #{completed_cycles + 1}\n")

        print(f"\n🔄 AUTO-RESET COMPLETED! Starting cycle #{completed_cycles + 1}")
        return True, completed_cycles

    return False, 0

def send_bulk_emails_automated(excel_file, cv_path, batch_size=90, cc_emails=None, delay=5):
    """
    Completely automated bulk email sender with no user input
    """
    progress_file = "send_progress.json"

    # Read Excel file
    try:
        df = pd.read_excel(excel_file)
        total_records = len(df)
        print(f"📊 Loaded {total_records} records from {excel_file}")
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return False

    # Required columns check
    if 'email' not in df.columns:
        print(f"❌ Error: 'email' column not found in Excel file")
        print(f"📋 Found columns: {list(df.columns)}")
        return False

    # Auto-reset if all emails have been sent
    was_reset, completed_cycles = auto_reset_progress(progress_file, total_records, batch_size)

    # Get current batch progress
    start_index = get_current_batch(progress_file)

    # Check if all emails have been sent (should be caught by auto-reset, but just in case)
    if start_index >= total_records:
        print("✅ All emails have been sent and cycle complete. Nothing to send today.")
        return True

    # Calculate end index for this batch
    end_index = min(start_index + batch_size, total_records)
    batch_df = df.iloc[start_index:end_index]

    # Display progress
    print(f"\n📧 TODAY'S BATCH: Sending emails {start_index + 1} to {end_index} (Total: {len(batch_df)} emails)")
    print(f"📦 Batch size: {batch_size} emails per day")
    print(f"🔄 Cycle #{completed_cycles + 1 if was_reset else completed_cycles + 1}")
    print(f"📊 Overall progress: {start_index}/{total_records} ({((start_index)/total_records*100):.1f}%)")

    # Check if CV file exists
    if not os.path.exists(cv_path):
        print(f"❌ Error: CV file not found at {cv_path}")
        return False

    # Initialize email sender
    email_sender = EmailSender()
    if not email_sender.connect():
        return False

    # Read CV file
    try:
        with open(cv_path, 'rb') as cv_file:
            cv_data = cv_file.read()
        cv_filename = os.path.basename(cv_path)
        print(f"📎 CV file loaded: {cv_filename}")
    except Exception as e:
        print(f"❌ Error reading CV file: {e}")
        email_sender.quit()
        return False

    # Send emails for today's batch
    successful = 0
    failed = 0
    failed_emails_list = []

    print(f"\n📧 Sending {len(batch_df)} emails...")
    print("-" * 50)

    for idx, (_, row) in enumerate(batch_df.iterrows()):
        try:
            recipient_email = str(row['email']).strip()
            recipient_name = str(row.get('name', 'Candidate')).strip() if 'name' in df.columns else "Candidate"

            # Skip invalid emails
            if '@' not in recipient_email or pd.isna(recipient_email):
                print(f"⏭️ [{idx+1}/{len(batch_df)}] Skipping invalid email: {recipient_email}")
                failed += 1
                failed_emails_list.append({'name': recipient_name, 'email': recipient_email, 'reason': 'Invalid email'})
                continue

            # Create email
            msg = MIMEMultipart()
            msg['From'] = email_sender.SENDER_EMAIL
            msg['To'] = recipient_email

            # Add CC recipients if provided
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)

            # Subject
            subject = f"IT Support | Sale Representative | Application - Maxwell Tinashe Vheremu"
            if 'name' in df.columns:
                subject = f"Application for IT Support | Sales Representative at {recipient_name} - Maxwell Tinashe Vheremu"
            msg['Subject'] = subject

            # HTML email body
            html_message = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #27ae60; margin-top: 0;">Application for IT Support | Sales Representative Role</h2>

                        <p>Dear Hiring Manager,</p>

                        <p>I am writing to apply for the IT Support | Sales Representative role, as my hands-on experience in Dubai Field IT Services Sales , IT infrastructure management, system troubleshooting, and user support across banking, security, and tech sectors aligns well with your needs.</p>

                        <p>With a strong background in Customer Relationship Management, Business Development, Windows Server, Active Directory, cloud platforms (AWS/Azure), and security tools, I am confident in delivering reliable and efficient IT operations and Business Development.</p>

                        <p>I would greatly appreciate the opportunity to discuss how I can contribute to your team.</p>

                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <strong>Maxwell Tinashe Vheremu</strong><br>
                            IT Support | Sales Representative<br>
                            <a href="mailto:vheremu007@gmail.com">vheremu007@gmail.com</a> | +971556204604
                        </div>
                    </div>
                </body>
            </html>
            """

            msg.attach(MIMEText(html_message, 'html'))

            # Attach CV
            cv_attachment = MIMEBase('application', 'octet-stream')
            cv_attachment.set_payload(cv_data)
            encoders.encode_base64(cv_attachment)
            cv_attachment.add_header('Content-Disposition', f'attachment; filename="{cv_filename}"')
            msg.attach(cv_attachment)

            # Prepare recipient list
            all_recipients = [recipient_email]
            if cc_emails:
                all_recipients.extend(cc_emails)

            # Send email
            if email_sender.send_email(msg, all_recipients):
                print(f"✅ [{idx+1}/{len(batch_df)}] Sent to {recipient_email}")
                successful += 1
            else:
                print(f"❌ [{idx+1}/{len(batch_df)}] Failed to send to {recipient_email}")
                failed += 1
                failed_emails_list.append({'name': recipient_name, 'email': recipient_email, 'reason': 'Sending failed'})

            # Delay between emails
            if delay > 0 and idx < len(batch_df) - 1:
                time.sleep(delay)

        except Exception as e:
            print(f"❌ [{idx+1}/{len(batch_df)}] Error: {e}")
            failed += 1
            failed_emails_list.append({'name': recipient_name, 'email': recipient_email, 'reason': str(e)})

    # Close connection
    email_sender.quit()

    # Save progress if all emails succeeded
    if successful == len(batch_df):
        # Get current cycle count
        current_cycles = 0
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r') as f:
                    progress = json.load(f)
                    current_cycles = progress.get('completed_cycles', 0)
            except:
                pass

        save_progress(progress_file, end_index, batch_size, successful, current_cycles)
        print(f"\n✅ PROGRESS SAVED! Next batch will start at index {end_index}")

        # Check if we completed a cycle
        if end_index >= total_records:
            print(f"\n🎉 CYCLE #{current_cycles + 1} COMPLETED! All {total_records} emails sent!")
    else:
        print(f"\n⚠️ ONLY {successful}/{len(batch_df)} emails sent successfully.")
        print(f"❌ Progress NOT saved. Will retry the same batch tomorrow.")

        # Save failed emails
        if failed_emails_list:
            retry_df = pd.DataFrame(failed_emails_list)
            retry_file = f"failed_batch_{datetime.now().strftime('%Y%m%d')}.xlsx"
            retry_df.to_excel(retry_file, index=False)
            print(f"📁 Failed emails saved to: {retry_file}")

    # Summary
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📧 Batch: {start_index + 1} - {end_index}")

    if end_index < total_records:
        remaining = total_records - end_index
        days_left = (remaining + batch_size - 1) // batch_size
        print(f"📈 Progress: {end_index}/{total_records} ({((end_index)/total_records*100):.1f}%)")
        print(f"📅 Estimated days left: {days_left}")

    return successful == len(batch_df)

def main():
    # Configuration - Change these as needed
    EXCEL_FILE = "emails1.xlsx"
    CV_PATH = "MAXWELLTINASHE.pdf"
    BATCH_SIZE = 1  # Change to 90 for production, use 2 for testing
    CC_EMAILS = []  # Add emails if needed: ["hr@company.com"]
    DELAY_BETWEEN_EMAILS = 5  # Seconds between emails

    print("="*60)
    print("🤖 AUTOMATED BATCH EMAIL SYSTEM")
    print("="*60)
    print(f"📂 Excel file: {EXCEL_FILE}")
    print(f"📎 CV: {CV_PATH}")
    print(f"📦 Batch size: {BATCH_SIZE} emails/day")
    print(f"⏰ Delay: {DELAY_BETWEEN_EMAILS} seconds")
    print(f"🔄 Auto-reset: ENABLED")
    print("="*60 + "\n")

    # Run automated sending
    success = send_bulk_emails_automated(
        excel_file=EXCEL_FILE,
        cv_path=CV_PATH,
        batch_size=BATCH_SIZE,
        cc_emails=CC_EMAILS,
        delay=DELAY_BETWEEN_EMAILS
    )

    # Exit with appropriate code for GitHub Actions
    if success:
        print("\n✅ Daily batch completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Batch completed with some errors, but will retry tomorrow.")
        sys.exit(0)  # Exit with 0 to not fail the action

if __name__ == "__main__":
    main()
# At the very end of email_automation.py, add this function if not present
def save_progress_locally(last_index, batch_size):
    """Save progress to JSON file"""
    import json
    from datetime import datetime

    progress = {
        'last_index': last_index,
        'last_date': datetime.now().isoformat(),
        'total_sent': last_index,
        'batch_size': batch_size
    }
    with open('send_progress.json', 'w') as f:
        json.dump(progress, f, indent=2)
    print(f"✅ Progress saved: {last_index} emails sent")
