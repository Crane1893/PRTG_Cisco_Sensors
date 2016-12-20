from pysnmp.entity.rfc3413.oneliner import cmdgen
import time
import pyicmp.ping as ping
from decimal import Decimal

import sys
import json
from paepy.ChannelDefinition import CustomSensorResult

cmdGen = cmdgen.CommandGenerator()

data_par = json.loads(sys.argv[1])

#Connection Settings
ipAddr = data_par['host']
portNr = 161
snmpStr = "public"

#Time between the two polls in seconds
deltaTime = 5

#Define global variables
switchType = ""
numberSwitchPorts = ""
switchPortsExtensions = []

tempOID = ""
tempValue = ""

ifInOctetsOID = ""
ifOutOctetsOID = ""
ifSpeedOID = ""

#Contains data in the following order:
	#0: [interface_name(10101),
	#1:  interface_speed,
	#2:  time_first_poll,
	#3:  result_first_poll_in,
	#4:  result_first_poll_out,
	#5:  time_second_poll,
	#6:  result_second_poll_in,
	#7:  result_second_poll_out,
	#8:  time_difference,
	#9:  result_difference_in,
	#10: result_difference_out]
arrMultipleValues = []

#Convert int to string with leading zeroes
def intToStringWithZeroes(intOld):
	intNew = format(intOld, "02")
	return(intNew)

#Get type of switch and return it 
def getSwitchType():
	#Get General Information
	errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
		cmdgen.CommunityData(snmpStr),
		cmdgen.UdpTransportTarget((ipAddr, portNr)),
		"iso.0.8802.1.1.2.1.5.4795.1.2.7.0"
	)
	return varBinds[0][1]

#Define OID values according to switch model
def writeOIDValues(model):
	global tempOID, numberSwitchPorts, ifInOctetsOID, ifOutOctetsOID, ifSpeedOID
	modelStr = str(model)
	if modelStr == "WS-C3560G-24PS":
		numberSwitchPorts = 24
		tempOID = "1.3.6.1.4.1.9.9.13.1.3.1.3.1005"
		ifInOctetsOID = "1.3.6.1.2.1.2.2.1.10."
		ifOutOctetsOID = "1.3.6.1.2.1.2.2.1.16."
		ifSpeedOID = "1.3.6.1.2.1.2.2.1.5."
	else:
		numberSwitchPorts = 48
		tempOID = "1.3.6.1.4.1.9.9.13.1.3.1.3.1005"
		ifInOctetsOID = "1.3.6.1.2.1.2.2.1.10."
		ifOutOctetsOID = "1.3.6.1.2.1.2.2.1.16."
		ifSpeedOID = "1.3.6.1.2.1.2.2.1.5."
	return None

#Return the switch temperature in celsius
def getSwitchTemperature():
	#Get temperature of the switch
	errorIndication1, errorStatus1, errorIndex1, varBinds1 = cmdGen.getCmd(
		cmdgen.CommunityData(snmpStr),
		cmdgen.UdpTransportTarget((ipAddr, portNr)),
		tempOID
	)
	return varBinds1[0][1]

def doPing():
	p = ping.Ping(ipAddr,0,0,555,128)
	return p
	
def printGeneralInformation():
	#Print General Information
	print("General Information:")
	if errorIndication0:
		print(errorIndication0)
	else:
		if errorStatus0:
			print("%s at %s" % (
				errorStatus0.prettyPrint(),
				errorIndex0 and varBinds0[int(errorIndex0)-1] or "?"
				)
			)
		else:
			for name, val in varBinds0:
				print("\t%s = %s" % (name.prettyPrint(), val.prettyPrint()))

def getFirstResults():
	for i in range(0,numberSwitchPorts):
		arrMultipleValues[i].append(time.time())
		arrMultipleValues[i].append(getSwitchPortInterfaceInOctets(arrMultipleValues[i][0]))
		arrMultipleValues[i].append(getSwitchPortInterfaceOutOctets(arrMultipleValues[i][0]))
		
def getSecondResults():
	for i in range(0,numberSwitchPorts):
		arrMultipleValues[i].append(time.time())
		arrMultipleValues[i].append(getSwitchPortInterfaceInOctets(arrMultipleValues[i][0]))
		arrMultipleValues[i].append(getSwitchPortInterfaceOutOctets(arrMultipleValues[i][0]))	

def getDifferences():
	for i in range(0,numberSwitchPorts):
		arrMultipleValues[i].append(getTimeDiff(i))
		arrMultipleValues[i].append(getInDiff(i))
		arrMultipleValues[i].append(getOutDiff(i))
		
#Convert the port-numbers into snmp-compatible values: 1 -> 10101, 13 -> 10113, ...	
def writeSwitchPortsExtensionsToArray():
	for x in range(1, numberSwitchPorts+1):
		arrMultipleValues.append([10100 + x])

def writeSwitchPortSpeedToArray():
	for i in range(0, numberSwitchPorts):
		arrMultipleValues[i].append(getSwitchPortSpeed(arrMultipleValues[i][0]))
		
def getSwitchPortSpeed(port):
	errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
		cmdgen.CommunityData(snmpStr),
		cmdgen.UdpTransportTarget((ipAddr, portNr)),
		ifSpeedOID + str(port)
	)
	return(int(varBinds[0][1]))

def getSwitchPortInterfaceInOctets(port):
	errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
		cmdgen.CommunityData(snmpStr),
		cmdgen.UdpTransportTarget((ipAddr, portNr)),
		ifInOctetsOID + str(port)
	)
	return(int(varBinds[0][1]))
	
def getSwitchPortInterfaceOutOctets(port):
	errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
		cmdgen.CommunityData(snmpStr),
		cmdgen.UdpTransportTarget((ipAddr, portNr)),
		ifOutOctetsOID + str(port)
	)
	return(int(varBinds[0][1]))

#Calculate Differences between first poll time and second poll time
def getTimeDiff(arrayIndex):
	f = arrMultipleValues[arrayIndex][2]
	s = arrMultipleValues[arrayIndex][5]
	return(s - f)
	
#Calculate Differences between first in_result and second in_result
def getInDiff(arrayIndex):
	f = arrMultipleValues[arrayIndex][3]
	s = arrMultipleValues[arrayIndex][6]
	return(s - f)
		
#Calculate Differences between first out_result and second out_result
def getOutDiff(arrayIndex):
	f = arrMultipleValues[arrayIndex][4]
	s = arrMultipleValues[arrayIndex][7]
	return(s - f)

#Calculate the ifInOctets-Speed	
def getInSpeed(arrayIndex):
	deltaIfIn = arrMultipleValues[arrayIndex][9]
	deltaTimeInOut = arrMultipleValues[arrayIndex][8]
	portSpeed = arrMultipleValues[arrayIndex][1]
	return((deltaIfIn * 8 * 100)/(deltaTimeInOut * portSpeed))
	
#Calculate the ifInOctets-Speed	
def getOutSpeed(arrayIndex):
	deltaIfOut = arrMultipleValues[arrayIndex][10]
	deltaTimeInOut = arrMultipleValues[arrayIndex][8]
	portSpeed = arrMultipleValues[arrayIndex][1]
	return((deltaIfOut * 8 * 100)/(deltaTimeInOut * portSpeed))
	
def getInSpeedTotal(arrayIndex):
	deltaIfIn = arrMultipleValues[arrayIndex][9]
	deltaTimeInOut = arrMultipleValues[arrayIndex][8]
	inSpeed = ((deltaIfIn*8)/(deltaTimeInOut)/1000)
	inSpeedD = Decimal(inSpeed)
	return(round(inSpeedD,2))
	
#Calculate the ifInOctets-Speed	
def getOutSpeedTotal(arrayIndex):
	deltaIfOut = arrMultipleValues[arrayIndex][10]
	deltaTimeInOut = arrMultipleValues[arrayIndex][8]
	outSpeed = ((deltaIfOut*8)/(deltaTimeInOut)/1000)
	outSpeedD = Decimal(outSpeed)
	return(round(outSpeedD,2))
		
errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
	cmdgen.CommunityData("public"),
	cmdgen.UdpTransportTarget((ipAddr, portNr)),
#	cmdgen.MibVariable("IF-MIB", "ifOperStatus.1", 0)
	#Location:
	".1.3.6.1.2.1.1.6.0",
	#
	"1.3.6.1.2.1.2.1",
	#Number of Ports?
	"1.3.6.1.2.1.2.1.0",
	#
	"1.3.6.1.2.1.2.2.1.2",
	#VLAN 1?
	"1.3.6.1.2.1.2.2.1.2.1",
	#VLAN100:
	"1.3.6.1.2.1.2.2.1.2.100",
	#Port-channel 1
	"1.3.6.1.2.1.2.2.1.2.5001",
	#Name Port 1
	"1.3.6.1.2.1.2.2.1.2.10101",
	#Name Port 2
	"1.3.6.1.2.1.2.2.1.2.10102",
	#
	"1.3.6.1.2.1.2.2.1.8",
	#
	"1.3.6.1.2.1.2.2.1.8.1",
	#
	"1.3.6.1.4.1.9.9.46.1.4.2.1.4.1.48.10101",
	#local:
	"1.3.6.1.4.1.9.2",
	#ifInOctets:
	".1.3.6.1.2.1.2.2.1.10.10115",
	#ifOutOctets:
	".1.3.6.1.2.1.2.2.1.16.10115",
	#ifSpeed:
	".1.3.6.1.2.1.2.2.1.5.10115",
	lookupNames=True, lookupValues=True
)

#Get second set of results
errorIndication2, errorStatus2, errorIndex2, varBinds2 = cmdGen.getCmd(
	cmdgen.CommunityData("public"),
	cmdgen.UdpTransportTarget((ipAddr, portNr)),
	#ifInOctets:
	".1.3.6.1.2.1.2.2.1.10.10115",
	#ifOutOctets:
	".1.3.6.1.2.1.2.2.1.16.10115",
	#ifSpeed:
	".1.3.6.1.2.1.2.2.1.5.10115",
	#duplex - 1: unknown 2: half 3: full:
	".1.3.6.1.2.1.10.7.2.1.19.10115",
	#temp:
	"1.3.6.1.4.1.9.9.13.1.3.1.3.1005",
	#type:
	"iso.0.8802.1.1.2.1.5.4795.1.2.7.0",
	lookupNames=True, lookupValues=True
)

def test():	
	#Check for errors and print out results
	if errorIndication:
		print(errorIndication)
	else:
		if errorStatus:
			print("%s at %s" % (
				errorStatus.prettyPrint(),
				errorIndex and varBinds[int(errorIndex)-1] or "?"
				)
			)
		else:
			for name, val in varBinds:
				print("%s = %s" % (name.prettyPrint(), val.prettyPrint()))
				print(val.prettyPrint())


switchType = getSwitchType()
#print("switchtype: " + switchType)
writeOIDValues(switchType)
tempValue = getSwitchTemperature()
#print("Temp: " + str(tempValue))
writeSwitchPortsExtensionsToArray()
writeSwitchPortSpeedToArray()
getFirstResults()
time.sleep(deltaTime)
getSecondResults()
getDifferences()

def printArrMultipleValues():
	for i in range(0,len(arrMultipleValues)):
		print("Port: " + str(i+1))
		#print(arrMultipleValues[i])
		print("In-Speed:  " + str(getInSpeed(i)))
		print("Out-Speed: " + str(getOutSpeed(i)))
		print("In-Speed:  " + str(getInSpeedTotal(i)))
		print("Out-Speed: " + str(getOutSpeedTotal(i)))
	
ping_result = doPing()

result = CustomSensorResult("OK")

result.add_channel(channel_name="Pingzeit", unit="ms", value=ping_result.result["avg_time"], is_float=True, primary_channel=True,
                       is_limit_mode=True, limit_min_error=0, limit_max_error=250,
                       limit_error_msg="Percentage too high")

result.add_channel(channel_name="Temparatur", unit="°C", value=tempValue, is_float=False, primary_channel=False,
                       is_limit_mode=True, limit_min_error=25, limit_max_error=50,
                       limit_error_msg="Switch temperature too high")

for p in range(0,len(arrMultipleValues)):
	result.add_channel(channel_name="Port "+str(intToStringWithZeroes(p+1))+" In-Traffic", unit="kbit/Sek.", value=getInSpeedTotal(p), is_float=True, primary_channel=False,
                       is_limit_mode=True, limit_min_error=0, limit_max_error=10000,
                       limit_error_msg="Percentage too high")
	result.add_channel(channel_name="Port "+str(intToStringWithZeroes(p+1))+" Out-Traffic", unit="kbit/Sek.", value=getOutSpeedTotal(p), is_float=True, primary_channel=False,
                       is_limit_mode=True, limit_min_error=0, limit_max_error=10000,
                       limit_error_msg="Percentage too high")

print(result.get_json_result())