# kill_switch.py

A simple VPN kill switch for OS X. If your VPN connection drops for any reason, network interfaces are disabled. The goal is to prevent your real IP address from leaking. This script was originally designed for external penetration tests to prevent scan traffic and testing activity from originating from your real IP in the event that your VPN connection dies.

# Installation

kill_switch runs on Python 2.7. To install the required libraries, first make sure pip is installed.

On Macports, run:
    
    sudo port install py27-pip

Next, install the required libraries via pip:

    pip install -r requirements.txt

# Bash Profile
    
This repo also includes wrapper functions to start and stop your VPN connection, using the built-in OS X VPN client, along with kill_switch. To do this, append the functions in bash_profile.txt to your ~/.bash_profile, and make the following modifications:

 - Add the name of your VPN connection to the 'vpn_name' variable
 - Line 7 of the 'vpn-connect' controls the execution of kill_switch.py. Either place kill_switch.py in your PATH or update this line reflect the full path to kill_switch.py. You can also add your preferred command line flags here.
 
   
Lastly, be sure to source your updated bash_profile in order to use the new functions in your existing terminal session.
For example:

    source ~/.bash_profile

# Usage

If you have added the default functions to your bash_profile, then simply type 'vpn-connect' into a terminal window. The terminal will prompt for your sudo password (this is necessary to kill networking when the VPN connection drops). Next, a pop-up window will open, asking for your VPN password. Finally, you can type 'vpn-disconnect' to disconnect from the VPN and stop kill_switch.py gracefully.

Alternatively, you can execute kill_switch.py directly. This can be done prior to connecting to the VPN, or immediately after. Examples are detailed in the next section.

Options are as follows:

    python kill_switch.py -h
    usage: kill_switch.py [-h] [-m MON] [-k KILL] [-l LOG]
    
    Kills network interfaces when your VPN connection drops.
    Tested on Python 2.7 and OS X 10.9.4 - 10.11.1.
    
    optional arguments:
      -h, --help            show this help message and exit
      -m MON, --mon MON     VPN interface to monitor. If this option is not set,
                            the default interface, utun0, will be monitored.
      -k KILL, --kill KILL  Comma separated list of network interfaces to kill if
                            VPN drops. If this option is not set, the interface
                            with the default route will be killed.
      -l LOG, --log LOG     Direct output to log file.


If and when kill_switch.py kills your network connection, bring your interfaces back up with ifconfig. For example:

    sudo ifconfig <interface name> up
    
# Examples
    
Use kill_switch to monitor the default VPN interface and kill any network interfaces with default routes if the VPN dies:

    sudo python kill_switch.py
    
Use kill_switch to monitor and kill specific interfaces:
  
    sudo python kill_switch.py -m utun1 -k en0,en2
    
Output to log:

    sudo python kill_switch.py -l ~/kill_switch.log
