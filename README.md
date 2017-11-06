GitHub-Mailing List Bridge
-----

GitHub-Mailing List Bridge (GMLB) is a simple program to bridge GitHub and mailing list.

It does 3 things:

- when there is a pull-request on GitHub it sends it to the mailing list
- when there are comments about the pull-request on the mailing list it sends them back to github
- when there are answers to these comments on GitHub it sends them to the mailing list

Configuration
======

There are several values to be set in the `info.cfg` file.
- *token* is the access token for github (see [Personal access tokens](https://github.com/settings/tokens))
- *bot_email* and *bot_name* contain the info of the bot (needed to pick the right comments from the mailing list)
- *mailing_list* indicates the address of the mailing list where to send the messages
- *email*, *smtp* and *imap* contain the info needed to send and read emails through an email account

Use
======

GMLB is a typical Python program, so you can use it like any other Python software.

* Set a virtualenv

```
# virtualenv venv
# source venv/bin/activate
```

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
