import sys
import json
from pprint import pprint
from github import Github
from pulldb import PullDB
import logging
from mailclient import MailClient
from githubclient import GithubClient
from models import *

def multiply_symbol(additions, deletions):
    text = ""
    for count in range(0, additions):
        text += '+'
    for count in range(0, deletions):
        text += '-'

    return text

def multiply_space(length, name):
    text = name
    for count in range(0, length-len(name)):
        text += ' '
    
    return text

def load_config(config_file="info.cfg"):
    with open(config_file) as json_data:
        d = json.load(json_data)
        return d

def run(setup=False):
    logging.basicConfig(filename='github_bot.log',level=logging.INFO)

    config = load_config()
    
    try:
        if(not config['token']):
            raise Exception('Missing GitHub token')

        if(not config['bot_email'] or not config['bot_name']):
            raise Exception('Missing Bot configuration info')

        if(not config['mailing_list']):
            raise Exception('Missing Mailing List address')
        
        if(not config['smtp']['host'] or config['smtp']['port'] == 0 or not config['imap']['host'] or config['imap']['port'] == 0 or not config['email']['user'] or not config['email']['password']):
            raise Exception('Missing Email info needed to send email')
        
    except Exception as error:            
        print("Configuration Error: ", error)        
        sys.exit(1)

    database = PullDB("dati_pull.db")
    
    mailer = MailClient(config['bot_email'], config['bot_name'], config['mailing_list'], config['smtp']['host'], config['smtp']['port'], config['imap']['host'], config['imap']['port'], config['email']['user'], config['email']['password'])    
    
    projects = database.get_projects()
    for project in projects:  
        github = GithubClient(database, config['token'], project['Owner'], project['Repo'], mailer)
        pull_requests = github.check_pull_requests(setup)
    
        # no need to check for comments at setup
        #if(setup == False):
        #    mailer.check_ml_comments(github)

def warning():
    print("""Usage: python main.py COMMANDS
        

Commands:

    setup OWNER REPO
    
    To add the specified project and initialize the database with the current pull requests.
    This means that currents pull requests and comments will not be sent to the mailing list. However, subsequents comments will be sent to the mailing list

    projects

    To list all projects

    delete ID

    To delete the specified project

    run
        
    To normally execute the program         
        """)

def main(argv):     
    if (sys.argv[1] == "setup"):
        if(len(sys.argv) < 4):            
            warning()
        else:
            database = PullDB("dati_pull.db")        
            database.setup_project(str(argv[2]), str(argv[3]))             
            run(setup=True)
    elif (sys.argv[1] == "projects"):
        database = PullDB("dati_pull.db")
        projects = database.get_projects()
        print("There are %d projects.\n" % len(projects))            
        if(len(projects) > 0):
            print("Id\tOwner\tRepo")
            print("------------------------")
        for pro in projects:
            print("%d\t%s\t%s" % (int(pro["Id"]), pro["Owner"], pro["Repo"]))
    elif (sys.argv[1] == "delete"):
        database = PullDB("dati_pull.db")
        if(len(sys.argv) < 3):
            warning()

        if(database.delete_project(int(sys.argv[2])) == False):
            print("The project does not exist.")
        else:
            print("The project has been deleted.")

    elif (sys.argv[1] == "run"):
        run()               
    else:
        warning()

if __name__ == "__main__":
    main(sys.argv)
    