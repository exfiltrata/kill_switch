#!/usr/bin/env python

# Some CFRunLoopRun() code appropriated from:
# https://github.com/sandeep-sidhu/dynamic_dns/blob/master/dynamic_dns.py

import argparse
import os
import subprocess
import re
from datetime import datetime
import logging

from Foundation import CFAbsoluteTimeGetCurrent, CFRunLoopAddSource, CFRunLoopAddTimer
from Foundation import CFRunLoopGetCurrent, CFRunLoopRun, CFRunLoopTimerCreate, kCFRunLoopCommonModes, NSDate
from objc import lookUpClass
from SystemConfiguration import SCDynamicStoreCopyValue, SCDynamicStoreCreate
from SystemConfiguration import SCDynamicStoreCreateRunLoopSource, SCDynamicStoreSetNotificationKeys


# initialize logging
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)s:\t%(message)s")
handler.setFormatter(formatter)
log.addHandler(handler)


class Monitor(object):

    def __init__(self, mon, kill_ifaces):

        mon_string = "State:/Network/Interface/" + mon + "/IPv4"

        self.store = SCDynamicStoreCreate(None, "kill_switch", self.dynamicStoreChanged, None)

        self.source = SCDynamicStoreCreateRunLoopSource(None, self.store, 0)

        SCDynamicStoreSetNotificationKeys(self.store, None, [mon_string])

        self.loop = CFRunLoopGetCurrent()
        CFRunLoopAddSource(self.loop, self.source, kCFRunLoopCommonModes)
        CFRunLoopRun()

    def dynamicStoreChanged(self, store, keys, kill_ifaces):
        # loop through the keys we're watching
        for key in keys:

            val = SCDynamicStoreCopyValue(store, key)

            # if val is none, then the VPN connection has dropped
            if val is None:
                kill_network(kill_ifaces)


def priv_check():
    # Checks for id of current user. If not root, generate an error message and exit.

    if os.geteuid() != 0:
        msg = "kill_switch started with insufficient permissions.\n" \
              "\tRun the script again with sudo. Exiting now...\n"

        # generate log entry
        log.error(msg)

        # throw a notification
        notify("kill_switch", "Error!", (msg), sound=True)

        exit(1)


def notify(title, subtitle, msg_text, sound=False):
    # Function to generate OS X notification.

    NSUserNotification = lookUpClass("NSUserNotification")
    NSUserNotificationCenter = lookUpClass("NSUserNotificationCenter")

    notification = NSUserNotification.alloc().init()
    notification.setTitle_(title)
    notification.setSubtitle_(subtitle)
    notification.setInformativeText_(msg_text)
    if sound:
        notification.setSoundName_("NSUserNotificationDefaultSoundName")
    notification.setDeliveryDate_(NSDate.dateWithTimeInterval_sinceDate_(0, NSDate.date()))
    NSUserNotificationCenter.defaultUserNotificationCenter().scheduleNotification_(notification)


def kill_network(kill_ifaces):
    # Function to kill networking

    # check if user specified interfaces to kill
    if kill_ifaces is not None:
        ifaces = kill_ifaces

    else:
        # Pull the routing table.
        result = subprocess.check_output("netstat -rn", shell=True)

        # Regex out all default interfaces.
        ifaces = re.findall("^default.*?(\w+)$", result, re.M)

    # loop through interfaces, disabling each one
    for iface in ifaces:
        p = subprocess.Popen(["sudo", "ifconfig", iface, "down"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

    # get the current time
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # create message
    msg = "VPN connection died at: %s\n" % now

    # throw a notification
    notify("kill_switch", "VPN ALERT", (msg), sound=True)

    # generate log entry
    log.info(msg)

    # exit the script
    exit()


def dummy_timer(*args):
    # This function is called every second when the main CFRunLoop runs.
    # We don't want to do anything, unless a keyboard interrupt was sent by the user, so this function just passes.
    pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="kill_switch.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Kills network interfaces when your VPN connection drops.\n"
                    "Tested on Python 2.7 and OS X 10.9.4 - 10.11.1.")

    parser.add_argument("-m", "--mon", type=str, help="VPN interface to monitor. If this option is not set, the "
                                                        "default interface, utun0, will be monitored.")

    parser.add_argument("-k", "--kill", type=str, help="Comma separated list of network interfaces to kill if VPN drops."
                                                       " If this option is not set, the interface with the default route"
                                                       " will be killed.")

    parser.add_argument("-l", "--log", type=str, help="Direct output to log file.")

    args = parser.parse_args()

    mon = "utun0"
    if args.mon:
        iface = args.mon

    kill_ifaces = None
    if args.kill:
        if "," in args.kill:
            kill_ifaces = args.kill.split(",")
        else:
            kill_ifaces = [args.kill]

    if args.log:
        handler = logging.FileHandler(args.log, "w")
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(levelname)s:\t%(message)s")
        handler.setFormatter(formatter)
        log.addHandler(handler)

    priv_check()

    # call back to python process to catch keyboard interrupt
    CFRunLoopAddTimer(CFRunLoopGetCurrent(),
        CFRunLoopTimerCreate(None, CFAbsoluteTimeGetCurrent(), 1.0, 0, 0,
            dummy_timer, None),
        kCFRunLoopCommonModes)
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = "kill_switch VPN monitor initiated at %s\n" % now
        log.info(msg)
        Monitor(mon, kill_ifaces)
    except KeyboardInterrupt:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.info("Keyboard Interrupt, exiting kill_switch at %s\n" % now)
        exit()
