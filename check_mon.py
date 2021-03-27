import smtplib 
from os import popen
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
from os import getcwd
from configparser import ConfigParser

HOST = 'smtp.gmail.com'
PORT = 587 #gmail port 
WARNING = '!WARNING!'
TEXT_MESSAGE = 'Current time: ' + str(time.time()) + '\n'


def read_config(filename, section='mail'):
    # create parser and read ini configuration file
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to mysql
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception('{0} not found in the {1} file'.format(section, filename))

    return db


if __name__ == '__main__':
    path_to_config = getcwd() + '/config.ini'
    data_config = read_config(path_to_config)

    command = 'systemctl is-active ' + data_config['service_config']
    output = popen(command)
    process = output.read()
    output.close()
    
    if str(process) != 'active\n':
        TEXT_MESSAGE += 'I`m not active. Please, turn me on!'

        server = smtplib.SMTP(host=HOST, port=PORT)
        server.starttls()
        server.login(data_config['email'], data_config['password'])

        message = MIMEMultipart()

        message['From'] = data_config['email']
        message['To'] = data_config['email']
        message['Subject'] = WARNING

        message.attach(MIMEText(TEXT_MESSAGE))

        server.send_message(message)	
        del message

        server.quit()
