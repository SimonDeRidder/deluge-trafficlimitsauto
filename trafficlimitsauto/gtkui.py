#
# gtkui.py
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
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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

import gtk

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common
from common import get_resource
import time

class GtkUI(GtkPluginBase):
    def enable(self):
        self.builder = gtk.Builder();
        self.builder.add_from_file(get_resource("config.ui"))
        self.builder.connect_signals({
                "on_button_clear_clicked": self.on_button_clear_clicked,
                });
		self.builder.get_object("combobox_upload").new_text()
        self.builder.get_object("combobox_upload").insert_text(0,"B")
        self.builder.get_object("combobox_upload").insert_text(1,"kiB")
        self.builder.get_object("combobox_upload").insert_text(2,"MiB")
        self.builder.get_object("combobox_upload").insert_text(3,"GiB")
        self.builder.get_object("combobox_download").insert_text(0,"B")
        self.builder.get_object("combobox_download").insert_text(1,"kiB")
        self.builder.get_object("combobox_download").insert_text(2,"MiB")
        self.builder.get_object("combobox_download").insert_text(3,"GiB")
        self.builder.get_object("combobox_total").insert_text(0,"B")
        self.builder.get_object("combobox_total").insert_text(1,"kiB")
        self.builder.get_object("combobox_total").insert_text(2,"MiB")
        self.builder.get_object("combobox_total").insert_text(3,"GiB")
        self.builder.get_object("combobox_time").insert_text(0,"s")
        self.builder.get_object("combobox_time").insert_text(1,"min")
        self.builder.get_object("combobox_time").insert_text(2,"h")
        self.builder.get_object("combobox_time").insert_text(3,"d")
        self.builder.get_object("combobox_time").insert_text(4,"w")

        component.get("Preferences").add_page("TrafficLimitsAuto", self.builder.get_object("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)

        self.status_item = component.get("StatusBar").add_item(
            image=get_resource("monitor.png"),
            text="",
            callback=self.on_status_item_clicked,
            tooltip="TrafficLimitsAuto plugin"
        )

        def on_get_state(state):
            self.set_status(*state)

        self.state_deferred = client.trafficlimitsauto.get_state().addCallback(on_get_state)
        client.register_event_handler("TrafficLimitAutoUpdate", self.on_trafficlimitsauto_update)

    def disable(self):
        component.get("StatusBar").remove_item(self.status_item)
        del self.status_item
        component.get("Preferences").remove_page("TrafficLimitsAuto")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for TrafficLimitsAuto")
        upmult = self.unit_byte_mult(self.builder.get_object("combobox_upload").get_active_text())
        downmult = self.unit_byte_mult(self.builder.get_object("combobox_download").get_active_text())
        totmult = self.unit_byte_mult(self.builder.get_object("combobox_total").get_active_text())
        timemult = self.unit_time_mult(self.builder.get_object("combobox_time").get_active_text())
        config = {
            "upload_limit":
                int(self.builder.get_object("spinbutton_upload").get_value() * upmult),
            "download_limit":
                int(self.builder.get_object("spinbutton_download").get_value() * downmult),
            "total_limit":
                int(self.builder.get_object("spinbutton_total").get_value() * totmult),
            "time_limit":
                int(self.builder.get_object("spinbutton_time").get_value() * timemult)
        }
        client.trafficlimitsauto.set_config(config)

    def on_show_prefs(self):
        client.trafficlimitsauto.get_config().addCallback(self.cb_get_config)
        client.trafficlimitsauto.get_state().addCallback(self.cb_get_state)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        up, upunit = self.unit_byte_split(config["upload_limit"])
        self.builder.get_object("spinbutton_upload").set_value(up)
        self.builder.get_object("combobox_upload").set_active_id(upunit)
        down, downunit = self.unit_byte_split(config["download_limit"])
        self.builder.get_object("spinbutton_download").set_value(down)
        self.builder.get_object("combobox_download").set_active_id(downunit)
        total, totunit = self.unit_byte_split(config["total_limit"])
        self.builder.get_object("spinbutton_total").set_value(total)
        self.builder.get_object("combobox_total").set_active_id(totunit)
        time, timeunit = self.unit_time_split(config["time_limit"])
        self.builder.get_object("spinbutton_time").set_value(time)
        self.builder.get_object("combobox_time").set_active_id(timeunit)

    def cb_get_state(self, state):
        "callback for on show_prefs"
        self.builder.get_object("label_uploaded").set_text(
            str(state[0]) + " bytes since "
            + time.strftime("%c", time.localtime(state[6])))
        self.builder.get_object("label_downloaded").set_text(
            str(state[1]) + " bytes since "
            + time.strftime("%c", time.localtime(state[6])))
        self.builder.get_object("label_transferred").set_text(
            str(state[2]) + " bytes since "
            + time.strftime("%c", time.localtime(state[6])))

    def on_status_item_clicked(self, widget, event):
        component.get("Preferences").show("TrafficLimitsAuto")

    def on_button_clear_clicked(self, widget):
        client.trafficlimitsauto.reset()
        client.trafficlimitsauto.get_state().addCallback(self.cb_get_state)

    def set_status(self, upload, download, total, upload_limit,
                   download_limit, total_limit, reset_time, time_limit):
        status = ""
        pairs = [
             [download, download_limit],
             [upload, upload_limit],
             [total, total_limit],
         ]
        used = "/".join(
            ["%s" % deluge.common.fsize(p[0]) for p in pairs if p[1] >= 0]
        )
        status += used + " (" + "/".join(
            ["%d%%" % (100 * p[0] / p[1]) for p in pairs if p[1] >= 0]
        ) + ")"

        self.status_item.set_text(status)

        tooltip = "/".join(
            ["%s" % p[0] for p in [
                ["download", download_limit],
                ["upload", upload_limit],
                ["total", total_limit],
            ] if p[1] >= 0]
        ).capitalize()
        if tooltip == "":
            tooltip = "TrafficLimitsAuto plugin"
        else:
            tooltip += " since " + time.strftime("%c", time.localtime(reset_time))
        self.status_item.set_tooltip(tooltip)
        
    def on_trafficlimitsauto_update(self, upload, download, total, upload_limit,
                                    download_limit, total_limit, reset_time, time_limit):
        def on_state_deferred(s):
            self.set_status(upload, download, total, upload_limit, download_limit,
                            total_limit, reset_time, time_limit)
            self.cb_get_state([upload, download, total, upload_limit, download_limit,
                               total_limit, reset_time, time_limit])
        self.state_deferred.addCallback(on_state_deferred)

    def unit_byte_mult(self, unit):
        mult = 1
        if unit == "kiB":
            mult = mult *1024
        if unit == "MiB":
            mult = mult *1024*1024
        if unit == "GiB":
            mult = mult *1024*1024*1024
        return mult

    def unit_time_mult(self, unit):
        mult = 1
        if unit == "min":
            mult = mult *60
        elif unit == "h":
            mult = mult *60*60
        elif unit == "d":
            mult = mult *60*60*24
        elif unit == "w":
            mult = mult *60*60*24*7
        return mult

    def unit_byte_split(self, bytes):
        if bytes>=1024 and bytes%1024==0:
            bytes = bytes/1024 # now in kiB
            if bytes>=1024 and bytes%1024==0:
                bytes = bytes/1024 # now in MiB
                if bytes>=1024 and bytes%1024==0:
                    bytes = bytes/1024 # now in GiB
                    unit = 3#"GiB"
                else:
                    unit = 2#"MiB"
            else:
                unit = 1#"kiB"
        else:
            unit = 0#"B"
        return bytes, unit

    def unit_time_split(self, time):
        if time>=60 and time%60==0:
            time = time/60 # now in mins
            if time>=60 and time%60==0:
                time = time/60 # now in h
                if time>=24 and time%24==0:
                    time = time/24 # now in days
                    if time>=7 and time%7==0:
                        time = time/7 # now in days
                        unit = 4#"w"
                    else:
                        unit = 3#"d"
                else:
                    unit = 2#"h"
            else:
                unit = 1#"min"
        else:
            unit = 0#"s"
        return time, unit
        
