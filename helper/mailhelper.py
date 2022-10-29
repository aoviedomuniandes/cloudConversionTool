# import necessary packages
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import codecs


# create message object instance
msg = MIMEMultipart()
 
file = codecs.open("template.html", "r", 'utf-8')
message = file.read()
 
# setup the parameters of the message
password = "your_password"
msg['From'] = "your_address"
msg['To'] = "to_address"
msg['Subject'] = "Subscription"
 
# add in the message body
msg.attach(MIMEText(message, 'plain'))
 
#create server
server = smtplib.SMTP('smtp.gmail.com: 587')
 
server.starttls()
 
# Login Credentials for sending the mail
server.login(msg['From'], password)
 
 
# send the message via the server.
server.sendmail(msg['From'], msg['To'], msg.as_string())
 
server.quit()
 