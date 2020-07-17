# fritzbox-traffic

Fetches upload and download statistics from a fritzbox.

Right now for munin. The munin plugin gives the mean and max of the last minute's data.


Change the login info in helpers_fritz.py before running

This is a scraping solution - we're actually fetching the data fritzbox uses for the graph.


# notes
Yes, the auth is currently hardcoded in the library, and as a global. You only have one fritzbox, right?

The login is a challenge-response thing. Details depend slightly on version.

fritz_fetch() returns a dict like

```
{u'_node': u'sg0',
 u'downstream': 214868000,
 u'ds_bps_curr_max': 526334,
 u'ds_bps_max': 26858500,
 u'dynamic': False,
 u'mode': u'VDSL',
 u'name': u'sync_dsl',
 u'upstream': 32272000,
 u'us_bps_curr_max': 219772,
 u'us_bps_max': 4034000,
 u'ds_mc_bps_curr': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
 u'ds_bps_curr': [446023, 448728, 458205, 318816, 401131, 382887, 520784, 417167, 328721,  407530,
                  385023, 393786, 384885, 448877, 412175, 304371, 378578, 357142, 526334, 289975],
 u'us_background_bps_curr': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
 u'us_default_bps_curr': [81934, 119163, 83695, 156271, 182721, 167155, 187029, 168391, 122218, 68770, 
                          140439, 157814, 137203, 146380, 155806, 157812, 173545, 192133, 115922, 67846],
 u'us_important_bps_curr': [12063, 7328, 16234, 9262, 14278, 9043, 12665, 8434, 9512, 7560,
                            7154, 10995, 10071, 6756, 9295, 7718, 8086, 7136, 5741, 5395],
 u'us_realtime_bps_curr': [7660, 308, 76, 143, 84, 359, 112, 203, 39742, 33576, 
                           82, 417, 394, 294, 199, 445, 433, 20503, 52273, 10928]
}

```

The traffic stuff mostly a bunch of ds_ (downstream) and us_ (upstream) details, including some guest stuff, which seems to be in bytes per second (a bit of a unit mix, the link speed seems to be in bits per second).

Upstream is split into into background (few things), normal (most things), priotitized, and realtime

The lists are the most recent first.

They are apparently averages calculated every 5-sec averages (the fetch from the graphing page is every 5 sec, the reported values also stay constant over 5 seconds).
