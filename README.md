# fritzbox-traffic

Fetches upload and download statistics from a fritzbox, right now for munin.

We're actually fetching the data fritzbox uses for the graph.
This munin plugin uses the maximum over a minute. 
Which may overrreport - TODO: look at that.


Change the login info in helpers_fritz.py before running


# notes


The login is a challenge-response thing. Details depend slightly on version.


You then get data like that mentioned at https://github.com/kbr/fritzconnection/issues/3

The traffic stuff mostly a bunch of ds_ (downstream) and us_ (upstream) details, including some guest stuff, which seems to be in bytes per second (a bit of a unit mix, the link speed seems to be in bits per second).

Upstram is split into into background (few things), normal (most things), priotitized, and realtime

The lists are the most recent first.

They are apparently averages calculated every 5-sec averages (the fetch from the graphing page is every 5 sec, the reported values also stay constant over 5 seconds).
