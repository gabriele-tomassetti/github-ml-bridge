import sys
import json
from pprint import pprint
from github import Github
from pulldb import PullDB
import mailbox
import smtplib
import textwrap
import email
import email.header
import logging
import imaplib
from mailclient import MailClient
from models import *
import time

class GithubClient:    
    def __init__(self, database, token, owner, repo, mailer: MailClient):
        self.token = token
        self.owner = owner
        self.repo = repo
        #self.api_url = api_url
        #self.pull_requests = pull_requests
        self.database = database
        self.mailer = mailer

    def check_pull_requests(self, setup):  
        # create a Github instance:
        g = Github(self.token)        

        # then get the pull requests for each project        
        pull_requests = []                
        for pull_request in g.get_user(self.owner).get_repo(self.repo).get_pulls(sort="Updated"):            
            pull = self.database.find_pull_request(self.owner, self.repo, pull_request.number)
            if(pull == None):            
                pull = {}
                pull['Id'] = 0
                pull['Commits'] = 0
                pull['Comments'] = 0
                pull['ReviewComments'] = 0
            
            commits = []            
            
            # start logging
            # logging.basicConfig(filename='github_bot.log',level=logging.INFO)

            if(pull['Commits'] != pull_request.commits):
                logging.info("There are new commits")
                for comm in pull_request.get_commits():
                    logging.info("Found a commit")
                    if(self.database.exists_commit(pull['Id'], comm.sha) == False):
                        logging.info("-> the commit is new")
                        files = []
                        list_files = g.get_user(self.owner).get_repo(self.repo) .get_commit(comm.sha).files
                        for file in list_files:
                            files.append(File(file.filename, file.additions,    file.deletions, file.changes, file.patch))

                        commit = Commit(comm.author.name, comm.author.email,    comm.committer.name, comm.committer.email, comm.sha,   comm.commit.message, comm.stats.additions,    comm.stats.deletions, comm.stats.total, files)
                        commits.append(commit)                                                                  
            comments = []

            if (pull['Comments'] != pull_request.comments):
                logging.info("There are new comments")
                # this gets us the comments related to the whole pull request
                for comment in pull_request.get_issue_comments():
                    logging.info("Found an issue comment")
                    if(self.database.exists_comment(pull['Id'], comment.id) == False):
                        logging.info("-> the comment is new")
                        comments.append(Comment(comment.id, comment.user.name, comment.user.email, comment.created_at, comment.body)) 
            
            if(pull['ReviewComments'] != pull_request.review_comments):
                logging.info("There are new review comments")
                # this gets us the comments related to a single modification
                for comment in pull_request.get_review_comments():
                    logging.info("Found a review comment")
                    if(self.database.exists_comment(pull['Id'], comment.id) == False):
                        logging.info("-> the comment is new")
                        comments.append(Comment(comment.id, comment.user.name,comment.user.email, comment.created_at, comment.body,comment.diff_hunk, comment.path))
                                  
            sent = False
            
            if(pull['Id'] == 0):
                # it is a new pull request
                pull = PullRequest(pull_request.title, pull_request.html_url, pull_request.diff_url, pull_request.user.login, pull_request.number, pull_request.body, pull_request.base.label, pull_request.comments, pull_request.review_comments, pull_request.commits, pull_request.updated_at, pull_request.changed_files, pull_request.additions, pull_request.deletions, commits, comments)
                pull_requests.append(pull)

                pull.download_diff()

                if(setup == True):
                    sent = True
                else:
                    sent = self.mailer.send_email_pull_request(self.owner, self.repo, pull)
                
                if(sent == True):
                    # record that we have already sent this pull request, with additional information to detect future changes to the pull request
                    self.database.record_pull_request(self.owner, self.repo, pull_request.number, pull_request.comments, pull_request.review_comments, pull_request.commits)           
                    pull_id = self.database.get_pull_request_id(self.owner, self.repo, pull_request.number)                
            else:      
                # it is a pull request we have already seen
                if(len(commits) > 0):                    
                    # it is an updated pull request                 
                    pull.download_diff()

                    if(setup == True):
                        sent = True
                    else:
                        sent = self.mailer.send_email_pull_request(self.owner, self.repo, pull, True)
                
                    if(sent == True):
                        # record the updated pull request
                        self.database.update_pull_request(pull['Id'], self.owner,   self.repo, pull_request.number,pull_request.comments, pull_request.review_comments, pull_request.commits)
                        pull_id = pull['Id']
                elif (len(comments) > 0):
                    # we have found new comments
                    sent = True
            
            if(len(comments) > 0):
                logging.info("There are %d comments " % len(comments))
                for comment in comments:
                    if(self.database.exists_comment(pull['Id'], comment.id) == False):
                        # send comment if we have sent a pull request or there is already one in the database
                        if(sent == True):                        
                            logging.info("Sending a comment")                        
                            if(self.mailer.send_email_comment(self.owner, self.repo, pull_request, comment) ==  True):                                
                                # record the updated pull request
                                self.database.update_pull_request(pull['Id'], self.owner,   self.repo, pull_request.number,pull_request.comments, pull_request.review_comments, pull_request.commits)
                                # record the comment
                                self.database.record_comment(pull["Id"], comment.id, comment.created_at, comment.body)
            
            if(sent == True):
                for commit in commits:
                    if(self.database.exists_commit(pull_id, commit.sha) == False):
                        self.database.record_commit(pull_id, commit.sha)                                
    
    def send_comment_from_email(self, email_subject, email_from, email_date, email_message):        
        start = email_subject.find("[#")
        end = email_subject.find("]", start)
        pull_number = int(email_subject[start+2:end])
        
        start = email_subject.find("[-")
        end = email_subject.find("]", start)
        (owner, repo) = str(email_subject[start+2:end]).split("/")                

        # we send back comments only for the current project        
        if(self.owner == owner and self.repo == repo):
            # we have to check that the message was sent after the start of the project  
            project = self.database.get_project(self.owner, self.repo)
            time_message = time.strptime(email_date, "%a, %d %b %Y %X %z")
            start_project = time.strptime(project["StartingDate"], "%a, %d %b %Y %X %z")            

            # we have to check if there is already a comment with the same date and text           
            if (self.database.exists_email_comment(email_date, email_message) == False and time_message > start_project == True):                
                g = Github(self.token)
                comment = g.get_user(self.owner).get_repo(self.repo).get_issue(pull_number).create_comment("From #%s\n\n%s" % (email_from, email_message))            

                # record comment
                pull_id = self.database.get_pull_request_id(owner, repo, pull_number)
                # we record the date and text of the email message
                self.database.record_comment(pull_id, comment.id, email_date, email_message)

