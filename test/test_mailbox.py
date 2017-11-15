import sys
import json
from email.message import EmailMessage
import mailbox
import email
import email.header
import logging
import imaplib
from models import *
from mailclient import MailClient
from githubclient import GithubClient
import unittest
from unittest.mock import MagicMock
import mailbox
import main

class TestMailbox(unittest.TestCase):
    def setUp(self):        
        self.config = main.load_config("data/config.json")
        self.mailer = MailClient(self.config['bot_email'], self.config['bot_name'], self.config['mailing_list'], self.config['smtp']['host'], self.config['smtp']['port'], self.config['smtp']['safe'], self.config['imap']['host'], self.config['imap']['port'], self.config['imap']['safe'], self.config['account_imap']['user'], self.config['account_imap']['password'], self.config['account_smtp']['user'], self.config['account_smtp']['password']) 
        self.pull_request = PullRequest("A modest change", "", "", "pull_author", 1, "A pull request", "pull:master", 0, 0, 1, "2017-11-09T09:56:43Z", 1, 2, 3, [Commit("commit_author", "author@example", "committer_name", "committer@example", "", "Message of the commit", 2, 3, 5, [])], [])
        self.pull_request.diff_content = "#Here there is a real diff#"
        self.comment = Comment(1, "author_name", "guy@example", "2017-11-09T09:56:43Z", "This is a comment on a pull request", None, None)        
        self.github_client = GithubClient("", "", "", "", None)
        self.github_client.send_comment_from_email = MagicMock(return_value=True)        
        pass     

    def tearDown(self):
        pass

    def test_send_email_pull_request(self):
        # send email
        self.mailer.send_email_pull_request("owner", "repo", self.pull_request)

        # open message
        mbox = mailbox.mbox("localmail.mbox")        
        msg = mbox.get(len(mbox)-1)
        
        # assertions
        self.assertEqual('[GitHubBot][-owner/repo][#1] A modest change', msg['Subject'])
        self.assertEqual('bot@example', msg['From'])
        self.assertEqual('mailing_list@example', msg['To'])

    def test_send_email_comment(self):
        # send email
        self.mailer.send_email_comment("owner", "repo", self.pull_request, self.comment)

        # open message
        mbox = mailbox.mbox("localmail.mbox")        
        msg = mbox.get(len(mbox)-1)
        
        # assertions
        self.assertEqual('[GitHubBot][-owner/repo][#1] A modest change', msg['Subject'])
        self.assertEqual('bot@example', msg['From'])
        self.assertEqual('mailing_list@example', msg['To'])

    def send_test_email(self, msg):
        smtp = smtplib.SMTP(self.config['smtp']['host'], self.config['smtp']['port'])
        smtp.ehlo_or_helo_if_needed()
        smtp.send_message(msg)
        smtp.quit()

    def test_check_email_comment(self):                
        #mbox = mailbox.mbox("localmail.mbox")  
        
        # create messages
        # real reply
        msg = EmailMessage()
        msg['Subject'] = "[GitHubBot][-owner/repo][#1] A modest change"
        msg['From'] = "guy@example"
        msg['To'] = "mailing_list@example"
        msg['Date'] = "Thu, 09 Nov 2017 20:39:58 +0000"
        msg.set_content("This is a reply to a pull request.\n\n9 novembre 2017 09:28, thumbria@yahoo.it wrote:\n\n> There was a comment on the pull request.\n>\n> ------\n> \n> Author: Gabriele<None>\n> Date: 2017-11-09 07:43:42\n> \n> Test comment")    
        self.send_test_email(msg)

        # wrong from
        msg = EmailMessage()
        msg['Subject'] = "[GitHubBot][-owner/repo][#1] A modest change"
        msg['From'] = "bot@example"
        msg['To'] = "mailing_list@example"
        msg['Date'] = "Thu, 09 Nov 2017 20:49:58 +0000"
        msg.set_content("This is a reply to a pull request with the wrong from address")        
        self.send_test_email(msg)

        # wrong to
        msg = EmailMessage()
        msg['Subject'] = "[GitHubBot][-owner/repo][#1] A modest change"
        msg['From'] = "guy@example"
        msg['To'] = "random@example"
        msg['Date'] = "Thu, 09 Nov 2017 20:59:58 +0000"
        msg.set_content("This is a reply to a pull request with the wrong to address")
        self.send_test_email(msg)

        # wrong subject
        msg = EmailMessage()
        msg['Subject'] = "Ehi"
        msg['From'] = "bot@example"
        msg['To'] = "mailing_list@example"
        msg['Date'] = "Thu, 09 Nov 2017 20:29:58 +0000"
        msg.set_content("""This is a reply to a pull request with the wrong subject=0A=0A9 novembre 2017 09:28, thumb=
ria@yahoo.it wrote:=0A=0A> There was a comment on the pull request.=0A> =
=0A> ------=0A> =0A> Author: Gabriele<None>=0A> Date: 2017-11-09 07:43:42=
=0A> =0A> Test comment""")
        self.send_test_email(msg)

        # random message
        msg = EmailMessage()
        msg['Subject'] = "Ehi"
        msg['From'] = "guy@example"
        msg['To'] = "random@example"
        msg['Date'] = "Thu, 09 Nov 2017 20:19:58 +0000"
        msg.set_content("This is a random message")
        self.send_test_email(msg)

        # check comments
        self.mailer.check_ml_comments(self.github_client)
        self.github_client.send_comment_from_email.assert_called_with("[GitHubBot][-owner/repo][#1] A modest change", "guy@example", "Thu, 09 Nov 2017 20:39:58 +0000", "This is a reply to a pull request.\n")


        
