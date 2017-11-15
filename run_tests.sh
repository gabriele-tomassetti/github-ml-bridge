#!/bin/sh

cd test
# start the fake server
twistd localmail --imap 2000 --smtp 3000 --http 4000 --file localmail.mbox

# run tests
nose2

# kill the fake server
ps -ef | grep "twistd localmail" | grep -v grep | awk '{print $2}' | xargs kill

cd ..
