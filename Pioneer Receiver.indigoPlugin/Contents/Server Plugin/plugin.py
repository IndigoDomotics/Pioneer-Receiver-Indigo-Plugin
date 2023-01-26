#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2012, Nathan Sheldon. All rights reserved.
http://www.nathansheldon.com/files/Pioneer-Receiver-Plugin.php  <--- this link may not remain active.

Version 2022.0.11
"""

################################################################################
# import os
# import sys
# import signal
import telnetlib
from constants import *

try:
    import indigo
except ImportError:
    ...


################################################################################
# noinspection PyPep8Naming
class Plugin(indigo.PluginBase):
    """
    Placeholder - fixme

    """
    ########################################
    # Class Globals
    ########################################

    # Dictionary of device telnet sessions.
    tn = {}
    # List of devices whose complete status is being updated.
    devicesBeingUpdated = []
    # Dictionary of device connection waiting counters (device ID:1/10 second count)
    devicesWaitingToConnect = {}

    ########################################
    def __init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs):
        indigo.PluginBase.__init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs)
        self.debug = plugin_prefs.get('showDebugInfo', False)
        self.device_list = []
        self.volume_device_list = []

    ########################################
    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    # Class-Supported Methods
    ########################################

    # Device Start
    ########################################
    def startup(self):
        """
        Placeholder - fixme

        :return:
        """
        # ...

    ########################################
    def deviceCreated(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        try:
            self.debugLog(f"deviceCreated called: {device}")
        except Exception as err:
            self.debugLog(f"deviceCreated called: {device.name} (Unable to display device states due to error: {err})")

        #
        # VSX-1021-K, VSX-1022-K, VSX-1122-K, VSX-1123-K, SC-75 Devices
        #
        if device.deviceTypeId in ["vsx1021k", "vsx1022k", "vsx1122k", "vsx1123k", "sc75"]:
            # Delete extra lines if valid - fixme
            # (
            # device.deviceTypeId == "vsx1021k"
            # or device.deviceTypeId == "vsx1022k"
            # or device.deviceTypeId == "vsx1122k"
            # or device.deviceTypeId == "vsx1123k"
            # or device.deviceTypeId == "sc75"
            # ):

            # If the device has the same IP address as another device, generate an error.
            self.debugLog("deviceCreated: Testing to see if using duplicate IP.")
            dev_props = device.pluginProps
            for device_id in self.device_list:
                self.debugLog(
                    f"deviceCreated: checking device {indigo.devices[device_id].name} (ID {device_id} address "
                    f"{indigo.devices[device_id].pluginProps['address']}."
                )
                if (
                        (device_id != device.id)
                        and (dev_props['address'] == indigo.devices[device_id].pluginProps['address'])
                ):
                    self.errorLog(
                        f"{device.name} is configured to connect on the same IP address as \""
                        f"{indigo.devices[device_id].name}\". Only one Indigo device can connect to the same Pioneer "
                        f"receiver at a time. Change the IP address of, or remove one of the devices.")
                    self.updateDeviceState(device, 'status', "error")
                    self.updateDeviceState(device, 'connected', False)
                    indigo.device.enable(device, False)

            # Start the device.
            if device.enabled:
                self.deviceStartComm(device)

        #
        # Virtual Volume Controller Device
        #
        if device.deviceTypeId == "virtualVolume":
            self.deviceStartComm(device)

    ########################################
    def deviceStartComm(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        try:
            self.debugLog(f"deviceStartComm called: {device}")
        except Exception as err:
            self.debugLog(
                f"deviceStartComm called: {device.name} (Unable to display device states due to error: {err})"
            )
        #
        # VSX-1021-K Device
        #
        if device.deviceTypeId == "vsx1021k":
            # Prior to version 0.9.7, the "onOffState" state did not exist. If that state does not exist, force an
            # update of the device.
            if not device.states.get('onOffState', False):
                self.debugLog("Updating device state list.")
                # This will force Indigo to update the device with the new states.
                device.stateListOrDisplayStateIdChanged()

            # Add this device to the list of devices associated with this plugin.
            if device.id not in self.device_list:
                self.debugLog(f"deviceStartComm: adding vsx1021k device_id {device.id} to deviceList.")
                self.device_list.append(device.id)

        #
        # VSX-1022-K Device
        #
        if device.deviceTypeId == "vsx1022k":
            # Add this device to the list of devices associated with this plugin.
            if device.id not in self.device_list:
                self.debugLog(f"deviceStartComm: adding vsx1022k device_id {device.id} to deviceList.")
                self.device_list.append(device.id)

        #
        # VSX-1122-K Device
        #
        if device.deviceTypeId == "vsx1122k":
            # Add this device to the list of devices associated with this plugin.
            if device.id not in self.device_list:
                self.debugLog(f"deviceStartComm: adding vsx1122k device_id {device.id} to deviceList.")
                self.device_list.append(device.id)

        #
        # VSX-1123-K Device
        #
        if device.deviceTypeId == "vsx1123k":
            # Add this device to the list of devices associated with this plugin.
            if device.id not in self.device_list:
                self.debugLog(f"deviceStartComm: adding vsx1123k device_id {device.id} to deviceList.")
                self.device_list.append(device.id)

        #
        # SC-75 Device
        #
        if device.deviceTypeId == "sc75":
            # Add this device to the list of devices associated with this plugin.
            if device.id not in self.device_list:
                self.debugLog(f"deviceStartComm: adding sc75 device_id {device.id} to deviceList.")
                self.device_list.append(device.id)

        #
        # Virtual Volume Controller Device
        #
        if device.deviceTypeId == "virtualVolume":
            # Add this device to the list of volume devices associated with this plugin.
            if device.id not in self.volume_device_list:
                self.debugLog(
                    f"deviceStartComm: adding virtualVolume device_id {device.id} to volumeDeviceList."
                )
                self.volume_device_list.append(device.id)
            # Update the device to the value of the receiver device control to which it is configured to virtualize.
            receiver_device_id = int(device.pluginProps.get('receiverDeviceId', ""))
            control_destination = device.pluginProps.get('controlDestination', "")
            if receiver_device_id > 0 and len(control_destination) > 0:
                # Query the receiver devices for volume and mute status. This will update the virtual volume controller.
                receiver = indigo.devices[receiver_device_id]
                if receiver.states['connected']:
                    self.getVolumeStatus(receiver)
                    self.getMuteStatus(receiver)

    ########################################
    def deviceStopComm(self, device):
        """
        Placeholder - fixme
        :param device:
        :return:
        """
        self.debugLog(f"deviceStopComm called: {device.name}")
        #
        # VSX-1021-K Device
        #
        if device.deviceTypeId == "vsx1021k":
            # Remove this device from the list of devices associated with this plugin.
            if device.id in self.device_list:
                self.device_list.remove(device.id)
            # Make sure it's disconnected.
            if device.states['connected']:
                self.disconnect(device)

        #
        # VSX-1022-K Device
        #
        if device.deviceTypeId == "vsx1022k":
            # Remove this device from the list of devices associated with this plugin.
            if device.id in self.device_list:
                self.device_list.remove(device.id)
            # Make sure it's disconnected.
            if device.states['connected']:
                self.disconnect(device)

        #
        # VSX-1122-K Device
        #
        if device.deviceTypeId == "vsx1122k":
            # Remove this device from the list of devices associated with this plugin.
            if device.id in self.device_list:
                self.device_list.remove(device.id)
            # Make sure it's disconnected.
            if device.states['connected']:
                self.disconnect(device)

        #
        # VSX-1123-K Device
        #
        if device.deviceTypeId == "vsx1123k":
            # Remove this device from the list of devices associated with this plugin.
            if device.id in self.device_list:
                self.device_list.remove(device.id)
            # Make sure it's disconnected.
            if device.states['connected']:
                self.disconnect(device)

        #
        # SC-75 Device
        #
        if device.deviceTypeId == "sc75":
            # Remove this device from the list of devices associated with this plugin.
            if device.id in self.device_list:
                self.device_list.remove(device.id)
            # Make sure it's disconnected.
            if device.states['connected']:
                self.disconnect(device)

        #
        # Virtual Volume Controller Device
        #
        if device.deviceTypeId == "virtualVolume":
            # Remove this device from the list of level devices associated with this plugin.
            if device.id in self.volume_device_list:
                self.volume_device_list.remove(device.id)

    ########################################
    def didDeviceCommPropertyChange(self, orig_dev, new_dev):
        """
        Placeholder - fixme

        :param orig_dev:
        :param new_dev:
        :return:
        """
        # Automatically called by plugin host when device properties change.
        self.debugLog("didDeviceCommPropertyChange called.")
        #
        # VSX-1021-K, VSX-1022-K, VSX-1122-K, VSX-1123-K, or SC-75
        #
        if (
                orig_dev.deviceTypeId == "vsx1021k"
                or new_dev.deviceTypeId == "vsx1022k"
                or new_dev.deviceTypeId == "vsx1122k"
                or new_dev.deviceTypeId == "vsx1123k"
                or new_dev.deviceTypeId == "sc75"
        ):
            if orig_dev.pluginProps['address'] != new_dev.pluginProps['address']:
                return True
            return False
        else:
            if orig_dev.pluginProps != new_dev.pluginProps:
                return True
            return False

    ########################################
    def runConcurrentThread(self):
        """
        Placeholder - fixme

        :return:
        """
        self.debugLog("runConcurrentThread called.")
        # loopCount = 0  TODO: the only reference now. No longer necessary?
        #
        # Continuously loop through all receiver devices. Obtain any data that they might be providing and process it.
        #
        try:
            while True:
                self.sleep(0.1)
                # Cycle through each receiver device.
                for device_id in self.device_list:
                    response = ""
                    response_line = ""
                    result = ""

                    connected = indigo.devices[device_id].states.get('connected', False)

                    # Only proceed if we're connected.
                    if connected:
                        # Remove the device ID from the devicesWaitingToConnect dictionary.
                        if self.devicesWaitingToConnect.get(device_id, -1) > -1:
                            del self.devicesWaitingToConnect[device_id]
                        # Call the readData method with the device instance
                        response = self.readData(indigo.devices[device_id])
                        # If a response was returned, process it.
                        if response != "":
                            # There is often more than one line.  Process all of them.
                            for response_line in response.splitlines():
                                result = self.processResponse(indigo.devices[device_id], response_line)
                                # If there was a result, send it to the log.
                                if result != "":
                                    indigo.server.log(result, indigo.devices[device_id].name)
                    else:
                        # Since we're not connected, try to connect.
                        self.connect(indigo.devices[device_id])

        except self.StopThread:
            self.debugLog("runConcurrentThread stopped.")
            # Cycle through each receiver device.
            for device_id in self.device_list:
                self.disconnect(indigo.devices[device_id])

        self.debugLog("runConcurrentThread exiting.")

    ########################################
    # Core Custom Methods
    ########################################

    # Update Device State
    ########################################
    def updateDeviceState(self, device, state, new_value):
        """
        Placeholder - fixme

        :param device:
        :param state:
        :param new_value:
        :return:
        """
        # Change the device state on the server if it's different from the current state.
        if new_value != device.states[state]:
            try:
                self.debugLog(f"updateDeviceState: Updating device {device.name} state: {state} = {new_value}")
            except Exception as err:
                self.debugLog(
                    f"updateDeviceState: Updating device {device.name} state: (Unable to display state due to "
                    f"error: {err})")
            # If this is a floating point number, specify the maximum number of digits to make visible in the state.
            # Everything in this plugin only needs 1 decimal place of precision. If this isn't a floating point value,
            # don't specify a number of decimal places to display.
            if new_value.__class__.__name__ == 'float':
                device.updateStateOnServer(key=state, value=new_value, decimalPlaces=1)
            else:
                device.updateStateOnServer(key=state, value=new_value)

    # Update Device Properties
    ########################################
    def updateDeviceProps(self, device, new_props):
        """
        Placeholder - fixme

        :param device:
        :param new_props:
        :return:
        """
        # Change the properties for this device that are stored on the server.
        if device.pluginProps != new_props:
            self.debugLog(f"updateDeviceProps: Updating device {device.name} properties.")
            device.replacePluginPropsOnServer(new_props)

    # Connect to a Receiver Device
    ########################################
    def connect(self, device):
        """
        Placeholder - fixme
        :param device:
        :return:
        """
        # Display this debug message only once every 50 times the method is called.
        if (self.devicesWaitingToConnect.get(device.id, 0) % 10 == 0
                or self.devicesWaitingToConnect.get(device.id, 0) == 0):
            self.debugLog("connect method called.")

        connected = device.states['connected']
        dev_props = device.pluginProps
        connecting = dev_props.get('tryingToConnect', False)
        # Get the device address.
        receiver_ip = dev_props['address']

        # Display these debug messages only once every 50 times the method is called.
        if self.devicesWaitingToConnect.get(device.id, 0) % 50 == 0:
            self.debugLog(f"connect: {device.name} connected? {connected}")
            self.debugLog(f"connect: {device.name} connecting? {connecting}")

        # Only try to connect if we're not already connected and aren't trying to connect.
        if not connected and not connecting:
            connecting = True
            # Update the device properties just in case the properties aren't up-to-date.
            dev_props['tryingToConnect'] = True
            self.updateDeviceProps(device, dev_props)

            # Try to connect to the receiver.
            self.debugLog(f"connect: Connecting to {device.name} at {receiver_ip}")
            try:
                self.updateDeviceState(device, 'status', "connecting")

                # Use the correct TCP port number based on device type.
                if device.deviceTypeId == "vsx1022k":
                    # The VSX-1022-K only accepts connections on port 8102.
                    self.tn[device.id] = telnetlib.Telnet(receiver_ip, 8102)
                else:
                    # All other receivers accept connections on the standard telnet port.
                    self.tn[device.id] = telnetlib.Telnet(receiver_ip)

                # Connection established if we get to this point.
                indigo.server.log("Connection established.", device.name)
                connected = True
                # Upon initial connection to a Pioneer receiver, it is necessary to "prime" the connection by simply
                # sending a CR and LF.
                # self.tn[device.id].write("\r\n")
                self.tn[device.id].write(str.encode("\r\n"))
                connecting = False
                # Update the device state on the server.
                self.updateDeviceState(device, 'status', "connected")
                self.updateDeviceState(device, 'connected', True)
                dev_props['tryingToConnect'] = False
                self.updateDeviceProps(device, dev_props)
                # Remove the device ID from the list of devices waiting to connect.
                waiting_count = self.devicesWaitingToConnect.get(device.id, -1)
                if waiting_count > -1:
                    del self.devicesWaitingToConnect[device.id]

                # Now that we're connected, gather receiver status information.
                self.getReceiverStatus(device)

            except Exception as err:
                # If this was a connection refused error, report it.
                if "(61," in str(err):
                    self.errorLog(
                        f"Connection refused when trying to connect to {device.name}. Will try again in "
                        f"{float((CONNECTION_RETRY_DELAY / 10))} seconds."
                    )
                    # Increment the number of times we attempted to connect but reached this point because we were
                    # already trying to connect.
                    waiting_count = self.devicesWaitingToConnect.get(device.id, -1)
                    if waiting_count > -1:
                        self.devicesWaitingToConnect[device.id] += 1
                    else:
                        self.devicesWaitingToConnect[device.id] = 1
                else:
                    self.errorLog(
                        f"Unable to establish a connection to {device.name}: {err}. Will try again in "
                        f"{float(CONNECTION_RETRY_DELAY / 10)} seconds."
                    )
                    # Increment the number of times we attempted to connect but reached this point because we were
                    # already trying to connect.
                    waiting_count = self.devicesWaitingToConnect.get(device.id, -1)
                    if waiting_count > -1:
                        self.devicesWaitingToConnect[device.id] += 1
                    else:
                        self.devicesWaitingToConnect[device.id] = 1
            except self.StopThread:
                self.debugLog("connect: Cancelling connection attempt.")
                return

        elif not connected and connecting:
            # Increment the number of times we attempted to connect but reached this point because we were already
            # trying to connect.
            waiting_count = self.devicesWaitingToConnect.get(device.id, -1)
            if waiting_count > -1:
                self.devicesWaitingToConnect[device.id] += 1
            else:
                self.devicesWaitingToConnect[device.id] = 1
            # If the number of times we've waited to connect is greater than connectionRetryDelay, then reset the
            # tryingToConnect property.
            if self.devicesWaitingToConnect.get(device.id, -1) > CONNECTION_RETRY_DELAY:
                connecting = False
                dev_props['tryingToConnect'] = False
                self.updateDeviceProps(device, dev_props)
                # Remove the device ID from the list of devices waiting to connect.
                waiting_count = self.devicesWaitingToConnect.get(device.id, -1)
                if waiting_count > -1:
                    del self.devicesWaitingToConnect[device.id]
                    self.debugLog(
                        "connect: Re-connect wait period over. Will try to connect next time the connect method is "
                        "called."
                    )
                else:
                    self.debugLog(
                        f"connect: Attempt to connect to {device.name} skipped because we're still trying to connect "
                        f"to it."
                    )

        elif connected:
            self.debugLog(
                f"connect: Attempt to connect to {device.name} skipped because we're already connected to it."
            )
            connected = True
            # Update the device to reflect this.
            self.updateDeviceState(device, 'connected', True)
            dev_props['tryingToConnect'] = False
            self.updateDeviceProps(device, dev_props)
            # Remove the device ID from the list of devices waiting to connect.
            waiting_count = self.devicesWaitingToConnect.get(device.id, -1)
            if waiting_count > -1:
                del self.devicesWaitingToConnect[device.id]

        # Display wait count in debug log.
        if self.devicesWaitingToConnect.get(device.id, 0) % 50 == 0:
            self.debugLog(f"connect: Connection wait count: {self.devicesWaitingToConnect.get(device.id, 0)}")

    # Disconnect from a Receiver Device
    #########################################
    def disconnect(self, device):
        """
        Placeholder - fixme
        :param device:
        :return:
        """
        self.debugLog("disconnect method called.")

        connected = device.states['connected']
        dev_props = device.pluginProps
        connecting = dev_props.get('tryingToConnect', False)

        # Disconnect the telnet session.
        try:
            self.tn[device.id].close()
            # Update the "status" device state.
            self.updateDeviceState(device, 'status', "disconnected")
            # Update the "connected" state on the server as well.
            self.updateDeviceState(device, 'connected', False)
            # Make sure the tryingToConnect device property is not on.
            dev_props['tryingToConnect'] = False
            self.updateDeviceProps(device, dev_props)
            self.debugLog(f"disconnect: {device.name} telnet connection is now closed.")
            # Remove the device ID from the list of devices waiting to connect (if it's in there).
            waiting_count = self.devicesWaitingToConnect.get(device.id, -1)
            if waiting_count > -1:
                del self.devicesWaitingToConnect[device.id]
        except EOFError:
            self.debugLog(f"disconnect: Connection to {device.name} is already closed.")
            self.updateDeviceState(device, 'status', "disconnected")
            self.updateDeviceState(device, 'connected', False)
            dev_props['tryingToConnect'] = False
            self.updateDeviceProps(device, dev_props)
            self.debugLog(f"disconnect: {device.name} connection is already closed.")
            # Remove the device ID from the list of devices waiting to connect (if it's in there).
            waiting_count = self.devicesWaitingToConnect.get(device.id, -1)
            if waiting_count > -1:
                del self.devicesWaitingToConnect[device.id]
        except Exception as err:
            self.errorLog(f"disconnect: Error disconnecting from {device.name}: {err}")
            self.updateDeviceState(device, 'status', "error")
            self.updateDeviceState(device, 'connected', False)
            dev_props['tryingToConnect'] = False
            self.updateDeviceProps(device, dev_props)
            self.debugLog(f"disconnect: {device.name} is now disconnected (error while disconnecting).")
            # Remove the device ID from the list of devices waiting to connect (if it's in there).
            waiting_count = self.devicesWaitingToConnect.get(device.id, -1)
            if waiting_count > -1:
                del self.devicesWaitingToConnect[device.id]

    #########################################
    # Send a Command
    #########################################
    def sendCommand(self, device, command):
        """
        Placeholder - fixme
        :param device:
        :param command:
        :return:
        """
        # Get the device type. Future versions of this plugin will support other receiver models.
        dev_type = device.deviceTypeId

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if dev_type == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command \"{command}\" to a Pioneer receiver instead of this  device."
            )
            return None

        # Get the device current connection status.
        connected = device.states['connected']
        # Get the device properties.
        dev_props = device.pluginProps
        connecting = dev_props.get('tryingToConnect', False)

        # Make sure the command is a string.
        command = str(command)
        # Make sure there's only one set of a carriage return and line feed.
        command = command.rstrip("\r\n")
        # SPECIAL CIRCUMSTANCE:
        #   The "TAC", "TFI" and "TFD" commands change the Tuner frequency. We need to clear the "tunerPreset" state
        #   if either of these commands are being sent.
        if command in ['TAC', 'TFI', 'TFD']:
            self.updateDeviceState(device, "tunerPreset", "")
        # Now send the command.
        self.debugLog(f"sendCommand: Telling {device.name}: {command}")

        command = f"{command}\r"

        # Only proceed if we're not trying to connect.
        if connected:
            try:
                # self.tn[device.id].write(command)
                self.tn[device.id].write(str.encode(command))
            except EOFError:
                # Connection is closed. Update status and try to re-open.
                self.errorLog(f"Connection to {device.name} lost while trying to send data. Will attempt to connect.")
                self.updateDeviceState(device, 'status', "disconnected")
                self.updateDeviceState(device, 'connected', False)
                self.connect(device)
            except Exception as err:
                # Unknown error.
                self.errorLog(f"Failed to send data to {device.name}: {err}")
                self.updateDeviceState(device, 'status', "error")
                self.updateDeviceState(device, 'connected', False)
        elif not connected and not connecting:
            # Show an error and try to connect.
            self.errorLog(f"Unable to send command to {device.name}. It is not connected. Attempting to re-connect.")
            self.connect(device)
        elif not connected and connecting:
            # Show an error indicating that we're still trying to connect.
            self.errorLog(f"Unable to send command to {device.name}. Still trying to connect to it.")

    #########################################
    # Read Data from a Receiver Connection
    #########################################
    def readData(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        response = ""

        # Get the device connection state and properties.
        connected = device.states['connected']
        dev_props = device.pluginProps
        connecting = dev_props.get('tryingToConnect', False)

        # Only proceed if we're connected.
        if connected:
            try:
                # Read the data and return it without blocking.
                response = self.tn[device.id].read_very_eager().decode()
                # Strip the CR and LF from the end of the response.
                response = response.rstrip("\r\n")
                # Force the response to be an ASCII string.
                response = str(response)
                if response != "":
                    self.debugLog(f"readData: {device.name} said: {response}")
            except EOFError:
                # Connection is closed, try to re-open.
                self.errorLog(
                    f"Connection to {device.name} lost while trying to receive data. Trying to re-connect.")
                self.updateDeviceState(device, 'status', "disconnected")
                self.updateDeviceState(device, 'connected', False)
                self.connect(device)
            except Exception as err:
                # Unknown error.
                self.errorLog(f"Failed to receive data from {device.name}: {err}")
                self.updateDeviceState(device, 'status', "error")
                self.updateDeviceState(device, 'connected', False)
        elif not connected and not connecting:
            # Show an error and try to connect.
            self.errorLog(f"Unable to read data from {device.name}. It is not connected. Attempting to re-connect.")
            self.connect(device)
        elif not connected and connecting:
            # Show an error indicating that we're still trying to connect.
            self.errorLog(f"Unable to read data from {device.name}. Still trying to connect to it.")

        return response

    #########################################
    # Process a Command Response
    #########################################
    def processResponse(self, device, response):
        """
        Placeholder - fixme

        :param device:
        :param response:
        :return:
        """
        # Update the Indigo receiver device based on the response from the receiver.
        self.debugLog(f"processResponse: from: {device.name} response: {response}")

        # Get the type of device.  In the future, we'll support different receiver types.
        dev_type = device.deviceTypeId

        # Make a copy of the device properties, so we can change them if needed.
        dev_props = device.pluginProps

        result = ""
        state = ""
        new_value = ""

        #
        # Test for each type of command response.
        #

        #
        # ERRORS
        #

        state = "status"
        new_value = "error"
        if response == "E02":
            self.errorLog(device.name + ": not available now.")
        elif response == "E03":
            self.errorLog(device.name + ": invalid command.")
        elif response == "E04":
            self.errorLog(device.name + ": command error.")
        elif response == "E06":
            self.errorLog(device.name + ": parameter error.")
        elif response == "B00":
            new_value = "busy"
            self.errorLog(device.name + ": system busy.")
        #
        # General Acknowledgement Response
        #
        elif response == "R":
            self.debugLog(f"processResponse: {device.name}: command acknowledged.")
        #
        # Zone 1 Specific Items
        #
        elif response.startswith("PWR"):
            # Power (zone 1) status.
            state = "zone1power"
            if response == "PWR0":
                # Power (zone 1) is on.
                new_value = True
                # Only set a result message if this is a change from the current state.
                if not device.states['zone1power']:
                    # Set the result to be logged.
                    result = "power (zone 1): on"
                # Update the onOffState.
                self.updateDeviceState(device, 'onOffState', True)
                # If zone 2 is also on, make sure the status reflects that.
                if device.states['zone2power']:
                    # Set the "status" state on the server.
                    self.updateDeviceState(device, "status", "on (zones 1+2)")
                else:
                    self.updateDeviceState(device, "status", "on (zone 1)")
            elif response == "PWR1":
                # Power (zone 1) is off.
                new_value = False
                if device.states['zone1power']:
                    result = "power (zone 1): off"
                # If zone 2 is on, make sure the status reflects that.
                if device.states['zone2power']:
                    self.updateDeviceState(device, "status", "on (zone 2)")
                else:
                    self.updateDeviceState(device, "status", "off")
                    # Update the onOffState.
                    self.updateDeviceState(device, 'onOffState', False)
                # Clear all the state values.
                #   Set "zone1volume" to -999.0 dB.
                self.updateDeviceState(device, "zone1volume", -999.0)
                #   Set "zone1source" to 0 (no source)
                self.updateDeviceState(device, "zone1source", 0)
                #   Set "zone1sourceName to (no source)
                self.updateDeviceState(device, "zone1sourceName", "")
                #   Set all channel levels to 0.
                for the_channel, the_name in CHANNEL_VOLUMES.items():
                    self.updateDeviceState(device, the_name, 0)
                #   Set MCACC Memory number to 0.
                self.updateDeviceState(device, "mcaccMemory", 0)
                #   Clear the MCACC memory name.
                self.updateDeviceState(device, "mcaccMemoryName", "")
                # Look for Virtual Volume Controllers that might need setting to zero.
                for this_id in self.volume_device_list:
                    virtual_volume_device = indigo.devices[this_id]
                    control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                    if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                            and control_destination == "zone1volume"):
                        self.updateDeviceState(virtual_volume_device, 'brightnessLevel', 0)
            elif response == "PWR2":
                # Power (zone 1) is off (network standby mode, only VSX-1022-K reports this).
                new_value = False
                if device.states['zone1power']:
                    result = "power (zone 1): off"
                # If zone 2 is on, make sure the status reflects that.
                if device.states['zone2power']:
                    self.updateDeviceState(device, "status", "on (zone 2)")
                else:
                    self.updateDeviceState(device, "status", "off")
                    # Update the onOffState.
                    self.updateDeviceState(device, 'onOffState', False)
                # Clear all the state values.
                #   Set "zone1volume" to -999.0 dB.
                self.updateDeviceState(device, "zone1volume", -999.0)
                #   Set "zone1source" to 0 (no source)
                self.updateDeviceState(device, "zone1source", 0)
                #   Set "zone1sourceName to (no source)
                self.updateDeviceState(device, "zone1sourceName", "")
                #   Set all channel levels to 0.
                for the_channel, the_name in CHANNEL_VOLUMES.items():
                    self.updateDeviceState(device, the_name, 0)
                #   Set MCACC Memory number to 0.
                self.updateDeviceState(device, "mcaccMemory", 0)
                #   Clear the MCACC memory name.
                self.updateDeviceState(device, "mcaccMemoryName", "")
                # Look for Virtual Volume Controllers that might need setting to zero.
                for this_id in self.volume_device_list:
                    virtual_volume_device = indigo.devices[this_id]
                    control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                    if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                            and control_destination == "zone1volume"):
                        self.updateDeviceState(virtual_volume_device, 'brightnessLevel', 0)
        elif response.startswith("MUT"):
            # Mute (zone 1) status.
            state = "zone1mute"
            if response == "MUT0":
                # Mute is on.
                new_value = True
                if not device.states['zone1mute']:
                    result = "mute (zone 1): on"
                # Look for Virtual Volume Controllers that might need updating.
                for this_id in self.volume_device_list:
                    virtual_volume_device = indigo.devices[this_id]
                    control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                    if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                            and control_destination == "zone1volume"):
                        self.updateDeviceState(virtual_volume_device, 'brightnessLevel', 0)
            elif response == "MUT1":
                # Mute is off.
                new_value = False
                if device.states['zone1mute']:
                    result = "mute (zone 1): off"
                # Look for Virtual Volume Controllers that might need updating.
                for this_id in self.volume_device_list:
                    virtual_volume_device = indigo.devices[this_id]
                    control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                    if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                            and control_destination == "zone1volume"):
                        # Update the Virtual Volume Controller to match current volume. Get the receiver's volume.
                        the_volume = float(device.states[control_destination])
                        # Convert the current volume of the receiver to a percentage to be displayed as a brightness
                        # level. If the volume is less than -80.5, the receiver is off and the brightness should be 0.
                        if float(the_volume) < -80.5:
                            the_volume = -80.5
                        the_volume = int(100 - round(the_volume / -80.5 * 100, 0))
                        self.updateDeviceState(virtual_volume_device, 'brightnessLevel', the_volume)
        elif response.startswith("FN"):
            # Source/function (zone 1) status.
            state = "zone1source"
            new_value = int(response[2:])
            # Check to see if zone 1 is already set to this input or if zone 1 power is off.  In either case, ignore
            # this update.
            if device.states[state] == new_value or not device.states['zone1power']:
                state = ""
                new_value = ""
        elif response.startswith("VOL"):
            # Volume (zone 1) status.
            state = "zone1volume"
            # Convert to dB.
            new_value = float(response[3:]) * 1.0
            new_value = -80.5 + 0.5 * new_value
            # Volume is at minimum or zone 1 power is off, volume is meaningless, so set it to minimum.
            if (new_value < -80.0) or (not device.states['zone1power']):
                new_value = -999.0
                result = "volume (zone 1): minimum."
            else:
                result = f"volume (zone 1): {new_value} dB"
            # Look for Virtual Volume Controllers that might need updating.
            self.debugLog(
                f"processResponse: Looking for connected Virtual Volume Controllers. volumeDeviceList: "
                f"{self.volume_device_list}"
            )
            for this_id in self.volume_device_list:
                virtual_volume_device = indigo.devices[this_id]
                self.debugLog(f"processResponse: Examining Virtual Volume Controller ID {this_id}")
                self.debugLog(f"processResponse: {virtual_volume_device}")
                control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                if int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id \
                        and control_destination == "zone1volume":
                    self.debugLog(f"processResponse: Virtual Volume Controller ID {this_id} is connected.")
                    # Update the Virtual Volume Controller to match new volume.
                    the_volume = new_value
                    # Convert the current volume of the receiver to a percentage to be displayed as a brightness level.
                    # If the volume is less than -80.5, the receiver is off and the brightness should be 0.
                    if the_volume < -80.0:
                        the_volume = -80.5
                    the_volume = int(100 - round(the_volume / -80.5 * 100, 0))
                    self.debugLog(
                        f"processResponse: updating Virtual Volume Device ID {this_id} brightness level to "
                        f"{the_volume}."
                    )
                    self.updateDeviceState(virtual_volume_device, 'brightnessLevel', the_volume)
        #
        # Zone 2 Specific Items
        #
        elif response.startswith("APR"):
            # Power (zone 2) status.
            state = "zone2power"
            if response == "APR0":
                # Power (zone 2) is on.
                new_value = True
                if not device.states['zone2power']:
                    result = "power (zone 2): on"
                # Update the onOffState.
                self.updateDeviceState(device, 'onOffState', True)
                # If main power (zone 1) is on, set the status to reflect that.
                if device.states['zone1power']:
                    self.updateDeviceState(device, "status", "on (zones 1+2)")
                else:
                    self.updateDeviceState(device, "status", "on (zone 2)")
            elif response == "APR1":
                # Power (zone 2) is off.
                new_value = False
                if device.states['zone2power']:
                    result = "power (zone 2): off"
                # If main power (zone 1) is on, make sure the status reflects that.
                if device.states['zone1power']:
                    self.updateDeviceState(device, "status", "on (zone 1)")
                else:
                    self.updateDeviceState(device, "status", "off")
                    # Update the onOffState.
                    self.updateDeviceState(device, 'onOffState', False)
                # Clear all the state values.
                #   Set "zone1volume" to -999 dB.
                self.updateDeviceState(device, "zone2volume", -999)
                #   Set "zone1source" to 0 (no source)
                self.updateDeviceState(device, "zone2source", 0)
                #   Set "zone1sourceName to (no source)
                self.updateDeviceState(device, "zone2sourceName", "")
                # Clear the tuner settings if zone 1 isn't using it.
                if device.states['zone1source'] != 2:
                    self.updateDeviceState(device, 'tunerPreset', "")
                    self.updateDeviceState(device, 'tunerFrequency', 0)
                    self.updateDeviceState(device, 'tunerFrequencyText', "")
                    self.updateDeviceState(device, 'tunerBand', "")
                # Look for Virtual Volume Controllers that might need setting to zero.
                for this_id in self.volume_device_list:
                    virtual_volume_device = indigo.devices[this_id]
                    control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                    if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                            and control_destination == "zone2volume"):
                        self.updateDeviceState(virtual_volume_device, 'brightnessLevel', 0)
        elif response.startswith("Z2F"):
            # Source/function (zone 2) status.
            state = "zone2source"
            new_value = int(response[3:])
            # Check to see if zone 2 is already set to this input or if zone 2 power is off.  If either is the case,
            # ignore this update.
            if device.states[state] == new_value or not device.states['zone2power']:
                state = ""
                new_value = ""
        elif response.startswith("Z2MUT"):
            # Mute (zone 2) status.
            state = "zone2mute"
            # If the speaker system arrangement is not set to A + Zone 2, zone mute and volume settings returned by
            # the receiver are meaningless. Set the state on the server to properly reflect this.
            if device.states['speakerSystem'] == "A + Zone 2":
                if response == "Z2MUT0":
                    # Mute is on.
                    new_value = True
                    result = "mute (zone 2): on"
                    # Look for Virtual Volume Controllers that might need updating.
                    for this_id in self.volume_device_list:
                        virtual_volume_device = indigo.devices[this_id]
                        control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                        if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                                and control_destination == "zone2volume"):
                            self.updateDeviceState(virtual_volume_device, 'brightnessLevel', 0)
                elif response == "Z2MUT1":
                    # Mute is off.
                    new_value = False
                    result = "mute (zone 2): off"
                    # Look for Virtual Volume Controllers that might need updating.
                    for this_id in self.volume_device_list:
                        virtual_volume_device = indigo.devices[this_id]
                        control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                        if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                                and control_destination == "zone2volume"):
                            # Update the Virtual Volume Controller to match current volume. Get the receiver's volume.
                            the_volume = float(device.states[control_destination])
                            # Convert the current volume of the receiver to a percentage to be displayed as a
                            # brightness level. If the volume is less than -80.5, the receiver is off and the
                            # brightness should be 0.
                            if float(the_volume) < -81:
                                the_volume = -81
                            the_volume = int(100 - round(the_volume / -81 * 100, 0))
                            self.updateDeviceState(virtual_volume_device, 'brightnessLevel', the_volume)
            else:
                new_value = False
                result = ""
                # Zone 2 mute is meaningless when using the RCA line outputs, so look for Virtual Volume Controllers
                # that might need updating. If zone 2 power is on, the zone 2 line output will always be at 100% volume.
                if device.states['zone2power']:
                    for this_id in self.volume_device_list:
                        virtual_volume_device = indigo.devices[this_id]
                        control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                        if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                                and control_destination == "zone2volume"):
                            self.updateDeviceState(virtual_volume_device, 'brightnessLevel', 100)
                else:
                    # If zone 2 power is off, the zone 2 line output will always be at 0% volume.
                    for this_id in self.volume_device_list:
                        virtual_volume_device = indigo.devices[this_id]
                        control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                        if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                                and control_destination == "zone2volume"):
                            self.updateDeviceState(virtual_volume_device, 'brightnessLevel', 0)
        elif response.startswith("ZV"):
            # Volume (zone 2) status.
            state = "zone2volume"
            # Convert to dB.
            new_value = int(response[2:])
            # new_value = -81 + new_value
            new_value += -81
            if new_value < -80 or not device.states['zone2power']:
                new_value = -999
                result = "volume (zone 2): minimum."
            else:
                result = f"volume (zone 2): {new_value} dB"
            # If the speaker system arrangement is not set to A + Zone 2, zone mute and volume settings returned by the
            # receiver are meaningless. Set the state on the server to properly reflect this.
            if device.states['speakerSystem'] == "A + Zone 2":
                # Look for Virtual Volume Controllers that might need updating.
                self.debugLog(
                    f"processResponse: Looking for zone 2 connected Virtual Volume Controllers. volumeDeviceList: "
                    f"{self.volume_device_list}"
                )
                for this_id in self.volume_device_list:
                    virtual_volume_device = indigo.devices[this_id]
                    self.debugLog(f"processResponse: Examining Virtual Volume Controller ID {this_id}")
                    self.debugLog(f"processResponse: {virtual_volume_device}")
                    control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                    if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                            and control_destination == "zone2volume"):
                        self.debugLog(
                            f"processResponse: Virtual Volume Controller ID {this_id} is connected to zone 2 volume."
                        )
                        # Update the Virtual Volume Controller to match current volume. Get the receiver's volume.
                        the_volume = new_value
                        # Convert the current volume of the receiver to a percentage to be displayed as a brightness
                        # level. If the volume is less than -81, the receiver is off and the brightness should be 0.
                        if the_volume < -81:
                            the_volume = -81
                        the_volume = 100 - int(round(the_volume / -81.0 * 100, 0))
                        # If zone 2 power is on, use theVolume. If not, use zero.
                        if device.states['zone2power']:
                            self.debugLog(
                                f"processResponse: updating Virtual Volume Device ID {this_id} brightness level to "
                                f"{the_volume}"
                            )
                            self.updateDeviceState(virtual_volume_device, 'brightnessLevel', the_volume)
                        else:
                            self.debugLog(
                                f"processResponse: updating Virtual Volume Device ID {this_id} brightness level to 0"
                            )
                            self.updateDeviceState(virtual_volume_device, 'brightnessLevel', 0)
            else:
                new_value = 0
                result = ""
                # Zone 2 volume is meaningless when using the RCA line outputs, so look for Virtual Volume Controllers
                # that might need updating. If zone 2 power is on, the zone 2 line output will always be at 100% volume.
                if device.states['zone2power']:
                    for this_id in self.volume_device_list:
                        virtual_volume_device = indigo.devices[this_id]
                        control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                        if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                                and control_destination == "zone2volume"):
                            self.updateDeviceState(virtual_volume_device, 'brightnessLevel', 100)
                else:
                    # If zone 2 power is off, the zone 2 line output will always be at 0% volume.
                    for this_id in self.volume_device_list:
                        virtual_volume_device = indigo.devices[this_id]
                        control_destination = virtual_volume_device.pluginProps.get('controlDestination', "")
                        if (int(virtual_volume_device.pluginProps.get('receiverDeviceId', "")) == device.id
                                and control_destination == "zone2volume"):
                            self.updateDeviceState(virtual_volume_device, 'brightnessLevel', 0)
        #
        # System-Wide Items
        #
        elif response.startswith("RGB"):
            # Source name update.
            new_value = response[6:]
            # Define the device property to update and make the change to the local copy.
            prop_name = f"source{response[3:5]}label"
            dev_props[prop_name] = new_value
            # Update the source name in the device properties on the server.
            self.updateDeviceProps(device, dev_props)
            # If the input source name update is for the currently selected zone 1 input source or zone 2 input source,
            # change the appropriate state in the device.
            if device.states['zone1source'] == int(response[3:5]):
                state = "zone1sourceName"
                result = f"input source (zone 1): {new_value}"
                self.updateDeviceState(device, state, new_value)
            if device.states['zone2source'] == int(response[3:5]):
                state = "zone2sourceName"
                result = f"input source (zone 2): {new_value}"
                self.updateDeviceState(device, state, new_value)
        elif response.startswith("FL"):
            # Display update.
            state = "display"
            new_value = ""
            # All characters after character 4 are ASCII representations of HEX numbers that represent ASCII characters
            # (!?)
            the_string = response[4:]
            index = 0
            while index < 28:
                # Convert the 2-character HEX representations to actual ASCII values.
                #   -- Add "0x" to the front of the 2-character representation to indicate that it should be a HEX
                #      number.
                #   -- Use the "int" builtin to convert from ASCII base 16 to an integer.
                ascii_val = int(f"0x{the_string[index:index + 2]}", 16)
                # Check for special characters.
                if ascii_val < 32 or ascii_val > 126:
                    # Add the special character to the new_value string from the character map dictionary defined at the
                    # top.
                    new_value += CHARACTER_MAP[ascii_val]
                else:
                    # Use the "chr" builtin to convert from integer to an ASCII character then add that to the existing
                    # new_value string.
                    # new_value += unicode(str(chr(asciiVal)))
                    new_value += f"{chr(ascii_val)}"
                # Increment the index by 2
                index += 2
        elif response.startswith("MC"):
            # MCACC Memory update.
            state = "mcaccMemory"
            new_value = int(response[2:])
            prop_name = f'mcaccMemory{new_value}label'
            mcacc_name = dev_props.get(prop_name, "")
            result = f"MCACC memory: {new_value}: {mcacc_name}"
        elif response.startswith("IS"):
            # Phase Control update.
            state = "phaseControl"
            if response == "IS0":
                # Phase Control Off.
                new_value = "off"
            elif response == "IS1":
                # Phase Control On.
                new_value = "on"
            elif response == "IS2":
                # Full Band Phase Control On.
                new_value = "on - full band"
            result = f"Phase Control: {new_value}"
        elif response.startswith("VSP"):
            # Virtual Speakers.
            state = "vsp"
            if response == "VSP0":
                # Virtual Speakers Auto.
                new_value = "auto"
                result = "Virtual Speakers: auto"
            elif response == "VSP1":
                # Virtual Speakers Manual.
                new_value = "manual"
                result = "Virtual Speakers: manual"
        elif response.startswith("VSB"):
            # Virtual Surround Back update.
            state = "vsb"
            if response == "VSB0":
                # Virtual Surround Back Off.
                new_value = False
                result = "Virtual Surround Back: off"
            elif response == "VSB1":
                # Virtual Surround Back On.
                new_value = True
                result = "Virtual Surround Back: on"
        elif response.startswith("VHT"):
            # Virtual Surround Height update.
            state = "vht"
            if response == "VHT0":
                # Virtual Surround Height Off.
                new_value = False
                result = "Virtual Surround Height: off"
            elif response == "VSB1":
                # Virtual Surround Height On.
                new_value = True
                result = "Virtual Surround Height: on"
        elif response.startswith("CLV"):
            # Channel Volume Level update.
            channel = response[3:6]
            # Get the state name from the global dictionary defined at the top.
            state = CHANNEL_VOLUMES[channel]
            level = float(response[6:]) * 1.0
            # convert the level to decibels.
            new_value = -12 + 0.5 * (level - 26.0)
            result = f"{channel.strip('_')} channel level: {new_value} dB."
        elif response.startswith("SPK"):
            # Speaker mode update.
            state = "speakers"
            if response == "SPK0":
                # Speakers off.
                new_value = "off"
            elif response == "SPK1":
                # Speaker group A on.
                new_value = "on - A"
            elif response == "SPK2":
                # Speaker group B on.
                new_value = "on - B"
            elif response == "SPK3":
                # Both speaker groups A and B on.
                new_value = "on - A+B"
            result = f"speaker mode: {new_value}"
        elif response.startswith("HA"):
            # HDMI Audio Pass-through update.
            state = "hdmiAudio"
            if response == "HA0":
                # HDMI Audio processed by amp.
                new_value = False
                result = "HDMI Audio Pass-Through: off"
            elif response == "HA1":
                # HDMI Audio passed through unaltered.
                new_value = True
                result = "HDMI Audio Pass-Through: on"
        elif response.startswith("PQ"):
            # PQLS status update.
            state = "pqls"
            if response == "PQ0":
                # PQLS off.
                new_value = False
                result = "PQLS: off"
            elif response == "PQ1":
                # PQLS auto.
                new_value = True
                result = "PQLS: on"
        elif response.startswith("SSA"):
            # Operating Mode.
            state = "operatingMode"
            if response == "SSA0":
                # Expert Mode.
                new_value = "Expert"
            elif response == "SSA1":
                # reserved mode.
                new_value = "(factory reserved)"
            elif response == "SSA2":
                # Basic Mode.
                new_value = "Basic"
            result = f"operating mode: {new_value}"
        elif response.startswith("SSE"):
            # OSD Language setting.
            if response == "SSE00":
                new_value = "English"
            else:
                new_value = "non-English"
            # Define the device property to update and make the change to the local copy.
            prop_name = 'osdLanguage'
            dev_props[prop_name] = new_value
            # Update the source name in the device properties on the server.
            self.updateDeviceProps(device, dev_props)
        elif response.startswith("SSF"):
            # Speaker System status.
            state = "speakerSystem"
            if response == "SSF00":
                new_value = "A + Surround Height"
            if response == "SSF01":
                new_value = "A + Surround Width"
            if response == "SSF02":
                new_value = "A Bi-Amped"
            if response == "SSF03":
                new_value = "A + B 2-Channel"
            if response == "SSF04":
                new_value = "A + Zone 2"
            result = f"speaker system layout: {new_value}"
        elif response.startswith("SAA"):
            # Dimmer Brightness change.
            if response == "SAA0":
                new_value = "bright"
            elif response == "SAA1":
                new_value = "medium"
            elif response == "SAA2":
                new_value = "dim"
            elif response == "SAA3":
                new_value = "off"
        elif response.startswith("SAB"):
            # Sleep Timer time remaining.
            state = "sleepTime"
            new_value = int(response[3:])
            if new_value == 0:
                # Sleep timer is off
                self.updateDeviceState(device, "sleepMode", False)
                result = "sleep timer: off"
            else:
                # Sleep timer is on
                self.updateDeviceState(device, "sleepMode", True)
                result = f"sleep timer: {new_value} minutes remaining."
        elif response.startswith("PKL"):
            # Panel Key Lock status.
            state = "panelKeyLockMode"
            if response == "PKL0":
                # Unlocked.
                new_value = "off"
            elif response == "PKL1":
                # Panel locked.
                new_value = "on - panel"
            elif response == "PKL2":
                # Panel and volume locked.
                new_value = "on - panel+volume"
            result = f"front panel lock: {new_value}"
        elif response.startswith("RML"):
            # Remote Lock Mode status.
            state = "remoteLock"
            if response == "RML0":
                new_value = False
                result = "remote control lock: off"
            elif response == "RML1":
                new_value = True
                result = "remote control lock: on"
        elif response.startswith("FR"):
            # Tuner Frequency update. Only update the state if either zone 1 or 2 is actually using the Tuner.
            if device.states['zone1source'] == 2 or device.states['zone2source'] == 2:
                state = "tunerFrequency"
                # Extract the band (AM or FM)
                band = response[2:3] + "M"
                # Set the tuner band on the server.
                self.updateDeviceState(device, "tunerBand", str(band))
                # Extract the frequency.
                frequency = response[3:]
                frequency_text = frequency
                if band == "FM":
                    # If the band is FM, put the decimal in the right place.
                    frequency_text = f"{frequency[0:3]}.{frequency[3:]} MHz"
                    frequency_text = frequency_text.lstrip("0")  # Eliminate leading zeros.
                    frequency = float(f"{frequency[0:3]}.{frequency[3:]}")
                elif band == "AM":
                    # If the band is AM, convert the text to an integer.
                    frequency = int(frequency)  # Eliminates leading zeros.
                    frequency_text = f"{frequency} kHz"
                # Only log the change if the frequency is actually different.
                if frequency != device.states['tunerFrequency'] or band != device.states['tunerBand']:
                    result = f"tuner frequency: {frequency_text} {band}"
                # Set the tuner frequency on the server
                new_value = frequency
        elif response.startswith("PR"):
            # Tuner Preset update. Only update the state if either zone 1 or 2 is actually using the Tuner.
            if device.states['zone1source'] == 2 or device.states['zone2source'] == 2:
                state = "tunerPreset"
                # Get the preset letter plus the non-leading-zero number.
                new_value = response[2:3] + str(int(response[3:]))
                # Now add the custom name (if set) for the preset.
                prop_name = f"tunerPreset{new_value}label"
                new_value += f": {device.pluginProps[prop_name]}"
                # Ignore this information if the state is already set to this setting.
                if device.states[state] == new_value:
                    state = ""
                    new_value = ""
                else:
                    result = f"tuner preset: {new_value}"
        elif response.startswith("TQ"):
            # Tuner Preset Label update.
            new_value = response[4:]  # Strip off the "TQ"
            new_value = new_value.strip('"')  # Remove the enclosing quotes.
            new_value = new_value.strip()  # Remove the white space.
            # Define the device property to update and make the change to the local copy.
            prop_name = f"tunerPreset{response[2:4]}label"
            dev_props[prop_name] = new_value
            # Update the source name in the device properties on the server.
            self.updateDeviceProps(device, dev_props)
        elif response.startswith("SR"):
            # Listening Mode update.
            state = "listeningMode"
            new_value = LISTENING_MODES[response[2:]]
            # Ignore this information if the state is already set to this setting.
            if device.states[state] == new_value:
                state = ""
                new_value = ""
            else:
                result = f"listening mode: {new_value}"
        elif response.startswith("LM"):
            # Playback Listening Mode update.
            state = "displayListeningMode"
            new_value = DISPLAY_LISTENING_MODES[response[2:]]
            # Ignore this information if the state is already set to this setting.
            if device.states[state] == new_value:
                state = ""
                new_value = ""
            else:
                result = f"displayed listening mode: {new_value}"
        elif response.startswith("TO"):
            # Tone Control on/off change.
            state = "toneControl"
            if response == "TO0":
                new_value = False
                result = "tone control: off"
            elif response == "TO1":
                new_value = True
                result = "tone control: on"
        elif response.startswith("BA"):
            # Bass Tone Control change.
            state = "toneBass"
            new_value = (6 - int(response[2:]))
            result = f"bass tone level: {new_value} dB"
        elif response.startswith("TR"):
            # Treble Tone Control change.
            state = "toneTreble"
            new_value = (6 - int(response[2:]))
            result = f"bass tone level: {new_value} dB"
        elif response.startswith("ATA"):
            # Sound Retriever status change.
            state = "soundRetriever"
            if response == "ATA0":
                new_value = False
                result = "Sound Retriever: off"
            elif response == "ATA1":
                new_value = True
                result = "Sound Retriever: on"
        elif response.startswith("SDA"):
            # Signal Source selection.
            state = "signalSource"
            if response == "SDA0":
                new_value = "AUTO"
            elif response == "SDA1":
                new_value = "ANALOG"
            elif response == "SDA2":
                new_value = "DIGITAL"
            elif response == "SDA3":
                new_value = "HDMI"
            result = f"audio signal source: {new_value}"
        elif response.startswith("SDB"):
            # Analog Input Attenuator status.
            state = "analogInputAttenuator"
            if response == "SDB0":
                new_value = False
                result = "analog input attenuator: off"
            elif response == "SDB1":
                new_value = True
                result = "analog input attenuator: on"
        elif response.startswith("ATC"):
            # Equalizer status.
            state = "equalizer"
            if response == "ATC0":
                new_value = False
                result = "equalizer: off"
            elif response == "ATC1":
                new_value = True
                result = "equalizer: on"
            # Don't update the state if it's the same.
            if device.states[state] == new_value:
                state = ""
                new_value = ""
                result = ""
        elif response.startswith("ATD"):
            # Standing Wave compensation status.
            state = "standingWave"
            if response == "ATD0":
                new_value = False
                result = "standing wave compensation: off"
            elif response == "ATD1":
                new_value = True
                result = "standing wave compensation: on"
            # Don't update the state if it's the same.
            if device.states[state] == new_value:
                state = ""
                new_value = ""
                result = ""
        elif response.startswith("ATE"):
            # Phase Control Plus delay time (ms) change.
            state = "phaseControlPlusTime"
            new_value = int(response[3:])
            result = f"Phase Control Plus time: {new_value} ms"
        elif response.startswith("ATF"):
            # Sound Delay time (fractional sample frames) change.
            state = "soundDelay"
            new_value = (float(response[3:]) / 10.0)
            result = f"sound delay: {new_value} sample frames"
        elif response.startswith("ATG"):
            # Digital Noise Reduction status.
            state = "digitalNR"
            if response == "ATG0":
                new_value = False
                result = "Digital Noise Reduction: off"
            elif response == "ATG1":
                new_value = True
                result = "Digital Noise Reduction: on"
        elif response.startswith("ATH"):
            # Dialog Enhancement change.
            state = "dialogEnhancement"
            if response == "ATH0":
                new_value = "off"
            elif response == "ATH1":
                new_value = "flat"
            elif response == "ATH2":
                new_value = "up1"
            elif response == "ATH3":
                new_value = "up2"
            elif response == "ATH4":
                new_value = "up3"
            elif response == "AHT5":
                new_value = "up4"
            result = f"Dialog Enhancement mode: {new_value}"
        elif response.startswith("ATI"):
            # Hi-bit 24 status.
            state = "hiBit24"
            if response == "ATI0":
                new_value = False
                result = "Hi-bit 24: off"
            elif response == "ATI1":
                new_value = True
                result = "Hi-bit 24: on"
        elif response.startswith("ATJ"):
            # Dual Mono processing change.
            state = "dualMono"
            if response == "ATJ0":
                new_value = False
                result = "Dual Mono sound processing: off"
            elif response == "ATJ1":
                new_value = True
                result = "Dual Mono sound processing: on"
        elif response.startswith("ATK"):
            # Fixed PCM rate processing change.
            state = "fixedPCM"
            if response == "ATK0":
                new_value = False
                result = "fixed rate PCM: off"
            elif response == "ATK1":
                new_value = True
                result = "fixed rate PCM: on"
        elif response.startswith("ATL"):
            # Dynamic Range Compression mode change.
            state = "dynamicRangeCompression"
            if response == "ATL0":
                new_value = "off"
            elif response == "ATL1":
                new_value = "auto"
            elif response == "ATL2":
                new_value = "mid"
            elif response == "ATL3":
                new_value = "max"
            result = f"Dynamic Range Compression: {new_value}"
        elif response.startswith("ATM"):
            # LFE Attenuation change.
            state = "lfeAttenuatorAmount"
            new_value = (-5 * int(response[3:]))
            result = f"LFE attenuation amount: {new_value} dB"
            if new_value < -20:
                # A response of ATM5 translates to the attenuator being turned off.
                self.updateDeviceState(device, "lfeAttenuator", False)
                result = "LFE attenuation: off"
            else:
                self.updateDeviceState(device, "lfeAttenuator", True)
        elif response.startswith("ATN"):
            # SACD Gain change.
            state = "sacdGain"
            if response == "ATN0":
                new_value = 0
            elif response == "ATN1":
                new_value = 6
            result = f"SACD gain: {new_value} dB"
        elif response.startswith("ATO"):
            # Auto Sound Delay status update.
            state = "autoDelay"
            if response == "ATO0":
                new_value = False
                result = "Auto Sound Delay: off"
            elif response == "ATO1":
                new_value = True
                result = "Auto Sound Delay: on"
        elif response.startswith("ATP"):
            # Dolby Pro Logic II Music Center Width change.
            state = "pl2musicCenterWidth"
            new_value = int(response[3:])
            result = f"Dolby Pro Logic II Music center width: {new_value}"
        elif response.startswith("ATQ"):
            # Dolby Pro Logic II Music Panorama status.
            state = "pl2musicPanorama"
            if response == "ATQ0":
                new_value = False
                result = "Dolby Pro Logic II Music panorama: off"
            elif response == "ATQ1":
                new_value = True
                result = "Dolby Pro Logic II Music panorama: on"
        elif response.startswith("ATR"):
            # Dolby Pro Logic II Music Dimension level change.
            state = "pl2musicDimension"
            new_value = (int(response[3:]) - 50)
            result = f"Dolby Pro Logic II Music dimension: {new_value}"
        elif response.startswith("ATS"):
            # Neo:6 Center Image change.
            state = "neo6centerImage"
            new_value = (float(response[3:]) / 10.0)
            result = f"Neo:6 center image: {new_value}"
        elif response.startswith("ATT"):
            # Effect amount change.
            state = "effectAmount"
            new_value = (int(response[3:]) * 10)
            result = f"effect level: {new_value}"
        elif response.startswith("ATU"):
            # Dolby Pro Logic IIz Height Gain change.
            state = "pl2zHeightGain"
            if response == "ATU0":
                new_value = "LOW"
            elif response == "ATU1":
                new_value = "MID"
            elif response == "ATU2":
                new_value = "HIGH"
            result = f"Dolby Pro Logic IIz height gain: {new_value}"
        elif response.startswith("VTB"):
            # Video Converter update.
            state = "videoConverter"
            if response == "VTB0":
                # Video Converter Off.
                new_value = False
                result = "video converter: off"
            elif response == "VTB1":
                # Video Converter On.
                new_value = True
                result = "video converter: on"
        elif response.startswith("VTC"):
            # Video Resolution update.
            state = "videoResolution"
            new_value = VIDEO_RESOLUTION_PREFS[response[3:]]
            result = f"preferred video resolution: {new_value}"
        elif response.startswith("VTD"):
            # Video Pure Cinema mode update.
            state = "videoPureCinema"
            if response == "VTD0":
                # Pure Cinema Auto.
                new_value = "auto"
            elif response == "VTD1":
                # Pure Cinema On.
                new_value = "on"
            elif response == "VTD2":
                # Pure Cinema Off.
                new_value = "off"
            result = f"Pure Cinema mode: {new_value}"
        elif response.startswith("VTE"):
            # Video Progressive Motion Quality update.
            state = "videoProgressiveQuality"
            new_value = -4 + (int(response[3:]) - 46)
            result = f"video progressive scan motion quality: {new_value}"
        elif response.startswith("VTG"):
            # Video Advanced Adjustment update.
            state = "videoAdvancedAdjust"
            if response == "VTG0":
                # PDP (Plasma Display Panel)
                new_value = "PDP (Plasma)"
            elif response == "VTG1":
                # LCD (Liquid Crystal Display)
                new_value = "LCD"
            elif response == "VTG2":
                # FPJ (Front Projection)
                new_value = "FPJ (Front Projection)"
            elif response == "VTG3":
                # Professional
                new_value = "Professional"
            elif response == "VTG4":
                # Memory
                new_value = "Memory"
            result = f"Advanced Video Adjustment: {new_value}"
        elif response.startswith("VTH"):
            # Video YNR (Luminance Noise Reduction) update.
            state = "videoYNR"
            new_value = int(response[3:]) - 50
            result = f"video YNR: {new_value}"
        elif response.startswith("VTL"):
            # Video Detail Adjustment update.
            state = "videoDetail"
            new_value = 50 - int(response[3:])
            result = f"video detail amount: {new_value}"
        elif response.startswith("AST"):
            # Audio Status information update. Multiple data are provided in this response (43 bytes, or 55 for
            # VSX-1123-K).
            state = ""
            new_value = ""
            data = response[3:]  # strip the AST text.

            # == Data Common to All Models ==
            audio_input_format = data[0:2]  # 2-byte signal format code.
            # Convert signal format code to a named format.
            audio_input_format = AUDIO_INPUT_FORMATS[audio_input_format]
            state = "audioInputFormat"
            new_value = audio_input_format
            self.updateDeviceState(device, state, new_value)

            audio_input_frequency = data[2:4]  # 2-byte sample frequency code.
            # Convert sample frequency code to a value.
            audio_input_frequency = AUDIO_INPUT_FREQUENCIES[audio_input_frequency]
            state = "audioInputFrequency"
            new_value = audio_input_frequency
            self.updateDeviceState(device, state, new_value)

            state = "inputChannels"
            new_value = ""
            # Convert data bytes 5-25 into an input channel format string. Loop through data bytes and add channels
            # that are enabled.
            state = "inputChannels"
            new_value = ""
            for i in range(5, 26):
                if data[(i - 1):i] == "1":
                    # Add a comma if this is not the first item.
                    # if new_value is not "": fixme
                    if new_value != "":
                        new_value += ", "
                    new_value += AUDIO_CHANNELS[(i - 5)]
            self.updateDeviceState(device, state, new_value)

            # Convert data bytes 26-43 into an output channel format string. Loop through data bytes and add channels
            # that are enabled.
            state = "outputChannels"
            new_value = ""
            for i in range(26, 44):
                if data[(i - 1):i] == "1":
                    # Add a comma if this is not the first item.
                    # if new_value is not "": fixme
                    if new_value != "":
                        new_value += ", "
                    new_value += AUDIO_CHANNELS[(i - 26)]
            self.updateDeviceState(device, state, new_value)

            # The VSX-1123-K responds with a 55 instead of 43 characters. These extra data represent features found
            # only in this and other 2014 models.
            if device.deviceTypeId == "vsx1123k":
                audio_output_frequency = data[43:45]  # 2-byte sample frequency code.
                # Convert sample frequency code to a value.
                audio_output_frequency = AUDIO_OUTPUT_FREQUENCIES[audio_output_frequency]
                state = "audioOutputFrequency"
                new_value = audio_output_frequency
                self.updateDeviceState(device, state, new_value)

                audio_output_bit_depth = data[45:47]  # 2-byte sample bit depth value.
                # Convert sample bit depth from a string to a number.
                audio_output_bit_depth = int(audio_output_bit_depth)
                state = "audioOutputBitDepth"
                new_value = audio_output_bit_depth
                self.updateDeviceState(device, state, new_value)

                # Bytes 48 through 51 are reserved.

                pqls_mode = data[51:52]  # 1-byte PQLS working mode code.
                # Convert PQLS code to working state.
                if pqls_mode == "0":
                    pqls_mode = "off"
                elif pqls_mode == "1":
                    pqls_mode = "2-channel"
                elif pqls_mode == "2":
                    pqls_mode = "multi-channel"
                elif pqls_mode == "3":
                    pqls_mode = "bitstream"
                state = "pqlsMode"
                new_value = pqls_mode
                self.updateDeviceState(device, state, new_value)

                phase_control_plus_working_delay = data[52:54]  # 2-byte Phase Control Plus working delay (ms).
                # Convert Phase Control Plus string to number.
                phase_control_plus_working_delay = int(phase_control_plus_working_delay)
                state = "phaseControlPlusWorkingTime"
                new_value = phase_control_plus_working_delay
                self.updateDeviceState(device, state, new_value)

                phase_control_plus_reversed = data[54:55]  # 1-byte Phase Control Plus reversed phase.
                # Translate Phase Control Plus reversed state.
                if phase_control_plus_reversed == "0":
                    phase_control_plus_reversed = True
                elif phase_control_plus_reversed == "1":
                    phase_control_plus_reversed = False
                state = "phaseControlPlusReversed"
                new_value = phase_control_plus_reversed
                self.updateDeviceState(device, state, new_value)

            result = "audio input/output information updated"

        elif response.startswith("VST"):
            # Video Status information update. Multiple data are provided in this response.
            state = ""
            new_value = ""
            data = response[3:]  # Strip off the leading "VST".

            # Video Input Terminal
            state = "videoInputTerminal"
            new_value = int(data[0:1])
            if new_value == 0:
                new_value = ""
            elif new_value == 1:
                new_value = "Video"
            elif new_value == 2:
                new_value = "S-Video"
            elif new_value == 3:
                new_value = "Component"
            elif new_value == 4:
                new_value = "HDMI"
            elif new_value == 5:
                new_value = "Self (OSD/JPEG)"
            self.updateDeviceState(device, state, new_value)

            # Video Input Resolution
            state = "videoInputResolution"
            new_value = VIDEO_RESOLUTIONS[data[1:3]]
            self.updateDeviceState(device, state, new_value)

            # Video Input Aspect Ratio
            state = "videoInputAspect"
            new_value = int(data[3:4])
            if new_value == 0:
                new_value = ""
            elif new_value == 1:
                new_value = "4:3"
            elif new_value == 2:
                new_value = "16:9"
            elif new_value == 3:
                new_value = "14:9"
            self.updateDeviceState(device, state, new_value)

            # Video Input Color Format
            state = "videoInputColorFormat"
            new_value = int(data[4:5])
            if new_value == 0:
                new_value = ""
            elif new_value == 1:
                new_value = "RGB Limited"
            elif new_value == 2:
                new_value = "RGB Full"
            elif new_value == 3:
                new_value = "YCbCr 4:4:4"
            elif new_value == 4:
                new_value = "YCbCr 4:2:2"
            self.updateDeviceState(device, state, new_value)

            # Video Input Bit Depth
            state = "videoInputBitDepth"
            new_value = int(data[5:6])
            if new_value == 0:
                new_value = ""
            elif new_value == 1:
                new_value = "24-bit (8-bit per pixel)"
            elif new_value == 2:
                new_value = "30-bit (10-bit per pixel)"
            elif new_value == 3:
                new_value = "36-bit (12-bit per pixel)"
            elif new_value == 4:
                new_value = "48-bit (16-bit per pixel)"
            self.updateDeviceState(device, state, new_value)

            # Video Input Color Space
            state = "videoInputColorSpace"
            new_value = int(data[6:7])
            if new_value == 0:
                new_value = ""
            elif new_value == 1:
                new_value = "Standard"
            elif new_value == 2:
                new_value = "xv.Color YCC 601"
            elif new_value == 3:
                new_value = "xv.Color YCC 709"
            elif new_value == 4:
                new_value = "sYCC"
            elif new_value == 5:
                new_value = "Adobe YCC 601"
            elif new_value == 6:
                new_value = "Adobe RGB"
            self.updateDeviceState(device, state, new_value)

            # Video Output Resolution
            state = "videoOutputResolution"
            new_value = VIDEO_RESOLUTIONS[data[7:9]]
            self.updateDeviceState(device, state, new_value)

            # Video Output Aspect Ratio
            state = "videoOutputAspect"
            new_value = int(data[9:10])
            if new_value == 0:
                new_value = ""
            elif new_value == 1:
                new_value = "4:3"
            elif new_value == 2:
                new_value = "16:9"
            elif new_value == 3:
                new_value = "14:9"
            self.updateDeviceState(device, state, new_value)

            # Video Output Color Format
            state = "videoOutputColorFormat"
            new_value = int(data[10:11])
            if new_value == 0:
                new_value = ""
            elif new_value == 1:
                new_value = "RGB Limited"
            elif new_value == 2:
                new_value = "RGB Full"
            elif new_value == 3:
                new_value = "YCbCr 4:4:4"
            elif new_value == 4:
                new_value = "YCbCr 4:2:2"
            self.updateDeviceState(device, state, new_value)

            # Video Output Bit Depth
            state = "videoOutputBitDepth"
            new_value = int(data[11:12])
            if new_value == 0:
                new_value = ""
            elif new_value == 1:
                new_value = "24-bit (8-bit per pixel)"
            elif new_value == 2:
                new_value = "30-bit (10-bit per pixel)"
            elif new_value == 3:
                new_value = "36-bit (12-bit per pixel)"
            elif new_value == 4:
                new_value = "48-bit (16-bit per pixel)"
            self.updateDeviceState(device, state, new_value)

            # Video Output Color Space
            state = "videoOutputColorSpace"
            new_value = int(data[12:13])
            if new_value == 0:
                new_value = ""
            elif new_value == 1:
                new_value = "Standard"
            elif new_value == 2:
                new_value = "xv.Color YCC 601"
            elif new_value == 3:
                new_value = "xv.Color YCC 709"
            elif new_value == 4:
                new_value = "sYCC"
            elif new_value == 5:
                new_value = "Adobe YCC 601"
            elif new_value == 6:
                new_value = "Adobe RGB"
            self.updateDeviceState(device, state, new_value)

            # Monitor Recommended Resolution (HDMI 1)
            state = "monitorRecommendedResolution"
            new_value = VIDEO_RESOLUTIONS[data[13:15]]
            self.updateDeviceState(device, state, new_value)

            # Monitor Bit Depth Support
            state = "monitorBitDepth"
            new_value = int(data[15:16])
            if new_value == 0:
                new_value = ""
            elif new_value == 1:
                new_value = "24-bit (8-bit per pixel)"
            elif new_value == 2:
                new_value = "30-bit (10-bit per pixel)"
            elif new_value == 3:
                new_value = "36-bit (12-bit per pixel)"
            elif new_value == 4:
                new_value = "48-bit (16-bit per pixel)"
            self.updateDeviceState(device, state, new_value)

            # Monitor Supported Color Spaces (HDMI 1)
            state = "monitorColorSpaces"
            new_value = ""
            color_spaces = data[16:21]
            if color_spaces[0:1] == "1":
                new_value += "xv.Color YCC 601"
            if color_spaces[1:2] == "1":
                if len(new_value) > 0:
                    new_value += ", "
                new_value += "xv.Color YCC 709"
            if color_spaces[2:3] == "1":
                if len(new_value) > 0:
                    new_value += ", "
                new_value += "xYCC"
            if color_spaces[3:4] == "1":
                if len(new_value) > 0:
                    new_value += ", "
                new_value += "Adobe YCC 601"
            if color_spaces[4:5] == "1":
                if len(new_value) > 0:
                    new_value += ", "
                new_value += "Adobe RGB"
            self.updateDeviceState(device, state, new_value)

            result = "video input/output information updated"

        else:
            # Unrecognized response received.
            self.debugLog(f"Unrecognized response received from {device.name}: {response}")
            new_value = "unknown"

        get_status_update = False  # Should we perform a full status update?

        # Only update the device if the state is not blank.
        if state != "":
            # If this is a zone power state change to True and the current zone power state is False, get more status
            # information.
            if (state == "zone1power" and new_value and not device.states['zone1power']) or (
                    state == "zone2power" and new_value and not device.states['zone2power']):
                get_status_update = True

            # Update the state on the server.
            self.updateDeviceState(device, state, new_value)

        #
        # CHECK IF ADDITIONAL PROCESSING IS NEEDED
        #

        # If this is a zone source input change, request additional information.
        if state == "zone1source":
            # Get the specified input source name (just in case the user changed the input name since the last full
            # status update).
            self.sendCommand(device, f"?RGB{response[2:]}")
            # Audio Status.
            self.getAudioInOutStatus(device)
            # If this is an input change to the Tuner, get the station preset info.
            if response == "FN02":
                self.getTunerPresetStatus(device)
            else:
                # Since zone 1 is not using the Tuner, as long as zone 2 isn't either, let's clear the Tuner statuses
                # in the device.
                if device.states['zone2source'] != 2:
                    self.debugLog("processResponse: Neither zone is using the tuner. Clearing frequency info.")
                    self.updateDeviceState(device, 'tunerFrequency', 0)
                    self.updateDeviceState(device, 'tunerFrequencyText', "")
                    self.updateDeviceState(device, 'tunerPreset', "")
                    self.updateDeviceState(device, 'tunerBand', "")

        elif state == "zone2source":
            # Get the specified input source name (just in case the user changed the input name since the last full
            # status update).
            self.sendCommand(device, f"?RGB{response[3:]}")
            # Audio Status.
            self.getAudioInOutStatus(device)
            # If this is an input change to the Tuner, get the band, frequency, and preset info.
            if response == "Z2F02":
                self.getTunerPresetStatus(device)
            else:
                # Since zone 2 is not using the Tuner, as long as zone 1 isn't either, let's clear the Tuner statuses
                # in the device.
                if device.states['zone1source'] != 2:
                    self.debugLog("processResponse: Neither zone is using the tuner. Clearing frequency info.")
                    self.updateDeviceState(device, 'tunerFrequency', 0)
                    self.updateDeviceState(device, 'tunerFrequencyText', "")
                    self.updateDeviceState(device, 'tunerPreset', "")
                    self.updateDeviceState(device, 'tunerBand', "")

        elif state == "tunerPreset":
            # Tuner preset was changed. Get the new frequency.
            self.getTunerFrequency(device)

        elif state == "mcaccMemory":
            # MCACC Memory change. Set the mcaccMemory#label value.
            # TODO: 'mcaccName' might be referenced before assignment
            self.updateDeviceState(device, 'mcaccMemoryName', mcacc_name)

        elif state == "tunerFrequency":
            # Also set the tunerFrequencyText.
            # TODO: 'frequencyText' might be referenced before assignment
            self.updateDeviceState(device, 'tunerFrequencyText', frequency_text)

        # If both zones are off, clear some states that should have no value when the unit is off.
        if not device.states['zone1power'] and not device.states['zone2power']:
            self.updateDeviceState(device, "audioInputFormat", "")
            self.updateDeviceState(device, "audioInputFrequency", 0)
            self.updateDeviceState(device, "inputChannels", "")
            self.updateDeviceState(device, "outputChannels", "")
            self.updateDeviceState(device, "monitorBitDepth", "")
            self.updateDeviceState(device, "monitorColorSpaces", "")
            self.updateDeviceState(device, "monitorRecommendedResolution", "")
            self.updateDeviceState(device, "signalSource", "")
            self.updateDeviceState(device, "sleepMode", False)
            self.updateDeviceState(device, "sleepTime", 0)
            self.updateDeviceState(device, "tunerBand", "")
            self.updateDeviceState(device, "tunerFrequency", 0)
            self.updateDeviceState(device, "tunerFrequencyText", "")
            self.updateDeviceState(device, "tunerPreset", "")
            self.updateDeviceState(device, "videoInputAspect", "")
            self.updateDeviceState(device, "videoInputBitDepth", "")
            self.updateDeviceState(device, "videoInputColorFormat", "")
            self.updateDeviceState(device, "videoInputColorSpace", "")
            self.updateDeviceState(device, "videoInputResolution", "")
            self.updateDeviceState(device, "videoInputTerminal", "")
            self.updateDeviceState(device, "videoOutputAspect", "")
            self.updateDeviceState(device, "videoOutputBitDepth", "")
            self.updateDeviceState(device, "videoOutputColorFormat", "")
            self.updateDeviceState(device, "videoOutputColorSpace", "")
            self.updateDeviceState(device, "videoOutputResolution", "")

        # Now get the additional status info if needed.
        if get_status_update:
            self.getReceiverStatus(device)

        return result

    #########################################
    # Information Gathering Methods
    #########################################
    #
    # Current Display Content
    #
    def getDisplayContent(self, device):
        """
        Placeholder - fixme
        :param device:
        :return:
        """
        self.debugLog(f"getDisplayContent: Getting {device.name} display content.")

        # Get th device type. Future versions of this plugin will support other receiver models.
        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            self.sendCommand(device, "?FL")  # Display Content Query.
            self.sleep(0.1)  # Wait for responses to be processed.

    #
    # Power Status
    #
    def getPowerStatus(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getPowerStatus: Getting {device.name} power status.")

        # Get th device type. Future versions of this plugin will support other receiver models.
        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            self.sendCommand(device, "?P")  # Power Query (Zone 1).
            self.sleep(0.1)  # Wait for responses to be processed.
            self.sendCommand(device, "?AP")  # Power Query (Zone 2).
            self.sleep(0.1)

            # It's important that we get the result of this status request before proceeding.
            response = self.readData(device)
            response = response.rstrip("\r\n")
            for response_line in response.splitlines():
                result = self.processResponse(device, response_line)
                if result != "":
                    indigo.server.log(result, device.name)

    #
    # Input Source Names
    #
    def getInputSourceNames(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getInputSourceNames: Getting {device.name} input source names.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            # Get the names of all the input sources.
            for the_number, the_name in SOURCE_NAMES.items():
                # Only ask for information on sources recognized by the device type.
                #   VSX-1021-K
                # if dev_type is "vsk1021k": fixme
                if dev_type == "vsk1021k":
                    if the_number not in VSX1021k_SOURCE_MASK:
                        self.sendCommand(device, f"?RGB{the_number}")
                        self.sleep(0.1)  # Wait for responses to be processed.
                #   VSX-1022-K
                # if dev_type is "vsk1022k": fixme
                if dev_type == "vsk1022k":
                    if the_number not in VSX1022K_SOURCE_MASK:
                        self.sendCommand(device, f"?RGB{the_number}")
                        self.sleep(0.1)  # Wait for responses to be processed.
                #   VSX-1122-K
                # if dev_type is "vsk1122k": fixme
                if dev_type == "vsk1122k":
                    if the_number not in VSX1122K_SOURCE_MASK:
                        self.sendCommand(device, f"?RGB{the_number}")
                        self.sleep(0.1)  # Wait for responses to be processed.
                #   VSX-1123-K
                # if dev_type is "vsk1123k": fixme
                if dev_type == "vsk1123k":
                    if the_number not in VSX1123K_SOURCE_MASK:
                        self.sendCommand(device, f"?RGB{the_number}")
                        self.sleep(0.1)  # Wait for responses to be processed.
                #   SC-75
                # if dev_type is "sc75": fixme
                if dev_type == "sc75":
                    if the_number not in SC75_SOURCE_MASK:
                        self.sendCommand(device, f"?RGB{the_number}")
                        self.sleep(0.1)  # Wait for responses to be processed.

    #
    # Tuner Preset Names
    #
    def getTunerPresetNames(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getTunerPresetNames: Getting {device.name} tuner preset station names.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            self.sendCommand(device, "?TQ")  # Tuner Preset label query.
            self.sleep(0.2)

    #
    # Tuner Band and Frequency
    #
    def getTunerFrequency(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getTunerFrequency: Getting {device.name} tuner band and frequency.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            self.sendCommand(device, "?FR")
            self.sleep(0.1)

    #
    # Tuner Preset Status
    #
    def getTunerPresetStatus(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getTunerPresetStatus: Getting {device.name} tuner preset status.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            self.sendCommand(device, "?PR")
            self.sleep(0.1)

    #
    # Volume Status (Zones 1 and 2)
    #
    def getVolumeStatus(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getVolumeStatus: Getting {device.name} volume status.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            self.sendCommand(device, "?V")  # Volume Query (Zone 1)
            self.sleep(0.1)
            self.sendCommand(device, "?ZV")  # Volume Query (Zone 2)
            self.sleep(0.1)

    #
    # Mute Status (Zones 1 and 2)
    #
    def getMuteStatus(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getMuteStatus: Getting {device.name} mute status.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            self.sendCommand(device, "?M")  # Mute Query (Zone 1)
            self.sleep(0.1)
            self.sendCommand(device, "?Z2M")  # Mute Query (Zone 2)
            self.sleep(0.1)

    #
    # Input Source Status (Zones 1 and 2)
    #
    def getInputSourceStatus(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getInputSourceStatus: Getting {device.name} input source status.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            self.sendCommand(device, "?F")  # Input Source Query (Zone 1)
            self.sleep(0.1)
            self.sendCommand(device, "?ZS")  # Input Source Query (Zone 2)
            self.sleep(0.1)

    #
    # Channel Volume Levels
    #
    def getChannelVolumeLevels(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getChannelVolumeLevels: Getting {device.name} individual channel volume levels.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            for the_channel, the_state in CHANNEL_VOLUMES.items():
                self.sendCommand(device, f"?{the_channel}CLV")
                self.sleep(0.1)

    #
    # System Setup Status
    #
    def getSystemSetupStatus(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getSystemSetupStatus: Getting {device.name} system settings.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            self.sendCommand(device, "?SPK")  # Amp speaker setting.
            self.sleep(0.1)
            self.sendCommand(device, "?PKL")  # Panel Key Lock status.
            self.sleep(0.1)
            self.sendCommand(device, "?RML")  # Remote Lock status.
            self.sleep(0.1)
            self.sendCommand(device, "?SSA")  # Operating Mode status.
            self.sleep(0.1)
            self.sendCommand(device, "?SSE")  # OSD Language status.
            self.sleep(0.1)
            self.sendCommand(device, "?SSF")  # Speaker System status.
            self.sleep(0.1)
            self.sendCommand(device, "?SAB")  # Sleep timer time remaining.
            self.sleep(0.1)

    #
    # Audio DSP Settings
    #
    def getAudioDspSettings(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getAudioDspSettings: Getting {device.name} audio DSP settings.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            self.sendCommand(device, "?TO")  # Tone Control status.
            self.sleep(0.1)
            self.sendCommand(device, "?BA")  # Bass Tone Control level.
            self.sleep(0.1)
            self.sendCommand(device, "?TR")  # Treble Tone Control level.
            self.sleep(0.1)
            self.sendCommand(device, "?MC")  # MCACC Memory setting.
            self.sleep(0.1)
            self.sendCommand(device, "?IS")  # Phase Control setting.
            self.sleep(0.1)
            self.sendCommand(device, "?PQ")  # PQLS Auto status.
            self.sleep(0.1)
            self.sendCommand(device, "?VSB")  # Virtual Surround Back setting.
            self.sleep(0.1)
            self.sendCommand(device, "?VHT")  # Virtual Height setting.
            self.sleep(0.1)
            self.sendCommand(device, "?HA")  # HDMI Audio pass-through setting.
            self.sleep(0.1)
            self.sendCommand(device, "?L")  # Playback Listening Mode.
            self.sleep(0.1)
            self.sendCommand(device, "?S")  # Surround Listening Mode.
            self.sleep(0.1)
            self.sendCommand(device, "?SDA")  # Signal Source selection status.
            self.sleep(0.1)
            self.sendCommand(device, "?SDB")  # Analog Input Attenuator status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATA")  # Sound Retriever status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATC")  # Equalizer status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATD")  # Standing Wave compensation status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATE")  # Phase Control Plus delay (ms).
            self.sleep(0.1)
            self.sendCommand(device, "?ATF")  # Sound Delay (sample frames).
            self.sleep(0.1)
            self.sendCommand(device, "?ATG")  # Digital Noise Reduction status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATH")  # Dialog Enhancement status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATJ")  # Dual Mono processing status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATK")  # Fixed PCM processing status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATL")  # Dynamic Range Compression mode.
            self.sleep(0.1)
            self.sendCommand(device, "?ATM")  # LFE Attenuation status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATN")  # SACD Gain status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATO")  # Auto Sound Delay status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATP")  # Dolby Pro Logic II Music Center Width status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATQ")  # Dolby Pro Logic II Music Panorama status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATR")  # Dolby Pro Logic II Music Dimension status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATS")  # Neo:6 Center Image status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATT")  # Effect level status.
            self.sleep(0.1)
            self.sendCommand(device, "?ATU")  # Dolby Pro Logic IIz Height Gain status.
            self.sleep(0.1)

    #
    # Video DSP Settings
    #
    def getVideoDspSettings(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getVideoDspSettings: Getting {device.name} video DSP settings.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            self.sendCommand(device, "?VTB")  # Video Converter status.
            self.sleep(0.1)
            self.sendCommand(device, "?VTC")  # Resolution Preferences status.
            self.sleep(0.1)
            self.sendCommand(device, "?VTD")  # Pure Cinema Mode.
            self.sleep(0.1)
            self.sendCommand(device, "?VTE")  # Progressive Motion Quality.
            self.sleep(0.1)
            self.sendCommand(device, "?VTG")  # Advanced Video Adjustment mode.
            self.sleep(0.1)
            self.sendCommand(device, "?VTH")  # YNR amount.
            self.sleep(0.1)
            self.sendCommand(device, "?VTL")  # Video Detail adjustment.
            self.sleep(0.1)

    #
    # Audio I/O Status
    #
    def getAudioInOutStatus(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getAudioInOutStatus: Getting {device.name} audio I/O status.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            # Since this method is called just after an input source change, wait a bit for the system to finalize the
            # change.
            self.sleep(1)
            self.sendCommand(device, "?AST")  # Audio Status.

    #
    # Video I/O Status
    #
    def getVideoInOutStatus(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getVideoInOutStatus: Getting {device.name} video I/O status.")

        dev_type = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if dev_type != "virtualVolume":
            # Since this method is called just after an input source change, wait half a second for the system to
            # finalize the change.
            self.sleep(0.5)
            self.sendCommand(device, "?VST")  # Video Status.

    #
    # All Status Information
    #
    def getReceiverStatus(self, device):
        """
        Placeholder - fixme

        :param device:
        :return:
        """
        self.debugLog(f"getReceiverStatus: Getting all information for{device.name}.")
        self.debugLog(f"getReceiverStatus: List of device IDs being updated: {self.devicesBeingUpdated}")

        # Make sure we aren't already updating this device.
        if device.id not in self.devicesBeingUpdated:
            # Add it to the list of devices being updated.
            self.devicesBeingUpdated.append(device.id)

            # Now gather all receiver data.

            dev_type = device.deviceTypeId

            # Indicate in the log that we're going to be gathering all kinds of information.
            indigo.server.log("Gathering receiver system information.", device.name)

            # Make sure it's not a virtual volume device.
            if dev_type != "virtualVolume":
                # Get this information regardless of whether the receiver is on or off.
                self.getDisplayContent(device)  # Display Content Query.
                self.getPowerStatus(device)  # Power Status.
                self.getInputSourceNames(device)  # Input Source Names.

                # Information related to both zones...
                if device.states['zone1power'] or device.states['zone2power']:
                    self.getVolumeStatus(device)  # Volume Status.
                    self.getMuteStatus(device)  # Mute Status
                    self.getInputSourceStatus(device)  # Input Source Status.
                    self.getAudioInOutStatus(device)  # Audio I/O Status.
                    self.getVideoInOutStatus(device)  # Video I/O Status.
                    self.getTunerPresetNames(device)  # Tuner Preset Names.
                    self.getTunerPresetStatus(device)  # Tuner Preset Status.
                    # self.getTunerFrequency(device)  # Tuner Band and Frequency.
                    self.getSystemSetupStatus(device)  # System Setup Status.

                # Information relevant only to the main zone (1)...
                if device.states['zone1power']:
                    self.getAudioDspSettings(device)  # Audio DSP Settings.
                    self.getVideoDspSettings(device)  # Video DSP Settings.
                    self.getChannelVolumeLevels(device)  # Channel Volume Levels.

            self.sleep(0.5)  # Wait a bit for processing.

            # Now remove the device from the list of devices being updated.
            self.devicesBeingUpdated.remove(device.id)

    #########################################
    # ACTION METHODS
    #########################################
    #
    # Power On (Zone 1)
    #
    def zone1powerOn(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Turn on power (zone 1) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Turning on power (zone 1) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # For VSX-1021-K
        if device.deviceTypeId == "vsx1021k":
            command = "PO"  # Power On
            self.sendCommand(device, command)
            self.sleep(0.1)

        # For VSX-1022-K and later.
        if device.deviceTypeId in ["vsx1022k", "vsx1122k", "vsx1123k", "sc75"]:
            # Delete extra lines if valid - fixme
            # if (device.deviceTypeId == "vsx1022k"
            #         or device.deviceTypeId == "vsx1122k"
            #         or device.deviceTypeId == "vsx1123k"
            #         or device.deviceTypeId == "sc75"):
            command = "PO"  # Power On
            self.sendCommand(device, command)
            self.sleep(0.1)
            # Pioneer suggests that for 2012 and later models, this command be sent twice.
            command = "PO"  # Power On
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Power Off (Zone 1)
    #
    def zone1powerOff(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Turn off power (zone 1) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Turning off power (zone 1) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "PF"  # Power Off
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Power Toggle (Zone 1)
    #
    def zone1powerToggle(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Toggle power (zone 1) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Toggling power (zone 1) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "?P"  # Query power status first to wake up 2012+ receiver CPUs.
            self.sendCommand(device, command)
            self.sleep(0.1)
            command = "PZ"  # Power Toggle
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Volume Up 0.5 dB (Zone 1)
    #
    def zone1volumeUp(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Increment volume (zone 1) by 0.5 dB for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Volume Up 0.5 dB (zone 1) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "VU"  # Volume Up
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Volume Down 0.5 dB (Zone 1)
    #
    def zone1volumeDown(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Decrement volume (zone 1) by 0.5 dB for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Volume Down 0.5 dB (zone 1) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "VD"  # Volume Down
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Set Volume in dB (Zone 1)
    #
    def zone1setVolume(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Set the volume (zone 1) for the device..
        device = indigo.devices[action.deviceId]

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        new_value = float(action.props.get('volume', "-90"))
        if new_value == -90.0:  # No value was provided.
            self.errorLog(f"No Zone 1 Volume was specified in the action for \"{device.name}\"")
            return False

        self.debugLog(f"Set volume to {new_value} dB (zone 1) for {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            new_value = 161 + int(new_value / 0.5)
            if new_value < 10:
                new_value = f"00{new_value}"
            elif new_value < 100:
                new_value = f"0{new_value}"
            else:
                new_value = f"{new_value}"
            command = new_value + "VL"  # Set Volume.
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Mute On (Zone 1)
    #
    def zone1muteOn(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Turn on mute (zone 1) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Turning on mute (zone 1) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device.")
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "MO"  # Mute On
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Mute Off (Zone 1)
    #
    def zone1muteOff(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Turn off (zone 1) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Turning off mute (zone 1) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "MF"  # Mute Off
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Mute Toggle (Zone 1)
    #
    def zone1muteToggle(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Toggle mute (zone 1) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Toggling mute (zone 1) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "MZ"  # Toggle Mute
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Select Next Source (Zone 1)
    #
    def zone1sourceUp(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Go to the next available input source.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Select Next Source (zone 1) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "FU"  # Source Up (Next)
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Select Previous Source (Zone 1)
    #
    def zone1sourceDown(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Go to the previous available input source.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Select Previous Source (zone 1) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "FD"  # Source Down (Previous)
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Set Input Source (Zone 1)
    #
    def zone1setSource(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Set the input source to something specific.
        device = indigo.devices[action.deviceId]

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        new_value = action.props.get('source', False)
        self.debugLog(f"zone1setSource called: source: {new_value}, device: {device.name}")

        if not new_value:
            self.errorLog(f"No source selected for \"{device.name}\"")
            return False
        self.debugLog(f"(Source name: {SOURCE_NAMES[str(new_value)]}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = new_value + "FN"  # Set Source.
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Power On (Zone 2)
    #
    def zone2powerOn(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Turn on power (zone 2) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"zone2powerOn: Turning on power (zone 2) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "APO"  # Power On
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Power Off (Zone 2)
    #
    def zone2powerOff(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Turn off power (zone 2) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"zone2powerOff: Turning off power (zone 2) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "APF"  # Power Off
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Power Toggle (Zone 2)
    #
    def zone2powerToggle(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Toggle power (zone 2) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"zone2powerToggle: Toggling power (zone 2) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "APZ"  # Power Toggle
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Volume Up 1 dB (Zone 2)
    #
    def zone2volumeUp(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Increment volume (zone 2) by 1 dB for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Volume Up 1 dB (zone 2) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            # If the current speaker system setup is not "A + Zone 2", zone mute and volume commands will be ignored.
            if device.states['speakerSystem'] == "A + Zone 2":
                command = "ZU"  # Volume Up
                self.sendCommand(device, command)
                self.sleep(0.1)
            else:
                self.errorLog(
                    f"Zone 2 mute and volume level control not supported with the {device.states['speakerSystem']} "
                    f"speaker system layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > "
                    f"Speaker System setup menu."
                )

    #
    # Volume Down 1 dB (Zone 2)
    #
    def zone2volumeDown(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Decrement volume (zone 2) by 1 dB for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Volume Down 1 dB (zone 2) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            # If the current speaker system setup is not "A + Zone 2", zone mute and volume commands will be ignored.
            if device.states['speakerSystem'] == "A + Zone 2":
                command = "ZD"  # Volume Down
                self.sendCommand(device, command)
                self.sleep(0.1)
            else:
                self.errorLog(
                    f"Zone 2 mute and volume level control not supported with the {device.states['speakerSystem']} "
                    f"speaker system layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > "
                    f"Speaker System setup menu."
                )

    #
    # Set Volume in dB (Zone 2)
    #
    def zone2setVolume(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Set the volume (zone 2) for the device..
        device = indigo.devices[action.deviceId]

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        new_value = int(action.props.get('volume', "-90"))
        if new_value == -90:
            self.errorLog(f"No Zone 2 Volume was specified in action for \"{device.name}\"")
            return False

        self.debugLog(f"Set volume to {new_value} dB (zone 2) for {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            # If the current speaker system setup is not "A + Zone 2", zone mute and volume commands will be ignored.
            if device.states['speakerSystem'] == "A + Zone 2":
                new_value = 81 + int(new_value)
                if new_value < 10:
                    new_value = f"0{new_value}"
                else:
                    new_value = str(new_value)
                command = new_value + "ZV"  # Set Volume.
                self.sendCommand(device, command)
                self.sleep(0.1)
            else:
                self.errorLog(
                    f"Zone 2 mute and volume level control not supported with the {device.states['speakerSystem']} "
                    f"speaker system layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > "
                    f"Speaker System setup menu."
                )

    #
    # Mute On (Zone 2)
    #
    def zone2muteOn(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Turn on mute (zone 2) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Turning on mute (zone 2) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            # If the current speaker system setup is not "A + Zone 2",
            #   zone mute and volume commands will be ignored.
            if device.states['speakerSystem'] == "A + Zone 2":
                command = "Z2MO"  # Mute On
                self.sendCommand(device, command)
                self.sleep(0.1)
            else:
                self.errorLog(
                    f"Zone 2 mute and volume level control not supported with the {device.states['speakerSystem']} "
                    f"speaker system layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > "
                    f"Speaker System setup menu."
                )

    #
    # Mute Off (Zone 2)
    #
    def zone2muteOff(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Turn off (zone 2) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Turning off mute (zone 2) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            # If the current speaker system setup is not "A + Zone 2", zone mute and volume commands will be ignored.
            if device.states['speakerSystem'] == "A + Zone 2":
                command = "Z2MF"  # Mute Off
                self.sendCommand(device, command)
                self.sleep(0.1)
            else:
                self.errorLog(
                    f"Zone 2 mute and volume level control not supported with the {device.states['speakerSystem']} "
                    f"speaker system layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > "
                    f"Speaker System setup menu."
                )

    #
    # Mute Toggle (Zone 2)
    #
    def zone2muteToggle(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Toggle mute (zone 1) for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Toggling mute (zone 2) for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            # If the current speaker system setup is not "A + Zone 2", zone mute and volume commands will be ignored.
            if device.states['speakerSystem'] == "A + Zone 2":
                command = "Z2MZ"  # Toggle Mute
                self.sendCommand(device, command)
                self.sleep(0.1)
            else:
                self.errorLog(
                    f"Zone 2 mute and volume level control not supported with the {device.states['speakerSystem']} "
                    f"speaker system layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > "
                    f"Speaker System setup menu."
                )

    #
    # Set Input Source (Zone 2)
    #
    def zone2setSource(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Set the input source to something specific.
        device = indigo.devices[action.deviceId]
        self.debugLog("zone2setSource called.")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        new_value = action.props['source']
        self.debugLog(f"Set input source to {SOURCE_NAMES[str(new_value)]} (zone 2) for {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = new_value + "ZS"  # Set Source.
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Select Tuner Preset
    #
    def tunerPresetSelect(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Set the tuner preset to the specified preset.
        device = indigo.devices[action.deviceId]

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        new_value = action.props.get('tunerPreset', False)
        if not new_value:
            self.errorLog(f"No Tuner preset specified in action for \"{device.name}\"")
            return False

        # Define the tuner preset device property name based on the menu selection.
        prop_name = f"tunerPreset{new_value.replace('0', '')}label"
        self.debugLog(f"tunerPresetSelect: Set tuner preset to {device.pluginProps[prop_name]} for {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            if (device.states['zone1source'] == 2) or (device.states['zone2source'] == 2):
                command = new_value + "PR"  # Select Tuner Preset.
                self.sendCommand(device, command)
                self.sleep(0.1)
            else:
                # Neither of zones 1 or 2 are using the Tuner. Cannot set the preset.
                self.errorLog(
                    f"Cannot set tuner preset. The {device.name} zone 1 or 2 input source must be set to the tuner in "
                    f"order to set the tuner preset."
                )

    #
    # Set Tuner Frequency
    #
    def tunerFrequencySet(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Set the tuner band and frequency to the specified values.
        device = indigo.devices[action.deviceId]

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        frequency = action.props.get('frequency', False)
        band = action.props.get('band', False)
        if not band or not frequency:
            if not band:
                self.errorLog(f"A tuner Band must be selected for \"{device.name}\"")
            if not frequency:
                self.errorLog(f"A tuner Frequency must be selected for \"{device.name}\"")
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            # Make sure we can actually change the frequency directly.
            if not device.states['zone1power']:
                # Zone 1 power is off.  Can't make any changes.
                self.errorLog(f"Cannot set tuner frequency. {device.name} zone 1 is currently turned off.")
            elif device.states['zone1source'] != 2:
                # Zone 1 source is not Tuner.  Cannot set frequency directly.
                self.errorLog(
                    f"Cannot set tuner frequency directly. {device.name} zone 1 input source must be set to the tuner "
                    f"in order to set the tuner frequency directly."
                )
            else:
                band_command = ""
                # Zone 1 power is on and input source is source 2. Send the commands.
                self.debugLog(f"tunerFrequencySet: Set tuner frequency to {frequency} {band} for {device.name}")
                # Define band change command and correct frequency character sequence.
                if band == "FM":
                    band_command = "00TN"  # Command to set band to AM.
                    frequency = frequency.replace(".", "")  # Remove the decimal.
                    if len(frequency) < 3:
                        frequency = f"{frequency}00"  # Add 2 trailing zeros.
                    elif len(frequency) < 4:
                        frequency = f"{frequency}0"  # Add 1 trailing zero.
                    # Add another trailing zero if the frequency was 100 or higher.
                    if frequency.startswith("1"):
                        frequency = f"{frequency}0"
                elif band == "AM":
                    band_command = "01TN"  # Command to set band to FM.
                    if len(frequency) < 4:
                        frequency = f"0{frequency}"  # Add a leading zero.

                # Start sending the command.
                self.sendCommand(device, band_command)  # Set the frequency band.
                self.sleep(0.1)  # Wait for the band to change.
                self.sendCommand(device, "TAC")  # Begin direct frequency entry.
                self.sleep(0.1)
                for the_char in frequency:
                    # Send each frequency number character individually.
                    self.sendCommand(device, the_char + "TP")
                    self.sleep(0.1)
                # Clear the device's preset state since entering a frequency directly.
                self.updateDeviceState(device, 'tunerPreset', "")

    #
    # Next Stereo Listening Mode
    #
    def listeningModeStereoNext(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Cycle through the next Stereo Listening Mode.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"listeningModeStereoNext: Select next Stereo Listening Mode on {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "0001SR"
            self.sendCommand(device, command)
            self.sleep(0.1)
            # Wait a bit and get an update on the actual listening mode.
            self.sendCommand(device, "?S")
            self.sleep(0.1)

    #
    # Next Auto Surround/Stream Direct Listening Mode
    #
    def listeningModeAutoSurroundNext(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Cycle through the next Auto Surround Listening Mode.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"listeningModeAutoSurroundNext: Select next Auto Surround Listening Mode on {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "0005SR"
            self.sendCommand(device, command)
            self.sleep(0.1)
            # Wait a bit and get an update on the actual listening mode.
            self.sendCommand(device, "?S")
            self.sleep(0.1)

    #
    # Next Advanced Surround Listening Mode
    #
    def listeningModeAdvancedSurroundNext(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Cycle through the next Advanced Surround Listening Mode.
        device = indigo.devices[action.deviceId]
        self.debugLog(
            f"listeningModeAdvancedSurroundNext: Select next Advanced Surround Listening Mode on {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = "0100SR"
            self.sendCommand(device, command)
            self.sleep(0.1)
            # Wait a bit and get an update on the actual listening mode.
            self.sendCommand(device, "?S")
            self.sleep(0.1)

    #
    # Select Listening Mode
    #
    def listeningModeSelect(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Set the Listening Mode setting to a specific setting.
        device = indigo.devices[action.deviceId]

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        command = action.props.get('listeningMode', False)
        if not command:
            self.errorLog(f"No Listening Mode selected in action for \"{device.name}\"")
            return False

        self.debugLog(f"listeningModeSelect: Select Listening Mode \"{LISTENING_MODES[command]}\" on {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            # Make sure the listeningMode is valid.
            if LISTENING_MODES.get(command, None) is None:
                self.errorLog(f"Invalid listening mode ID \"{command}\" specified.")
                return

            # Add the proper characters to the listening mode ID to make it a valid command.
            command = f"{command}SR"
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Next MCACC Memory
    #
    def mcaccNext(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Select the next MCACC setting memory.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"mcaccNext called for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            mcacc_memory = device.states['mcaccMemory']
            mcacc_memory += 1
            if mcacc_memory > 6:
                mcacc_memory = 1
            command = f"{mcacc_memory}MC"
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Previous MCACC Memory
    #
    def mcaccPrevious(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Select the previous MCACC setting memory.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"mcaccPrevious called for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            mcacc_memory = device.states['mcaccMemory']
            mcacc_memory -= 1
            if mcacc_memory < 1:
                mcacc_memory = 6
            command = f"{mcacc_memory}MC"
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Select MCACC Memory
    #
    def mcaccSelect(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Set the MCACC Memory setting to something specific.
        device = indigo.devices[action.deviceId]

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        command = action.props.get('mcaccMemory', False)
        if not command:
            self.errorLog(f"No MCACC Memory selected in action for \"{device.name}\"")
            return False

        self.debugLog(f"mcaccSelect: Recall MCACC Memory number {command[0:1]} on {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Send Remote Control Button Press
    #
    def remoteButtonPress(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Send a remote control button press to the receiver.
        device = indigo.devices[action.deviceId]
        error = False  # Used to track if there was an error or not.

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        source = device.states['zone1source']
        command = action.props.get('remoteButton', False)
        if not command:
            self.errorLog(f"No Remote Button was specified in action for \"{device.name}\"")
            return False

        self.debugLog(f"remoteButtonPress called: command: {command} for {device.name}")

        # For VSX-1021-K
        if device.deviceTypeId == "vsx1021k":
            # Define the translation from submitted button command to correct source command. 02 - Tuner The below
            # button maps work on the first button press, but don't for subsequent presses. source2commandMap = {
            # 'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN", 'CRT':"CRT", 'STS':"06TN"}
            # The Pioneer VSX-1021-K Used to test this plugin exhibited a bug when using the "TFI" and "TFD" commands
            # where the receiver would completely mute the tuner even across power cycles. The tuner could only be
            # unmuted by pressing a tuner control button on the IR remote or on the receiver front panel.  For this
            # reason, the "TFI" and "TFD" tuner frequency increment/decrement commands have been omitted.
            source2command_map = {'CRI': "TPI", 'CLE': "TPD", 'CEN': "03TN", 'CRT': "04TN", 'STS': "06TN"}
            # 17 - iPod/USB The below button maps work on the first button press, but don't for subsequent presses.
            # source17commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN",
            # 'CRT':"CRT", 'STS':"09IP", '00IP':"00IP", '01IP':"01IP", '02IP':"02IP", '03IP':"03IP", '04IP':"04IP",
            # '07IP':"07IP", '08IP':"08IP", '19SI':"19IP"}
            source17command_map = {'CUP': "13IP", 'CDN': "14IP", 'CRI': "15IP", 'CLE': "16IP", 'CEN': "17IP",
                                   'CRT': "18IP", 'STS': "09IP", '00IP': "00IP", '01IP': "01IP", '02IP': "02IP",
                                   '03IP': "03IP", '04IP': "04IP", '07IP': "07IP", '08IP': "08IP", '19SI': "19IP"}
            # 26 - HMG (Home Media Gallery/Internet Radio) The below button maps work on the first button press,
            # but don't for subsequent presses. source26commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN",
            # 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN", 'CRT':"CRT", 'STS':"18NW", '00IP':"10NW", '01IP':"11NW",
            # '02IP':"20NW", '03IP':"12NW", '04IP':"12NW", '07IP':"34NW", '08IP':"35NW", '19SI':"36NW",
            # '00SI':"00NW", '01SI':"01NW", '02SI':"02NW", '03SI':"03NW", '04SI':"04NW", '05SI':"04NW",
            # '06SI':"05NW", '07SI':"07NW", '08SI':"08NW", '09SI':"09NW"}
            source26command_map = {'CUP': "26NW", 'CDN': "27NW", 'CRI': "28NW", 'CLE': "29NW", 'CEN': "30NW",
                                   'CRT': "31NW", 'STS': "18NW", '00IP': "10NW", '01IP': "11NW", '02IP': "20NW",
                                   '03IP': "12NW", '04IP': "12NW", '07IP': "34NW", '08IP': "35NW", '19SI': "36NW",
                                   '00SI': "00NW", '01SI': "01NW", '02SI': "02NW", '03SI': "03NW", '04SI': "04NW",
                                   '05SI': "04NW", '06SI': "05NW", '07SI': "07NW", '08SI': "08NW", '09SI': "09NW"}
            # 27 - Sirius The below button maps work on the first button press, but don't for subsequent presses.
            # source27commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN",
            # 'CRT':"CRT", 'STS':"14SI", '19SI':"19SI", '00SI':"00SI", '01SI':"01SI", '02SI':"02SI", '03SI':"03SI",
            # '04SI':"04SI", '05SI':"04SI", '06SI':"05SI", '07SI':"07SI", '08SI':"08SI", '09SI':"09SI"}
            source27command_map = {'CUP': "10SI", 'CDN': "11SI", 'CRI': "12SI", 'CLE': "13SI", 'CEN': "21SI",
                                   'CRT': "22SI", 'STS': "14SI", '19SI': "19SI", '00SI': "00SI", '01SI': "01SI",
                                   '02SI': "02SI", '03SI': "03SI", '04SI': "04SI", '05SI': "04SI", '06SI': "05SI",
                                   '07SI': "07SI", '08SI': "08SI", '09SI': "09SI"}
            # 33 - Adapter Port The below button maps work on the first button press, but don't for subsequent
            # presses. source33commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE",
            # 'CEN':"CEN", 'CRT':"CRT", '00IP':"10BT", '01IP':"11BT", '02IP':"12BT", '03IP':"13BT", '04IP':"14BT"}
            source33command_map = {'CRI': "23BT", 'CLE': "24BT", 'CEN': "25BT", 'CRT': "26BT", '00IP': "10BT",
                                   '01IP': "11BT", '02IP': "12BT", '03IP': "13BT", '04IP': "14BT"}
            # List of default cursor button commands to use if the above sources aren't the current input source.
            default_cursor_commands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']

            # Translate the command based on the current zone 1 input source.
            if source == 2:
                # See if the requested command is compatible with this input source.
                command = source2command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 17:
                command = source17command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 26:
                command = source26command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 27:
                command = source27command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 33:
                command = source33command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            else:
                # Current zone 1 input source is something other than the special ones above. Make sure the command
                # being sent is one of the standard commands.
                if command not in default_cursor_commands:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True

            # Send the command if no errors.
            if not error:
                self.sendCommand(device, command)
                self.sleep(0.1)

        # For VSX-1022-K
        if device.deviceTypeId == "vsx1022k":
            # Define the translation from submitted button command to correct source command. THIS HAS NOT BEEN UPDATED
            # FOR ALL VSX-1022-K SUPPORTED SOURCES.
            #
            # 02 - Tuner
            source2command_map = {'CUP': "TFI", 'CDN': "TFD", 'CRI': "TPI", 'CLE': "TPD", 'CEN': "03TN", 'CRT': "04TN",
                                  'STS': "06TN"}
            # 17 - iPod/USB
            source17command_map = {'CUP': "13IP", 'CDN': "14IP", 'CRI': "15IP", 'CLE': "16IP", 'CEN': "17IP",
                                   'CRT': "18IP", 'STS': "09IP", '00IP': "00IP", '01IP': "01IP", '02IP': "02IP",
                                   '03IP': "03IP", '04IP': "04IP", '07IP': "07IP", '08IP': "08IP", '19SI': "19IP"}
            # 26 - HMG (Home Media Gallery/Internet Radio)
            source26command_map = {'CUP': "26NW", 'CDN': "27NW", 'CRI': "28NW", 'CLE': "29NW", 'CEN': "30NW",
                                   'CRT': "31NW", 'STS': "18NW", '00IP': "10NW", '01IP': "11NW", '02IP': "20NW",
                                   '03IP': "12NW", '04IP': "12NW", '07IP': "34NW", '08IP': "35NW", '19SI': "36NW",
                                   '00SI': "00NW", '01SI': "01NW", '02SI': "02NW", '03SI': "03NW", '04SI': "04NW",
                                   '05SI': "04NW", '06SI': "05NW", '07SI': "07NW", '08SI': "08NW", '09SI': "09NW"}
            # 27 - Sirius
            source27command_map = {'CUP': "10SI", 'CDN': "11SI", 'CRI': "12SI", 'CLE': "13SI", 'CEN': "21SI",
                                   'CRT': "22SI", 'STS': "14SI", '19SI': "19SI", '00SI': "00SI", '01SI': "01SI",
                                   '02SI': "02SI", '03SI': "03SI", '04SI': "04SI", '05SI': "04SI", '06SI': "05SI",
                                   '07SI': "07SI", '08SI': "08SI", '09SI': "09SI"}
            # 33 - Adapter Port
            source33command_map = {'CRI': "23BT", 'CLE': "24BT", 'CEN': "25BT", 'CRT': "26BT", '00IP': "10BT",
                                   '01IP': "11BT", '02IP': "12BT", '03IP': "13BT", '04IP': "14BT"}
            # List of default cursor button commands to use if the above sources aren't the current input source.
            default_cursor_commands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']

            # Translate the command based on the current zone 1 input source.
            if source == 2:
                # See if the requested command is compatible with this input source.
                command = source2command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 17:
                command = source17command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 26:
                command = source26command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 27:
                command = source27command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 33:
                command = source33command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            else:
                # Current zone 1 input source is something other than the special ones above. Make sure the command
                # being sent is one of the standard commands.
                if command not in default_cursor_commands:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True

            # Send the command if no errors.
            if not error:
                self.sendCommand(device, command)
                self.sleep(0.1)

        # For VSX-1122-K
        if device.deviceTypeId == "vsx1122k":
            # Define the translation from submitted button command to correct source command. THIS HAS NOT BEEN UPDATED
            # FOR ALL VSX-1122-K SUPPORTED SOURCES.
            #
            # 02 - Tuner
            source2command_map = {'CUP': "TFI", 'CDN': "TFD", 'CRI': "TPI", 'CLE': "TPD", 'CEN': "03TN", 'CRT': "04TN",
                                  'STS': "06TN"}
            # 17 - iPod/USB
            source17command_map = {'CUP': "13IP", 'CDN': "14IP", 'CRI': "15IP", 'CLE': "16IP", 'CEN': "17IP",
                                   'CRT': "18IP", 'STS': "09IP", '00IP': "00IP", '01IP': "01IP", '02IP': "02IP",
                                   '03IP': "03IP", '04IP': "04IP", '07IP': "07IP", '08IP': "08IP", '19SI': "19IP"}
            # 26 - HMG (Home Media Gallery/Internet Radio)
            source26command_map = {'CUP': "26NW", 'CDN': "27NW", 'CRI': "28NW", 'CLE': "29NW", 'CEN': "30NW",
                                   'CRT': "31NW", 'STS': "18NW", '00IP': "10NW", '01IP': "11NW", '02IP': "20NW",
                                   '03IP': "12NW", '04IP': "12NW", '07IP': "34NW", '08IP': "35NW", '19SI': "36NW",
                                   '00SI': "00NW", '01SI': "01NW", '02SI': "02NW", '03SI': "03NW", '04SI': "04NW",
                                   '05SI': "04NW", '06SI': "05NW", '07SI': "07NW", '08SI': "08NW", '09SI': "09NW"}
            # 27 - Sirius
            source27command_map = {'CUP': "10SI", 'CDN': "11SI", 'CRI': "12SI", 'CLE': "13SI", 'CEN': "21SI",
                                   'CRT': "22SI", 'STS': "14SI", '19SI': "19SI", '00SI': "00SI", '01SI': "01SI",
                                   '02SI': "02SI", '03SI': "03SI", '04SI': "04SI", '05SI': "04SI", '06SI': "05SI",
                                   '07SI': "07SI", '08SI': "08SI", '09SI': "09SI"}
            # 33 - Adapter Port
            source33command_map = {'CRI': "23BT", 'CLE': "24BT", 'CEN': "25BT", 'CRT': "26BT", '00IP': "10BT",
                                   '01IP': "11BT", '02IP': "12BT", '03IP': "13BT", '04IP': "14BT"}
            # List of default cursor button commands to use if the above sources aren't the current input source.
            default_cursor_commands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']

            # Translate the command based on the current zone 1 input source.
            if source == 2:
                # See if the requested command is compatible with this input source.
                command = source2command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 17:
                command = source17command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 26:
                command = source26command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 27:
                command = source27command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 33:
                command = source33command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            else:
                # Current zone 1 input source is something other than the special ones above. Make sure the command
                # being sent is one of the standard commands.
                if command not in default_cursor_commands:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True

            # Send the command if no errors.
            if not error:
                self.sendCommand(device, command)
                self.sleep(0.1)

        # For VSX-1123-K
        if device.deviceTypeId == "vsx1123k":
            # Define the translation from submitted button command to correct source command. THIS HAS NOT BEEN UPDATED
            # FOR ALL VSX-1123-K SUPPORTED SOURCES.
            #
            # 02 - Tuner
            source2command_map = {'CUP': "TFI", 'CDN': "TFD", 'CRI': "TPI", 'CLE': "TPD", 'CEN': "03TN", 'CRT': "04TN",
                                  'STS': "06TN"}
            # 17 - iPod/USB
            source17command_map = {'CUP': "13IP", 'CDN': "14IP", 'CRI': "15IP", 'CLE': "16IP", 'CEN': "17IP",
                                   'CRT': "18IP", 'STS': "09IP", '00IP': "00IP", '01IP': "01IP", '02IP': "02IP",
                                   '03IP': "03IP", '04IP': "04IP", '07IP': "07IP", '08IP': "08IP", '19SI': "19IP"}
            # 26 - HMG (Home Media Gallery/Internet Radio)
            source26command_map = {'CUP': "26NW", 'CDN': "27NW", 'CRI': "28NW", 'CLE': "29NW", 'CEN': "30NW",
                                   'CRT': "31NW", 'STS': "18NW", '00IP': "10NW", '01IP': "11NW", '02IP': "20NW",
                                   '03IP': "12NW", '04IP': "12NW", '07IP': "34NW", '08IP': "35NW", '19SI': "36NW",
                                   '00SI': "00NW", '01SI': "01NW", '02SI': "02NW", '03SI': "03NW", '04SI': "04NW",
                                   '05SI': "04NW", '06SI': "05NW", '07SI': "07NW", '08SI': "08NW", '09SI': "09NW"}
            # 27 - Sirius
            source27command_map = {'CUP': "10SI", 'CDN': "11SI", 'CRI': "12SI", 'CLE': "13SI", 'CEN': "21SI",
                                   'CRT': "22SI", 'STS': "14SI", '19SI': "19SI", '00SI': "00SI", '01SI': "01SI",
                                   '02SI': "02SI", '03SI': "03SI", '04SI': "04SI", '05SI': "04SI", '06SI': "05SI",
                                   '07SI': "07SI", '08SI': "08SI", '09SI': "09SI"}
            # 33 - Adapter Port
            source33command_map = {'CRI': "23BT", 'CLE': "24BT", 'CEN': "25BT", 'CRT': "26BT", '00IP': "10BT",
                                   '01IP': "11BT", '02IP': "12BT", '03IP': "13BT", '04IP': "14BT"}
            # List of default cursor button commands to use if the above sources aren't the current input source.
            default_cursor_commands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']

            # Translate the command based on the current zone 1 input source.
            if source == 2:
                # See if the requested command is compatible with this input source.
                command = source2command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 17:
                command = source17command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 26:
                command = source26command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 27:
                command = source27command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 33:
                command = source33command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored.")
                    error = True
            else:
                # Current zone 1 input source is something other than the special ones above. Make sure the command
                # being sent is one of the standard commands.
                if command not in default_cursor_commands:
                    self.errorLog(
                        f"{device.name}: remote control button "
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the "
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True

        # For SC-75
        if device.deviceTypeId == "sc75":
            # Define the translation from submitted button command to correct source command. THIS HAS NOT BEEN UPDATED
            # FOR ALL SC-75 SUPPORTED SOURCES.
            #
            # 02 - Tuner
            source2command_map = {'CUP': "TFI", 'CDN': "TFD", 'CRI': "TPI", 'CLE': "TPD", 'CEN': "03TN", 'CRT': "04TN",
                                  'STS': "06TN"}
            # 17 - iPod/USB
            source17command_map = {'CUP': "13IP", 'CDN': "14IP", 'CRI': "15IP", 'CLE': "16IP", 'CEN': "17IP",
                                   'CRT': "18IP", 'STS': "09IP", '00IP': "00IP", '01IP': "01IP", '02IP': "02IP",
                                   '03IP': "03IP", '04IP': "04IP", '07IP': "07IP", '08IP': "08IP", '19SI': "19IP"}
            # 26 - HMG (Home Media Gallery/Internet Radio)
            source26command_map = {'CUP': "26NW", 'CDN': "27NW", 'CRI': "28NW", 'CLE': "29NW", 'CEN': "30NW",
                                   'CRT': "31NW", 'STS': "18NW", '00IP': "10NW", '01IP': "11NW", '02IP': "20NW",
                                   '03IP': "12NW", '04IP': "12NW", '07IP': "34NW", '08IP': "35NW", '19SI': "36NW",
                                   '00SI': "00NW", '01SI': "01NW", '02SI': "02NW", '03SI': "03NW", '04SI': "04NW",
                                   '05SI': "04NW", '06SI': "05NW", '07SI': "07NW", '08SI': "08NW", '09SI': "09NW"}
            # 33 - Adapter Port
            source33command_map = {'CRI': "23BT", 'CLE': "24BT", 'CEN': "25BT", 'CRT': "26BT", '00IP': "10BT",
                                   '01IP': "11BT", '02IP': "12BT", '03IP': "13BT", '04IP': "14BT"}
            # List of default cursor button commands to use if the above sources aren't the current input source.
            default_cursor_commands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']

            # Translate the command based on the current zone 1 input source.
            if source == 2:
                # See if the requested command is compatible with this input source.
                command = source2command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button "
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the "
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 17:
                command = source17command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button "
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the "
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 26:
                command = source26command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button "
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the "
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            # TODO: there doesn't appear to be a source '27commandMap' above.
            elif source == 27:
                command = source27command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button "
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the "
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 33:
                command = source33command_map.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button "
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the "
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            else:
                # Current zone 1 input source is something other than the special ones above. Make sure the command
                # being sent is one of the standard commands.
                if command not in default_cursor_commands:
                    self.errorLog(
                        f" {device.name}: remote control button "
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the "
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True

            # Send the command if no errors.
            if not error:
                self.sendCommand(device, command)
                self.sleep(0.1)

    #
    # Set Display Brightness
    #
    def setDisplayBrightness(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Set the front display brightness.
        device = indigo.devices[action.deviceId]

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        command = action.props.get('displayBrightness', False)
        if not command:
            self.errorLog(f"No Display Brightness setting was specified in action for \"{device.name}\"")
            return False

        self.debugLog(f"setDisplayBrightness called: command: {command} for {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Set Sleep Timer
    #
    def setSleepTimer(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Set the sleep timer minutes (or off).
        device = indigo.devices[action.deviceId]

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device.")
            return False

        command = action.props.get('sleepTime', False)
        if not command:
            self.errorLog(f"No Sleep Time was specified in action for \"{device.name}\"")
            return False

        self.debugLog(f"setSleepTimer called: command: {command} for {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Send Raw Command
    #
    def sendRawCommand(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Send a command directly to the receiver.
        device = indigo.devices[action.deviceId]

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        command = action.props.get('command', False)
        if not command:
            self.errorLog(f"No Command was specified in action for \"{device.name}\"")
            return False

        self.debugLog(f"sendRawCommand called: command: {command} for {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Refresh All States
    #
    def refreshAllStates(self, action):
        """
        Placeholder - fixme

        :param action:
        :return:
        """
        # Refresh all states for a device.
        device = indigo.devices[action.deviceId]
        self.debugLog(f"Refresh all states for {device.name}")

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return False

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            self.getReceiverStatus(device)

    ########################################
    # Virtual Level Controller
    #   (Class-Supported)
    ########################################
    def actionControlDimmerRelay(self, action, device):
        """
        Placeholder - fixme

        :param action:
        :param device:
        :return:
        """
        try:
            self.debugLog(
                f"actionControlDimmerRelay called for device {device.name}. action: {action}\n\ndevice: {device}"
            )
        except Exception as err:
            self.debugLog(
                f"actionControlDimmerRelay called for device {device.name}. (Unable to display action or device data "
                f"due to error: {err})"
            )
        receiver_device_id = device.pluginProps.get('receiverDeviceId', "")
        control_destination = device.pluginProps.get('controlDestination', "")
        # Get the current brightness and on-state of the device.
        current_brightness = device.states['brightnessLevel']
        current_on_state = device.states['onOffState']
        # Verify the validity of the data.
        if len(receiver_device_id) < 1:
            self.errorLog(
                f"{device.name} is not set to control any receiver device. Double-click the {device.name} device in "
                f"Indigo to select a receiver to control."
            )
            self.updateDeviceState(device, 'onOffState', current_on_state)
            self.updateDeviceState(device, 'brightnessLevel', 0)
            return
        if int(receiver_device_id) not in self.device_list:
            self.errorLog(
                f"{device.name} is configured to control a receiver device that no longer exists. Double-click the "
                f"{device.name} device in Indigo to select a receiver to control."
            )
            self.updateDeviceState(device, 'onOffState', current_on_state)
            self.updateDeviceState(device, 'brightnessLevel', 0)
            return
        # Get the receiver device object.
        receiver_device_id = int(receiver_device_id)
        receiver = indigo.devices[receiver_device_id]

        # ====== TURN ON ======
        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            try:
                self.debugLog(f"device on:\n{action}")
            except Exception as err:
                self.debugLog(f"device on: (Unable to display action data due to error: {err})")
            # Select the proper action based on the controlDestination value.
            # VOLUME / MUTE
            if control_destination in ["zone1volume", "zone2volume"]:
            # DaveL17 delete extra lines if valid - fixme
            # if control_destination == "zone1volume" or control_destination == "zone2volume":
                try:
                    # Turn off the select zone's mute.
                    if control_destination == "zone1volume":
                        # Execute the action.
                        self.sendCommand(receiver, "MF")
                    if control_destination == "zone2volume":
                        # Execute the action.
                        self.sendCommand(receiver, "Z2MF")
                except Exception as err:
                    self.errorLog(
                        f"{device.name}: Error executing Mute Off action for receiver device {receiver.name}. {err}"
                    )

        # ====== TURN OFF ======
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            try:
                self.debugLog(f"device off:\n{action}")
            except Exception as err:
                self.debugLog(f"device off: (Unable to display action due to error: {err})")
            # Select the proper action based on the controlDestination value.
            # VOLUME / MUTE
            if control_destination in ["zone1volume", "zone2volume"]:
            # DaveL17 delete extra lines if valid
            # if control_destination == "zone1volume" or control_destination == "zone2volume":
                try:
                    # Turn on the select zone's mute.
                    if control_destination == "zone1volume":
                        self.sendCommand(receiver, "MO")
                    if control_destination == "zone2volume":
                        self.sendCommand(receiver, "Z2MO")
                except Exception as err:
                    self.errorLog(
                        f"{device.name}: Error executing Mute On action for receiver device {receiver.name}. {err}"
                    )

        # ====== TOGGLE ======
        elif action.deviceAction == indigo.kDeviceAction.Toggle:
            try:
                self.debugLog(f"device toggle:\n{action}")
            except Exception as err:
                self.debugLog(f"device toggle: (Unable to display action due to error: {err})")

            # Select the proper action based on the controlDestination value.
            # VOLUME / MUTE
            # DaveL17 delete extra lines if valid - fixme
            # if control_destination == "zone1volume" or control_destination == "zone2volume":
            if control_destination in ["zone1volume", "zone2volume"]:
                # Turn off or on the select zone's mute, depending on current state.
                try:
                    # Turn on mute if toggling device to "Off". Turn off mute if toggling the device to "On".
                    if device.states['onOffState']:
                        if control_destination == "zone1volume":
                            self.sendCommand(receiver, "MO")  # Zone 1 Mute On
                        if control_destination == "zone2volume":
                            self.sendCommand(receiver, "Z2MO")  # Zone 2 Mute On
                    # device.updateStateOnServer('onOffState', False)
                    else:
                        if control_destination == "zone1volume":
                            self.sendCommand(receiver, "MF")  # Zone 1 Mute Off
                        if control_destination == "zone2volume":
                            self.sendCommand(receiver, "Z2MF")  # Zone 2 Mute Off
                except Exception as err:
                    self.errorLog(
                        f"{device.name}: Error executing Mute On action for receiver device {receiver.name}. {err}"
                    )

        # ====== SET BRIGHTNESS ======
        elif action.deviceAction == indigo.kDeviceAction.SetBrightness:
            try:
                self.debugLog(f"device set brightness:\n{action}")
            except Exception as err:
                self.debugLog(f"device set brightness: (Unable to display action due to error: {err})")
            # Select the proper action based on the controlDestination value.

            # VOLUME / MUTE
            # DaveL17 delete extra lines if valid - fixme
            # if control_destination == "zone1volume" or control_destination == "zone2volume":
            if control_destination in ["zone1volume", "zone2volume"]:
                try:
                    brightness_level = action.actionValue
                    # Convert the brightness level to a valid volume command.
                    if control_destination == "zone1volume":
                        # This formula converts from the 100 unit scale to the 161 unit scale used by the receiver's
                        # zone 1 volume commands.
                        the_volume = int(round(161 * 0.01 * brightness_level, 0))
                        if the_volume < 10:
                            the_volume = f"00{the_volume}"
                        elif the_volume < 100:
                            the_volume = f"0{the_volume}"
                        else:
                            the_volume = f"{the_volume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone1mute']:
                            self.sendCommand(receiver, "MF")
                        # Now send the volume command.
                        command = the_volume + "VL"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightness_level}, theVolume: {the_volume}"
                        )
                    elif control_destination == "zone2volume":
                        # This formula converts from the 100 unit scale to the 81 unit scale used by the receiver's
                        # zone 2 volume commands.
                        the_volume = int(round(81 * 0.01 * brightness_level, 0))
                        if the_volume < 10:
                            the_volume = f"0{the_volume}"
                        else:
                            the_volume = f"{the_volume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone2mute']:
                            self.sendCommand(receiver, "Z2MF")
                        # Now send the volume command.
                        command = the_volume + "ZV"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightness_level}, theVolume: {the_volume}"
                        )
                except Exception as err:
                    self.errorLog(
                        f"{device.name}: Error executing Set Volume action for receiver device {receiver.name}. {err}"
                    )

        # ====== BRIGHTEN BY ======
        elif action.deviceAction == indigo.kDeviceAction.BrightenBy:
            try:
                self.debugLog(f"device brighten by:\n{action}")
            except Exception as err:
                self.debugLog(f"device brighten by: (Unable to display action due to error: {err})")
            # Select the proper action based on the controlDestination value.

            # VOLUME / MUTE
            # DaveL17 delete extra lines if valid - fixme
            # if control_destination == "zone1volume" or control_destination == "zone2volume":
            if control_destination in ["zone1volume", "zone2volume"]:
                try:
                    # Convert the brightness level to a valid volume command.
                    if control_destination == "zone1volume":
                        # Set the currentBrightness to the current receiver volume. We're doing this because if the
                        # receiver is muted, this virtual device will have a brightness of 0 and brightening by
                        # anything will set brightness to 0 plus the brightening amount.
                        current_brightness = int(100 - round(float(receiver.states['zone1volume']) / -80.5 * 100, 0))
                        brightness_level = current_brightness + int(action.actionValue)

                        # Sanity check...
                        # DaveL17 - delete extra lines if valid fixme
                        # if brightness_level > 100:
                        #     brightness_level = 100
                        brightness_level = min(brightness_level, 100)

                        self.debugLog(f"   set brightness of {device.name} to {brightness_level}")
                        # This formula converts from the 100 unit scale to the 161 unit scale used by the receiver's
                        # zone 1 volume commands.
                        the_volume = int(round(161 * 0.01 * brightness_level, 0))
                        if the_volume < 10:
                            the_volume = f"00{the_volume}"
                        elif the_volume < 100:
                            the_volume = f"0{the_volume}"
                        else:
                            the_volume = f"{the_volume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone1mute']:
                            self.sendCommand(receiver, "MF")
                        # Now send the volume command.
                        command = the_volume + "VL"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightness_level}, theVolume: {the_volume}")
                    elif control_destination == "zone2volume":
                        # Set the currentBrightness to the current receiver volume. We're doing this because if the
                        # receiver is muted, this virtual device will have a brightness of 0 and brightening by
                        # anything will set brightness to 0 plus the brightening amount.
                        current_brightness = int(100 - round(float(receiver.states['zone2volume']) / -81 * 100, 0))
                        brightness_level = current_brightness + int(action.actionValue)

                        # Sanity check...
                        # DaveL17 - delete extra lines if valid fixme
                        # if brightness_level > 100:
                        #     brightness_level = 100
                        brightness_level = min(brightness_level, 100)

                        self.debugLog(f"   set brightness of {device.name} to {brightness_level}")
                        # This formula converts from the 100 unit scale to the 81 unit scale used by the receiver's
                        # zone 2 volume commands.
                        the_volume = int(round(81 * 0.01 * brightness_level, 0))
                        if the_volume < 10:
                            the_volume = f"0{the_volume}"
                        else:
                            the_volume = f"{the_volume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone2mute']:
                            self.sendCommand(receiver, "Z2MF")
                        # Now send the volume command.
                        command = the_volume + "ZV"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightness_level}, theVolume: {the_volume}"
                        )
                except Exception as err:
                    self.errorLog(
                        f"{device.name}: Error executing Set Volume action for receiver device {receiver.name}. {err}"
                    )

        # ====== DIM BY ======
        elif action.deviceAction == indigo.kDeviceAction.DimBy:
            try:
                self.debugLog(f"device dim by:\n{action}")
            except Exception as err:
                self.debugLog(f"device dim by: (Unable to display action due to error: {err})")
            brightness_level = current_brightness - int(action.actionValue)

            # Sanity check...
            # DaveL17 - delete extra lines if valid fixme
            # if brightness_level > 100:
            #     brightness_level = 100
            brightness_level = min(brightness_level, 100)

            self.debugLog(f"   set brightness of {device.name} to {brightness_level}")
            # Select the proper action based on the controlDestination value.

            # VOLUME / MUTE
            # DaveL17 Delete extra lines if valid - fixme
            # if control_destination == "zone1volume" or control_destination == "zone2volume":
            if control_destination in ["zone1volume", "zone2volume"]:
                try:
                    # Convert the brightness level to a valid volume command.
                    if control_destination == "zone1volume":
                        # This formula converts from the 100 unit scale to the 161 unit scale used by the receiver's
                        # zone 1 volume commands.
                        the_volume = int(round(161 * 0.01 * brightness_level, 0))
                        if the_volume < 10:
                            the_volume = f"00{the_volume}"
                        elif the_volume < 100:
                            the_volume = f"0{the_volume}"
                        else:
                            the_volume = f"{the_volume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone1mute']:
                            self.sendCommand(receiver, "MF")
                        # Now send the volume command.
                        command = the_volume + "VL"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightness_level}, theVolume: {the_volume}"
                        )
                    elif control_destination == "zone2volume":
                        # This formula converts from the 100 unit scale to the 81 unit scale used by the receiver's
                        # zone 2 volume commands.
                        the_volume = int(round(81 * 0.01 * brightness_level, 0))
                        if the_volume < 10:
                            the_volume = f"0{the_volume}"
                        else:
                            the_volume = f"{the_volume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone2mute']:
                            self.sendCommand(receiver, "Z2MF")
                        # Now send the volume command.
                        command = the_volume + "ZV"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightness_level}, theVolume: {the_volume}"
                        )
                except Exception as err:
                    self.errorLog(
                        f"{device.name}: Error executing Set Volume action for receiver device {receiver.name}. {err}"
                    )

    ########################################
    # UI Interaction Methods
    #   (Class-Supported)
    ########################################

    # Actions Dialog
    ########################################
    def validateActionConfigUi(self, values_dict, type_id, device_id):
        """
        Placeholder - fixme

        :param values_dict:
        :param type_id:
        :param device_id:
        :return:
        """
        self.debugLog("validateActionConfigUi called.")
        self.debugLog(f"type_id: {type_id}, device_id: {device_id}")
        try:
            self.debugLog(f"values_dict: {values_dict}")
        except Exception as err:
            self.debugLog(f"(Unable to display values_dict due to error: {err})")

        device = indigo.devices[device_id]
        error_msg_dict = indigo.Dict()
        desc_string = ""

        #
        # Set Volume dB (Zone 1)
        #
        if type_id == "zone1setVolume":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['volume'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['volume']
                return False, values_dict, error_msg_dict

            try:
                the_number = float(values_dict.get('volume', "-90"))
            except ValueError:
                error_msg_dict['volume'] = "The volume must be a number between -80.5 and 12 dB."
                error_msg_dict['showAlertText'] = error_msg_dict['volume']
                return False, values_dict, error_msg_dict

            if (the_number < -80.5) or (the_number > 12.0):
                error_msg_dict['volume'] = "The volume must be a number between -80.5 and 12 dB."
                error_msg_dict['showAlertText'] = error_msg_dict['volume']
                return False, values_dict, error_msg_dict

            if the_number % 0.5 != 0:
                error_msg_dict['volume'] = "The volume must be evenly divisible by 0.5 dB."
                error_msg_dict['showAlertText'] = error_msg_dict['volume']
                return False, values_dict, error_msg_dict

            desc_string += f"set volume (zone 1) to {the_number}"

        #
        # Set Source (Zone 1)
        #
        if type_id == "zone1setSource":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['source'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['source']
                return False, values_dict, error_msg_dict

            the_source = values_dict['source']
            prop_name = f"source{the_source}label"
            the_name = device.pluginProps.get(prop_name, "")
            if len(the_name) < 1:
                error_msg_dict['source'] = "Please select an Input Source."
                error_msg_dict['showAlertText'] = error_msg_dict['source']
                return False, values_dict, error_msg_dict

            if device.deviceTypeId == "vsx1021k":
                if the_source in VSX1021k_SOURCE_MASK:
                    error_msg_dict[
                        'source'] = "The selected source is not available on this receiver. Choose a different source."
                    error_msg_dict['showAlertText'] = error_msg_dict['source']
                    return False, values_dict, error_msg_dict
            elif device.deviceTypeId == "vsx1022k":
                if the_source in VSX1022K_SOURCE_MASK:
                    error_msg_dict[
                        'source'] = "The selected source is not available on this receiver. Choose a different source."
                    error_msg_dict['showAlertText'] = error_msg_dict['source']
                    return False, values_dict, error_msg_dict
            elif device.deviceTypeId == "vsx1122k":
                if the_source in VSX1122K_SOURCE_MASK:
                    error_msg_dict[
                        'source'] = "The selected source is not available on this receiver. Choose a different source."
                    error_msg_dict['showAlertText'] = error_msg_dict['source']
                    return False, values_dict, error_msg_dict
            elif device.deviceTypeId == "vsx1123k":
                if the_source in VSX1123K_SOURCE_MASK:
                    error_msg_dict[
                        'source'] = "The selected source is not available on this receiver. Choose a different source."
                    error_msg_dict['showAlertText'] = error_msg_dict['source']
                    return False, values_dict, error_msg_dict
            elif device.deviceTypeId == "sc75":
                if the_source in SC75_SOURCE_MASK:
                    error_msg_dict[
                        'source'] = "The selected source is not available on this receiver. Choose a different source."
                    error_msg_dict['showAlertText'] = error_msg_dict['source']
                    return False, values_dict, error_msg_dict

            desc_string += f"set input source (zone 1) to {the_name}"

        #
        # Set Volume dB (Zone 2)
        #
        if type_id == "zone2setVolume":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['volume'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['volume']
                return False, values_dict, error_msg_dict

            try:
                the_number = int(values_dict.get('volume', "-90"))
            except ValueError:
                error_msg_dict['volume'] = "The volume must be a whole number between -81 and 0 dB."
                error_msg_dict['showAlertText'] = error_msg_dict['volume']
                return False, values_dict, error_msg_dict

            if (the_number < -81) or (the_number > 0):
                error_msg_dict['volume'] = "The volume must be a whole number between -81 and 0 dB."
                error_msg_dict['showAlertText'] = error_msg_dict['volume']
                return False, values_dict, error_msg_dict

            desc_string += f"set volume (zone 2) to {the_number}"

        #
        # Set Source (Zone 2)
        #
        if type_id == "zone2setSource":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['source'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['source']
                return False, values_dict, error_msg_dict

            the_source = values_dict['source']
            prop_name = f"source{the_source}label"
            the_name = device.pluginProps.get(prop_name, "")
            if len(the_name) < 1:
                error_msg_dict['source'] = "Please select an Input Source."
                error_msg_dict['showAlertText'] = error_msg_dict['source']
                return False, values_dict, error_msg_dict

            if device.deviceTypeId == "vsx1021k":
                if the_source in VSX1021K_ZONE2_SOURCE_MASK:
                    error_msg_dict[
                        'source'] = (
                        "The selected source is not available for this zone on this receiver. Choose a different "
                        "source."
                    )
                    error_msg_dict['showAlertText'] = error_msg_dict['source']
                    return False, values_dict, error_msg_dict
            elif device.deviceTypeId == "vsx1022k":
                if the_source in VSX1022K_ZONE2_SOURCE_MASK:
                    error_msg_dict[
                        'source'] = (
                        "The selected source is not available for this zone on this receiver. Choose a different "
                        "source."
                    )
                    error_msg_dict['showAlertText'] = error_msg_dict['source']
                    return False, values_dict, error_msg_dict
            elif device.deviceTypeId == "vsx1122k":
                if the_source in VSX1122K_ZONE2_SOURCE_MASK:
                    error_msg_dict[
                        'source'] = (
                        "The selected source is not available for this zone on this receiver. Choose a different "
                        "source."
                    )
                    error_msg_dict['showAlertText'] = error_msg_dict['source']
                    return False, values_dict, error_msg_dict
            elif device.deviceTypeId == "vsx1123k":
                if the_source in VSX1123k_ZONE2_SOURCE_MASK:
                    error_msg_dict['source'] = (
                        "The selected source is not available for this zone on this receiver. Choose a different "
                        "source."
                    )
                    error_msg_dict['showAlertText'] = error_msg_dict['source']
                    return False, values_dict, error_msg_dict
            elif device.deviceTypeId == "sc75":
                if the_source in SC75_ZONE2_SOURCE_MASK:
                    error_msg_dict['source'] = (
                        "The selected source is not available for this zone on this receiver. Choose a different "
                        "source."
                    )
                    error_msg_dict['showAlertText'] = error_msg_dict['source']
                    return False, values_dict, error_msg_dict

            desc_string += f"set input source (zone 2) to {the_name}"

        #
        # Select Tuner Preset
        #
        if type_id == "tunerPresetSelect":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['tunerPreset'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['tunerPreset']
                return False, values_dict, error_msg_dict

            the_preset = values_dict['tunerPreset']
            prop_name = f"tunerPreset{the_preset.replace('0', '')}label"
            the_name = device.pluginProps.get(prop_name, "")
            if len(the_name) < 1:
                error_msg_dict['tunerPreset'] = "Please select a Tuner Preset."
                error_msg_dict['showAlertText'] = error_msg_dict['tunerPreset']
                return False, values_dict, error_msg_dict

            desc_string += f"select tuner preset {the_preset.replace('0', '')}: {the_name}"

        #
        # Set Tuner Frequency
        #
        if type_id == "tunerFrequencySet":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['band'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['frequency'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['band']
                return False, values_dict, error_msg_dict

            # Make sure a tuner band was selected.
            band = values_dict.get('band', "")
            if len(band) < 2:
                error_msg_dict['band'] = "Please select a Tuner Band."

            # Make sure a frequency value was entered.
            frequency = values_dict.get('frequency', "")
            if len(frequency) == 0:
                error_msg_dict['frequency'] = "A Tuner Frequency value is required."
            else:
                # A tuner frequency was entered, now make sure it's realistic.
                try:
                    frequency = float(values_dict['frequency'])
                    # Make sure the frequency is a sane value based on band.
                    if band == "AM":
                        if (frequency < 530) or (frequency > 1700):
                            error_msg_dict[
                                'frequency'] = (
                                "AM frequencies must be a whole number between 530 and 1700 in increments of 10 kHz."
                            )
                        if frequency % 10 != 0:
                            error_msg_dict['frequency'] = (
                                "AM frequencies must be a whole number between 530 and 1700 in increments of 10 kHz."
                            )
                        # Convert the frequency to an integer.
                        frequency = int(frequency)
                    elif band == "FM":
                        if (frequency < 87.5) or (frequency > 108):
                            error_msg_dict[
                                'frequency'] = "FM frequencies must be between 87.5 and 108 in increments of 0.1 MHz."
                        if int(frequency * 10) != frequency * 10:  # Make sure the precision is at most 0.1.
                            error_msg_dict[
                                'frequency'] = "FM frequencies must be between 87.5 and 108 in increments of 0.1 MHz."
                except ValueError:
                    error_msg_dict['frequency'] = "The Tuner Frequency field can only contain numbers."

            # If there were errors, return them now.
            if len(error_msg_dict) > 0:
                error_msg_dict['showAlertText'] = f"{error_msg_dict['band']}\r\r{error_msg_dict['frequency']}"
                return False, values_dict, error_msg_dict

            desc_string += f"set tuner frequency to {frequency} {band}"

        #
        # Select Listening Mode
        #
        if type_id == "listeningModeSelect":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['listeningMode'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['listeningMode']
                return False, values_dict, error_msg_dict

            listening_mode = values_dict.get('listeningMode', "")
            if len(listening_mode) < 1:
                error_msg_dict['listeningMode'] = "Please select a Listening Mode."
                error_msg_dict['showAlertText'] = error_msg_dict['listeningMode']
                return False, values_dict, error_msg_dict
            else:
                desc_string += f"set listening mode to \"{LISTENING_MODES[listening_mode]}\""

        #
        # Set Display Brightness
        #
        if type_id == "setDisplayBrightness":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['displayBrightness'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['displayBrightness']
                return False, values_dict, error_msg_dict

            display_brightness = values_dict.get('displayBrightness', "")
            if len(display_brightness) < 1:
                error_msg_dict['displayBrightness'] = "Please select a value for Display Brightness."
                error_msg_dict['showAlertText'] = error_msg_dict['displayBrightness']
                return False, values_dict, error_msg_dict
            else:
                desc_string += "set display brightness to "
                # Translate the displayBrightness value into something readable for the description.
                if display_brightness == "3SAA":
                    desc_string = "turn off display"
                elif display_brightness == "2SAA":
                    desc_string += "dim"
                elif display_brightness == "1SAA":
                    desc_string += "medium"
                elif display_brightness == "0SAA":
                    desc_string += "bright"

        #
        # Set Sleep Timer
        #
        if type_id == "setSleepTimer":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['sleepTime'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['sleepTime']
                return False, values_dict, error_msg_dict

            sleep_time = values_dict.get('sleepTime', "")
            if len(sleep_time) < 1:
                error_msg_dict['sleepTime'] = "Please select a value for Sleep Time Minutes."
                error_msg_dict['showAlertText'] = error_msg_dict['sleepTime']
                return False, values_dict, error_msg_dict
            else:
                desc_string += "set sleep timer to "
                # Translate the sleepTime value into something readable for the description.
                sleep_time = int(sleep_time[1:3])
                if sleep_time == 0:
                    desc_string += "off"
                else:
                    desc_string += f"{sleep_time} min"

        #
        # Select MCACC Memory
        #
        if type_id == "mcaccSelect":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['mcaccMemory'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['mcaccMemory']
                return False, values_dict, error_msg_dict

            # Make sure a MCACC memory was selected.
            mcacc_memory = values_dict.get('mcaccMemory', "")
            if len(mcacc_memory) < 1:
                error_msg_dict['mcaccMemory'] = "Please select a MCACC Memory item."
                error_msg_dict['showAlertText'] = error_msg_dict['mcaccMemory']
                return False, values_dict, error_msg_dict
            else:
                dev_props = device.pluginProps
                prop_name = f"mcaccMemory{mcacc_memory[0:1]}label"
                mcacc_memory_name = dev_props[prop_name]
                desc_string += f"set mcacc memory to {mcacc_memory[0:1]}: {mcacc_memory_name}"

        #
        # Send Remote Button Press
        #
        if type_id == "remoteButtonPress":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['remoteButton'] = (
                        f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                        f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['remoteButton']
                return False, values_dict, error_msg_dict

            command = values_dict.get('remoteButton', "")
            # Make sure they selected a button to send.
            if len(command) == 0:
                error_msg_dict['remoteButton'] = "Please select a Button press to send to the receiver."
                error_msg_dict['showAlertText'] = error_msg_dict['remoteButton']
                return False, values_dict, error_msg_dict

            desc_string += f"press remote control button \"{REMOTE_BUTTON_NAMES.get(command, '')}\""

        #
        # Send a Raw Command
        #
        if type_id == "sendRawCommand":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                error_msg_dict['command'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['command']
                return False, values_dict, error_msg_dict

            command = values_dict['command']
            # Attempt to encode the command as ASCII.  If this fails.
            try:
                command = command.encode("ascii")
            except UnicodeEncodeError:
                error_msg_dict[
                    'command'] = (
                    "Commands can only contain standard ASCII characters. Extended characters are not supported."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['command']
                return False, values_dict, error_msg_dict
            # Make sure the command isn't blank.
            if len(command) == 0:
                error_msg_dict['command'] = (
                    "Nothing was entered for the Command. Please enter a text command to send to the receiver."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['command']
                return False, values_dict, error_msg_dict

            desc_string += f"send raw command \"{command}\""

        values_dict['description'] = desc_string
        return True, values_dict

    # Device Configuration Dialog
    ########################################
    def validateDeviceConfigUi(self, values_dict, type_id=0, device_id=0):
        """
        Placeholder - fixme

        :param values_dict:
        :param type_id:
        :param device_id:
        :return:
        """
        try:
            self.debugLog(
                f"validateDeviceConfig called. values_dict: {values_dict} type_id: {type_id}, device_id: {device_id}."
            )
        except Exception as err:
            self.debugLog(
                f"validateDeviceConfig called. type_id: {type_id} device_id: {device_id} (Unable to display "
                f"values_dict due to error: {err})"
            )

        error = False  # To flag if any errors were found.
        error_msg_dict = indigo.Dict()

        #
        # VSX-1021-K Device
        #
        if type_id == "vsx1021k":
            address = values_dict.get('address', "")

            # Make sure a value was entered for the address.
            if len(address) < 1:
                error_msg_dict['address'] = "Please enter an IP address for the receiver."
                error_msg_dict['showAlertText'] = error_msg_dict['address']
                return False, values_dict, error_msg_dict

            # Make sure the address entered is in the correct IP address format.
            address_parts = address.split(".")
            # (This is easier than using Regular Expressions.  :-) )
            for part in address_parts:
                try:
                    part = int(part)
                    if part < 0 or part > 255:
                        error_msg_dict['address'] = "Please enter a valid IP address for the receiver."
                        error_msg_dict['showAlertText'] = error_msg_dict['address']
                        return False, values_dict, error_msg_dict
                except ValueError:
                    error_msg_dict['address'] = "Please enter a valid IP address for the receiver."
                    error_msg_dict['showAlertText'] = error_msg_dict['address']
                    return False, values_dict, error_msg_dict

            # For newly created devices, the device_id won't be in the device list.
            if device_id > 0:
                device = indigo.devices[device_id]
                dev_props = device.pluginProps

                # See if any other devices are using the same address by going through all devices for this plugin.
                for dev in self.device_list:
                    the_address = indigo.devices[dev].pluginProps['address']
                    # If the address found is the same as this device's address (and the matching address is not for
                    # this device), generate an error.
                    if (the_address == address) and (dev != device_id):
                        error = True
                        error_msg_dict['address'] = (
                            f"This address is already being used by the device \"{indigo.devices[dev].name}\". Only "
                            f"one device at a time can connect to a receiver."
                        )
                        error_msg_dict['showAlertText'] = error_msg_dict['address']

                # Make sure the MCACC Memory Label properties are created, even if they aren't specified.
                for mcmcc_memory in range(1, 7):
                    prop_name = f"mcmccMemory{mcmcc_memory}label"
                    if values_dict.get(prop_name, "") == "":
                        dev_props.update({prop_name: ""})
                        self.updateDeviceProps(device, dev_props)

        #
        # VSX-1022-K Device
        #
        if type_id == "vsx1022k":
            address = values_dict.get('address', "")

            # Make sure a value was entered for the address.
            if len(address) < 1:
                error_msg_dict['address'] = "Please enter an IP address for the receiver."
                error_msg_dict['showAlertText'] = error_msg_dict['address']
                return False, values_dict, error_msg_dict

            # Make sure the address entered is in the correct IP address format.
            address_parts = address.split(".")
            # (This is easier than using Regular Expressions.  :-) )
            for part in address_parts:
                try:
                    part = int(part)
                    if part < 0 or part > 255:
                        error_msg_dict['address'] = "Please enter a valid IP address for the receiver."
                        error_msg_dict['showAlertText'] = error_msg_dict['address']
                        return False, values_dict, error_msg_dict
                except ValueError:
                    error_msg_dict['address'] = "Please enter a valid IP address for the receiver."
                    error_msg_dict['showAlertText'] = error_msg_dict['address']
                    return False, values_dict, error_msg_dict

            # For newly created devices, the device_id won't be in the device list.
            if device_id > 0:
                device = indigo.devices[device_id]
                dev_props = device.pluginProps

                # See if any other devices are using the same address by going through all devices for this plugin.
                for dev in self.device_list:
                    the_address = indigo.devices[dev].pluginProps['address']
                    # If the address found is the same as this device's address (and the matching address is not for
                    # this device), generate an error.
                    if (the_address == address) and (dev != device_id):
                        error = True
                        error_msg_dict['address'] = (
                                f"This address is already being used by the device \"{indigo.devices[dev].name}\". "
                                f"Only one device at a time can connect to a receiver."
                        )
                        error_msg_dict['showAlertText'] = error_msg_dict['address']

                # Make sure the MCACC Memory Label properties are created, even if they aren't specified.
                for mcmcc_memory in range(1, 7):
                    prop_name = f"mcmccMemory{mcmcc_memory}label"
                    if values_dict.get(prop_name, "") == "":
                        dev_props.update({prop_name: ""})
                        self.updateDeviceProps(device, dev_props)

        #
        # VSX-1122-K Device
        #
        if type_id == "vsx1122k":
            address = values_dict.get('address', "")

            # Make sure a value was entered for the address.
            if len(address) < 1:
                error_msg_dict['address'] = "Please enter an IP address for the receiver."
                error_msg_dict['showAlertText'] = error_msg_dict['address']
                return False, values_dict, error_msg_dict

            # Make sure the address entered is in the correct IP address format.
            address_parts = address.split(".")
            # (This is easier than using Regular Expressions.  :-) )
            for part in address_parts:
                try:
                    part = int(part)
                    if part < 0 or part > 255:
                        error_msg_dict['address'] = "Please enter a valid IP address for the receiver."
                        error_msg_dict['showAlertText'] = error_msg_dict['address']
                        return False, values_dict, error_msg_dict
                except ValueError:
                    error_msg_dict['address'] = "Please enter a valid IP address for the receiver."
                    error_msg_dict['showAlertText'] = error_msg_dict['address']
                    return False, values_dict, error_msg_dict

            # For newly created devices, the device_id won't be in the device list.
            if device_id > 0:
                device = indigo.devices[device_id]
                dev_props = device.pluginProps

                # See if any other devices are using the same address by going through all devices for this plugin.
                for dev in self.device_list:
                    the_address = indigo.devices[dev].pluginProps['address']
                    # If the address found is the same as this device's address (and the matching address is not for
                    # this device), generate an error.
                    if (the_address == address) and (dev != device_id):
                        error = True
                        error_msg_dict['address'] = (
                            f"This address is already being used by the device \"{indigo.devices[dev].name}\". Only "
                            f"one device at a time can connect to a receiver."
                        )
                        error_msg_dict['showAlertText'] = error_msg_dict['address']

                # Make sure the MCACC Memory Label properties are created, even if they aren't specified.
                for mcmcc_memory in range(1, 7):
                    prop_name = f"mcmccMemory{mcmcc_memory}label"
                    if values_dict.get(prop_name, "") == "":
                        dev_props.update({prop_name: ""})
                        self.updateDeviceProps(device, dev_props)

        #
        # VSX-1123-K Device
        #
        if type_id == "vsx1123k":
            address = values_dict.get('address', "")

            # Make sure a value was entered for the address.
            if len(address) < 1:
                error_msg_dict['address'] = "Please enter an IP address for the receiver."
                error_msg_dict['showAlertText'] = error_msg_dict['address']
                return False, values_dict, error_msg_dict

            # Make sure the address entered is in the correct IP address format.
            address_parts = address.split(".")
            # (This is easier than using Regular Expressions.  :-) )
            for part in address_parts:
                try:
                    part = int(part)
                    if part < 0 or part > 255:
                        error_msg_dict['address'] = "Please enter a valid IP address for the receiver."
                        error_msg_dict['showAlertText'] = error_msg_dict['address']
                        return False, values_dict, error_msg_dict
                except ValueError:
                    error_msg_dict['address'] = "Please enter a valid IP address for the receiver."
                    error_msg_dict['showAlertText'] = error_msg_dict['address']
                    return False, values_dict, error_msg_dict

            # For newly created devices, the device_id won't be in the device list.
            if device_id > 0:
                device = indigo.devices[device_id]
                dev_props = device.pluginProps

                # See if any other devices are using the same address by going through all devices for this plugin.
                for dev in self.device_list:
                    the_address = indigo.devices[dev].pluginProps['address']
                    # If the address found is the same as this device's address (and the matching address is not for
                    # this device), generate an error.
                    if (the_address == address) and (dev != device_id):
                        error = True
                        error_msg_dict['address'] = (
                            f"This address is already being used by the device \"{indigo.devices[dev].name}\". Only "
                            f"one device at a time can connect to a receiver."
                        )
                        error_msg_dict['showAlertText'] = error_msg_dict['address']

                # Make sure the MCACC Memory Label properties are created, even if they aren't specified.
                for mcmcc_memory in range(1, 7):
                    prop_name = f"mcmccMemory{mcmcc_memory}label"
                    if values_dict.get(prop_name, "") == "":
                        dev_props.update({prop_name: ""})
                        self.updateDeviceProps(device, dev_props)

        #
        # SC-75 Device
        #
        if type_id == "sc75":
            address = values_dict.get('address', "")

            # Make sure a value was entered for the address.
            if len(address) < 1:
                error_msg_dict['address'] = "Please enter an IP address for the receiver."
                error_msg_dict['showAlertText'] = error_msg_dict['address']
                return False, values_dict, error_msg_dict

            # Make sure the address entered is in the correct IP address format.
            address_parts = address.split(".")
            # (This is easier than using Regular Expressions.  :-) )
            for part in address_parts:
                try:
                    part = int(part)
                    if part < 0 or part > 255:
                        error_msg_dict['address'] = "Please enter a valid IP address for the receiver."
                        error_msg_dict['showAlertText'] = error_msg_dict['address']
                        return False, values_dict, error_msg_dict
                except ValueError:
                    error_msg_dict['address'] = "Please enter a valid IP address for the receiver."
                    error_msg_dict['showAlertText'] = error_msg_dict['address']
                    return False, values_dict, error_msg_dict

            # For newly created devices, the device_id won't be in the device list.
            if device_id > 0:
                device = indigo.devices[device_id]
                dev_props = device.pluginProps

                # See if any other devices are using the same address by going through all devices for this plugin.
                for dev in self.device_list:
                    the_address = indigo.devices[dev].pluginProps['address']
                    # If the address found is the same as this device's address (and the matching address is not for
                    # this device), generate an error.
                    if (the_address == address) and (dev != device_id):
                        error = True
                        error_msg_dict['address'] = (
                            f"This address is already being used by the device \"{indigo.devices[dev].name}\". Only "
                            f"one device at a time can connect to a receiver."
                        )
                        error_msg_dict['showAlertText'] = error_msg_dict['address']

                # Make sure the MCACC Memory Label properties are created, even if they aren't specified.
                for mcmcc_memory in range(1, 7):
                    prop_name = f"mcmccMemory{mcmcc_memory}label"
                    if values_dict.get(prop_name, "") == "":
                        dev_props.update({prop_name: ""})
                        self.updateDeviceProps(device, dev_props)

        #
        # Virtual Level Control Device
        #
        elif type_id == "virtualVolume":
            receiver_device_id = values_dict.get('receiverDeviceId', 0)
            control_destination = values_dict.get('controlDestination', "")
            if len(receiver_device_id) < 1:
                error_msg_dict['receiverDeviceId'] = "Please select a Pioneer Receiver device."
                error_msg_dict['showAlertText'] = error_msg_dict['receiverDeviceId']
                error = True
            elif int(receiver_device_id) in self.volume_device_list:
                error_msg_dict['receiverDeviceId'] = (
                    "The selected device is another Virtual Volume Controller. Only receiver devices can be controlled "
                    "with this Virtual Volume Controller."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['receiverDeviceId']
                error = True
            elif int(receiver_device_id) not in self.device_list:
                error_msg_dict['receiverDeviceId'] = (
                    "The selected device no longer exists. Please click Cancel then click on Edit Device Settings "
                    "again."
                )
                error_msg_dict['showAlertText'] = error_msg_dict['receiverDeviceId']
                error = True
            if len(control_destination) < 1:
                error_msg_dict['controlDestination'] = "Please select a Control Destination."
                error_msg_dict['showAlertText'] = error_msg_dict['controlDestination']
                error = True

        # Return errors if there were any.
        if error:
            return False, values_dict, error_msg_dict

        return True, values_dict

    # Plugin Configuration Dialog
    ########################################
    def closedPrefsConfigUi(self, values_dict, user_cancelled):
        """
        Placeholder - fixme

        :param values_dict:
        :param user_cancelled:
        :return:
        """
        self.debugLog("closedPrefsConfigUi called.")

        if not user_cancelled:
            self.debug = values_dict.get("showDebugInfo", False)
            if self.debug:
                indigo.server.log("Debug logging enabled")
            else:
                indigo.server.log("Debug logging disabled")

    ########################################
    # UI Interaction Methods
    #   (Custom)
    ########################################

    # Get Source List for Use in UI.
    ########################################
    def uiSourceList(self, filter="", values_dict=None, type_id="", device_id=0):  # noqa
        """
        Placeholder - fixme

        :param filter:
        :param values_dict:
        :param type_id:
        :param device_id:
        :return:
        """
        self.debugLog(f"uiSourceList called. type_id: {type_id}, device_id: {device_id}")

        the_list = []  # Menu item list.
        device = indigo.devices[device_id]  # The device whose action is being configured.

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device.")
            return []

        # Go through the defined sources to decide which to add to the list.
        for this_number, this_name in SOURCE_NAMES.items():
            # Create the list based on which zone for which this is being compiled.
            if type_id == "zone1setSource":
                # If this source ID is not masked (i.e. is available) on this model, add it.
                if device.deviceTypeId == "vsx1021k":
                    if this_number not in VSX1021k_SOURCE_MASK:
                        prop_name = f"source{this_number}label"
                        this_name = device.pluginProps[prop_name]
                        the_list.append((this_number, this_name))
                elif device.deviceTypeId == "vsx1022k":
                    if this_number not in VSX1022K_SOURCE_MASK and this_number not in ['46', '47']:
                        # Source 46 (AirPlay) and 47 (DMR) are not selectable, but are valid sources, so they're not in
                        # the mask array.
                        prop_name = f"source{this_number}label"
                        this_name = device.pluginProps[prop_name]
                        the_list.append((this_number, this_name))
                elif device.deviceTypeId == "vsx1122k":
                    if this_number not in VSX1122K_SOURCE_MASK:
                        prop_name = f"source{this_number}label"
                        this_name = device.pluginProps[prop_name]
                        the_list.append((this_number, this_name))
                elif device.deviceTypeId == "vsx1123k":
                    if this_number not in VSX1123K_SOURCE_MASK:
                        prop_name = f"source{this_number}label"
                        this_name = device.pluginProps[prop_name]
                        the_list.append((this_number, this_name))
                elif device.deviceTypeId == "sc75":
                    if this_number not in SC75_SOURCE_MASK:
                        prop_name = f"source{this_number}label"
                        this_name = device.pluginProps[prop_name]
                        the_list.append((this_number, this_name))
            elif type_id == "zone2setSource":
                # If this source ID is not masked (i.e. is available) on this model, add it.
                if device.deviceTypeId == "vsx1021k":
                    if this_number not in VSX1021K_ZONE2_SOURCE_MASK:
                        prop_name = f"source{this_number}label"
                        this_name = device.pluginProps[prop_name]
                        the_list.append((this_number, this_name))
                elif device.deviceTypeId == "vsx1022k":
                    if this_number not in VSX1022K_ZONE2_SOURCE_MASK and this_number not in ['46', '47']:
                        # Source 46 (AirPlay) and 47 (DMR) are not selectable, but are valid sources, so they're not in
                        # the mask array.
                        prop_name = f"source{this_number}label"
                        this_name = device.pluginProps[prop_name]
                        the_list.append((this_number, this_name))
                elif device.deviceTypeId == "vsx1122k":
                    if this_number not in VSX1122K_ZONE2_SOURCE_MASK:
                        prop_name = f"source{this_number}label"
                        this_name = device.pluginProps[prop_name]
                        the_list.append((this_number, this_name))
                elif device.deviceTypeId == "vsx1123k":
                    if this_number not in VSX1123k_ZONE2_SOURCE_MASK:
                        prop_name = f"source{this_number}label"
                        this_name = device.pluginProps[prop_name]
                        the_list.append((this_number, this_name))
                elif device.deviceTypeId == "sc75":
                    if this_number not in SC75_ZONE2_SOURCE_MASK:
                        prop_name = f"source{this_number}label"
                        this_name = device.pluginProps[prop_name]
                        the_list.append((this_number, this_name))

        return the_list

    # Get Tuner Preset List for Use in UI.
    ########################################
    def uiTunerPresetList(self, filter="", values_dict=None, type_id="", device_id=0):  # noqa
        """
        Placeholder - fixme

        :param filter:
        :param values_dict:
        :param type_id:
        :param device_id:
        :return:
        """
        self.debugLog(f"uiTunerPresetList called. type_id: {type_id}, device_id: {device_id}")

        the_list = []  # Menu item list.
        device = indigo.devices[device_id]  # The device whose action is being configured.
        prop_name = ""  # Device property name to be queried.
        preset_name = ""  # Tuner Preset name to be listed.
        preset_number = ""  # Tuner Preset number to be returned in the list selection.

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI, we
        # must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return []

        # Define the tuner preset "classes" (groups).
        preset_classes = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        # Go through the preset classes and numbers 1 through 9 to get the preset names.
        for the_class in preset_classes:
            for the_preset in range(1, 9):
                prop_name = f"tunerPreset{the_class}{the_preset}label"
                preset_name = f"{the_class}{the_preset}: {device.pluginProps[prop_name]}"
                preset_number = f"{the_class}0{the_preset}"
                the_list.append((preset_number, preset_name))

        return the_list

    # Get MCACC Label List for Use in UI.
    ########################################
    def uiMcaccLabelList(self, filter="", values_dict=None, type_id="", device_id=0):  # noqa
        """
        Placeholder - fixme

        :param filter:
        :param values_dict:
        :param type_id:
        :param device_id:
        :return:
        """
        self.debugLog(f"uiMcaccLabelList called. type_id: {type_id}, device_id: {device_id}")

        the_list = []  # Menu item list.
        device = indigo.devices[device_id]  # The device whose action is being configured.
        prop_name = ""  # Device property name to be queried.
        mcacc_memory_name = ""  # MCACC Memory label (name) to be listed.
        mcacc_memory = ""  # MCACC Memory number to be returned in the list selection.

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return []

        # Go through the MCACC memory numbers 1 through 6 to get the labels/names.
        for mcacc_memory in range(1, 7):
            prop_name = f"mcaccMemory{mcacc_memory}label"
            mcacc_memory_name = f"{mcacc_memory}: {device.pluginProps[prop_name]}"
            # Convert the mcaccMemory number into a command.
            mcacc_memory = f"{mcacc_memory}MC"
            the_list.append((mcacc_memory, mcacc_memory_name))

        return the_list

    # Get Remote Control Button Names
    ########################################
    def uiButtonNames(self, filter="", values_dict=None, type_id="", device_id=0):  # noqa
        """
        Placeholder - fixme

        :param filter:
        :param values_dict:
        :param type_id:
        :param device_id:
        :return:
        """
        self.debugLog(f"uiButtonNames called. type_id: {type_id}, device_id: {device_id}")

        the_list = []  # Menu item list.
        device = indigo.devices[device_id]  # The device whose action is being configured.
        command = ""  # The button press command.
        button_name = ""  # The name of the button to list in the menu.

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI, we
        # must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device.")
            return []

        # Go through the remoteButtonNames dictionary items to create the list.
        for command in REMOTE_BUTTON_NAMES_ORDER:
            button_name = REMOTE_BUTTON_NAMES.get(command, "")
            the_list.append((command, button_name))

        return the_list

    # Get List of Listening Modes.
    ########################################
    def uiListeningModeList(self, filter="", values_dict=None, type_id="", device_id=0):  # noqa
        """
        Placeholder - fixme

        :param filter:
        :param values_dict:
        :param type_id:
        :param device_id:
        :return:
        """
        self.debugLog(f"uiListeningModeList called. type_id: {type_id}, device_id: {device_id}")

        the_list = []  # Menu item list.
        the_number = ""  # The listening mode ID number
        the_name = ""  # The listening mode name.
        device = indigo.devices[device_id]  # The device whose action is being configured.

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device."
            )
            return []

        # Create a list of listeningModes keys sorted by listeningModes values.
        items = LISTENING_MODES.items()
        reverse_items = [[v[1], v[0]] for v in items]
        reverse_items.sort()
        sortedlist = [reverse_items[i][1] for i in range(0, len(reverse_items))]

        for the_number in sortedlist:
            the_name = LISTENING_MODES[the_number]
            # Show only items related to the device type passed in the "filter" variable.
            if filter == "vsx1021k":
                if the_number not in VSX1021K_LISTENING_MODE_MASK:
                    # Don't list modes with "(cyclic)" in the name.
                    if "(cyclic)" not in the_name:
                        the_list.append((the_number, the_name))
            elif filter == "vsx1022k":
                if the_number not in VSX1022K_LISTENING_MODE_MASK:
                    # Don't list modes with "(cyclic)" in the name.
                    if "(cyclic)" not in the_name:
                        the_list.append((the_number, the_name))
            elif filter == "vsx1122k":
                if the_number not in VSX1122K_LISTENING_MODE_MASK:
                    # Don't list modes with "(cyclic)" in the name.
                    if "(cyclic)" not in the_name:
                        the_list.append((the_number, the_name))
            elif filter == "vsx1123k":
                if the_number not in VSX1123K_LISTENING_MODE_MASK:
                    # Don't list modes with "(cyclic)" in the name.
                    if "(cyclic)" not in the_name:
                        the_list.append((the_number, the_name))
            elif filter == "sc75":
                if the_number not in SC75_LISTENING_MODE_MASK:
                    # Don't list modes with "(cyclic)" in the name.
                    if "(cyclic)" not in the_name:
                        the_list.append((the_number, the_name))

        return the_list

    # Get List of Pioneer Receiver Devices.
    ########################################
    # (This method is deprecated as of 0.9.6, but kept for possible future reference.
    def uiReceiverDevices(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa
        """
        Placeholder - fixme

        :param filter:
        :param values_dict:
        :param type_id:
        :param target_id:
        :return:
        """
        self.debugLog(f"uiReceiverDevices called. type_id: {type_id}, targetId: {target_id}")

        the_list = []  # Menu item list.

        # Go through the deviceList and list the devices.
        for device_id in self.device_list:
            device_name = indigo.devices[device_id].name  # The name of the Pioneer Receiver device listed.
            the_list.append((device_id, device_name))

        return the_list
