#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2012, Nathan Sheldon. All rights reserved.
http://www.nathansheldon.com/files/Pioneer-Receiver-Plugin.php  <--- this link may not remain active.

Version 2022.0.10
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
    ########################################
    # Class Globals
    ########################################

    # Dictionary of device telnet sessions.
    tn = dict()
    # List of devices whose complete status is being updated.
    devicesBeingUpdated = []
    # Dictionary of device connection waiting counters (device ID:1/10 second count)
    devicesWaitingToConnect = dict()

    ########################################
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug = pluginPrefs.get('showDebugInfo', False)
        self.deviceList = []
        self.volumeDeviceList = []

    ########################################
    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    # Class-Supported Methods
    ########################################

    # Device Start
    ########################################
    def startup(self):
        ...

    ########################################
    def deviceCreated(self, device):
        try:
            self.debugLog(f"deviceCreated called: {device}")
        except Exception as e:
            self.debugLog(f"deviceCreated called: {device.name} (Unable to display device states due to error: {e})")

        #
        # VSX-1021-K, VSX-1022-K, VSX-1122-K, VSX-1123-K, SC-75 Devices
        #
        if (
                device.deviceTypeId == "vsx1021k"
                or device.deviceTypeId == "vsx1022k"
                or device.deviceTypeId == "vsx1122k"
                or device.deviceTypeId == "vsx1123k"
                or device.deviceTypeId == "sc75"
        ):
            # If the device has the same IP address as another device, generate an error.
            self.debugLog("deviceCreated: Testing to see if using duplicate IP.")
            devProps = device.pluginProps
            for deviceId in self.deviceList:
                self.debugLog(
                    f"deviceCreated: checking device {indigo.devices[deviceId].name} (ID {deviceId} address "
                    f"{indigo.devices[deviceId].pluginProps['address']}."
                )
                if (deviceId != device.id) and (devProps['address'] == indigo.devices[deviceId].pluginProps['address']):
                    self.errorLog(
                        f"{device.name} is configured to connect on the same IP address as \""
                        f"{indigo.devices[deviceId].name}\". Only one Indigo device can connect to the same Pioneer "
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
        try:
            self.debugLog(f"deviceStartComm called: {device}")
        except Exception as e:
            self.debugLog(f"deviceStartComm called: {device.name} (Unable to display device states due to error: {e})")
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
            if device.id not in self.deviceList:
                self.debugLog(f"deviceStartComm: adding vsx1021k deviceId {device.id} to deviceList.")
                self.deviceList.append(device.id)

        #
        # VSX-1022-K Device
        #
        if device.deviceTypeId == "vsx1022k":
            # Add this device to the list of devices associated with this plugin.
            if device.id not in self.deviceList:
                self.debugLog(f"deviceStartComm: adding vsx1022k deviceId {device.id} to deviceList.")
                self.deviceList.append(device.id)

        #
        # VSX-1122-K Device
        #
        if device.deviceTypeId == "vsx1122k":
            # Add this device to the list of devices associated with this plugin.
            if device.id not in self.deviceList:
                self.debugLog(f"deviceStartComm: adding vsx1122k deviceId {device.id} to deviceList.")
                self.deviceList.append(device.id)

        #
        # VSX-1123-K Device
        #
        if device.deviceTypeId == "vsx1123k":
            # Add this device to the list of devices associated with this plugin.
            if device.id not in self.deviceList:
                self.debugLog(f"deviceStartComm: adding vsx1123k deviceId {device.id} to deviceList.")
                self.deviceList.append(device.id)

        #
        # SC-75 Device
        #
        if device.deviceTypeId == "sc75":
            # Add this device to the list of devices associated with this plugin.
            if device.id not in self.deviceList:
                self.debugLog(f"deviceStartComm: adding sc75 deviceId {device.id} to deviceList.")
                self.deviceList.append(device.id)

        #
        # Virtual Volume Controller Device
        #
        if device.deviceTypeId == "virtualVolume":
            # Add this device to the list of volume devices associated with this plugin.
            if device.id not in self.volumeDeviceList:
                self.debugLog(
                    f"deviceStartComm: adding virtualVolume deviceId {device.id} to volumeDeviceList."
                )
                self.volumeDeviceList.append(device.id)
            # Update the device to the value of the receiver device control to which it is configured to virtualize.
            receiverDeviceId = int(device.pluginProps.get('receiverDeviceId', ""))
            controlDestination = device.pluginProps.get('controlDestination', "")
            if receiverDeviceId > 0 and len(controlDestination) > 0:
                # Query the receiver devices for volume and mute status. This will update the virtual volume controller.
                receiver = indigo.devices[receiverDeviceId]
                if receiver.states['connected']:
                    self.getVolumeStatus(receiver)
                    self.getMuteStatus(receiver)

    ########################################
    def deviceStopComm(self, device):
        self.debugLog(f"deviceStopComm called: {device.name}")
        #
        # VSX-1021-K Device
        #
        if device.deviceTypeId == "vsx1021k":
            # Remove this device from the list of devices associated with this plugin.
            if device.id in self.deviceList:
                self.deviceList.remove(device.id)
            # Make sure it's disconnected.
            if device.states['connected']:
                self.disconnect(device)

        #
        # VSX-1022-K Device
        #
        if device.deviceTypeId == "vsx1022k":
            # Remove this device from the list of devices associated with this plugin.
            if device.id in self.deviceList:
                self.deviceList.remove(device.id)
            # Make sure it's disconnected.
            if device.states['connected']:
                self.disconnect(device)

        #
        # VSX-1122-K Device
        #
        if device.deviceTypeId == "vsx1122k":
            # Remove this device from the list of devices associated with this plugin.
            if device.id in self.deviceList:
                self.deviceList.remove(device.id)
            # Make sure it's disconnected.
            if device.states['connected']:
                self.disconnect(device)

        #
        # VSX-1123-K Device
        #
        if device.deviceTypeId == "vsx1123k":
            # Remove this device from the list of devices associated with this plugin.
            if device.id in self.deviceList:
                self.deviceList.remove(device.id)
            # Make sure it's disconnected.
            if device.states['connected']:
                self.disconnect(device)

        #
        # SC-75 Device
        #
        if device.deviceTypeId == "sc75":
            # Remove this device from the list of devices associated with this plugin.
            if device.id in self.deviceList:
                self.deviceList.remove(device.id)
            # Make sure it's disconnected.
            if device.states['connected']:
                self.disconnect(device)

        #
        # Virtual Volume Controller Device
        #
        if device.deviceTypeId == "virtualVolume":
            # Remove this device from the list of level devices associated with this plugin.
            if device.id in self.volumeDeviceList:
                self.volumeDeviceList.remove(device.id)

    ########################################
    def didDeviceCommPropertyChange(self, origDev, newDev):
        # Automatically called by plugin host when device properties change.
        self.debugLog("didDeviceCommPropertyChange called.")
        #
        # VSX-1021-K, VSX-1022-K, VSX-1122-K, VSX-1123-K, or SC-75
        #
        if (
                origDev.deviceTypeId == "vsx1021k"
                or newDev.deviceTypeId == "vsx1022k"
                or newDev.deviceTypeId == "vsx1122k"
                or newDev.deviceTypeId == "vsx1123k"
                or newDev.deviceTypeId == "sc75"
        ):
            if origDev.pluginProps['address'] != newDev.pluginProps['address']:
                return True
            return False
        else:
            if origDev.pluginProps != newDev.pluginProps:
                return True
            return False

    ########################################
    def runConcurrentThread(self):
        self.debugLog("runConcurrentThread called.")
        # loopCount = 0  TODO: the only reference now. No longer necessary?
        #
        # Continuously loop through all receiver devices. Obtain any data that they might be providing and process it.
        #
        try:
            while True:
                # self.debugLog("runConcurrentThread while loop started.")
                self.sleep(0.1)
                # Cycle through each receiver device.
                for deviceId in self.deviceList:
                    response = ""
                    responseLine = ""
                    result = ""

                    connected = indigo.devices[deviceId].states.get('connected', False)

                    # Only proceed if we're connected.
                    if connected:
                        # Remove the device ID from the devicesWaitingToConnect dictionary.
                        if self.devicesWaitingToConnect.get(deviceId, -1) > -1:
                            del self.devicesWaitingToConnect[deviceId]
                        # Call the readData method with the device instance
                        # self.debugLog(f"Reading data for {indigo.devices[deviceId].name}.")
                        response = self.readData(indigo.devices[deviceId])
                        # If a response was returned, process it.
                        if response != "":
                            # There is often more than one line.  Process all of them.
                            for responseLine in response.splitlines():
                                result = self.processResponse(indigo.devices[deviceId], responseLine)
                                # If there was a result, send it to the log.
                                if result != "":
                                    indigo.server.log(result, indigo.devices[deviceId].name)
                    else:
                        # Since we're not connected, try to connect.
                        self.connect(indigo.devices[deviceId])

        except self.StopThread:
            self.debugLog("runConcurrentThread stopped.")
            # Cycle through each receiver device.
            for deviceId in self.deviceList:
                self.disconnect(indigo.devices[deviceId])

        self.debugLog("runConcurrentThread exiting.")

    ########################################
    # Core Custom Methods
    ########################################

    # Update Device State
    ########################################
    def updateDeviceState(self, device, state, newValue):
        # Change the device state on the server if it's different from the current state.
        if newValue != device.states[state]:
            try:
                self.debugLog(f"updateDeviceState: Updating device {device.name} state: {state} = {newValue}")
            except Exception as e:
                self.debugLog(
                    f"updateDeviceState: Updating device {device.name} state: (Unable to display state due to "
                    f"error: {e})")
            # If this is a floating point number, specify the maximum number of digits to make visible in the state.
            # Everything in this plugin only needs 1 decimal place of precision. If this isn't a floating point value,
            # don't specify a number of decimal places to display.
            if newValue.__class__.__name__ == 'float':
                device.updateStateOnServer(key=state, value=newValue, decimalPlaces=1)
            else:
                device.updateStateOnServer(key=state, value=newValue)

    # Update Device Properties
    ########################################
    def updateDeviceProps(self, device, newProps):
        # Change the properties for this device that are stored on the server.
        if device.pluginProps != newProps:
            self.debugLog(f"updateDeviceProps: Updating device {device.name} properties.")
            device.replacePluginPropsOnServer(newProps)

    # Connect to a Receiver Device
    ########################################
    def connect(self, device):
        # Display this debug message only once every 50 times the method is called.
        if (self.devicesWaitingToConnect.get(device.id, 0) % 10 == 0
                or self.devicesWaitingToConnect.get(device.id, 0) == 0):
            self.debugLog("connect method called.")

        connected = device.states['connected']
        devProps = device.pluginProps
        connecting = devProps.get('tryingToConnect', False)
        # Get the device address.
        receiverIp = devProps['address']

        # Display these debug messages only once every 50 times the method is called.
        if self.devicesWaitingToConnect.get(device.id, 0) % 50 == 0:
            self.debugLog(f"connect: {device.name} connected? {connected}")
            self.debugLog(f"connect: {device.name} connecting? {connecting}")

        # Only try to connect if we're not already connected and aren't trying to connect.
        if not connected and not connecting:
            connecting = True
            # Update the device properties just in case the properties aren't up-to-date.
            devProps['tryingToConnect'] = True
            self.updateDeviceProps(device, devProps)

            # Try to connect to the receiver.
            self.debugLog(f"connect: Connecting to {device.name} at {receiverIp}")
            try:
                self.updateDeviceState(device, 'status', "connecting")

                # Use the correct TCP port number based on device type.
                if device.deviceTypeId == "vsx1022k":
                    # The VSX-1022-K only accepts connections on port 8102.
                    self.tn[device.id] = telnetlib.Telnet(receiverIp, 8102)
                else:
                    # All other receivers accept connections on the standard telnet port.
                    self.tn[device.id] = telnetlib.Telnet(receiverIp)

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
                devProps['tryingToConnect'] = False
                self.updateDeviceProps(device, devProps)
                # Remove the device ID from the list of devices waiting to connect.
                waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
                if waitingCount > -1:
                    del self.devicesWaitingToConnect[device.id]

                # Now that we're connected, gather receiver status information.
                self.getReceiverStatus(device)

            except Exception as e:
                # If this was a connection refused error, report it.
                if "(61," in str(e):
                    self.errorLog(
                        f"Connection refused when trying to connect to {device.name}. Will try again in "
                        f"{float((CONNECTION_RETRY_DELAY / 10))} seconds."
                    )
                    # Increment the number of times we attempted to connect but reached this point because we were
                    # already trying to connect.
                    waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
                    if waitingCount > -1:
                        self.devicesWaitingToConnect[device.id] += 1
                    else:
                        self.devicesWaitingToConnect[device.id] = 1
                else:
                    self.errorLog(
                        f"Unable to establish a connection to {device.name}: {e}. Will try again in "
                        f"{float(CONNECTION_RETRY_DELAY / 10)} seconds."
                    )
                    # Increment the number of times we attempted to connect but reached this point because we were
                    # already trying to connect.
                    waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
                    if waitingCount > -1:
                        self.devicesWaitingToConnect[device.id] += 1
                    else:
                        self.devicesWaitingToConnect[device.id] = 1
            except self.StopThread:
                self.debugLog("connect: Cancelling connection attempt.")
                return

        elif not connected and connecting:
            # Increment the number of times we attempted to connect but reached this point because we were already
            # trying to connect.
            waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
            if waitingCount > -1:
                self.devicesWaitingToConnect[device.id] += 1
            else:
                self.devicesWaitingToConnect[device.id] = 1
            # If the number of times we've waited to connect is greater than connectionRetryDelay, then reset the
            # tryingToConnect property.
            if self.devicesWaitingToConnect.get(device.id, -1) > CONNECTION_RETRY_DELAY:
                connecting = False
                devProps['tryingToConnect'] = False
                self.updateDeviceProps(device, devProps)
                # Remove the device ID from the list of devices waiting to connect.
                waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
                if waitingCount > -1:
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
            devProps['tryingToConnect'] = False
            self.updateDeviceProps(device, devProps)
            # Remove the device ID from the list of devices waiting to connect.
            waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
            if waitingCount > -1:
                del self.devicesWaitingToConnect[device.id]

        # Display wait count in debug log.
        if self.devicesWaitingToConnect.get(device.id, 0) % 50 == 0:
            self.debugLog(f"connect: Connection wait count: {self.devicesWaitingToConnect.get(device.id, 0)}")

    # Disconnect from a Receiver Device
    #########################################
    def disconnect(self, device):
        self.debugLog("disconnect method called.")

        connected = device.states['connected']
        devProps = device.pluginProps
        connecting = devProps.get('tryingToConnect', False)

        # Disconnect the telnet session.
        try:
            self.tn[device.id].close()
            # Update the "status" device state.
            self.updateDeviceState(device, 'status', "disconnected")
            # Update the "connected" state on the server as well.
            self.updateDeviceState(device, 'connected', False)
            # Make sure the tryingToConnect device property is not on.
            devProps['tryingToConnect'] = False
            self.updateDeviceProps(device, devProps)
            self.debugLog(f"disconnect: {device.name} telnet connection is now closed.")
            # Remove the device ID from the list of devices waiting to connect (if it's in there).
            waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
            if waitingCount > -1:
                del self.devicesWaitingToConnect[device.id]
        except EOFError:
            self.debugLog(f"disconnect: Connection to {device.name} is already closed.")
            self.updateDeviceState(device, 'status', "disconnected")
            self.updateDeviceState(device, 'connected', False)
            devProps['tryingToConnect'] = False
            self.updateDeviceProps(device, devProps)
            self.debugLog(f"disconnect: {device.name} connection is already closed.")
            # Remove the device ID from the list of devices waiting to connect (if it's in there).
            waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
            if waitingCount > -1:
                del self.devicesWaitingToConnect[device.id]
        except Exception as e:
            self.errorLog(f"disconnect: Error disconnecting from {device.name}: {e}")
            self.updateDeviceState(device, 'status', "error")
            self.updateDeviceState(device, 'connected', False)
            devProps['tryingToConnect'] = False
            self.updateDeviceProps(device, devProps)
            self.debugLog(f"disconnect: {device.name} is now disconnected (error while disconnecting).")
            # Remove the device ID from the list of devices waiting to connect (if it's in there).
            waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
            if waitingCount > -1:
                del self.devicesWaitingToConnect[device.id]

    #########################################
    # Send a Command
    #########################################
    def sendCommand(self, device, command):
        # Get the device type. Future versions of this plugin will support other receiver models.
        devType = device.deviceTypeId

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if devType == "virtualVolume":
            self.errorLog(f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify "
                          f"the Indigo action to send the command \"{command}\" to a Pioneer receiver instead of this "
                          f"device.")
            return None

        # Get the device current connection status.
        connected = device.states['connected']
        # Get the device properties.
        devProps = device.pluginProps
        connecting = devProps.get('tryingToConnect', False)

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
                self.errorLog(
                    f"Connection to {device.name} lost while trying to send data. Will attempt to connect.")
                self.updateDeviceState(device, 'status', "disconnected")
                self.updateDeviceState(device, 'connected', False)
                self.connect(device)
            except Exception as e:
                # Unknown error.
                self.errorLog(f"Failed to send data to {device.name}: {e}")
                self.updateDeviceState(device, 'status', "error")
                self.updateDeviceState(device, 'connected', False)
        elif not connected and not connecting:
            # Show an error and try to connect.
            self.errorLog(
                f"Unable to send command to {device.name}. It is not connected. Attempting to re-connect.")
            self.connect(device)
        elif not connected and connecting:
            # Show an error indicating that we're still trying to connect.
            self.errorLog(f"Unable to send command to {device.name}. Still trying to connect to it.")

    #########################################
    # Read Data from a Receiver Connection
    #########################################
    def readData(self, device):

        response = ""

        # Get the device connection state and properties.
        connected = device.states['connected']
        devProps = device.pluginProps
        connecting = devProps.get('tryingToConnect', False)

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
            except Exception as e:
                # Unknown error.
                self.errorLog(f"Failed to receive data from {device.name}: {e}")
                self.updateDeviceState(device, 'status', "error")
                self.updateDeviceState(device, 'connected', False)
        elif not connected and not connecting:
            # Show an error and try to connect.
            self.errorLog(
                f"Unable to read data from {device.name}. It is not connected. Attempting to re-connect.")
            self.connect(device)
        elif not connected and connecting:
            # Show an error indicating that we're still trying to connect.
            self.errorLog(f"Unable to read data from {device.name}. Still trying to connect to it.")

        return response

    #########################################
    # Process a Command Response
    #########################################
    def processResponse(self, device, response):
        # Update the Indigo receiver device based on the response from the receiver.
        self.debugLog(f"processResponse: from: {device.name} response: {response}")

        # Get the type of device.  In the future, we'll support different receiver types.
        devType = device.deviceTypeId

        # Make a copy of the device properties, so we can change them if needed.
        devProps = device.pluginProps

        result = ""
        state = ""
        newValue = ""

        #
        # Test for each type of command response.
        #

        #
        # ERRORS
        #

        state = "status"
        newValue = "error"
        if response == "E02":
            self.errorLog(device.name + ": not available now.")
        elif response == "E03":
            self.errorLog(device.name + ": invalid command.")
        elif response == "E04":
            self.errorLog(device.name + ": command error.")
        elif response == "E06":
            self.errorLog(device.name + ": parameter error.")
        elif response == "B00":
            newValue = "busy"
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
                newValue = True
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
                newValue = False
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
                for theChannel, theName in CHANNEL_VOLUMES.items():
                    self.updateDeviceState(device, theName, 0)
                #   Set MCACC Memory number to 0.
                self.updateDeviceState(device, "mcaccMemory", 0)
                #   Clear the MCACC memory name.
                self.updateDeviceState(device, "mcaccMemoryName", "")
                # Look for Virtual Volume Controllers that might need setting to zero.
                for thisId in self.volumeDeviceList:
                    virtualVolumeDevice = indigo.devices[thisId]
                    controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                    if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                            and controlDestination == "zone1volume"):
                        self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
            elif response == "PWR2":
                # Power (zone 1) is off (network standby mode, only VSX-1022-K reports this).
                newValue = False
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
                for theChannel, theName in CHANNEL_VOLUMES.items():
                    self.updateDeviceState(device, theName, 0)
                #   Set MCACC Memory number to 0.
                self.updateDeviceState(device, "mcaccMemory", 0)
                #   Clear the MCACC memory name.
                self.updateDeviceState(device, "mcaccMemoryName", "")
                # Look for Virtual Volume Controllers that might need setting to zero.
                for thisId in self.volumeDeviceList:
                    virtualVolumeDevice = indigo.devices[thisId]
                    controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                    if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                            and controlDestination == "zone1volume"):
                        self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
        elif response.startswith("MUT"):
            # Mute (zone 1) status.
            state = "zone1mute"
            if response == "MUT0":
                # Mute is on.
                newValue = True
                if not device.states['zone1mute']:
                    result = "mute (zone 1): on"
                # Look for Virtual Volume Controllers that might need updating.
                for thisId in self.volumeDeviceList:
                    virtualVolumeDevice = indigo.devices[thisId]
                    controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                    if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                            and controlDestination == "zone1volume"):
                        self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
            elif response == "MUT1":
                # Mute is off.
                newValue = False
                if device.states['zone1mute']:
                    result = "mute (zone 1): off"
                # Look for Virtual Volume Controllers that might need updating.
                for thisId in self.volumeDeviceList:
                    virtualVolumeDevice = indigo.devices[thisId]
                    controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                    if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                            and controlDestination == "zone1volume"):
                        # Update the Virtual Volume Controller to match current volume. Get the receiver's volume.
                        theVolume = float(device.states[controlDestination])
                        # Convert the current volume of the receiver to a percentage to be displayed as a brightness
                        # level. If the volume is less than -80.5, the receiver is off and the brightness should be 0.
                        if float(theVolume) < -80.5:
                            theVolume = -80.5
                        theVolume = int(100 - round(theVolume / -80.5 * 100, 0))
                        self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', theVolume)
        elif response.startswith("FN"):
            # Source/function (zone 1) status.
            state = "zone1source"
            newValue = int(response[2:])
            # Check to see if zone 1 is already set to this input or if zone 1 power is off.  In either case, ignore
            # this update.
            if device.states[state] == newValue or not device.states['zone1power']:
                state = ""
                newValue = ""
        elif response.startswith("VOL"):
            # Volume (zone 1) status.
            state = "zone1volume"
            # Convert to dB.
            newValue = float(response[3:]) * 1.0
            newValue = -80.5 + 0.5 * newValue
            # Volume is at minimum or zone 1 power is off, volume is meaningless, so set it to minimum.
            if (newValue < -80.0) or (not device.states['zone1power']):
                newValue = -999.0
                result = "volume (zone 1): minimum."
            else:
                result = f"volume (zone 1): {newValue} dB"
            # Look for Virtual Volume Controllers that might need updating.
            self.debugLog(
                f"processResponse: Looking for connected Virtual Volume Controllers. volumeDeviceList: "
                f"{self.volumeDeviceList}"
            )
            for thisId in self.volumeDeviceList:
                virtualVolumeDevice = indigo.devices[thisId]
                self.debugLog(f"processResponse: Examining Virtual Volume Controller ID {thisId}")
                self.debugLog(f"processResponse: {virtualVolumeDevice}")
                controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id \
                        and controlDestination == "zone1volume":
                    self.debugLog(f"processResponse: Virtual Volume Controller ID {thisId} is connected.")
                    # Update the Virtual Volume Controller to match new volume.
                    theVolume = newValue
                    # Convert the current volume of the receiver to a percentage to be displayed as a brightness level.
                    # If the volume is less than -80.5, the receiver is off and the brightness should be 0.
                    if theVolume < -80.0:
                        theVolume = -80.5
                    theVolume = int(100 - round(theVolume / -80.5 * 100, 0))
                    self.debugLog(
                        f"processResponse: updating Virtual Volume Device ID {thisId} brightness level to {theVolume}."
                    )
                    self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', theVolume)
        #
        # Zone 2 Specific Items
        #
        elif response.startswith("APR"):
            # Power (zone 2) status.
            state = "zone2power"
            if response == "APR0":
                # Power (zone 2) is on.
                newValue = True
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
                newValue = False
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
                for thisId in self.volumeDeviceList:
                    virtualVolumeDevice = indigo.devices[thisId]
                    controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                    if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                            and controlDestination == "zone2volume"):
                        self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
        elif response.startswith("Z2F"):
            # Source/function (zone 2) status.
            state = "zone2source"
            newValue = int(response[3:])
            # Check to see if zone 2 is already set to this input or if zone 2 power is off.  If either is the case,
            # ignore this update.
            if device.states[state] == newValue or not device.states['zone2power']:
                state = ""
                newValue = ""
        elif response.startswith("Z2MUT"):
            # Mute (zone 2) status.
            state = "zone2mute"
            # If the speaker system arrangement is not set to A + Zone 2, zone mute and volume settings returned by
            # the receiver are meaningless. Set the state on the server to properly reflect this.
            if device.states['speakerSystem'] == "A + Zone 2":
                if response == "Z2MUT0":
                    # Mute is on.
                    newValue = True
                    result = "mute (zone 2): on"
                    # Look for Virtual Volume Controllers that might need updating.
                    for thisId in self.volumeDeviceList:
                        virtualVolumeDevice = indigo.devices[thisId]
                        controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                        if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                                and controlDestination == "zone2volume"):
                            self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
                elif response == "Z2MUT1":
                    # Mute is off.
                    newValue = False
                    result = "mute (zone 2): off"
                    # Look for Virtual Volume Controllers that might need updating.
                    for thisId in self.volumeDeviceList:
                        virtualVolumeDevice = indigo.devices[thisId]
                        controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                        if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                                and controlDestination == "zone2volume"):
                            # Update the Virtual Volume Controller to match current volume. Get the receiver's volume.
                            theVolume = float(device.states[controlDestination])
                            # Convert the current volume of the receiver to a percentage to be displayed as a
                            # brightness level. If the volume is less than -80.5, the receiver is off and the
                            # brightness should be 0.
                            if float(theVolume) < -81:
                                theVolume = -81
                            theVolume = int(100 - round(theVolume / -81 * 100, 0))
                            self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', theVolume)
            else:
                newValue = False
                result = ""
                # Zone 2 mute is meaningless when using the RCA line outputs, so look for Virtual Volume Controllers
                # that might need updating. If zone 2 power is on, the zone 2 line output will always be at 100% volume.
                if device.states['zone2power']:
                    for thisId in self.volumeDeviceList:
                        virtualVolumeDevice = indigo.devices[thisId]
                        controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                        if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                                and controlDestination == "zone2volume"):
                            self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 100)
                else:
                    # If zone 2 power is off, the zone 2 line output will always be at 0% volume.
                    for thisId in self.volumeDeviceList:
                        virtualVolumeDevice = indigo.devices[thisId]
                        controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                        if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                                and controlDestination == "zone2volume"):
                            self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
        elif response.startswith("ZV"):
            # Volume (zone 2) status.
            state = "zone2volume"
            # Convert to dB.
            newValue = int(response[2:])
            # newValue = -81 + newValue
            newValue += -81
            if newValue < -80 or not device.states['zone2power']:
                newValue = -999
                result = "volume (zone 2): minimum."
            else:
                result = f"volume (zone 2): {newValue} dB"
            # If the speaker system arrangement is not set to A + Zone 2, zone mute and volume settings returned by the
            # receiver are meaningless. Set the state on the server to properly reflect this.
            if device.states['speakerSystem'] == "A + Zone 2":
                # Look for Virtual Volume Controllers that might need updating.
                self.debugLog(
                    f"processResponse: Looking for zone 2 connected Virtual Volume Controllers. volumeDeviceList: "
                    f"{self.volumeDeviceList}"
                )
                for thisId in self.volumeDeviceList:
                    virtualVolumeDevice = indigo.devices[thisId]
                    self.debugLog(f"processResponse: Examining Virtual Volume Controller ID {thisId}")
                    self.debugLog(f"processResponse: {virtualVolumeDevice}")
                    controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                    if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                            and controlDestination == "zone2volume"):
                        self.debugLog(
                            f"processResponse: Virtual Volume Controller ID {thisId} is connected to zone 2 volume."
                        )
                        # Update the Virtual Volume Controller to match current volume. Get the receiver's volume.
                        theVolume = newValue
                        # Convert the current volume of the receiver to a percentage to be displayed as a brightness
                        # level. If the volume is less than -81, the receiver is off and the brightness should be 0.
                        if theVolume < -81:
                            theVolume = -81
                        theVolume = 100 - int(round(theVolume / -81.0 * 100, 0))
                        # If zone 2 power is on, use theVolume. If not, use zero.
                        if device.states['zone2power']:
                            self.debugLog(
                                f"processResponse: updating Virtual Volume Device ID {thisId} brightness level to "
                                f"{theVolume}"
                            )
                            self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', theVolume)
                        else:
                            self.debugLog(
                                f"processResponse: updating Virtual Volume Device ID {thisId} brightness level to 0"
                            )
                            self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
            else:
                newValue = 0
                result = ""
                # Zone 2 volume is meaningless when using the RCA line outputs, so look for Virtual Volume Controllers
                # that might need updating. If zone 2 power is on, the zone 2 line output will always be at 100% volume.
                if device.states['zone2power']:
                    for thisId in self.volumeDeviceList:
                        virtualVolumeDevice = indigo.devices[thisId]
                        controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                        if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                                and controlDestination == "zone2volume"):
                            self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 100)
                else:
                    # If zone 2 power is off, the zone 2 line output will always be at 0% volume.
                    for thisId in self.volumeDeviceList:
                        virtualVolumeDevice = indigo.devices[thisId]
                        controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
                        if (int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id
                                and controlDestination == "zone2volume"):
                            self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
        #
        # System-Wide Items
        #
        elif response.startswith("RGB"):
            # Source name update.
            newValue = response[6:]
            # Define the device property to update and make the change to the local copy.
            propName = f"source{response[3:5]}label"
            devProps[propName] = newValue
            # Update the source name in the device properties on the server.
            self.updateDeviceProps(device, devProps)
            # If the input source name update is for the currently selected zone 1 input source or zone 2 input source,
            # change the appropriate state in the device.
            if device.states['zone1source'] == int(response[3:5]):
                state = "zone1sourceName"
                result = f"input source (zone 1): {newValue}"
                self.updateDeviceState(device, state, newValue)
            if device.states['zone2source'] == int(response[3:5]):
                state = "zone2sourceName"
                result = f"input source (zone 2): {newValue}"
                self.updateDeviceState(device, state, newValue)
        elif response.startswith("FL"):
            # Display update.
            state = "display"
            newValue = ""
            # All characters after character 4 are ASCII representations of HEX numbers that represent ASCII characters
            # (!?)
            theString = response[4:]
            index = 0
            while index < 28:
                # Convert the 2-character HEX representations to actual ASCII values.
                #   -- Add "0x" to the front of the 2-character representation to indicate that it should be a HEX
                #      number.
                #   -- Use the "int" builtin to convert from ASCII base 16 to an integer.
                asciiVal = int(f"0x{theString[index:index + 2]}", 16)
                # Check for special characters.
                if asciiVal < 32 or asciiVal > 126:
                    # Add the special character to the newValue string from the character map dictionary defined at the
                    # top.
                    newValue += CHARACTER_MAP[asciiVal]
                else:
                    # Use the "chr" builtin to convert from integer to an ASCII character then add that to the existing
                    # newValue string.
                    # newValue += unicode(str(chr(asciiVal)))
                    newValue += f"{chr(asciiVal)}"
                # Increment the index by 2
                index += 2
        elif response.startswith("MC"):
            # MCACC Memory update.
            state = "mcaccMemory"
            newValue = int(response[2:])
            propName = f'mcaccMemory{newValue}label'
            mcaccName = devProps.get(propName, "")
            result = f"MCACC memory: {newValue}: {mcaccName}"
        elif response.startswith("IS"):
            # Phase Control update.
            state = "phaseControl"
            if response == "IS0":
                # Phase Control Off.
                newValue = "off"
            elif response == "IS1":
                # Phase Control On.
                newValue = "on"
            elif response == "IS2":
                # Full Band Phase Control On.
                newValue = "on - full band"
            result = f"Phase Control: {newValue}"
        elif response.startswith("VSP"):
            # Virtual Speakers.
            state = "vsp"
            if response == "VSP0":
                # Virtual Speakers Auto.
                newValue = "auto"
                result = "Virtual Speakers: auto"
            elif response == "VSP1":
                # Virtual Speakers Manual.
                newValue = "manual"
                result = "Virtual Speakers: manual"
        elif response.startswith("VSB"):
            # Virtual Surround Back update.
            state = "vsb"
            if response == "VSB0":
                # Virtual Surround Back Off.
                newValue = False
                result = "Virtual Surround Back: off"
            elif response == "VSB1":
                # Virtual Surround Back On.
                newValue = True
                result = "Virtual Surround Back: on"
        elif response.startswith("VHT"):
            # Virtual Surround Height update.
            state = "vht"
            if response == "VHT0":
                # Virtual Surround Height Off.
                newValue = False
                result = "Virtual Surround Height: off"
            elif response == "VSB1":
                # Virtual Surround Height On.
                newValue = True
                result = "Virtual Surround Height: on"
        elif response.startswith("CLV"):
            # Channel Volume Level update.
            channel = response[3:6]
            # Get the state name from the global dictionary defined at the top.
            state = CHANNEL_VOLUMES[channel]
            level = float(response[6:]) * 1.0
            # convert the level to decibels.
            newValue = -12 + 0.5 * (level - 26.0)
            result = f"{channel.strip('_')} channel level: {newValue} dB."
        elif response.startswith("SPK"):
            # Speaker mode update.
            state = "speakers"
            if response == "SPK0":
                # Speakers off.
                newValue = "off"
            elif response == "SPK1":
                # Speaker group A on.
                newValue = "on - A"
            elif response == "SPK2":
                # Speaker group B on.
                newValue = "on - B"
            elif response == "SPK3":
                # Both speaker groups A and B on.
                newValue = "on - A+B"
            result = f"speaker mode: {newValue}"
        elif response.startswith("HA"):
            # HDMI Audio Pass-through update.
            state = "hdmiAudio"
            if response == "HA0":
                # HDMI Audio processed by amp.
                newValue = False
                result = "HDMI Audio Pass-Through: off"
            elif response == "HA1":
                # HDMI Audio passed through unaltered.
                newValue = True
                result = "HDMI Audio Pass-Through: on"
        elif response.startswith("PQ"):
            # PQLS status update.
            state = "pqls"
            if response == "PQ0":
                # PQLS off.
                newValue = False
                result = "PQLS: off"
            elif response == "PQ1":
                # PQLS auto.
                newValue = True
                result = "PQLS: on"
        elif response.startswith("SSA"):
            # Operating Mode.
            state = "operatingMode"
            if response == "SSA0":
                # Expert Mode.
                newValue = "Expert"
            elif response == "SSA1":
                # reserved mode.
                newValue = "(factory reserved)"
            elif response == "SSA2":
                # Basic Mode.
                newValue = "Basic"
            result = f"operating mode: {newValue}"
        elif response.startswith("SSE"):
            # OSD Language setting.
            if response == "SSE00":
                newValue = "English"
            else:
                newValue = "non-English"
            # Define the device property to update and make the change to the local copy.
            propName = 'osdLanguage'
            devProps[propName] = newValue
            # Update the source name in the device properties on the server.
            self.updateDeviceProps(device, devProps)
        elif response.startswith("SSF"):
            # Speaker System status.
            state = "speakerSystem"
            if response == "SSF00":
                newValue = "A + Surround Height"
            if response == "SSF01":
                newValue = "A + Surround Width"
            if response == "SSF02":
                newValue = "A Bi-Amped"
            if response == "SSF03":
                newValue = "A + B 2-Channel"
            if response == "SSF04":
                newValue = "A + Zone 2"
            result = f"speaker system layout: {newValue}"
        elif response.startswith("SAA"):
            # Dimmer Brightness change.
            if response == "SAA0":
                newValue = "bright"
            elif response == "SAA1":
                newValue = "medium"
            elif response == "SAA2":
                newValue = "dim"
            elif response == "SAA3":
                newValue = "off"
        elif response.startswith("SAB"):
            # Sleep Timer time remaining.
            state = "sleepTime"
            newValue = int(response[3:])
            if newValue == 0:
                # Sleep timer is off
                self.updateDeviceState(device, "sleepMode", False)
                result = "sleep timer: off"
            else:
                # Sleep timer is on
                self.updateDeviceState(device, "sleepMode", True)
                result = f"sleep timer: {newValue} minutes remaining."
        elif response.startswith("PKL"):
            # Panel Key Lock status.
            state = "panelKeyLockMode"
            if response == "PKL0":
                # Unlocked.
                newValue = "off"
            elif response == "PKL1":
                # Panel locked.
                newValue = "on - panel"
            elif response == "PKL2":
                # Panel and volume locked.
                newValue = "on - panel+volume"
            result = f"front panel lock: {newValue}"
        elif response.startswith("RML"):
            # Remote Lock Mode status.
            state = "remoteLock"
            if response == "RML0":
                newValue = False
                result = "remote control lock: off"
            elif response == "RML1":
                newValue = True
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
                frequencyText = frequency
                if band == "FM":
                    # If the band is FM, put the decimal in the right place.
                    frequencyText = f"{frequency[0:3]}.{frequency[3:]} MHz"
                    frequencyText = frequencyText.lstrip("0")  # Eliminate leading zeros.
                    frequency = float(f"{frequency[0:3]}.{frequency[3:]}")
                elif band == "AM":
                    # If the band is AM, convert the text to an integer.
                    frequency = int(frequency)  # Eliminates leading zeros.
                    frequencyText = f"{frequency} kHz"
                # Only log the change if the frequency is actually different.
                if frequency != device.states['tunerFrequency'] or band != device.states['tunerBand']:
                    result = f"tuner frequency: {frequencyText} {band}"
                # Set the tuner frequency on the server
                newValue = frequency
        elif response.startswith("PR"):
            # Tuner Preset update. Only update the state if either zone 1 or 2 is actually using the Tuner.
            if device.states['zone1source'] == 2 or device.states['zone2source'] == 2:
                state = "tunerPreset"
                # Get the preset letter plus the non-leading-zero number.
                newValue = response[2:3] + str(int(response[3:]))
                # Now add the custom name (if set) for the preset.
                propName = f"tunerPreset{newValue}label"
                newValue += f": {device.pluginProps[propName]}"
                # Ignore this information if the state is already set to this setting.
                if device.states[state] == newValue:
                    state = ""
                    newValue = ""
                else:
                    result = f"tuner preset: {newValue}"
        elif response.startswith("TQ"):
            # Tuner Preset Label update.
            newValue = response[4:]  # Strip off the "TQ"
            newValue = newValue.strip('"')  # Remove the enclosing quotes.
            newValue = newValue.strip()  # Remove the white space.
            # Define the device property to update and make the change to the local copy.
            propName = f"tunerPreset{response[2:4]}label"
            devProps[propName] = newValue
            # Update the source name in the device properties on the server.
            self.updateDeviceProps(device, devProps)
        elif response.startswith("SR"):
            # Listening Mode update.
            state = "listeningMode"
            newValue = LISTENING_MODES[response[2:]]
            # Ignore this information if the state is already set to this setting.
            if device.states[state] == newValue:
                state = ""
                newValue = ""
            else:
                result = f"listening mode: {newValue}"
        elif response.startswith("LM"):
            # Playback Listening Mode update.
            state = "displayListeningMode"
            newValue = DISPLAY_LISTENING_MODES[response[2:]]
            # Ignore this information if the state is already set to this setting.
            if device.states[state] == newValue:
                state = ""
                newValue = ""
            else:
                result = f"displayed listening mode: {newValue}"
        elif response.startswith("TO"):
            # Tone Control on/off change.
            state = "toneControl"
            if response == "TO0":
                newValue = False
                result = "tone control: off"
            elif response == "TO1":
                newValue = True
                result = "tone control: on"
        elif response.startswith("BA"):
            # Bass Tone Control change.
            state = "toneBass"
            newValue = (6 - int(response[2:]))
            result = f"bass tone level: {newValue} dB"
        elif response.startswith("TR"):
            # Treble Tone Control change.
            state = "toneTreble"
            newValue = (6 - int(response[2:]))
            result = f"bass tone level: {newValue} dB"
        elif response.startswith("ATA"):
            # Sound Retriever status change.
            state = "soundRetriever"
            if response == "ATA0":
                newValue = False
                result = "Sound Retriever: off"
            elif response == "ATA1":
                newValue = True
                result = "Sound Retriever: on"
        elif response.startswith("SDA"):
            # Signal Source selection.
            state = "signalSource"
            if response == "SDA0":
                newValue = "AUTO"
            elif response == "SDA1":
                newValue = "ANALOG"
            elif response == "SDA2":
                newValue = "DIGITAL"
            elif response == "SDA3":
                newValue = "HDMI"
            result = f"audio signal source: {newValue}"
        elif response.startswith("SDB"):
            # Analog Input Attenuator status.
            state = "analogInputAttenuator"
            if response == "SDB0":
                newValue = False
                result = "analog input attenuator: off"
            elif response == "SDB1":
                newValue = True
                result = "analog input attenuator: on"
        elif response.startswith("ATC"):
            # Equalizer status.
            state = "equalizer"
            if response == "ATC0":
                newValue = False
                result = "equalizer: off"
            elif response == "ATC1":
                newValue = True
                result = "equalizer: on"
            # Don't update the state if it's the same.
            if device.states[state] == newValue:
                state = ""
                newValue = ""
                result = ""
        elif response.startswith("ATD"):
            # Standing Wave compensation status.
            state = "standingWave"
            if response == "ATD0":
                newValue = False
                result = "standing wave compensation: off"
            elif response == "ATD1":
                newValue = True
                result = "standing wave compensation: on"
            # Don't update the state if it's the same.
            if device.states[state] == newValue:
                state = ""
                newValue = ""
                result = ""
        elif response.startswith("ATE"):
            # Phase Control Plus delay time (ms) change.
            state = "phaseControlPlusTime"
            newValue = int(response[3:])
            result = f"Phase Control Plus time: {newValue} ms"
        elif response.startswith("ATF"):
            # Sound Delay time (fractional sample frames) change.
            state = "soundDelay"
            newValue = (float(response[3:]) / 10.0)
            result = f"sound delay: {newValue} sample frames"
        elif response.startswith("ATG"):
            # Digital Noise Reduction status.
            state = "digitalNR"
            if response == "ATG0":
                newValue = False
                result = "Digital Noise Reduction: off"
            elif response == "ATG1":
                newValue = True
                result = "Digital Noise Reduction: on"
        elif response.startswith("ATH"):
            # Dialog Enhancement change.
            state = "dialogEnhancement"
            if response == "ATH0":
                newValue = "off"
            elif response == "ATH1":
                newValue = "flat"
            elif response == "ATH2":
                newValue = "up1"
            elif response == "ATH3":
                newValue = "up2"
            elif response == "ATH4":
                newValue = "up3"
            elif response == "AHT5":
                newValue = "up4"
            result = f"Dialog Enhancement mode: {newValue}"
        elif response.startswith("ATI"):
            # Hi-bit 24 status.
            state = "hiBit24"
            if response == "ATI0":
                newValue = False
                result = "Hi-bit 24: off"
            elif response == "ATI1":
                newValue = True
                result = "Hi-bit 24: on"
        elif response.startswith("ATJ"):
            # Dual Mono processing change.
            state = "dualMono"
            if response == "ATJ0":
                newValue = False
                result = "Dual Mono sound processing: off"
            elif response == "ATJ1":
                newValue = True
                result = "Dual Mono sound processing: on"
        elif response.startswith("ATK"):
            # Fixed PCM rate processing change.
            state = "fixedPCM"
            if response == "ATK0":
                newValue = False
                result = "fixed rate PCM: off"
            elif response == "ATK1":
                newValue = True
                result = "fixed rate PCM: on"
        elif response.startswith("ATL"):
            # Dynamic Range Compression mode change.
            state = "dynamicRangeCompression"
            if response == "ATL0":
                newValue = "off"
            elif response == "ATL1":
                newValue = "auto"
            elif response == "ATL2":
                newValue = "mid"
            elif response == "ATL3":
                newValue = "max"
            result = f"Dynamic Range Compression: {newValue}"
        elif response.startswith("ATM"):
            # LFE Attenuation change.
            state = "lfeAttenuatorAmount"
            newValue = (-5 * int(response[3:]))
            result = f"LFE attenuation amount: {newValue} dB"
            if newValue < -20:
                # A response of ATM5 translates to the attenuator being turned off.
                self.updateDeviceState(device, "lfeAttenuator", False)
                result = "LFE attenuation: off"
            else:
                self.updateDeviceState(device, "lfeAttenuator", True)
        elif response.startswith("ATN"):
            # SACD Gain change.
            state = "sacdGain"
            if response == "ATN0":
                newValue = 0
            elif response == "ATN1":
                newValue = 6
            result = f"SACD gain: {newValue} dB"
        elif response.startswith("ATO"):
            # Auto Sound Delay status update.
            state = "autoDelay"
            if response == "ATO0":
                newValue = False
                result = "Auto Sound Delay: off"
            elif response == "ATO1":
                newValue = True
                result = "Auto Sound Delay: on"
        elif response.startswith("ATP"):
            # Dolby Pro Logic II Music Center Width change.
            state = "pl2musicCenterWidth"
            newValue = int(response[3:])
            result = f"Dolby Pro Logic II Music center width: {newValue}"
        elif response.startswith("ATQ"):
            # Dolby Pro Logic II Music Panorama status.
            state = "pl2musicPanorama"
            if response == "ATQ0":
                newValue = False
                result = "Dolby Pro Logic II Music panorama: off"
            elif response == "ATQ1":
                newValue = True
                result = "Dolby Pro Logic II Music panorama: on"
        elif response.startswith("ATR"):
            # Dolby Pro Logic II Music Dimension level change.
            state = "pl2musicDimension"
            newValue = (int(response[3:]) - 50)
            result = f"Dolby Pro Logic II Music dimension: {newValue}"
        elif response.startswith("ATS"):
            # Neo:6 Center Image change.
            state = "neo6centerImage"
            newValue = (float(response[3:]) / 10.0)
            result = f"Neo:6 center image: {newValue}"
        elif response.startswith("ATT"):
            # Effect amount change.
            state = "effectAmount"
            newValue = (int(response[3:]) * 10)
            result = f"effect level: {newValue}"
        elif response.startswith("ATU"):
            # Dolby Pro Logic IIz Height Gain change.
            state = "pl2zHeightGain"
            if response == "ATU0":
                newValue = "LOW"
            elif response == "ATU1":
                newValue = "MID"
            elif response == "ATU2":
                newValue = "HIGH"
            result = f"Dolby Pro Logic IIz height gain: {newValue}"
        elif response.startswith("VTB"):
            # Video Converter update.
            state = "videoConverter"
            if response == "VTB0":
                # Video Converter Off.
                newValue = False
                result = "video converter: off"
            elif response == "VTB1":
                # Video Converter On.
                newValue = True
                result = "video converter: on"
        elif response.startswith("VTC"):
            # Video Resolution update.
            state = "videoResolution"
            newValue = VIDEO_RESOLUTION_PREFS[response[3:]]
            result = f"preferred video resolution: {newValue}"
        elif response.startswith("VTD"):
            # Video Pure Cinema mode update.
            state = "videoPureCinema"
            if response == "VTD0":
                # Pure Cinema Auto.
                newValue = "auto"
            elif response == "VTD1":
                # Pure Cinema On.
                newValue = "on"
            elif response == "VTD2":
                # Pure Cinema Off.
                newValue = "off"
            result = f"Pure Cinema mode: {newValue}"
        elif response.startswith("VTE"):
            # Video Progressive Motion Quality update.
            state = "videoProgressiveQuality"
            newValue = -4 + (int(response[3:]) - 46)
            result = f"video progressive scan motion quality: {newValue}"
        elif response.startswith("VTG"):
            # Video Advanced Adjustment update.
            state = "videoAdvancedAdjust"
            if response == "VTG0":
                # PDP (Plasma Display Panel)
                newValue = "PDP (Plasma)"
            elif response == "VTG1":
                # LCD (Liquid Crystal Display)
                newValue = "LCD"
            elif response == "VTG2":
                # FPJ (Front Projection)
                newValue = "FPJ (Front Projection)"
            elif response == "VTG3":
                # Professional
                newValue = "Professional"
            elif response == "VTG4":
                # Memory
                newValue = "Memory"
            result = f"Advanced Video Adjustment: {newValue}"
        elif response.startswith("VTH"):
            # Video YNR (Luminance Noise Reduction) update.
            state = "videoYNR"
            newValue = int(response[3:]) - 50
            result = f"video YNR: {newValue}"
        elif response.startswith("VTL"):
            # Video Detail Adjustment update.
            state = "videoDetail"
            newValue = 50 - int(response[3:])
            result = f"video detail amount: {newValue}"
        elif response.startswith("AST"):
            # Audio Status information update. Multiple data are provided in this response (43 bytes, or 55 for
            # VSX-1123-K).
            state = ""
            newValue = ""
            data = response[3:]  # strip the AST text.

            # == Data Common to All Models ==
            audioInputFormat = data[0:2]  # 2-byte signal format code.
            # Convert signal format code to a named format.
            audioInputFormat = AUDIO_INPUT_FORMATS[audioInputFormat]
            state = "audioInputFormat"
            newValue = audioInputFormat
            self.updateDeviceState(device, state, newValue)

            audioInputFrequency = data[2:4]  # 2-byte sample frequency code.
            # Convert sample frequency code to a value.
            audioInputFrequency = AUDIO_INPUT_FREQUENCIES[audioInputFrequency]
            state = "audioInputFrequency"
            newValue = audioInputFrequency
            self.updateDeviceState(device, state, newValue)

            state = "inputChannels"
            newValue = ""
            # Convert data bytes 5-25 into an input channel format string. Loop through data bytes and add channels
            # that are enabled.
            state = "inputChannels"
            newValue = ""
            for i in range(5, 26):
                if data[(i - 1):i] == "1":
                    # Add a comma if this is not the first item.
                    if newValue is not "":
                        newValue += ", "
                    newValue += AUDIO_CHANNELS[(i - 5)]
            self.updateDeviceState(device, state, newValue)

            # Convert data bytes 26-43 into an output channel format string. Loop through data bytes and add channels
            # that are enabled.
            state = "outputChannels"
            newValue = ""
            for i in range(26, 44):
                if data[(i - 1):i] == "1":
                    # Add a comma if this is not the first item.
                    if newValue is not "":
                        newValue += ", "
                    newValue += AUDIO_CHANNELS[(i - 26)]
            self.updateDeviceState(device, state, newValue)

            # The VSX-1123-K responds with a 55 instead of 43 characters. These extra data represent features found
            # only in this and other 2014 models.
            if device.deviceTypeId == "vsx1123k":
                audioOutputFrequency = data[43:45]  # 2-byte sample frequency code.
                # Convert sample frequency code to a value.
                audioOutputFrequency = AUDIO_OUTPUT_FREQUENCIES[audioOutputFrequency]
                state = "audioOutputFrequency"
                newValue = audioOutputFrequency
                self.updateDeviceState(device, state, newValue)

                audioOutputBitDepth = data[45:47]  # 2-byte sample bit depth value.
                # Convert sample bit depth from a string to a number.
                audioOutputBitDepth = int(audioOutputBitDepth)
                state = "audioOutputBitDepth"
                newValue = audioOutputBitDepth
                self.updateDeviceState(device, state, newValue)

                # Bytes 48 through 51 are reserved.

                pqlsMode = data[51:52]  # 1-byte PQLS working mode code.
                # Convert PQLS code to working state.
                if pqlsMode == "0":
                    pqlsMode = "off"
                elif pqlsMode == "1":
                    pqlsMode = "2-channel"
                elif pqlsMode == "2":
                    pqlsMode = "multi-channel"
                elif pqlsMode == "3":
                    pqlsMode = "bitstream"
                state = "pqlsMode"
                newValue = pqlsMode
                self.updateDeviceState(device, state, newValue)

                phaseControlPlusWorkingDelay = data[52:54]  # 2-byte Phase Control Plus working delay (ms).
                # Convert Phase Control Plus string to number.
                phaseControlPlusWorkingDelay = int(phaseControlPlusWorkingDelay)
                state = "phaseControlPlusWorkingTime"
                newValue = phaseControlPlusWorkingDelay
                self.updateDeviceState(device, state, newValue)

                phaseControlPlusReversed = data[54:55]  # 1-byte Phase Control Plus reversed phase.
                # Translate Phase Control Plus reversed state.
                if phaseControlPlusReversed == "0":
                    phaseControlPlusReversed = True
                elif phaseControlPlusReversed == "1":
                    phaseControlPlusReversed = False
                state = "phaseControlPlusReversed"
                newValue = phaseControlPlusReversed
                self.updateDeviceState(device, state, newValue)

            result = "audio input/output information updated"

        elif response.startswith("VST"):
            # Video Status information update. Multiple data are provided in this response.
            state = ""
            newValue = ""
            data = response[3:]  # Strip off the leading "VST".

            # Video Input Terminal
            state = "videoInputTerminal"
            newValue = int(data[0:1])
            if newValue == 0:
                newValue = ""
            elif newValue == 1:
                newValue = "Video"
            elif newValue == 2:
                newValue = "S-Video"
            elif newValue == 3:
                newValue = "Component"
            elif newValue == 4:
                newValue = "HDMI"
            elif newValue == 5:
                newValue = "Self (OSD/JPEG)"
            self.updateDeviceState(device, state, newValue)

            # Video Input Resolution
            state = "videoInputResolution"
            newValue = VIDEO_RESOLUTIONS[data[1:3]]
            self.updateDeviceState(device, state, newValue)

            # Video Input Aspect Ratio
            state = "videoInputAspect"
            newValue = int(data[3:4])
            if newValue == 0:
                newValue = ""
            elif newValue == 1:
                newValue = "4:3"
            elif newValue == 2:
                newValue = "16:9"
            elif newValue == 3:
                newValue = "14:9"
            self.updateDeviceState(device, state, newValue)

            # Video Input Color Format
            state = "videoInputColorFormat"
            newValue = int(data[4:5])
            if newValue == 0:
                newValue = ""
            elif newValue == 1:
                newValue = "RGB Limited"
            elif newValue == 2:
                newValue = "RGB Full"
            elif newValue == 3:
                newValue = "YCbCr 4:4:4"
            elif newValue == 4:
                newValue = "YCbCr 4:2:2"
            self.updateDeviceState(device, state, newValue)

            # Video Input Bit Depth
            state = "videoInputBitDepth"
            newValue = int(data[5:6])
            if newValue == 0:
                newValue = ""
            elif newValue == 1:
                newValue = "24-bit (8-bit per pixel)"
            elif newValue == 2:
                newValue = "30-bit (10-bit per pixel)"
            elif newValue == 3:
                newValue = "36-bit (12-bit per pixel)"
            elif newValue == 4:
                newValue = "48-bit (16-bit per pixel)"
            self.updateDeviceState(device, state, newValue)

            # Video Input Color Space
            state = "videoInputColorSpace"
            newValue = int(data[6:7])
            if newValue == 0:
                newValue = ""
            elif newValue == 1:
                newValue = "Standard"
            elif newValue == 2:
                newValue = "xv.Color YCC 601"
            elif newValue == 3:
                newValue = "xv.Color YCC 709"
            elif newValue == 4:
                newValue = "sYCC"
            elif newValue == 5:
                newValue = "Adobe YCC 601"
            elif newValue == 6:
                newValue = "Adobe RGB"
            self.updateDeviceState(device, state, newValue)

            # Video Output Resolution
            state = "videoOutputResolution"
            newValue = VIDEO_RESOLUTIONS[data[7:9]]
            self.updateDeviceState(device, state, newValue)

            # Video Output Aspect Ratio
            state = "videoOutputAspect"
            newValue = int(data[9:10])
            if newValue == 0:
                newValue = ""
            elif newValue == 1:
                newValue = "4:3"
            elif newValue == 2:
                newValue = "16:9"
            elif newValue == 3:
                newValue = "14:9"
            self.updateDeviceState(device, state, newValue)

            # Video Output Color Format
            state = "videoOutputColorFormat"
            newValue = int(data[10:11])
            if newValue == 0:
                newValue = ""
            elif newValue == 1:
                newValue = "RGB Limited"
            elif newValue == 2:
                newValue = "RGB Full"
            elif newValue == 3:
                newValue = "YCbCr 4:4:4"
            elif newValue == 4:
                newValue = "YCbCr 4:2:2"
            self.updateDeviceState(device, state, newValue)

            # Video Output Bit Depth
            state = "videoOutputBitDepth"
            newValue = int(data[11:12])
            if newValue == 0:
                newValue = ""
            elif newValue == 1:
                newValue = "24-bit (8-bit per pixel)"
            elif newValue == 2:
                newValue = "30-bit (10-bit per pixel)"
            elif newValue == 3:
                newValue = "36-bit (12-bit per pixel)"
            elif newValue == 4:
                newValue = "48-bit (16-bit per pixel)"
            self.updateDeviceState(device, state, newValue)

            # Video Output Color Space
            state = "videoOutputColorSpace"
            newValue = int(data[12:13])
            if newValue == 0:
                newValue = ""
            elif newValue == 1:
                newValue = "Standard"
            elif newValue == 2:
                newValue = "xv.Color YCC 601"
            elif newValue == 3:
                newValue = "xv.Color YCC 709"
            elif newValue == 4:
                newValue = "sYCC"
            elif newValue == 5:
                newValue = "Adobe YCC 601"
            elif newValue == 6:
                newValue = "Adobe RGB"
            self.updateDeviceState(device, state, newValue)

            # Monitor Recommended Resolution (HDMI 1)
            state = "monitorRecommendedResolution"
            newValue = VIDEO_RESOLUTIONS[data[13:15]]
            self.updateDeviceState(device, state, newValue)

            # Monitor Bit Depth Support
            state = "monitorBitDepth"
            newValue = int(data[15:16])
            if newValue == 0:
                newValue = ""
            elif newValue == 1:
                newValue = "24-bit (8-bit per pixel)"
            elif newValue == 2:
                newValue = "30-bit (10-bit per pixel)"
            elif newValue == 3:
                newValue = "36-bit (12-bit per pixel)"
            elif newValue == 4:
                newValue = "48-bit (16-bit per pixel)"
            self.updateDeviceState(device, state, newValue)

            # Monitor Supported Color Spaces (HDMI 1)
            state = "monitorColorSpaces"
            newValue = ""
            colorSpaces = data[16:21]
            if colorSpaces[0:1] == "1":
                newValue += "xv.Color YCC 601"
            if colorSpaces[1:2] == "1":
                if len(newValue) > 0:
                    newValue += ", "
                newValue += "xv.Color YCC 709"
            if colorSpaces[2:3] == "1":
                if len(newValue) > 0:
                    newValue += ", "
                newValue += "xYCC"
            if colorSpaces[3:4] == "1":
                if len(newValue) > 0:
                    newValue += ", "
                newValue += "Adobe YCC 601"
            if colorSpaces[4:5] == "1":
                if len(newValue) > 0:
                    newValue += ", "
                newValue += "Adobe RGB"
            self.updateDeviceState(device, state, newValue)

            result = "video input/output information updated"

        else:
            # Unrecognized response received.
            self.debugLog(f"Unrecognized response received from {device.name}: {response}")
            newValue = "unknown"

        getStatusUpdate = False  # Should we perform a full status update?

        # Only update the device if the state is not blank.
        if state != "":
            # If this is a zone power state change to True and the current zone power state is False, get more status
            # information.
            if (state == "zone1power" and newValue and not device.states['zone1power']) or (
                    state == "zone2power" and newValue and not device.states['zone2power']):
                getStatusUpdate = True

            # Update the state on the server.
            self.updateDeviceState(device, state, newValue)

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
            self.updateDeviceState(device, 'mcaccMemoryName', mcaccName)

        elif state == "tunerFrequency":
            # Also set the tunerFrequencyText.
            # TODO: 'frequencyText' might be referenced before assignment
            self.updateDeviceState(device, 'tunerFrequencyText', frequencyText)

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
        if getStatusUpdate:
            self.getReceiverStatus(device)

        return result

    #########################################
    # Information Gathering Methods
    #########################################
    #
    # Current Display Content
    #
    def getDisplayContent(self, device):
        self.debugLog(f"getDisplayContent: Getting {device.name} display content.")

        # Get th device type. Future versions of this plugin will support other receiver models.
        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            self.sendCommand(device, "?FL")  # Display Content Query.
            self.sleep(0.1)  # Wait for responses to be processed.

    #
    # Power Status
    #
    def getPowerStatus(self, device):
        self.debugLog(f"getPowerStatus: Getting {device.name} power status.")

        # Get th device type. Future versions of this plugin will support other receiver models.
        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            self.sendCommand(device, "?P")  # Power Query (Zone 1).
            self.sleep(0.1)  # Wait for responses to be processed.
            self.sendCommand(device, "?AP")  # Power Query (Zone 2).
            self.sleep(0.1)

            # It's important that we get the result of this status request before proceeding.
            response = self.readData(device)
            response = response.rstrip("\r\n")
            for responseLine in response.splitlines():
                result = self.processResponse(device, responseLine)
                if result != "":
                    indigo.server.log(result, device.name)

    #
    # Input Source Names
    #
    def getInputSourceNames(self, device):
        self.debugLog(f"getInputSourceNames: Getting {device.name} input source names.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            # Get the names of all the input sources.
            for theNumber, theName in SOURCE_NAMES.items():
                # Only ask for information on sources recognized by the device type.
                #   VSX-1021-K
                if devType is "vsk1021k":
                    if theNumber not in VSX1021k_SOURCE_MASK:
                        self.sendCommand(device, f"?RGB{theNumber}")
                        self.sleep(0.1)  # Wait for responses to be processed.
                #   VSX-1022-K
                if devType is "vsk1022k":
                    if theNumber not in VSX1022K_SOURCE_MASK:
                        self.sendCommand(device, f"?RGB{theNumber}")
                        self.sleep(0.1)  # Wait for responses to be processed.
                #   VSX-1122-K
                if devType is "vsk1122k":
                    if theNumber not in VSX1122K_SOURCE_MASK:
                        self.sendCommand(device, f"?RGB{theNumber}")
                        self.sleep(0.1)  # Wait for responses to be processed.
                #   VSX-1123-K
                if devType is "vsk1123k":
                    if theNumber not in VSX1123K_SOURCE_MASK:
                        self.sendCommand(device, f"?RGB{theNumber}")
                        self.sleep(0.1)  # Wait for responses to be processed.
                #   SC-75
                if devType is "sc75":
                    if theNumber not in SC75_SOURCE_MASK:
                        self.sendCommand(device, f"?RGB{theNumber}")
                        self.sleep(0.1)  # Wait for responses to be processed.

    #
    # Tuner Preset Names
    #
    def getTunerPresetNames(self, device):
        self.debugLog(f"getTunerPresetNames: Getting {device.name} tuner preset station names.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            self.sendCommand(device, "?TQ")  # Tuner Preset label query.
            self.sleep(0.2)

    #
    # Tuner Band and Frequency
    #
    def getTunerFrequency(self, device):
        self.debugLog(f"getTunerFrequency: Getting {device.name} tuner band and frequency.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            self.sendCommand(device, "?FR")
            self.sleep(0.1)

    #
    # Tuner Preset Status
    #
    def getTunerPresetStatus(self, device):
        self.debugLog(f"getTunerPresetStatus: Getting {device.name} tuner preset status.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            self.sendCommand(device, "?PR")
            self.sleep(0.1)

    #
    # Volume Status (Zones 1 and 2)
    #
    def getVolumeStatus(self, device):
        self.debugLog(f"getVolumeStatus: Getting {device.name} volume status.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            self.sendCommand(device, "?V")  # Volume Query (Zone 1)
            self.sleep(0.1)
            self.sendCommand(device, "?ZV")  # Volume Query (Zone 2)
            self.sleep(0.1)

    #
    # Mute Status (Zones 1 and 2)
    #
    def getMuteStatus(self, device):
        self.debugLog(f"getMuteStatus: Getting {device.name} mute status.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            self.sendCommand(device, "?M")  # Mute Query (Zone 1)
            self.sleep(0.1)
            self.sendCommand(device, "?Z2M")  # Mute Query (Zone 2)
            self.sleep(0.1)

    #
    # Input Source Status (Zones 1 and 2)
    #
    def getInputSourceStatus(self, device):
        self.debugLog(f"getInputSourceStatus: Getting {device.name} input source status.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            self.sendCommand(device, "?F")  # Input Source Query (Zone 1)
            self.sleep(0.1)
            self.sendCommand(device, "?ZS")  # Input Source Query (Zone 2)
            self.sleep(0.1)

    #
    # Channel Volume Levels
    #
    def getChannelVolumeLevels(self, device):
        self.debugLog(f"getChannelVolumeLevels: Getting {device.name} individual channel volume levels.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            for theChannel, theState in CHANNEL_VOLUMES.items():
                self.sendCommand(device, f"?{theChannel}CLV")
                self.sleep(0.1)

    #
    # System Setup Status
    #
    def getSystemSetupStatus(self, device):
        self.debugLog(f"getSystemSetupStatus: Getting {device.name} system settings.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
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
        self.debugLog(f"getAudioDspSettings: Getting {device.name} audio DSP settings.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
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
        self.debugLog(f"getVideoDspSettings: Getting {device.name} video DSP settings.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
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
        self.debugLog(f"getAudioInOutStatus: Getting {device.name} audio I/O status.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            # Since this method is called just after an input source change, wait a bit for the system to finalize the
            # change.
            self.sleep(1)
            self.sendCommand(device, "?AST")  # Audio Status.

    #
    # Video I/O Status
    #
    def getVideoInOutStatus(self, device):
        self.debugLog(f"getVideoInOutStatus: Getting {device.name} video I/O status.")

        devType = device.deviceTypeId

        # Make sure it's not a virtual volume device.
        if devType != "virtualVolume":
            # Since this method is called just after an input source change, wait half a second for the system to
            # finalize the change.
            self.sleep(0.5)
            self.sendCommand(device, "?VST")  # Video Status.

    #
    # All Status Information
    #
    def getReceiverStatus(self, device):
        self.debugLog(f"getReceiverStatus: Getting all information for{device.name}.")
        self.debugLog(f"getReceiverStatus: List of device IDs being updated: {self.devicesBeingUpdated}")

        # Make sure we aren't already updating this device.
        if device.id not in self.devicesBeingUpdated:
            # Add it to the list of devices being updated.
            self.devicesBeingUpdated.append(device.id)

            # Now gather all receiver data.

            devType = device.deviceTypeId

            # Indicate in the log that we're going to be gathering all kinds of information.
            indigo.server.log("Gathering receiver system information.", device.name)

            # Make sure it's not a virtual volume device.
            if devType != "virtualVolume":
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
                    # self.getTunerFrequency(device)        # Tuner Band and Frequency.
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
        if (device.deviceTypeId == "vsx1022k"
                or device.deviceTypeId == "vsx1122k"
                or device.deviceTypeId == "vsx1123k"
                or device.deviceTypeId == "sc75"):
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

        newValue = float(action.props.get('volume', "-90"))
        if newValue == -90.0:  # No value was provided.
            self.errorLog(f"No Zone 1 Volume was specified in the action for \"{device.name}\"")
            return False

        self.debugLog(f"Set volume to {newValue} dB (zone 1) for {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            newValue = 161 + int(newValue / 0.5)
            if newValue < 10:
                newValue = f"00{newValue}"
            elif newValue < 100:
                newValue = f"0{newValue}"
            else:
                newValue = f"{newValue}"
            command = newValue + "VL"  # Set Volume.
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Mute On (Zone 1)
    #
    def zone1muteOn(self, action):
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

        newValue = action.props.get('source', False)
        self.debugLog(f"zone1setSource called: source: {newValue}, device: {device.name}")

        if not newValue:
            self.errorLog(f"No source selected for \"{device.name}\"")
            return False
        self.debugLog(f"(Source name: {SOURCE_NAMES[str(newValue)]}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = newValue + "FN"  # Set Source.
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Power On (Zone 2)
    #
    def zone2powerOn(self, action):
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

        newValue = int(action.props.get('volume', "-90"))
        if newValue == -90:
            self.errorLog(f"No Zone 2 Volume was specified in action for \"{device.name}\"")
            return False

        self.debugLog(f"Set volume to {newValue} dB (zone 2) for {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            # If the current speaker system setup is not "A + Zone 2",
            #   zone mute and volume commands will be ignored.
            if device.states['speakerSystem'] == "A + Zone 2":
                newValue = 81 + int(newValue)
                if newValue < 10:
                    newValue = f"0{newValue}"
                else:
                    newValue = str(newValue)
                command = newValue + "ZV"  # Set Volume.
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
            # If the current speaker system setup is not "A + Zone 2",
            #   zone mute and volume commands will be ignored.
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

        newValue = action.props['source']
        self.debugLog(f"Set input source to {SOURCE_NAMES[str(newValue)]} (zone 2) for {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            command = newValue + "ZS"  # Set Source.
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Select Tuner Preset
    #
    def tunerPresetSelect(self, action):
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

        newValue = action.props.get('tunerPreset', False)
        if not newValue:
            self.errorLog(f"No Tuner preset specified in action for \"{device.name}\"")
            return False

        # Define the tuner preset device property name based on the menu selection.
        propName = f"tunerPreset{newValue.replace('0', '')}label"
        self.debugLog(f"tunerPresetSelect: Set tuner preset to {device.pluginProps[propName]} for {device.name}")

        # Make sure it's not a virtual volume device.
        if device.deviceTypeId != "virtualVolume":
            if (device.states['zone1source'] == 2) or (device.states['zone2source'] == 2):
                command = newValue + "PR"  # Select Tuner Preset.
                self.sendCommand(device, command)
                self.sleep(0.1)
            else:
                # Neither of zones 1 or 2 are using the Tuner.  Cannot set the preset.
                self.errorLog(
                    f"Cannot set tuner preset. The {device.name} zone 1 or 2 input source must be set to the tuner in "
                    f"order to set the tuner preset."
                )

    #
    # Set Tuner Frequency
    #
    def tunerFrequencySet(self, action):
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
                bandCommand = ""
                # Zone 1 power is on and input source is source 2. Send the commands.
                self.debugLog(f"tunerFrequencySet: Set tuner frequency to {frequency} {band} for {device.name}")
                # Define band change command and correct frequency character sequence.
                if band == "FM":
                    bandCommand = "00TN"  # Command to set band to AM.
                    frequency = frequency.replace(".", "")  # Remove the decimal.
                    if len(frequency) < 3:
                        frequency = f"{frequency}00"  # Add 2 trailing zeros.
                    elif len(frequency) < 4:
                        frequency = f"{frequency}0"  # Add 1 trailing zero.
                    # Add another trailing zero if the frequency was 100 or higher.
                    if frequency.startswith("1"):
                        frequency = f"{frequency}0"
                elif band == "AM":
                    bandCommand = "01TN"  # Command to set band to FM.
                    if len(frequency) < 4:
                        frequency = f"0{frequency}"  # Add a leading zero.

                # Start sending the command.
                self.sendCommand(device, bandCommand)  # Set the frequency band.
                self.sleep(0.1)  # Wait for the band to change.
                self.sendCommand(device, "TAC")  # Begin direct frequency entry.
                self.sleep(0.1)
                for theChar in frequency:
                    # Send each frequency number character individually.
                    self.sendCommand(device, theChar + "TP")
                    self.sleep(0.1)
                # Clear the device's preset state since entering a frequency directly.
                self.updateDeviceState(device, 'tunerPreset', "")

    #
    # Next Stereo Listening Mode
    #
    def listeningModeStereoNext(self, action):
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
            mcaccMemory = device.states['mcaccMemory']
            mcaccMemory += 1
            if mcaccMemory > 6:
                mcaccMemory = 1
            command = f"{mcaccMemory}MC"
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Previous MCACC Memory
    #
    def mcaccPrevious(self, action):
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
            mcaccMemory = device.states['mcaccMemory']
            mcaccMemory -= 1
            if mcaccMemory < 1:
                mcaccMemory = 6
            command = f"{mcaccMemory}MC"
            self.sendCommand(device, command)
            self.sleep(0.1)

    #
    # Select MCACC Memory
    #
    def mcaccSelect(self, action):
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
            source2commandMap = {'CRI': "TPI", 'CLE': "TPD", 'CEN': "03TN", 'CRT': "04TN", 'STS': "06TN"}
            # 17 - iPod/USB The below button maps work on the first button press, but don't for subsequent presses.
            # source17commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN",
            # 'CRT':"CRT", 'STS':"09IP", '00IP':"00IP", '01IP':"01IP", '02IP':"02IP", '03IP':"03IP", '04IP':"04IP",
            # '07IP':"07IP", '08IP':"08IP", '19SI':"19IP"}
            source17commandMap = {'CUP': "13IP", 'CDN': "14IP", 'CRI': "15IP", 'CLE': "16IP", 'CEN': "17IP",
                                  'CRT': "18IP", 'STS': "09IP", '00IP': "00IP", '01IP': "01IP", '02IP': "02IP",
                                  '03IP': "03IP", '04IP': "04IP", '07IP': "07IP", '08IP': "08IP", '19SI': "19IP"}
            # 26 - HMG (Home Media Gallery/Internet Radio) The below button maps work on the first button press,
            # but don't for subsequent presses. source26commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN",
            # 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN", 'CRT':"CRT", 'STS':"18NW", '00IP':"10NW", '01IP':"11NW",
            # '02IP':"20NW", '03IP':"12NW", '04IP':"12NW", '07IP':"34NW", '08IP':"35NW", '19SI':"36NW",
            # '00SI':"00NW", '01SI':"01NW", '02SI':"02NW", '03SI':"03NW", '04SI':"04NW", '05SI':"04NW",
            # '06SI':"05NW", '07SI':"07NW", '08SI':"08NW", '09SI':"09NW"}
            source26commandMap = {'CUP': "26NW", 'CDN': "27NW", 'CRI': "28NW", 'CLE': "29NW", 'CEN': "30NW",
                                  'CRT': "31NW", 'STS': "18NW", '00IP': "10NW", '01IP': "11NW", '02IP': "20NW",
                                  '03IP': "12NW", '04IP': "12NW", '07IP': "34NW", '08IP': "35NW", '19SI': "36NW",
                                  '00SI': "00NW", '01SI': "01NW", '02SI': "02NW", '03SI': "03NW", '04SI': "04NW",
                                  '05SI': "04NW", '06SI': "05NW", '07SI': "07NW", '08SI': "08NW", '09SI': "09NW"}
            # 27 - Sirius The below button maps work on the first button press, but don't for subsequent presses.
            # source27commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN",
            # 'CRT':"CRT", 'STS':"14SI", '19SI':"19SI", '00SI':"00SI", '01SI':"01SI", '02SI':"02SI", '03SI':"03SI",
            # '04SI':"04SI", '05SI':"04SI", '06SI':"05SI", '07SI':"07SI", '08SI':"08SI", '09SI':"09SI"}
            source27commandMap = {'CUP': "10SI", 'CDN': "11SI", 'CRI': "12SI", 'CLE': "13SI", 'CEN': "21SI",
                                  'CRT': "22SI", 'STS': "14SI", '19SI': "19SI", '00SI': "00SI", '01SI': "01SI",
                                  '02SI': "02SI", '03SI': "03SI", '04SI': "04SI", '05SI': "04SI", '06SI': "05SI",
                                  '07SI': "07SI", '08SI': "08SI", '09SI': "09SI"}
            # 33 - Adapter Port The below button maps work on the first button press, but don't for subsequent
            # presses. source33commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE",
            # 'CEN':"CEN", 'CRT':"CRT", '00IP':"10BT", '01IP':"11BT", '02IP':"12BT", '03IP':"13BT", '04IP':"14BT"}
            source33commandMap = {'CRI': "23BT", 'CLE': "24BT", 'CEN': "25BT", 'CRT': "26BT", '00IP': "10BT",
                                  '01IP': "11BT", '02IP': "12BT", '03IP': "13BT", '04IP': "14BT"}
            # List of default cursor button commands to use if the above sources aren't the current input source.
            defaultCursorCommands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']

            # Translate the command based on the current zone 1 input source.
            if source == 2:
                # See if the requested command is compatible with this input source.
                command = source2commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 17:
                command = source17commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 26:
                command = source26commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 27:
                command = source27commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 33:
                command = source33commandMap.get(command, "")
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
                if command not in defaultCursorCommands:
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
            source2commandMap = {'CUP': "TFI", 'CDN': "TFD", 'CRI': "TPI", 'CLE': "TPD", 'CEN': "03TN", 'CRT': "04TN",
                                 'STS': "06TN"}
            # 17 - iPod/USB
            source17commandMap = {'CUP': "13IP", 'CDN': "14IP", 'CRI': "15IP", 'CLE': "16IP", 'CEN': "17IP",
                                  'CRT': "18IP", 'STS': "09IP", '00IP': "00IP", '01IP': "01IP", '02IP': "02IP",
                                  '03IP': "03IP", '04IP': "04IP", '07IP': "07IP", '08IP': "08IP", '19SI': "19IP"}
            # 26 - HMG (Home Media Gallery/Internet Radio)
            source26commandMap = {'CUP': "26NW", 'CDN': "27NW", 'CRI': "28NW", 'CLE': "29NW", 'CEN': "30NW",
                                  'CRT': "31NW", 'STS': "18NW", '00IP': "10NW", '01IP': "11NW", '02IP': "20NW",
                                  '03IP': "12NW", '04IP': "12NW", '07IP': "34NW", '08IP': "35NW", '19SI': "36NW",
                                  '00SI': "00NW", '01SI': "01NW", '02SI': "02NW", '03SI': "03NW", '04SI': "04NW",
                                  '05SI': "04NW", '06SI': "05NW", '07SI': "07NW", '08SI': "08NW", '09SI': "09NW"}
            # 27 - Sirius
            source27commandMap = {'CUP': "10SI", 'CDN': "11SI", 'CRI': "12SI", 'CLE': "13SI", 'CEN': "21SI",
                                  'CRT': "22SI", 'STS': "14SI", '19SI': "19SI", '00SI': "00SI", '01SI': "01SI",
                                  '02SI': "02SI", '03SI': "03SI", '04SI': "04SI", '05SI': "04SI", '06SI': "05SI",
                                  '07SI': "07SI", '08SI': "08SI", '09SI': "09SI"}
            # 33 - Adapter Port
            source33commandMap = {'CRI': "23BT", 'CLE': "24BT", 'CEN': "25BT", 'CRT': "26BT", '00IP': "10BT",
                                  '01IP': "11BT", '02IP': "12BT", '03IP': "13BT", '04IP': "14BT"}
            # List of default cursor button commands to use if the above sources aren't the current input source.
            defaultCursorCommands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']

            # Translate the command based on the current zone 1 input source.
            if source == 2:
                # See if the requested command is compatible with this input source.
                command = source2commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 17:
                command = source17commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 26:
                command = source26commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 27:
                command = source27commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 33:
                command = source33commandMap.get(command, "")
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
                if command not in defaultCursorCommands:
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
            source2commandMap = {'CUP': "TFI", 'CDN': "TFD", 'CRI': "TPI", 'CLE': "TPD", 'CEN': "03TN", 'CRT': "04TN",
                                 'STS': "06TN"}
            # 17 - iPod/USB
            source17commandMap = {'CUP': "13IP", 'CDN': "14IP", 'CRI': "15IP", 'CLE': "16IP", 'CEN': "17IP",
                                  'CRT': "18IP", 'STS': "09IP", '00IP': "00IP", '01IP': "01IP", '02IP': "02IP",
                                  '03IP': "03IP", '04IP': "04IP", '07IP': "07IP", '08IP': "08IP", '19SI': "19IP"}
            # 26 - HMG (Home Media Gallery/Internet Radio)
            source26commandMap = {'CUP': "26NW", 'CDN': "27NW", 'CRI': "28NW", 'CLE': "29NW", 'CEN': "30NW",
                                  'CRT': "31NW", 'STS': "18NW", '00IP': "10NW", '01IP': "11NW", '02IP': "20NW",
                                  '03IP': "12NW", '04IP': "12NW", '07IP': "34NW", '08IP': "35NW", '19SI': "36NW",
                                  '00SI': "00NW", '01SI': "01NW", '02SI': "02NW", '03SI': "03NW", '04SI': "04NW",
                                  '05SI': "04NW", '06SI': "05NW", '07SI': "07NW", '08SI': "08NW", '09SI': "09NW"}
            # 27 - Sirius
            source27commandMap = {'CUP': "10SI", 'CDN': "11SI", 'CRI': "12SI", 'CLE': "13SI", 'CEN': "21SI",
                                  'CRT': "22SI", 'STS': "14SI", '19SI': "19SI", '00SI': "00SI", '01SI': "01SI",
                                  '02SI': "02SI", '03SI': "03SI", '04SI': "04SI", '05SI': "04SI", '06SI': "05SI",
                                  '07SI': "07SI", '08SI': "08SI", '09SI': "09SI"}
            # 33 - Adapter Port
            source33commandMap = {'CRI': "23BT", 'CLE': "24BT", 'CEN': "25BT", 'CRT': "26BT", '00IP': "10BT",
                                  '01IP': "11BT", '02IP': "12BT", '03IP': "13BT", '04IP': "14BT"}
            # List of default cursor button commands to use if the above sources aren't the current input source.
            defaultCursorCommands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']

            # Translate the command based on the current zone 1 input source.
            if source == 2:
                # See if the requested command is compatible with this input source.
                command = source2commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 17:
                command = source17commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 26:
                command = source26commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 27:
                command = source27commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 33:
                command = source33commandMap.get(command, "")
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
                if command not in defaultCursorCommands:
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
            source2commandMap = {'CUP': "TFI", 'CDN': "TFD", 'CRI': "TPI", 'CLE': "TPD", 'CEN': "03TN", 'CRT': "04TN",
                                 'STS': "06TN"}
            # 17 - iPod/USB
            source17commandMap = {'CUP': "13IP", 'CDN': "14IP", 'CRI': "15IP", 'CLE': "16IP", 'CEN': "17IP",
                                  'CRT': "18IP", 'STS': "09IP", '00IP': "00IP", '01IP': "01IP", '02IP': "02IP",
                                  '03IP': "03IP", '04IP': "04IP", '07IP': "07IP", '08IP': "08IP", '19SI': "19IP"}
            # 26 - HMG (Home Media Gallery/Internet Radio)
            source26commandMap = {'CUP': "26NW", 'CDN': "27NW", 'CRI': "28NW", 'CLE': "29NW", 'CEN': "30NW",
                                  'CRT': "31NW", 'STS': "18NW", '00IP': "10NW", '01IP': "11NW", '02IP': "20NW",
                                  '03IP': "12NW", '04IP': "12NW", '07IP': "34NW", '08IP': "35NW", '19SI': "36NW",
                                  '00SI': "00NW", '01SI': "01NW", '02SI': "02NW", '03SI': "03NW", '04SI': "04NW",
                                  '05SI': "04NW", '06SI': "05NW", '07SI': "07NW", '08SI': "08NW", '09SI': "09NW"}
            # 27 - Sirius
            source27commandMap = {'CUP': "10SI", 'CDN': "11SI", 'CRI': "12SI", 'CLE': "13SI", 'CEN': "21SI",
                                  'CRT': "22SI", 'STS': "14SI", '19SI': "19SI", '00SI': "00SI", '01SI': "01SI",
                                  '02SI': "02SI", '03SI': "03SI", '04SI': "04SI", '05SI': "04SI", '06SI': "05SI",
                                  '07SI': "07SI", '08SI': "08SI", '09SI': "09SI"}
            # 33 - Adapter Port
            source33commandMap = {'CRI': "23BT", 'CLE': "24BT", 'CEN': "25BT", 'CRT': "26BT", '00IP': "10BT",
                                  '01IP': "11BT", '02IP': "12BT", '03IP': "13BT", '04IP': "14BT"}
            # List of default cursor button commands to use if the above sources aren't the current input source.
            defaultCursorCommands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']

            # Translate the command based on the current zone 1 input source.
            if source == 2:
                # See if the requested command is compatible with this input source.
                command = source2commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 17:
                command = source17commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 26:
                command = source26commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 27:
                command = source27commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 33:
                command = source33commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button"
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the"
                        f"{device.states['zone1sourceName']} input source. Action ignored.")
                    error = True
            else:
                # Current zone 1 input source is something other than the special ones above. Make sure the command
                # being sent is one of the standard commands.
                if command not in defaultCursorCommands:
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
            source2commandMap = {'CUP': "TFI", 'CDN': "TFD", 'CRI': "TPI", 'CLE': "TPD", 'CEN': "03TN", 'CRT': "04TN",
                                 'STS': "06TN"}
            # 17 - iPod/USB
            source17commandMap = {'CUP': "13IP", 'CDN': "14IP", 'CRI': "15IP", 'CLE': "16IP", 'CEN': "17IP",
                                  'CRT': "18IP", 'STS': "09IP", '00IP': "00IP", '01IP': "01IP", '02IP': "02IP",
                                  '03IP': "03IP", '04IP': "04IP", '07IP': "07IP", '08IP': "08IP", '19SI': "19IP"}
            # 26 - HMG (Home Media Gallery/Internet Radio)
            source26commandMap = {'CUP': "26NW", 'CDN': "27NW", 'CRI': "28NW", 'CLE': "29NW", 'CEN': "30NW",
                                  'CRT': "31NW", 'STS': "18NW", '00IP': "10NW", '01IP': "11NW", '02IP': "20NW",
                                  '03IP': "12NW", '04IP': "12NW", '07IP': "34NW", '08IP': "35NW", '19SI': "36NW",
                                  '00SI': "00NW", '01SI': "01NW", '02SI': "02NW", '03SI': "03NW", '04SI': "04NW",
                                  '05SI': "04NW", '06SI': "05NW", '07SI': "07NW", '08SI': "08NW", '09SI': "09NW"}
            # 33 - Adapter Port
            source33commandMap = {'CRI': "23BT", 'CLE': "24BT", 'CEN': "25BT", 'CRT': "26BT", '00IP': "10BT",
                                  '01IP': "11BT", '02IP': "12BT", '03IP': "13BT", '04IP': "14BT"}
            # List of default cursor button commands to use if the above sources aren't the current input source.
            defaultCursorCommands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']

            # Translate the command based on the current zone 1 input source.
            if source == 2:
                # See if the requested command is compatible with this input source.
                command = source2commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button "
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the "
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 17:
                command = source17commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button "
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the "
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 26:
                command = source26commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button "
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the "
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            # TODO: there doesn't appear to be a source '27commandMap' above.
            elif source == 27:
                command = source27commandMap.get(command, "")
                if len(command) == 0:
                    self.errorLog(
                        f"{device.name}: remote control button "
                        f"{REMOTE_BUTTON_NAMES.get(action.props['remoteButton'], '')} is not supported by the "
                        f"{device.states['zone1sourceName']} input source. Action ignored."
                    )
                    error = True
            elif source == 33:
                command = source33commandMap.get(command, "")
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
                if command not in defaultCursorCommands:
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
        try:
            self.debugLog(
                f"actionControlDimmerRelay called for device {device.name}. action: {action}\n\ndevice: {device}"
            )
        except Exception as e:
            self.debugLog(
                f"actionControlDimmerRelay called for device {device.name}. (Unable to display action or device data "
                f"due to error: {e})"
            )
        receiverDeviceId = device.pluginProps.get('receiverDeviceId', "")
        controlDestination = device.pluginProps.get('controlDestination', "")
        # Get the current brightness and on-state of the device.
        currentBrightness = device.states['brightnessLevel']
        currentOnState = device.states['onOffState']
        # Verify the validity of the data.
        if len(receiverDeviceId) < 1:
            self.errorLog(
                f"{device.name} is not set to control any receiver device. Double-click the {device.name} device in "
                f"Indigo to select a receiver to control."
            )
            self.updateDeviceState(device, 'onOffState', currentOnState)
            self.updateDeviceState(device, 'brightnessLevel', 0)
            return
        if int(receiverDeviceId) not in self.deviceList:
            self.errorLog(
                f"{device.name} is configured to control a receiver device that no longer exists. Double-click the "
                f"{device.name} device in Indigo to select a receiver to control."
            )
            self.updateDeviceState(device, 'onOffState', currentOnState)
            self.updateDeviceState(device, 'brightnessLevel', 0)
            return
        # Get the receiver device object.
        receiverDeviceId = int(receiverDeviceId)
        receiver = indigo.devices[receiverDeviceId]

        # ====== TURN ON ======
        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            try:
                self.debugLog(f"device on:\n{action}")
            except Exception as e:
                self.debugLog(f"device on: (Unable to display action data due to error: {e})")
            # Select the proper action based on the controlDestination value.
            # VOLUME / MUTE
            if controlDestination == "zone1volume" or controlDestination == "zone2volume":
                try:
                    # Turn off the select zone's mute.
                    if controlDestination == "zone1volume":
                        # Execute the action.
                        self.sendCommand(receiver, "MF")
                    if controlDestination == "zone2volume":
                        # Execute the action.
                        self.sendCommand(receiver, "Z2MF")
                except Exception as e:
                    self.errorLog(
                        f"{device.name}: Error executing Mute Off action for receiver device {receiver.name}. {e}"
                    )

        # ====== TURN OFF ======
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            try:
                self.debugLog(f"device off:\n{action}")
            except Exception as e:
                self.debugLog(f"device off: (Unable to display action due to error: {e})")
            # Select the proper action based on the controlDestination value.
            # VOLUME / MUTE
            if controlDestination == "zone1volume" or controlDestination == "zone2volume":
                try:
                    # Turn on the select zone's mute.
                    if controlDestination == "zone1volume":
                        self.sendCommand(receiver, "MO")
                    if controlDestination == "zone2volume":
                        self.sendCommand(receiver, "Z2MO")
                except Exception as e:
                    self.errorLog(
                        f"{device.name}: Error executing Mute On action for receiver device {receiver.name}. {e}"
                    )

        # ====== TOGGLE ======
        elif action.deviceAction == indigo.kDeviceAction.Toggle:
            try:
                self.debugLog(f"device toggle:\n{action}")
            except Exception as e:
                self.debugLog(f"device toggle: (Unable to display action due to error: {e})")
            # Select the proper action based on the controlDestination value.
            # VOLUME / MUTE
            if controlDestination == "zone1volume" or controlDestination == "zone2volume":
                # Turn off or on the select zone's mute, depending on current state.
                try:
                    # Turn on mute if toggling device to "Off". Turn off mute if toggling the device to "On".
                    if device.states['onOffState']:
                        if controlDestination == "zone1volume":
                            self.sendCommand(receiver, "MO")  # Zone 1 Mute On
                        if controlDestination == "zone2volume":
                            self.sendCommand(receiver, "Z2MO")  # Zone 2 Mute On
                    # device.updateStateOnServer('onOffState', False)
                    else:
                        if controlDestination == "zone1volume":
                            self.sendCommand(receiver, "MF")  # Zone 1 Mute Off
                        if controlDestination == "zone2volume":
                            self.sendCommand(receiver, "Z2MF")  # Zone 2 Mute Off
                except Exception as e:
                    self.errorLog(
                        f"{device.name}: Error executing Mute On action for receiver device {receiver.name}. {e}"
                    )

        # ====== SET BRIGHTNESS ======
        elif action.deviceAction == indigo.kDeviceAction.SetBrightness:
            try:
                self.debugLog(f"device set brightness:\n{action}")
            except Exception as e:
                self.debugLog(f"device set brightness: (Unable to display action due to error: {e})")
            # Select the proper action based on the controlDestination value.
            # VOLUME / MUTE
            if controlDestination == "zone1volume" or controlDestination == "zone2volume":
                try:
                    brightnessLevel = action.actionValue
                    # Convert the brightness level to a valid volume command.
                    if controlDestination == "zone1volume":
                        # This formula converts from the 100 unit scale to the 161 unit scale used by the receiver's
                        # zone 1 volume commands.
                        theVolume = int(round(161 * 0.01 * brightnessLevel, 0))
                        if theVolume < 10:
                            theVolume = f"00{theVolume}"
                        elif theVolume < 100:
                            theVolume = f"0{theVolume}"
                        else:
                            theVolume = f"{theVolume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone1mute']:
                            self.sendCommand(receiver, "MF")
                        # Now send the volume command.
                        command = theVolume + "VL"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightnessLevel}, theVolume: {theVolume}"
                        )
                    elif controlDestination == "zone2volume":
                        # This formula converts from the 100 unit scale to the 81 unit scale used by the receiver's
                        # zone 2 volume commands.
                        theVolume = int(round(81 * 0.01 * brightnessLevel, 0))
                        if theVolume < 10:
                            theVolume = f"0{theVolume}"
                        else:
                            theVolume = f"{theVolume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone2mute']:
                            self.sendCommand(receiver, "Z2MF")
                        # Now send the volume command.
                        command = theVolume + "ZV"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightnessLevel}, theVolume: {theVolume}"
                        )
                except Exception as e:
                    self.errorLog(
                        f"{device.name}: Error executing Set Volume action for receiver device {receiver.name}. {e}"
                    )

        # ====== BRIGHTEN BY ======
        elif action.deviceAction == indigo.kDeviceAction.BrightenBy:
            try:
                self.debugLog(f"device brighten by:\n{action}")
            except Exception as e:
                self.debugLog(f"device brighten by: (Unable to display action due to error: {e})")
            # Select the proper action based on the controlDestination value.
            # VOLUME / MUTE
            if controlDestination == "zone1volume" or controlDestination == "zone2volume":
                try:
                    # Convert the brightness level to a valid volume command.
                    if controlDestination == "zone1volume":
                        # Set the currentBrightness to the current receiver volume. We're doing this because if the
                        # receiver is muted, this virtual device will have a brightness of 0 and brightening by
                        # anything will set brightness to 0 plus the brightening amount.
                        currentBrightness = int(100 - round(float(receiver.states['zone1volume']) / -80.5 * 100, 0))
                        brightnessLevel = currentBrightness + int(action.actionValue)
                        # Sanity check...
                        if brightnessLevel > 100:
                            brightnessLevel = 100
                        self.debugLog(f"   set brightness of {device.name} to {brightnessLevel}")
                        # This formula converts from the 100 unit scale to the 161 unit scale used by the receiver's
                        # zone 1 volume commands.
                        theVolume = int(round(161 * 0.01 * brightnessLevel, 0))
                        if theVolume < 10:
                            theVolume = f"00{theVolume}"
                        elif theVolume < 100:
                            theVolume = f"0{theVolume}"
                        else:
                            theVolume = f"{theVolume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone1mute']:
                            self.sendCommand(receiver, "MF")
                        # Now send the volume command.
                        command = theVolume + "VL"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightnessLevel}, theVolume: {theVolume}")
                    elif controlDestination == "zone2volume":
                        # Set the currentBrightness to the current receiver volume. We're doing this because if the
                        # receiver is muted, this virtual device will have a brightness of 0 and brightening by
                        # anything will set brightness to 0 plus the brightening amount.
                        currentBrightness = int(100 - round(float(receiver.states['zone2volume']) / -81 * 100, 0))
                        brightnessLevel = currentBrightness + int(action.actionValue)
                        # Sanity check...
                        if brightnessLevel > 100:
                            brightnessLevel = 100
                        self.debugLog(f"   set brightness of {device.name} to {brightnessLevel}")
                        # This formula converts from the 100 unit scale to the 81 unit scale used by the receiver's
                        # zone 2 volume commands.
                        theVolume = int(round(81 * 0.01 * brightnessLevel, 0))
                        if theVolume < 10:
                            theVolume = f"0{theVolume}"
                        else:
                            theVolume = f"{theVolume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone2mute']:
                            self.sendCommand(receiver, "Z2MF")
                        # Now send the volume command.
                        command = theVolume + "ZV"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightnessLevel}, theVolume: {theVolume}"
                        )
                except Exception as e:
                    self.errorLog(
                        f"{device.name}: Error executing Set Volume action for receiver device {receiver.name}. {e}"
                    )

        # ====== DIM BY ======
        elif action.deviceAction == indigo.kDeviceAction.DimBy:
            try:
                self.debugLog(f"device dim by:\n{action}")
            except Exception as e:
                self.debugLog(f"device dim by: (Unable to display action due to error: {e})")
            brightnessLevel = currentBrightness - int(action.actionValue)
            # Sanity check...
            if brightnessLevel < 0:
                brightnessLevel = 0
            self.debugLog(f"   set brightness of {device.name} to {brightnessLevel}")
            # Select the proper action based on the controlDestination value.
            # VOLUME / MUTE
            if controlDestination == "zone1volume" or controlDestination == "zone2volume":
                try:
                    # Convert the brightness level to a valid volume command.
                    if controlDestination == "zone1volume":
                        # This formula converts from the 100 unit scale to the 161 unit scale used by the receiver's
                        # zone 1 volume commands.
                        theVolume = int(round(161 * 0.01 * brightnessLevel, 0))
                        if theVolume < 10:
                            theVolume = f"00{theVolume}"
                        elif theVolume < 100:
                            theVolume = f"0{theVolume}"
                        else:
                            theVolume = f"{theVolume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone1mute']:
                            self.sendCommand(receiver, "MF")
                        # Now send the volume command.
                        command = theVolume + "VL"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightnessLevel}, theVolume: {theVolume}"
                        )
                    elif controlDestination == "zone2volume":
                        # This formula converts from the 100 unit scale to the 81 unit scale used by the receiver's
                        # zone 2 volume commands.
                        theVolume = int(round(81 * 0.01 * brightnessLevel, 0))
                        if theVolume < 10:
                            theVolume = f"0{theVolume}"
                        else:
                            theVolume = f"{theVolume}"
                        # Turn mute off if it's on.
                        if receiver.states['zone2mute']:
                            self.sendCommand(receiver, "Z2MF")
                        # Now send the volume command.
                        command = theVolume + "ZV"  # Set Volume.
                        self.sendCommand(receiver, command)
                        self.debugLog(
                            f"actionControlDimmerRelay: brightnessLevel: {brightnessLevel}, theVolume: {theVolume}"
                        )
                except Exception as e:
                    self.errorLog(
                        f"{device.name}: Error executing Set Volume action for receiver device {receiver.name}. {e}"
                    )

    ########################################
    # UI Interaction Methods
    #   (Class-Supported)
    ########################################

    # Actions Dialog
    ########################################
    def validateActionConfigUi(self, valuesDict, typeId, deviceId):
        self.debugLog("validateActionConfigUi called.")
        self.debugLog(f"typeId: {typeId}, deviceId: {deviceId}")
        try:
            self.debugLog(f"valuesDict: {valuesDict}")
        except Exception as e:
            self.debugLog(f"(Unable to display valuesDict due to error: {e})")

        device = indigo.devices[deviceId]
        errorMsgDict = indigo.Dict()
        descString = ""

        #
        # Set Volume dB (Zone 1)
        #
        if typeId == "zone1setVolume":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['volume'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['volume']
                return False, valuesDict, errorMsgDict

            try:
                theNumber = float(valuesDict.get('volume', "-90"))
            except ValueError:
                errorMsgDict['volume'] = "The volume must be a number between -80.5 and 12 dB."
                errorMsgDict['showAlertText'] = errorMsgDict['volume']
                return False, valuesDict, errorMsgDict

            if (theNumber < -80.5) or (theNumber > 12.0):
                errorMsgDict['volume'] = "The volume must be a number between -80.5 and 12 dB."
                errorMsgDict['showAlertText'] = errorMsgDict['volume']
                return False, valuesDict, errorMsgDict

            if theNumber % 0.5 != 0:
                errorMsgDict['volume'] = "The volume must be evenly divisible by 0.5 dB."
                errorMsgDict['showAlertText'] = errorMsgDict['volume']
                return False, valuesDict, errorMsgDict

            descString += f"set volume (zone 1) to {theNumber}"

        #
        # Set Source (Zone 1)
        #
        if typeId == "zone1setSource":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['source'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['source']
                return False, valuesDict, errorMsgDict

            theSource = valuesDict['source']
            propName = f"source{theSource}label"
            theName = device.pluginProps.get(propName, "")
            if len(theName) < 1:
                errorMsgDict['source'] = "Please select an Input Source."
                errorMsgDict['showAlertText'] = errorMsgDict['source']
                return False, valuesDict, errorMsgDict

            if device.deviceTypeId == "vsx1021k":
                if theSource in VSX1021k_SOURCE_MASK:
                    errorMsgDict[
                        'source'] = "The selected source is not available on this receiver. Choose a different source."
                    errorMsgDict['showAlertText'] = errorMsgDict['source']
                    return False, valuesDict, errorMsgDict
            elif device.deviceTypeId == "vsx1022k":
                if theSource in VSX1022K_SOURCE_MASK:
                    errorMsgDict[
                        'source'] = "The selected source is not available on this receiver. Choose a different source."
                    errorMsgDict['showAlertText'] = errorMsgDict['source']
                    return False, valuesDict, errorMsgDict
            elif device.deviceTypeId == "vsx1122k":
                if theSource in VSX1122K_SOURCE_MASK:
                    errorMsgDict[
                        'source'] = "The selected source is not available on this receiver. Choose a different source."
                    errorMsgDict['showAlertText'] = errorMsgDict['source']
                    return False, valuesDict, errorMsgDict
            elif device.deviceTypeId == "vsx1123k":
                if theSource in VSX1123K_SOURCE_MASK:
                    errorMsgDict[
                        'source'] = "The selected source is not available on this receiver. Choose a different source."
                    errorMsgDict['showAlertText'] = errorMsgDict['source']
                    return False, valuesDict, errorMsgDict
            elif device.deviceTypeId == "sc75":
                if theSource in SC75_SOURCE_MASK:
                    errorMsgDict[
                        'source'] = "The selected source is not available on this receiver. Choose a different source."
                    errorMsgDict['showAlertText'] = errorMsgDict['source']
                    return False, valuesDict, errorMsgDict

            descString += f"set input source (zone 1) to {theName}"

        #
        # Set Volume dB (Zone 2)
        #
        if typeId == "zone2setVolume":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['volume'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['volume']
                return False, valuesDict, errorMsgDict

            try:
                theNumber = int(valuesDict.get('volume', "-90"))
            except ValueError:
                errorMsgDict['volume'] = "The volume must be a whole number between -81 and 0 dB."
                errorMsgDict['showAlertText'] = errorMsgDict['volume']
                return False, valuesDict, errorMsgDict

            if (theNumber < -81) or (theNumber > 0):
                errorMsgDict['volume'] = "The volume must be a whole number between -81 and 0 dB."
                errorMsgDict['showAlertText'] = errorMsgDict['volume']
                return False, valuesDict, errorMsgDict

            descString += f"set volume (zone 2) to {theNumber}"

        #
        # Set Source (Zone 2)
        #
        if typeId == "zone2setSource":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['source'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['source']
                return False, valuesDict, errorMsgDict

            theSource = valuesDict['source']
            propName = f"source{theSource}label"
            theName = device.pluginProps.get(propName, "")
            if len(theName) < 1:
                errorMsgDict['source'] = "Please select an Input Source."
                errorMsgDict['showAlertText'] = errorMsgDict['source']
                return False, valuesDict, errorMsgDict

            if device.deviceTypeId == "vsx1021k":
                if theSource in VSX1021K_ZONE2_SOURCE_MASK:
                    errorMsgDict[
                        'source'] = (
                        "The selected source is not available for this zone on this receiver. Choose a different "
                        "source."
                    )
                    errorMsgDict['showAlertText'] = errorMsgDict['source']
                    return False, valuesDict, errorMsgDict
            elif device.deviceTypeId == "vsx1022k":
                if theSource in VSX1022K_ZONE2_SOURCE_MASK:
                    errorMsgDict[
                        'source'] = (
                        "The selected source is not available for this zone on this receiver. Choose a different "
                        "source."
                    )
                    errorMsgDict['showAlertText'] = errorMsgDict['source']
                    return False, valuesDict, errorMsgDict
            elif device.deviceTypeId == "vsx1122k":
                if theSource in VSX1122K_ZONE2_SOURCE_MASK:
                    errorMsgDict[
                        'source'] = (
                        "The selected source is not available for this zone on this receiver. Choose a different "
                        "source."
                    )
                    errorMsgDict['showAlertText'] = errorMsgDict['source']
                    return False, valuesDict, errorMsgDict
            elif device.deviceTypeId == "vsx1123k":
                if theSource in VSX1123k_ZONE2_SOURCE_MASK:
                    errorMsgDict['source'] = (
                        "The selected source is not available for this zone on this receiver. Choose a different "
                        "source."
                    )
                    errorMsgDict['showAlertText'] = errorMsgDict['source']
                    return False, valuesDict, errorMsgDict
            elif device.deviceTypeId == "sc75":
                if theSource in SC75_ZONE2_SOURCE_MASK:
                    errorMsgDict['source'] = (
                        "The selected source is not available for this zone on this receiver. Choose a different "
                        "source."
                    )
                    errorMsgDict['showAlertText'] = errorMsgDict['source']
                    return False, valuesDict, errorMsgDict

            descString += f"set input source (zone 2) to {theName}"

        #
        # Select Tuner Preset
        #
        if typeId == "tunerPresetSelect":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['tunerPreset'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['tunerPreset']
                return False, valuesDict, errorMsgDict

            thePreset = valuesDict['tunerPreset']
            propName = f"tunerPreset{thePreset.replace('0', '')}label"
            theName = device.pluginProps.get(propName, "")
            if len(theName) < 1:
                errorMsgDict['tunerPreset'] = "Please select a Tuner Preset."
                errorMsgDict['showAlertText'] = errorMsgDict['tunerPreset']
                return False, valuesDict, errorMsgDict

            descString += f"select tuner preset {thePreset.replace('0', '')}: {theName}"

        #
        # Set Tuner Frequency
        #
        if typeId == "tunerFrequencySet":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['band'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['frequency'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['band']
                return False, valuesDict, errorMsgDict

            # Make sure a tuner band was selected.
            band = valuesDict.get('band', "")
            if len(band) < 2:
                errorMsgDict['band'] = "Please select a Tuner Band."

            # Make sure a frequency value was entered.
            frequency = valuesDict.get('frequency', "")
            if len(frequency) == 0:
                errorMsgDict['frequency'] = "A Tuner Frequency value is required."
            else:
                # A tuner frequency was entered, now make sure it's realistic.
                try:
                    frequency = float(valuesDict['frequency'])
                    # Make sure the frequency is a sane value based on band.
                    if band == "AM":
                        if (frequency < 530) or (frequency > 1700):
                            errorMsgDict[
                                'frequency'] = (
                                "AM frequencies must be a whole number between 530 and 1700 in increments of 10 kHz."
                            )
                        if frequency % 10 != 0:
                            errorMsgDict['frequency'] = (
                                "AM frequencies must be a whole number between 530 and 1700 in increments of 10 kHz."
                            )
                        # Convert the frequency to an integer.
                        frequency = int(frequency)
                    elif band == "FM":
                        if (frequency < 87.5) or (frequency > 108):
                            errorMsgDict[
                                'frequency'] = "FM frequencies must be between 87.5 and 108 in increments of 0.1 MHz."
                        if int(frequency * 10) != frequency * 10:  # Make sure the precision is at most 0.1.
                            errorMsgDict[
                                'frequency'] = "FM frequencies must be between 87.5 and 108 in increments of 0.1 MHz."
                except ValueError:
                    errorMsgDict['frequency'] = "The Tuner Frequency field can only contain numbers."

            # If there were errors, return them now.
            if len(errorMsgDict) > 0:
                errorMsgDict['showAlertText'] = f"{errorMsgDict['band']}\r\r{errorMsgDict['frequency']}"
                return False, valuesDict, errorMsgDict

            descString += f"set tuner frequency to {frequency} {band}"

        #
        # Select Listening Mode
        #
        if typeId == "listeningModeSelect":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['listeningMode'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['listeningMode']
                return False, valuesDict, errorMsgDict

            listeningMode = valuesDict.get('listeningMode', "")
            if len(listeningMode) < 1:
                errorMsgDict['listeningMode'] = "Please select a Listening Mode."
                errorMsgDict['showAlertText'] = errorMsgDict['listeningMode']
                return False, valuesDict, errorMsgDict
            else:
                descString += f"set listening mode to \"{LISTENING_MODES[listeningMode]}\""

        #
        # Set Display Brightness
        #
        if typeId == "setDisplayBrightness":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['displayBrightness'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['displayBrightness']
                return False, valuesDict, errorMsgDict

            displayBrightness = valuesDict.get('displayBrightness', "")
            if len(displayBrightness) < 1:
                errorMsgDict['displayBrightness'] = "Please select a value for Display Brightness."
                errorMsgDict['showAlertText'] = errorMsgDict['displayBrightness']
                return False, valuesDict, errorMsgDict
            else:
                descString += "set display brightness to "
                # Translate the displayBrightness value into something readable for the description.
                if displayBrightness == "3SAA":
                    descString = "turn off display"
                elif displayBrightness == "2SAA":
                    descString += "dim"
                elif displayBrightness == "1SAA":
                    descString += "medium"
                elif displayBrightness == "0SAA":
                    descString += "bright"

        #
        # Set Sleep Timer
        #
        if typeId == "setSleepTimer":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['sleepTime'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['sleepTime']
                return False, valuesDict, errorMsgDict

            sleepTime = valuesDict.get('sleepTime', "")
            if len(sleepTime) < 1:
                errorMsgDict['sleepTime'] = "Please select a value for Sleep Time Minutes."
                errorMsgDict['showAlertText'] = errorMsgDict['sleepTime']
                return False, valuesDict, errorMsgDict
            else:
                descString += "set sleep timer to "
                # Translate the sleepTime value into something readable for the description.
                sleepTime = int(sleepTime[1:3])
                if sleepTime == 0:
                    descString += "off"
                else:
                    descString += f"{sleepTime} min"

        #
        # Select MCACC Memory
        #
        if typeId == "mcaccSelect":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['mcaccMemory'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['mcaccMemory']
                return False, valuesDict, errorMsgDict

            # Make sure a MCACC memory was selected.
            mcaccMemory = valuesDict.get('mcaccMemory', "")
            if len(mcaccMemory) < 1:
                errorMsgDict['mcaccMemory'] = "Please select a MCACC Memory item."
                errorMsgDict['showAlertText'] = errorMsgDict['mcaccMemory']
                return False, valuesDict, errorMsgDict
            else:
                devProps = device.pluginProps
                propName = f"mcaccMemory{mcaccMemory[0:1]}label"
                mcaccMemoryName = devProps[propName]
                descString += f"set mcacc memory to {mcaccMemory[0:1]}: {mcaccMemoryName}"

        #
        # Send Remote Button Press
        #
        if typeId == "remoteButtonPress":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['remoteButton'] = (
                        f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                        f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['remoteButton']
                return False, valuesDict, errorMsgDict

            command = valuesDict.get('remoteButton', "")
            # Make sure they selected a button to send.
            if len(command) == 0:
                errorMsgDict['remoteButton'] = "Please select a Button press to send to the receiver."
                errorMsgDict['showAlertText'] = errorMsgDict['remoteButton']
                return False, valuesDict, errorMsgDict

            descString += f"press remote control button \"{REMOTE_BUTTON_NAMES.get(command, '')}\""

        #
        # Send a Raw Command
        #
        if typeId == "sendRawCommand":
            # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but
            # because it's not currently possible to prevent the user from selecting it as a destination device in the
            # Indigo UI, we must check for it).
            if device.deviceTypeId == "virtualVolume":
                errorMsgDict['command'] = (
                    f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the "
                    f"Indigo action to send the command to a Pioneer receiver instead of this device."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['command']
                return False, valuesDict, errorMsgDict

            command = valuesDict['command']
            # Attempt to encode the command as ASCII.  If this fails.
            try:
                command = command.encode("ascii")
            except UnicodeEncodeError:
                errorMsgDict[
                    'command'] = (
                    "Commands can only contain standard ASCII characters. Extended characters are not supported."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['command']
                return False, valuesDict, errorMsgDict
            # Make sure the command isn't blank.
            if len(command) == 0:
                errorMsgDict['command'] = (
                    "Nothing was entered for the Command. Please enter a text command to send to the receiver."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['command']
                return False, valuesDict, errorMsgDict

            descString += f"send raw command \"{command}\""

        valuesDict['description'] = descString
        return True, valuesDict

    # Device Configuration Dialog
    ########################################
    def validateDeviceConfigUi(self, valuesDict, typeId=0, deviceId=0):
        try:
            self.debugLog(
                f"validateDeviceConfig called. valuesDict: {valuesDict} typeId: {typeId}, deviceId: {deviceId}."
            )
        except Exception as e:
            self.debugLog(
                f"validateDeviceConfig called. typeId: {typeId} deviceId: {deviceId} (Unable to display valuesDict due "
                f"to error: {e})"
            )

        error = False  # To flag if any errors were found.
        errorMsgDict = indigo.Dict()

        #
        # VSX-1021-K Device
        #
        if typeId == "vsx1021k":
            address = valuesDict.get('address', "")

            # Make sure a value was entered for the address.
            if len(address) < 1:
                errorMsgDict['address'] = "Please enter an IP address for the receiver."
                errorMsgDict['showAlertText'] = errorMsgDict['address']
                return False, valuesDict, errorMsgDict

            # Make sure the address entered is in the correct IP address format.
            addressParts = address.split(".")
            # (This is easier than using Regular Expressions.  :-) )
            for part in addressParts:
                try:
                    part = int(part)
                    if part < 0 or part > 255:
                        errorMsgDict['address'] = "Please enter a valid IP address for the receiver."
                        errorMsgDict['showAlertText'] = errorMsgDict['address']
                        return False, valuesDict, errorMsgDict
                except ValueError:
                    errorMsgDict['address'] = "Please enter a valid IP address for the receiver."
                    errorMsgDict['showAlertText'] = errorMsgDict['address']
                    return False, valuesDict, errorMsgDict

            # For newly created devices, the deviceId won't be in the device list.
            if deviceId > 0:
                device = indigo.devices[deviceId]
                devProps = device.pluginProps

                # See if any other devices are using the same address by going through all devices for this plugin.
                for d in self.deviceList:
                    a = indigo.devices[d].pluginProps['address']
                    # If the address found is the same as this device's address (and the matching address is not for
                    # this device), generate an error.
                    if (a == address) and (d != deviceId):
                        error = True
                        errorMsgDict['address'] = (
                            f"This address is already being used by the device \"{indigo.devices[d].name}\". Only one "
                            f"device at a time can connect to a receiver."
                        )
                        errorMsgDict['showAlertText'] = errorMsgDict['address']

                # Make sure the MCACC Memory Label properties are created, even if they aren't specified.
                for mcmccMemory in range(1, 7):
                    propName = f"mcmccMemory{mcmccMemory}label"
                    if valuesDict.get(propName, "") == "":
                        devProps.update({propName: ""})
                        self.updateDeviceProps(device, devProps)

        #
        # VSX-1022-K Device
        #
        if typeId == "vsx1022k":
            address = valuesDict.get('address', "")

            # Make sure a value was entered for the address.
            if len(address) < 1:
                errorMsgDict['address'] = "Please enter an IP address for the receiver."
                errorMsgDict['showAlertText'] = errorMsgDict['address']
                return False, valuesDict, errorMsgDict

            # Make sure the address entered is in the correct IP address format.
            addressParts = address.split(".")
            # (This is easier than using Regular Expressions.  :-) )
            for part in addressParts:
                try:
                    part = int(part)
                    if part < 0 or part > 255:
                        errorMsgDict['address'] = "Please enter a valid IP address for the receiver."
                        errorMsgDict['showAlertText'] = errorMsgDict['address']
                        return False, valuesDict, errorMsgDict
                except ValueError:
                    errorMsgDict['address'] = "Please enter a valid IP address for the receiver."
                    errorMsgDict['showAlertText'] = errorMsgDict['address']
                    return False, valuesDict, errorMsgDict

            # For newly created devices, the deviceId won't be in the device list.
            if deviceId > 0:
                device = indigo.devices[deviceId]
                devProps = device.pluginProps

                # See if any other devices are using the same address by going through all devices for this plugin.
                for d in self.deviceList:
                    a = indigo.devices[d].pluginProps['address']
                    # If the address found is the same as this device's address (and the matching address is not for
                    # this device), generate an error.
                    if (a == address) and (d != deviceId):
                        error = True
                        errorMsgDict['address'] = (
                                f"This address is already being used by the device \"{indigo.devices[d].name}\". Only "
                                f"one device at a time can connect to a receiver."
                        )
                        errorMsgDict['showAlertText'] = errorMsgDict['address']

                # Make sure the MCACC Memory Label properties are created, even if they aren't specified.
                for mcmccMemory in range(1, 7):
                    propName = f"mcmccMemory{mcmccMemory}label"
                    if valuesDict.get(propName, "") == "":
                        devProps.update({propName: ""})
                        self.updateDeviceProps(device, devProps)

        #
        # VSX-1122-K Device
        #
        if typeId == "vsx1122k":
            address = valuesDict.get('address', "")

            # Make sure a value was entered for the address.
            if len(address) < 1:
                errorMsgDict['address'] = "Please enter an IP address for the receiver."
                errorMsgDict['showAlertText'] = errorMsgDict['address']
                return False, valuesDict, errorMsgDict

            # Make sure the address entered is in the correct IP address format.
            addressParts = address.split(".")
            # (This is easier than using Regular Expressions.  :-) )
            for part in addressParts:
                try:
                    part = int(part)
                    if part < 0 or part > 255:
                        errorMsgDict['address'] = "Please enter a valid IP address for the receiver."
                        errorMsgDict['showAlertText'] = errorMsgDict['address']
                        return False, valuesDict, errorMsgDict
                except ValueError:
                    errorMsgDict['address'] = "Please enter a valid IP address for the receiver."
                    errorMsgDict['showAlertText'] = errorMsgDict['address']
                    return False, valuesDict, errorMsgDict

            # For newly created devices, the deviceId won't be in the device list.
            if deviceId > 0:
                device = indigo.devices[deviceId]
                devProps = device.pluginProps

                # See if any other devices are using the same address by going through all devices for this plugin.
                for d in self.deviceList:
                    a = indigo.devices[d].pluginProps['address']
                    # If the address found is the same as this device's address (and the matching address is not for
                    # this device), generate an error.
                    if (a == address) and (d != deviceId):
                        error = True
                        errorMsgDict['address'] = (
                            f"This address is already being used by the device \"{indigo.devices[d].name}\". Only one "
                            f"device at a time can connect to a receiver."
                        )
                        errorMsgDict['showAlertText'] = errorMsgDict['address']

                # Make sure the MCACC Memory Label properties are created, even if they aren't specified.
                for mcmccMemory in range(1, 7):
                    propName = f"mcmccMemory{mcmccMemory}label"
                    if valuesDict.get(propName, "") == "":
                        devProps.update({propName: ""})
                        self.updateDeviceProps(device, devProps)

        #
        # VSX-1123-K Device
        #
        if typeId == "vsx1123k":
            address = valuesDict.get('address', "")

            # Make sure a value was entered for the address.
            if len(address) < 1:
                errorMsgDict['address'] = "Please enter an IP address for the receiver."
                errorMsgDict['showAlertText'] = errorMsgDict['address']
                return False, valuesDict, errorMsgDict

            # Make sure the address entered is in the correct IP address format.
            addressParts = address.split(".")
            # (This is easier than using Regular Expressions.  :-) )
            for part in addressParts:
                try:
                    part = int(part)
                    if part < 0 or part > 255:
                        errorMsgDict['address'] = "Please enter a valid IP address for the receiver."
                        errorMsgDict['showAlertText'] = errorMsgDict['address']
                        return False, valuesDict, errorMsgDict
                except ValueError:
                    errorMsgDict['address'] = "Please enter a valid IP address for the receiver."
                    errorMsgDict['showAlertText'] = errorMsgDict['address']
                    return False, valuesDict, errorMsgDict

            # For newly created devices, the deviceId won't be in the device list.
            if deviceId > 0:
                device = indigo.devices[deviceId]
                devProps = device.pluginProps

                # See if any other devices are using the same address by going through all devices for this plugin.
                for d in self.deviceList:
                    a = indigo.devices[d].pluginProps['address']
                    # If the address found is the same as this device's address (and the matching address is not for
                    # this device), generate an error.
                    if (a == address) and (d != deviceId):
                        error = True
                        errorMsgDict['address'] = (
                            f"This address is already being used by the device \"{indigo.devices[d].name}\". Only one "
                            f"device at a time can connect to a receiver."
                        )
                        errorMsgDict['showAlertText'] = errorMsgDict['address']

                # Make sure the MCACC Memory Label properties are created, even if they aren't specified.
                for mcmccMemory in range(1, 7):
                    propName = f"mcmccMemory{mcmccMemory}label"
                    if valuesDict.get(propName, "") == "":
                        devProps.update({propName: ""})
                        self.updateDeviceProps(device, devProps)

        #
        # SC-75 Device
        #
        if typeId == "sc75":
            address = valuesDict.get('address', "")

            # Make sure a value was entered for the address.
            if len(address) < 1:
                errorMsgDict['address'] = "Please enter an IP address for the receiver."
                errorMsgDict['showAlertText'] = errorMsgDict['address']
                return False, valuesDict, errorMsgDict

            # Make sure the address entered is in the correct IP address format.
            addressParts = address.split(".")
            # (This is easier than using Regular Expressions.  :-) )
            for part in addressParts:
                try:
                    part = int(part)
                    if part < 0 or part > 255:
                        errorMsgDict['address'] = "Please enter a valid IP address for the receiver."
                        errorMsgDict['showAlertText'] = errorMsgDict['address']
                        return False, valuesDict, errorMsgDict
                except ValueError:
                    errorMsgDict['address'] = "Please enter a valid IP address for the receiver."
                    errorMsgDict['showAlertText'] = errorMsgDict['address']
                    return False, valuesDict, errorMsgDict

            # For newly created devices, the deviceId won't be in the device list.
            if deviceId > 0:
                device = indigo.devices[deviceId]
                devProps = device.pluginProps

                # See if any other devices are using the same address by going through all devices for this plugin.
                for d in self.deviceList:
                    a = indigo.devices[d].pluginProps['address']
                    # If the address found is the same as this device's address (and the matching address is not for
                    # this device), generate an error.
                    if (a == address) and (d != deviceId):
                        error = True
                        errorMsgDict['address'] = (
                            f"This address is already being used by the device \"{indigo.devices[d].name}\". Only one "
                            f"device at a time can connect to a receiver."
                        )
                        errorMsgDict['showAlertText'] = errorMsgDict['address']

                # Make sure the MCACC Memory Label properties are created, even if they aren't specified.
                for mcmccMemory in range(1, 7):
                    propName = f"mcmccMemory{mcmccMemory}label"
                    if valuesDict.get(propName, "") == "":
                        devProps.update({propName: ""})
                        self.updateDeviceProps(device, devProps)

        #
        # Virtual Level Control Device
        #
        elif typeId == "virtualVolume":
            receiverDeviceId = valuesDict.get('receiverDeviceId', 0)
            controlDestination = valuesDict.get('controlDestination', "")
            if len(receiverDeviceId) < 1:
                errorMsgDict['receiverDeviceId'] = "Please select a Pioneer Receiver device."
                errorMsgDict['showAlertText'] = errorMsgDict['receiverDeviceId']
                error = True
            elif int(receiverDeviceId) in self.volumeDeviceList:
                errorMsgDict['receiverDeviceId'] = (
                    "The selected device is another Virtual Volume Controller. Only receiver devices can be controlled "
                    "with this Virtual Volume Controller."
                )
                errorMsgDict['showAlertText'] = errorMsgDict['receiverDeviceId']
                error = True
            elif int(receiverDeviceId) not in self.deviceList:
                errorMsgDict['receiverDeviceId'] = ("The selected device no longer exists. Please click Cancel then "
                                                    "click on Edit Device Settings again.")
                errorMsgDict['showAlertText'] = errorMsgDict['receiverDeviceId']
                error = True
            if len(controlDestination) < 1:
                errorMsgDict['controlDestination'] = "Please select a Control Destination."
                errorMsgDict['showAlertText'] = errorMsgDict['controlDestination']
                error = True

        # Return errors if there were any.
        if error:
            return False, valuesDict, errorMsgDict

        return True, valuesDict

    # Plugin Configuration Dialog
    ########################################
    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        self.debugLog("closedPrefsConfigUi called.")

        if not userCancelled:
            self.debug = valuesDict.get("showDebugInfo", False)
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
    def uiSourceList(self, filter="", valuesDict=None, typeId="", deviceId=0):  # noqa
        self.debugLog(f"uiSourceList called. typeId: {typeId}, targetId: {deviceId}")

        theList = list()  # Menu item list.
        device = indigo.devices[deviceId]  # The device whose action is being configured.

        # Catch attempts to send a command to a Virtual Volume Controller device, which is not possible (but because
        # it's not currently possible to prevent the user from selecting it as a destination device in the Indigo UI,
        # we must check for it).
        if device.deviceTypeId == "virtualVolume":
            self.errorLog(
                f"Device \"{device.name}\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo "
                f"action to send the command to a Pioneer receiver instead of this device.")
            return []

        # Go through the defined sources to decide which to add to the list.
        for thisNumber, thisName in SOURCE_NAMES.items():
            # Create the list based on which zone for which this is being compiled.
            if typeId == "zone1setSource":
                # If this source ID is not masked (i.e. is available) on this model, add it.
                if device.deviceTypeId == "vsx1021k":
                    if thisNumber not in VSX1021k_SOURCE_MASK:
                        propName = f"source{thisNumber}label"
                        thisName = device.pluginProps[propName]
                        theList.append((thisNumber, thisName))
                elif device.deviceTypeId == "vsx1022k":
                    if thisNumber not in VSX1022K_SOURCE_MASK and thisNumber not in ['46', '47']:
                        # Source 46 (AirPlay) and 47 (DMR) are not selectable, but are valid sources, so they're not in
                        # the mask array.
                        propName = f"source{thisNumber}label"
                        thisName = device.pluginProps[propName]
                        theList.append((thisNumber, thisName))
                elif device.deviceTypeId == "vsx1122k":
                    if thisNumber not in VSX1122K_SOURCE_MASK:
                        propName = f"source{thisNumber}label"
                        thisName = device.pluginProps[propName]
                        theList.append((thisNumber, thisName))
                elif device.deviceTypeId == "vsx1123k":
                    if thisNumber not in VSX1123K_SOURCE_MASK:
                        propName = f"source{thisNumber}label"
                        thisName = device.pluginProps[propName]
                        theList.append((thisNumber, thisName))
                elif device.deviceTypeId == "sc75":
                    if thisNumber not in SC75_SOURCE_MASK:
                        propName = f"source{thisNumber}label"
                        thisName = device.pluginProps[propName]
                        theList.append((thisNumber, thisName))
            elif typeId == "zone2setSource":
                # If this source ID is not masked (i.e. is available) on this model, add it.
                if device.deviceTypeId == "vsx1021k":
                    if thisNumber not in VSX1021K_ZONE2_SOURCE_MASK:
                        propName = f"source{thisNumber}label"
                        thisName = device.pluginProps[propName]
                        theList.append((thisNumber, thisName))
                elif device.deviceTypeId == "vsx1022k":
                    if thisNumber not in VSX1022K_ZONE2_SOURCE_MASK and thisNumber not in ['46', '47']:
                        # Source 46 (AirPlay) and 47 (DMR) are not selectable, but are valid sources, so they're not in
                        # the mask array.
                        propName = f"source{thisNumber}label"
                        thisName = device.pluginProps[propName]
                        theList.append((thisNumber, thisName))
                elif device.deviceTypeId == "vsx1122k":
                    if thisNumber not in VSX1122K_ZONE2_SOURCE_MASK:
                        propName = f"source{thisNumber}label"
                        thisName = device.pluginProps[propName]
                        theList.append((thisNumber, thisName))
                elif device.deviceTypeId == "vsx1123k":
                    if thisNumber not in VSX1123k_ZONE2_SOURCE_MASK:
                        propName = f"source{thisNumber}label"
                        thisName = device.pluginProps[propName]
                        theList.append((thisNumber, thisName))
                elif device.deviceTypeId == "sc75":
                    if thisNumber not in SC75_ZONE2_SOURCE_MASK:
                        propName = f"source{thisNumber}label"
                        thisName = device.pluginProps[propName]
                        theList.append((thisNumber, thisName))

        return theList

    # Get Tuner Preset List for Use in UI.
    ########################################
    def uiTunerPresetList(self, filter="", valuesDict=None, typeId="", deviceId=0):  # noqa
        self.debugLog(f"uiTunerPresetList called. typeId: {typeId}, targetId: {deviceId}")

        theList = list()  # Menu item list.
        device = indigo.devices[deviceId]  # The device whose action is being configured.
        propName = ""  # Device property name to be queried.
        presetName = ""  # Tuner Preset name to be listed.
        presetNumber = ""  # Tuner Preset number to be returned in the list selection.

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
        presetClasses = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        # Go through the preset classes and numbers 1 through 9 to get the preset names.
        for theClass in presetClasses:
            for thePreset in range(1, 9):
                propName = f"tunerPreset{theClass}{thePreset}label"
                presetName = f"{theClass}{thePreset}: {device.pluginProps[propName]}"
                presetNumber = f"{theClass}0{thePreset}"
                theList.append((presetNumber, presetName))

        return theList

    # Get MCACC Label List for Use in UI.
    ########################################
    def uiMcaccLabelList(self, filter="", valuesDict=None, typeId="", deviceId=0):  # noqa
        self.debugLog(f"uiMcaccLabelList called. typeId: {typeId}, targetId: {deviceId}")

        theList = list()  # Menu item list.
        device = indigo.devices[deviceId]  # The device whose action is being configured.
        propName = ""  # Device property name to be queried.
        mcaccMemoryName = ""  # MCACC Memory label (name) to be listed.
        mcaccMemory = ""  # MCACC Memory number to be returned in the list selection.

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
        for mcaccMemory in range(1, 7):
            propName = f"mcaccMemory{mcaccMemory}label"
            mcaccMemoryName = f"{mcaccMemory}: {device.pluginProps[propName]}"
            # Convert the mcaccMemory number into a command.
            mcaccMemory = f"{mcaccMemory}MC"
            theList.append((mcaccMemory, mcaccMemoryName))

        return theList

    # Get Remote Control Button Names
    ########################################
    def uiButtonNames(self, filter="", valuesDict=None, typeId="", deviceId=0):  # noqa
        self.debugLog(f"uiButtonNames called. typeId: {typeId}, targetId: {deviceId}")

        theList = list()  # Menu item list.
        device = indigo.devices[deviceId]  # The device whose action is being configured.
        command = ""  # The button press command.
        buttonName = ""  # The name of the button to list in the menu.

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
            buttonName = REMOTE_BUTTON_NAMES.get(command, "")
            theList.append((command, buttonName))

        return theList

    # Get List of Listening Modes.
    ########################################
    def uiListeningModeList(self, filter="", valuesDict=None, typeId="", deviceId=0):  # noqa
        self.debugLog(f"uiListeningModeList called. typeId: {typeId}, targetId: {deviceId}")

        theList = list()  # Menu item list.
        theNumber = ""  # The listening mode ID number
        theName = ""  # The listening mode name.
        device = indigo.devices[deviceId]  # The device whose action is being configured.

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
        reverseItems = [[v[1], v[0]] for v in items]
        reverseItems.sort()
        sortedlist = [reverseItems[i][1] for i in range(0, len(reverseItems))]

        for theNumber in sortedlist:
            theName = LISTENING_MODES[theNumber]
            # Show only items related to the device type passed in the "filter" variable.
            if filter == "vsx1021k":
                if theNumber not in VSX1021K_LISTENING_MODE_MASK:
                    # Don't list modes with "(cyclic)" in the name.
                    if "(cyclic)" not in theName:
                        theList.append((theNumber, theName))
            elif filter == "vsx1022k":
                if theNumber not in VSX1022K_LISTENING_MODE_MASK:
                    # Don't list modes with "(cyclic)" in the name.
                    if "(cyclic)" not in theName:
                        theList.append((theNumber, theName))
            elif filter == "vsx1122k":
                if theNumber not in VSX1122K_LISTENING_MODE_MASK:
                    # Don't list modes with "(cyclic)" in the name.
                    if "(cyclic)" not in theName:
                        theList.append((theNumber, theName))
            elif filter == "vsx1123k":
                if theNumber not in VSX1123K_LISTENING_MODE_MASK:
                    # Don't list modes with "(cyclic)" in the name.
                    if "(cyclic)" not in theName:
                        theList.append((theNumber, theName))
            elif filter == "sc75":
                if theNumber not in SC75_LISTENING_MODE_MASK:
                    # Don't list modes with "(cyclic)" in the name.
                    if "(cyclic)" not in theName:
                        theList.append((theNumber, theName))

        return theList

    # Get List of Pioneer Receiver Devices.
    ########################################
    # (This method is deprecated as of 0.9.6, but kept for possible future reference.
    def uiReceiverDevices(self, filter="", valuesDict=None, typeId="", targetId=0):  # noqa
        self.debugLog(f"uiReceiverDevices called. typeId: {typeId}, targetId: {targetId}")

        theList = list()  # Menu item list.
        deviceId = ""  # The device ID of the Pioneer Receiver listed.
        deviceName = ""  # The name of the Pioneer Receiver device listed.

        # Go through the deviceList and list the devices.
        for deviceId in self.deviceList:
            deviceName = indigo.devices[deviceId].name
            theList.append((deviceId, deviceName))

        return theList
