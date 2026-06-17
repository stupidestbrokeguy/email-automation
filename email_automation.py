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
        self.SENDER_EMAIL = "dncezim@gmail.com"
        # Use environment variable or fallback (better to use secrets in production)
        self.SENDER_PASSWORD = os.environ.get('EMAIL_PASSWORD', "zwsmljneeupfupgv")
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

def send_bulk_emails_automated(excel_file, cv_path, batch_size=90, cc_emails=None, delay=5, qr_image_path="qr_code.png"):
    """
    Completely automated bulk email sender with no user input.
    Optionally embeds a QR code image (PNG) into the email body.
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

    if start_index >= total_records:
        print("✅ All emails have been sent and cycle complete. Nothing to send today.")
        return True

    end_index = min(start_index + batch_size, total_records)
    batch_df = df.iloc[start_index:end_index]

    print(f"\n📧 TODAY'S BATCH: Sending emails {start_index + 1} to {end_index} (Total: {len(batch_df)} emails)")
    print(f"📦 Batch size: {batch_size} emails per day")
    print(f"🔄 Cycle #{completed_cycles + 1 if was_reset else completed_cycles + 1}")
    print(f"📊 Overall progress: {start_index}/{total_records} ({((start_index)/total_records*100):.1f}%)")

    # Check if CV file exists
    if not os.path.exists(cv_path):
        print(f"❌ Error: CV file not found at {cv_path}")
        return False

    # Check if QR image exists (optional)
    qr_data = None
    if os.path.exists(qr_image_path):
        try:
            with open(qr_image_path, 'rb') as f:
                qr_data = f.read()
            print(f"🖼️ QR image loaded: {os.path.basename(qr_image_path)}")
        except Exception as e:
            print(f"⚠️ Could not read QR image: {e}")
    else:
        print(f"ℹ️ QR image not found at {qr_image_path} – will not embed image.")

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

    successful = 0
    failed = 0
    failed_emails_list = []

    print(f"\n📧 Sending {len(batch_df)} emails...")
    print("-" * 50)

    for idx, (_, row) in enumerate(batch_df.iterrows()):
        try:
            recipient_email = str(row['email']).strip()
            recipient_name = str(row.get('name', 'Candidate')).strip() if 'name' in df.columns else "Candidate"

            if '@' not in recipient_email or pd.isna(recipient_email):
                print(f"⏭️ [{idx+1}/{len(batch_df)}] Skipping invalid email: {recipient_email}")
                failed += 1
                failed_emails_list.append({'name': recipient_name, 'email': recipient_email, 'reason': 'Invalid email'})
                continue

            # Create email container
            msg = MIMEMultipart()
            msg['From'] = email_sender.SENDER_EMAIL
            msg['To'] = recipient_email

            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)

            # Subject
            subject = f"10 Things Companies In Dubai Miss That Cost Them $100M A Year | Case Study On 100+ Companies | IT Support | Sale Representative | Application - Maxwell Tinashe Vheremu"
            if 'name' in df.columns:
                subject = f"10 Things Companies In Dubai Miss That Cost Them $100M A Year | Case Study On 100+ Companies l worked with |Application for IT Support | Sales Representative at {recipient_name} - Maxwell Tinashe Vheremu"
            msg['Subject'] = subject

            # HTML body – note the <img> tag with cid:qr_image
                      html_message = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #27ae60; margin-top: 0;">Application for IT Support | Sales Representative Role</h2>

                        <p>Dear Hiring Manager,</p>

                        <p>I have worked with 100+ companies in Dubai as IT Support Executive with Sales Experience as my hands-on experience in Dubai Field IT Services Sales. Here Are Ten Things That are costing them $100M+ a year in lost business revenue. I hope you go through the list and identify where the average company is losing business.</p>

                        <p><strong>Number 1: Community</strong></p>
                        <p>Most of the companies I have worked with have not managed to gather a well-engaged community of people around their business. Why is this important? By having a well-engaged community companies can reduce the cost of customer acquisition significantly through word of mouth, attention, reselling and upselling. Transferring clients to your community gives comfort knowing that you have people who trust you, be it WhatsApp, Telegram, Facebook or Instagram. Most companies regard social media followers as community which is wrong; a community is people you can contact at any given time, which disqualifies followers who are fed content that interests them. But transferring followers to your channels is a good start.</p>

                        <p><strong>Number 2: Ads</strong></p>
                        <p>Most average companies in Dubai use ads to boost sales and increase brand visibility. However, companies in Dubai have not utilized standard landing pages that let leads view a picture of product, a call to action, a video of the product, and a long copy letting user know more about the product. Landing pages can 10x the returns from Ad spending when done correctly by allowing leads to make a decision with good resources. Some leads might not want to buy but opt in on joining your community and you can put that after they finish the long copy and last call to action.</p>

                        <p><strong>Number 3: Data</strong></p>
                        <p>The average company in Dubai handles a large number of operations; however, they do not generate much data. By shifting from fire fighting to analyzing, companies can 10x their business revenue by acting informatively. When managing a community for example it is important to look at the numbers – a community dies when there is no growth and engagement; with data you can know best ways to improve engagement and growth. You can also assess the revenue you are managing to generate from your community through isolated targeted campaigns. Historical data backs the thesis that ads to your community convert 60%+ on average. I have tested it with results exceeding 80%. This helps out when launching new products – you will know that you are not starting from 0.</p>

                        <p><strong>Conclusion</strong></p>
                        <p>I would love to list all 10 Things Companies in Dubai Are Missing Out On, but this email is a Job Application so I will cut right to the chase. Please inspect my CV, call me, I am open for new exciting roles to further my career at your company. I would love to hear from you.</p>

                        <!-- ============ UPDATED SOFT-SALE SECTION (BRIEF) ============ -->
                        <p>Sample project with 1000+ Dubai Leads waiting list ready to make discovery calls. Fully Automated No Button Click. 100+ leads a day</p>

                        <p>To prove these skills aren't just on paper, I built a live e-commerce ecosystem in Dubai that sells t-shirts. Instead of just telling you I can do it, I invite you to experience it: scan the QR code or click the link below to see the landing page, checkout flow, and automated lead capture in action. Feel free to grab a t-shirt—it's the best way to stress-test my system and see exactly what I can build for your company.</p>
                        <!-- ========================================================= -->

                        <p>Please scan the QR Code below to go to my landing page and see a simple standard landing page, or open this link: <a href="http://www.stupidorange.com/product/stupi/landing/">www.stupidorange.com/product/stupi/landing/</a></p>
                        <div style="text-align: center; margin: 20px 0;">
                            <img src="cid:qr_image" alt="QR Code" style="max-width: 200px; height: auto; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" />
                        </div>

                        <p>I look forward to hearing from you.</p>

                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <strong>Maxwell Tinashe Vheremu</strong><br>
                            IT Support | Sales Representative<br>
                            <a href="mailto:vheremu007@gmail.com">vheremu007@gmail.com</a> | +971556204604
                        </div>
                    </div>
                </body>
            </html>
            """

            # Attach HTML part
            msg.attach(MIMEText(html_message, 'html'))

            # Attach CV
            cv_attachment = MIMEBase('application', 'octet-stream')
            cv_attachment.set_payload(cv_data)
            encoders.encode_base64(cv_attachment)
            cv_attachment.add_header('Content-Disposition', f'attachment; filename="{cv_filename}"')
            msg.attach(cv_attachment)

            # Attach QR image (if available) as inline image
            if qr_data:
                try:
                    qr_part = MIMEImage(qr_data, name=os.path.basename(qr_image_path))
                    qr_part.add_header('Content-ID', '<qr_image>')   # matches cid:qr_image
                    qr_part.add_header('Content-Disposition', 'inline', filename=os.path.basename(qr_image_path))
                    msg.attach(qr_part)
                except Exception as e:
                    print(f"⚠️ Could not attach QR image: {e}")

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

    email_sender.quit()

    # Save progress if all emails succeeded
    if successful == len(batch_df):
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

        if end_index >= total_records:
            print(f"\n🎉 CYCLE #{current_cycles + 1} COMPLETED! All {total_records} emails sent!")
    else:
        print(f"\n⚠️ ONLY {successful}/{len(batch_df)} emails sent successfully.")
        print(f"❌ Progress NOT saved. Will retry the same batch tomorrow.")

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
    # Configuration – adjust these as needed
    EXCEL_FILE = "emails.xlsx"
    CV_PATH = "MAXWELLTINASHE.pdf"
    BATCH_SIZE = 90          # change to 90 for production, use 2 for testing
    CC_EMAILS = []           # e.g. ["hr@company.com"]
    DELAY_BETWEEN_EMAILS = 5 # seconds between emails
    QR_IMAGE_PATH = "qr_code.png"   # path to your QR code PNG file

    print("="*60)
    print("🤖 AUTOMATED BATCH EMAIL SYSTEM")
    print("="*60)
    print(f"📂 Excel file: {EXCEL_FILE}")
    print(f"📎 CV: {CV_PATH}")
    print(f"🖼️ QR image: {QR_IMAGE_PATH}")
    print(f"📦 Batch size: {BATCH_SIZE} emails/day")
    print(f"⏰ Delay: {DELAY_BETWEEN_EMAILS} seconds")
    print(f"🔄 Auto-reset: ENABLED")
    print("="*60 + "\n")

    success = send_bulk_emails_automated(
        excel_file=EXCEL_FILE,
        cv_path=CV_PATH,
        batch_size=BATCH_SIZE,
        cc_emails=CC_EMAILS,
        delay=DELAY_BETWEEN_EMAILS,
        qr_image_path=QR_IMAGE_PATH
    )

    if success:
        print("\n✅ Daily batch completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Batch completed with some errors, but will retry tomorrow.")
        sys.exit(0)  # Exit with 0 to not fail the action

if __name__ == "__main__":
    main()
