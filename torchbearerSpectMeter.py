import numpy as np
import serial
import matplotlib.pyplot as plt
# 显示中文
plt.rcParams['font.sans-serif'] = [u'SimHei']
plt.rcParams['axes.unicode_minus'] = False
# %matplotlib inline


ser = serial.Serial()
ser.port = "COM8"
ser.baudrate = 921600


cmd_get_start_and_end_wavelength = b'\xCC\x01\x09\x00\x00\x0F\xE5\x0D\x0A'
cmd_get_single_frame_data		 = b'\xCC\x01\x09\x00\x00\x32\x08\x0D\x0A'
cmd_start_continus_read 		 = b'\xCC\x01\x09\x00\x00\x33\x09\x0D\x0A'
cmd_end_continus_read 		     = b'\xCC\x01\x09\x00\x00\x04\xDA\x0D\x0A'
cmd_get_device_info				 = b'\xCC\x01\x0A\x00\x00\x08\x18\xf7\x0d\x0a'
cmd_set_manual_expo				 = b'\xCC\x01\x0A\x00\x00\x0A\x00\xE1\x0D\x0A'
cmd_set_auto_expo				 = b'\xCC\x01\x0A\x00\x00\x0A\x01\xE2\x0D\x0A'
cmd_set_expo_mode_success		 = b'\xCC\x81\x0A\x00\x00\x0A\x00\x61\x0D\x0A'
cmd_set_expo_mode_failed		 = b'\xCC\x81\x0A\x00\x00\x0A\x15\x76\x0D\x0A'
cmd_get_expo_mode			     = b'\xCC\x01\x09\x00\x00\x0B\xE1\x0D\x0A'
cmd_set_expo_time_success		 = b'\xCC\x81\x0A\x00\x00\x0C\x00\x63\x0D\x0A'
cmd_set_expo_time_failed		 = b'\xCC\x81\x0A\x00\x00\x0C\x15\x78\x0D\x0A'
cmd_get_expo_time				 = b'\xCC\x01\x09\x00\x00\x0D\xE3\x0D\x0A'
cmd_set_max_expo_time_success	 = b'\xCC\x81\x0A\x00\x00\x13\x00\x6a\x0D\x0A'
cmd_set_max_expo_time_failed	 = b'\xCC\x81\x0A\x00\x00\x13\x15\x7f\x0D\x0A'
cmd_get_max_expo_time			 = b'\xCC\x01\x09\x00\x00\x14\xEA\x0D\x0A'


def getCheckSum(byteIn):
	t = 0
	for i in byteIn:
		t += i
	return (t&0b11111111).to_bytes(1, byteorder='little',signed = False)

def get_start_and_end_wave_length(ser):
	ser.open()
	ser.write(cmd_get_start_and_end_wavelength)

	packageHead = ser.read(6)
	start = int.from_bytes(ser.read(2), "little")
	end = int.from_bytes(ser.read(2), "little")
	checkSum = int.from_bytes(ser.read(1), "little")
	packageTail = int.from_bytes(ser.read(2), "little")
	ser.close()
	return [start,end]

def get_single_frame_data(ser):
	ser.open()
	ser.write(cmd_get_single_frame_data)

	packageHead = ser.read(2)
	cmdLen = int.from_bytes(ser.read(3), "little")
	dataSize = int((cmdLen -(6+1+4+2+3))/2)
	dataType = int.from_bytes(ser.read(1), "little")

	exposure_status = int.from_bytes(ser.read(1), "little",signed=False)
	exposure_time = int.from_bytes(ser.read(4), "little",signed=False)
	spectro_para = int.from_bytes(ser.read(2), "little")
	spectro_data_raw = ser.read(dataSize*2)
	packageTail = ser.read(3)
	ser.close()
	spectro_data = []
	for i in range(dataSize):
		expo = int.from_bytes(spectro_data_raw[2*i:2*i+2], "little",signed=False)
		spectro_data.append(expo)

	return [exposure_status,exposure_time,dataSize,spectro_para,spectro_data]


def get_device_info(ser):
	ser.open()
	ser.write(cmd_get_device_info)
	packageHead = ser.read(2)
	cmdLen = int.from_bytes(ser.read(3), "little")
	dataType = int.from_bytes(ser.read(1), "little")
	dataSize = cmdLen - 9
	device_info = ser.read(dataSize)
	packageTail = ser.read(3)
	ser.close()
	return device_info.decode()


def set_auto_expo(ser,enable):
	ser.open()
	if enable:
		ser.write(cmd_set_auto_expo)
	else:
		ser.write(cmd_set_manual_expo)
	ret = ser.read(len(cmd_set_expo_mode_success))
	if ret == cmd_set_expo_mode_success:
		print("set success")
	elif ret ==cmd_set_expo_mode_failed:
		print("set failed")
	else:
		print("system error")
	ser.close()
	return

def get_expo_mode(ser):
	ser.open()
	ser.write(cmd_get_expo_mode)
	ret = ser.read(0xa)
	em  = ret[6]
	if em == 1:
		return True
	else:
		return False
	ser.close()


def set_expo_time_us(ser,expo_time):
	if expo_time>0xffffffff or expo_time<0:
		print("invalid exposure time")
		return

	expo_time_in_byte = expo_time.to_bytes(4, byteorder='little',signed = False)
	packageHead = b'\xCC\x01\x0D\x00\x00\x0C'
	checkSum = getCheckSum(packageHead+expo_time_in_byte)
	ser.open()
	ser.write(packageHead)
	ser.write(expo_time_in_byte)
	ser.write(checkSum)
	ser.write(b'\x0d\x0a')

	ret = ser.read(len(cmd_set_expo_time_success))
	if ret == cmd_set_expo_time_success:
		print("set success")
	elif ret ==cmd_set_expo_time_failed:
		print("set failed")
	else:
		print("system error")
	ser.close()


def get_expo_time_us(ser):
	ser.open()
	ser.write(cmd_get_expo_time)
	packageHead = ser.read(6)
	expo_time = int.from_bytes(ser.read(4), "little",signed = False)
	packageTail = ser.read(3)
	return expo_time

def set_max_expo_time_us(ser,max_expo_time):
	if max_expo_time>0xffffffff or max_expo_time<0:
		print("invalid max exposure time")
		return

	expo_time_in_byte = max_expo_time.to_bytes(4, byteorder='little',signed = False)
	packageHead = b'\xCC\x01\x0D\x00\x00\x13'
	checkSum = getCheckSum(packageHead+expo_time_in_byte)
	ser.open()
	ser.write(packageHead)
	ser.write(expo_time_in_byte)
	ser.write(checkSum)
	ser.write(b'\x0d\x0a')

	ret = ser.read(len(cmd_set_expo_time_success))
	if ret == cmd_set_expo_time_success:
		print("set success")
	elif ret ==cmd_set_expo_time_failed:
		print("set failed")
	else:
		print("system error")
	ser.close()

def get_max_expo_time_us(ser):
	ser.open()
	ser.write(cmd_get_max_expo_time)
	packageHead = ser.read(6)
	expo_time = int.from_bytes(ser.read(4), "little",signed = False)
	packageTail = ser.read(3)
	return expo_time

set_auto_expo(ser,False)
set_expo_time_us(ser,1000*100)
spec_start,spec_end = get_start_and_end_wave_length(ser)
single_test_result = get_single_frame_data(ser)
print(spec_start,spec_end,single_test_result)
exposure_status,exposure_time,dataSize,spectro_para,spectro_data = single_test_result

x = [i+spec_start for i in range(dataSize)]
y = [i for i in spectro_data]
# print(y)

# x=np.arange(0,10)
plt.title('盗火者光谱仪读取')
plt.plot(x,y)
plt.show()