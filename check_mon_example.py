import smtplib 
from os import popen
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time

SERVICE_NAME = 'mon'
EMAIL = 'mon.service.tk@gmail.com'
PASSWORD = 'A55d53j2y4ol32e'
HOST = 'smtp.gmail.com'
PORT = 587 #gmail port 
WARNING = '!WARNING!'
TEXT_MESSAGE = 'Current time: ' + str(time.time()) + '\n'

if __name__ == '__main__':
    command = 'systemctl is-active ' + SERVICE_NAME
    output = popen(command)
    process = output.read()
    output.close()
    
    if str(process) != 'active\n':
        TEXT_MESSAGE += 'I`m not active. Please, turn me on!'

	server = smtplib.SMTP(host=HOST, port=PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)

        message = MIMEMultipart()

        message['From'] = EMAIL
        message['To'] = EMAIL
        message['Subject'] = WARNING

        message.attach(MIMEText(TEXT_MESSAGE))

        server.send_message(message)	
        del message

        server.quit()
