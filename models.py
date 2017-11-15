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
import requests

class PullRequest:
    def __init__(self, title, url, diff_url, author, number, text, label, number_comments, number_review_comments, number_commits, updated_at, changed_files, additions, deletions, commits, comments):
        self.title = title
        self.url = url
        self.diff_url = diff_url
        self.number = number
        self.text = text
        self.label = label
        self.author = author
        self.number_comments = number_comments
        self.number_comments = number_review_comments
        self.number_commits = number_commits
        self.updated_at = updated_at
        self.changed_files = changed_files
        self.additions = additions
        self.deletions = deletions
        self.commits = commits
        self.comments = comments

    def download_diff(self):
        r = requests.get(self.diff_url)
        self.diff_content = r.text

class Comment:
    def __init__(self, id, author_name, author_email, created_at, text, referring_to = None, path = None):
        self.id = id
        self.author = str(author_name) + '<' + str(author_email) + '>'  
        self.created_at = created_at
        self.text = text
        self.referring_to = referring_to
        #self.in_reply_to_id = in_reply_to_id
        self.path = path

class Commit:
    def __init__(self, author_name, author_email, committer_name, committer_email, sha, message, additions, deletions, total, files):
        self.author = str(author_name) + '<' + str(author_email) + '>'  
        self.committer = str(committer_name) + '<' + str(committer_email) + '>'
        self.sha = sha
        self.message = message
        self.additions = additions
        self.deletions = deletions
        self.total = total
        self.files = files

class File:
    def __init__(self, filename, additions, deletions, changes, patch):
        self.name = filename
        self.additions = additions
        self.deletions = deletions
        self.changes = changes
        self.patch = patch