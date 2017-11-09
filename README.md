GitHub-Mailing List Bridge
-----

GitHub-Mailing List Bridge (GMLB) is a simple program to bridge GitHub and mailing list.

It does 3 things:

- when there is a pull-request on GitHub it sends it to the mailing list
- when there are comments about the pull-request on the mailing list it sends them back to github
- when there are answers to these comments on GitHub it sends them to the mailing list

Configuration
======

You have to rename or copy the file `info.cfg.default` in `info.cfg`.

There are several values to be set in the `info.cfg` file.
- *token* is the access token for github (see [Personal access tokens](https://github.com/settings/tokens))
- *bot_email* and *bot_name* contain the info of the bot (needed to pick the right comments from the mailing list)
- *mailing_list* indicates the address of the mailing list where to send the messages
- *account_imap*, *account_smtp*, *smtp* and *imap* contain the info needed to send and read emails through an email account

Use
======

GMLB is a typical Python program, so you can use it like any other Python software.

* Install the dependencies
```
# pip install -r requirements.txt
```
* Use `main.py` to execute the needed commands.
```
# to add the specified project and initialize the database with the current pull requests.
# this means that currents pull requests and comments will not be sent to the mailing list
# subsequents comments will be sent to the mailing list
# python main.py setup OWNER REPO

# to normally execute the program 
# python main.py run

# to list all projects
# python main.py projects

# to delete the specified project
# python main.py delete ID
```

The bot executes the command and then it stops: it is not a daemon, it does not check continuosly for new pull requests. However, you can setup a cron job to make the software run periodically.
```
# in this example the software is installed in /usr/local/github_ml_bridge
# cronjob that runs every 30 minutes
*/30 * * * * cd /usr/local/github_ml_bridge && python main.py run
```

Notes
======

* The bot does need to have its own account/address to send email, but it can read from any account that receives messages from the mailing list. It needs an address to detect its owns emails among the ones sent to the mailing list.
* The bot use the GitHub REST API to read pull requests and read/send comments: it does not rely on a webhook.
* The bot can read review comments from github, but it sends all comments from the mailing list as issue comments.