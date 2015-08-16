Deluge Traffic Limits Plus
==========================

_TrafficLimitsPlus_ is a plugin for the [Deluge bittorrent client](http://deluge-torrent.org/). It is based on the _TrafficLimits_ plugin and adds some extra control features to resume traffic after a certain time.

TrafficLimits can be found at
[http://github.com/mavit/deluge-trafficlimits](http://github.com/mavit/deluge-trafficlimits).

TrafficLimitsPlus can be found at
[https://github.com/SimonDeRidder/deluge-trafficlimitsplus](https://github.com/SimonDeRidder/deluge-trafficlimitsplus).

Questions may be asked on the
[http://forum.deluge-torrent.org/viewtopic.php?f=9&t=34343](Deluge forum).

## Configuration:

As well as setting the limits through the preferences (GTK UI only, for now), you can also create a file called `~/.config/deluge/trafficlimits` containing a label, the upload limit, the download limit, and the combined limit (in bytes), each on a line by themselves.  For example:

    January
    -1
    21474836480
    -1

## See also:

Please see also the [_Toggle_ plugin](http://dev.deluge-torrent.org/wiki/Plugins/Toggle).  You will need this to resume transfers once they have been paused, unless you use the automatic scheduling..
