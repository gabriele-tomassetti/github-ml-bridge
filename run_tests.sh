#!/bin/sh

cd test
# start the fake mail server
twistd localmail --imap 2000 --smtp 3000 --http 4000 --file localmail.mbox

# run tests
nose2

# kill the fake mail server
ps -ef | grep "twistd localmail" | grep -v grep | awk '{print $2}' | xargs kill

# clean the fake mail server data
rm ./localmail.mbox

cd ..
