import sys
import json
from pprint import pprint
from github import Github
from pulldb import PullDB
from email.message import EmailMessage
import mailbox
import smtplib
import textwrap
import email
import email.header
import logging
import imaplib
from models import *

class MailClient:
    def __init__(self, bot_email, bot_name, mailing_list, smtp_host, smtp_port, smtp_safe, imap_host, imap_port, imap_safe, imap_user, imap_password, smtp_user, smtp_password):
        self.bot_name = bot_name
        self.bot_email = bot_email
        self.mailing_list = mailing_list
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_safe = smtp_safe
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.imap_safe = imap_safe
        self.imap_user = imap_user
        self.imap_password = imap_password
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
    
    def send_email_pull_request(self, owner, repo, pull_request, update = False) -> bool: 
        msg = EmailMessage()
        if(update == False):
            branch = pull_request.label.split(":")[1]
            text = textwrap.dedent("""            Branch: %s
            Author: %s
            Date:   %s
        
            There are %d commits in this pull request.                        
            %d files changed, %d insertions(+), %d deletions(-)
        
            ------

            """ % (branch, pull_request.author, pull_request.updated_at, pull_request.number_commits, pull_request.changed_files, pull_request.additions, pull_request.deletions))
        else:
            branch = pull_request.label.split(":")[1]
            text = textwrap.dedent("""            Branch: %s
            Author: %s
            Date:   %s
        
            There are %d new commits in this pull request.                        
            %d files changed, %d insertions(+), %d deletions(-)
        
            ------

            """ % (branch, pull_request.author, pull_request.updated_at, pull_request.number_commits, pull_request.changed_files, pull_request.additions, pull_request.deletions))

        for commit in pull_request.commits:                        
            header_data = []
            max_length = 0                        

            text += textwrap.dedent("""            Author:    %s
            Committer: %s
            SHA: %s        

            """ % (commit.author, commit.committer, commit.sha))
            
            text += commit.message

            text += textwrap.dedent("""                        

            %d files changed, %d insertions(+), %d deletions(-)
            
            ---
            
            """ % (len(commit.files), commit.additions, commit.deletions))

            text += pull_request.diff_content

        msg['Subject'] = '[%s][-%s/%s][#%d] %s' % (self.bot_name, owner, repo, pull_request.number, pull_request.title)
        msg['From'] = self.bot_email
        msg['To'] = self.mailing_list

        msg.set_content(text)

        try:
            smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)            
            smtp.ehlo_or_helo_if_needed()
            if(self.smtp_safe):
                smtp.starttls()
            smtp.login(self.smtp_user,self.smtp_password)
            smtp.send_message(msg)
            smtp.quit()
            return True
        except Exception as error:                      
            logging.error("ERROR sending message ", error)          
            return False   
    
    def send_email_comment(self, owner, repo, pull_request, comment: Comment) -> bool:          
        msg = EmailMessage()
                
        text = textwrap.dedent("""        There was a comment on the pull request.
        
        ------

        Author: %s
        Date:   %s                
        """ % (comment.author, comment.created_at))

        if(comment.path != None):
            text += textwrap.dedent("""        File: %s        
        
        """ % comment.path)                   
        else:
            text += "\n"

        text += comment.text

        msg['Subject'] = '[%s][-%s/%s][#%d] %s' % (self.bot_name, owner, repo, pull_request.number, pull_request.title)
        msg['From'] = self.bot_email
        msg['To'] = self.mailing_list

        msg.set_content(text)        

        try:
            smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
            smtp.ehlo_or_helo_if_needed()
            if(self.smtp_safe):
                smtp.starttls()            
            smtp.login(self.smtp_user,self.smtp_password)
            smtp.send_message(msg)
            smtp.quit()
            return True
        except Exception as error:            
            logging.error("ERROR sending message ", error)
            return False
    
    def check_ml_comments(self, github_client):        
        if(self.imap_safe):
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
        else:
            mail = imaplib.IMAP4(self.imap_host, self.imap_port)
        mail.login(self.imap_user, self.imap_password)
        mail.select(mailbox='INBOX', readonly=True)
        
        typ, msgs = mail.search(None, 'SUBJECT "[%s]"' % self.bot_name)
        
        if typ != 'OK':
            logging.info("No messages found!")
            return        

        for num in msgs[0].split():            
            typ, msgs = mail.fetch(num, '(RFC822)')
            if typ != 'OK':
                logging.error("ERROR getting message", num)
                return            

            msg = email.message_from_bytes(msgs[0][1])
            decode = email.header.decode_header(msg['Subject'])[0]
            subject = decode[0]

            # deal only with messages to the mailing list from everybody but this bot           
            if msg['From'] != self.bot_email and msg['To'] == self.mailing_list:                
                text = ''
                # we assume a non-multipart message, possibly encoded
                lines = msg.get_payload(None, True).splitlines(keepends=True)                   

                for line in lines:                    
                    # exclude previous messages included in the body of the email                    
                    if (line.startswith(b'>') == False):
                        text += line.decode(encoding='ascii')
                
                # remove ending newlines
                text = text.rstrip()   
                # remove last line, which contains information about the sender of the reply            
                # e.g., 9 november 2017, admin@example.com wrote:
                text = text[0:text.rfind('\n')]
                
                github_client.send_comment_from_email(msg['Subject'], msg['From'], msg['Date'], text)
        
        mail.close()
        mail.logout()
