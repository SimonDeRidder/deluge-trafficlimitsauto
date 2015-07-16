#
# core.py
#
# Copyright (C) 2015 Simon De Ridder <simondr@belgacom.net>
#
# original TrafficLimits plugin by:
# Copyright (C) 2010 Peter Oliver <TrafficLimits@mavit.org.uk>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
import os
from twisted.internet.task import LoopingCall
import time

init_time = time.time()
update_interval = 5 #time in seconds between updates
DEFAULT_PREFS = {
    "upload_limit": -1,
    "download_limit": -1,
    "total_limit": -1,
    "upload": 0,
    "download": 0,
    "total": 0,
    "reset_time": init_time
    "time_limit": 86400 # 1 day
}

class Core(CorePluginBase):
    def enable(self):
        log.debug("TrafficLimitsPlus: Enabling...")
        self.config = deluge.configmanager.ConfigManager("trafficlimitsplus.conf",
                                                         DEFAULT_PREFS)
        self.paused = False
        self.upload = self.config["upload"]
        self.download = self.config["download"]
        self.total = self.config["total"]
        self.elapsed = time.time() - self.config["reset_time"]
        self.update_index = update_interval
        self.ignore_upload = 0
        self.ignore_download = 0

##        self.update_timer = LoopingCall(self.update_traffic)
##        self.update_timer.start(5)
        log.debug("TrafficLimitsPlus: Enabled.")


    def disable(self):
        log.debug("TrafficLimitsPlus: Disabling...")
        self.update_timer.stop()

        self.config["upload"] = self.upload
        self.config["download"] = self.upload
        self.config["total"] = self.total
        self.config.save()
        if self.paused:
            component.get("Core").session.resume()
        log.debug("TrafficLimitsPlus: Disabled.")

    def update(self):
        if self.update_index==update_interval:
            log.debug("TrafficLimitsPlus: Updating...")
            if not self.paused:
                update_traffic()
            update_time()
            self.update_index=0
           log.debug("TrafficLimitsPlus: Updated.")
        self.update_index+=1
            

    def update_traffic(self):
        status = component.get("Core").get_session_status(["total_upload","total_download"])
        self.upload = status["total_upload"] - self.ignore_upload
        self.download = status["total_download"] - self.ignore_download
        self.total = self.upload + self.download
        
        uploadreached = self.config["upload_limit"] >= 0 and self.upload > self.config["upload_limit"]
        downloadreached=self.config["download_limit"]>=0 and self.download>self.config["download_limit"]
        totalreached  = self.config["total_limit"]  >= 0 and self.total  > self.config["total_limit"]
        
        if uploadreached:
            log.info("TrafficLimitsPlus: Session paused: upload limit reached.")
        elif downloadreached:
            log.info("TrafficLimitsPlus: Session paused: download limit reached.")
        elif totalreached:
            log.info("TrafficLimitsPlus: Session paused: throughput limit reached.")

        if uploadreached or downloadreached or totalreached:
            self.paused = True
            component.get("Core").session.pause()

        component.get("EventManager").emit(
            TrafficLimitPlusUpdate(
                self.upload, self.download, self.total,
                self.config["upload_limit"]
                self.config["download_limit"]
                self.config["total_limit"],
                self.config["reset_time"]
            )
        )

    def update_time(self):
        self.elapsed = time.time() - self.config["reset_time"]
        if self.elapsed > self.config["time_limit"]:
            reset()
            component.get("Core").session.resume()
            self.paused = False
            

    @export
    def reset(self):
        self.config["upload"] = 0
        self.config["download"] = 0
        self.config["total"] = 0
        self.upload = 0
        self.download = 0
        self.total = 0
        status = component.get("Core").get_session_status(["total_upload","total_download"])
        self.ignore_upload = status["total_upload"]
        self.ignore_download = status["total_download"]
        self.config["reset_time"] = time.time()


    @export
    def set_config(self, config):
        """Sets the config dictionary"""
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()


    @export
    def get_config(self):
        """Returns the config dictionary"""
        return self.config.config


    @export
    def get_state(self):
        state = [
            self.upload, self.download, self.total,
            self.config["upload_limit"],
            self.config["download_limit"],
            self.config["total_limit"],
            self.config["reset_time"],
            self.config["time_limit"]
        ]
        return state


    

class TrafficLimitPlusUpdate (DelugeEvent):
    """
    Emitted when the ammount of transferred data changes.
    """
    def __init__(self, upload, download, total, upload_limit,
                 download_limit, total_limit, reset_time, time_limit):
        """
        :param upload: int, bytes uploaded during the current period
        :param download: int, bytes downloaded during the current period
        :param total: int, bytes up/downloaded during the current period
        :param upload_limit: int, upper bound for bytes transmitted
        :param download_limit: int, upper bound for bytes received
        :param total_limit: int, upper bound for bytes transferred
        :param reset_time: float, secs since epoch that limits were reset
        :param time_limit: float, secs after which counters reset
        """
        self._args = [upload, download, total, upload_limit, download_limit,
                      total_limit, reset_time, time_limit]
