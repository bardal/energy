"""Print solar readings from Resol KM2/DeltaSol CS4

Standalone script. Only uses standard packages.

Example usage:
>python.exe resol_solar_reading.py -v [IP.ADDRESS] [PASSWORD]
LOG:  Connecting to [IP.ADDRESS]:7053
LOG:  +HELLO
LOG:  +OK
LOG:  +OK
LOG:  Logged in
LOG:  Scanning for SYNC Byte 0xAA
LOG:  Got SYNC Byte. Reading first part of header
LOG:  Destination 0x0010
LOG:  Source 0x1122
LOG:  Protocol version 1.0
LOG:  command=0x0100 frames=10
LOG:  ['0xf9', '0x01', '0x27', '0x01', '0xb8', '0x22', '0xb8', ...]

Collector Temperature : 50.5 °C
Water     Temperature : 29.5 °C
Pump                  : 100%
Time                  : 8:54
Status                : 0

"""

import argparse
import sys
import socket
import struct

BUFSIZE = 1024
DFA_ADDRESS = 0x0010
DELTASOL_CS4_ADDRESS = 0x1122
PORT = 7053

def receive(sock, numbytes):
    chunks = []
    bytes_recd = 0
    while bytes_recd < numbytes:
        chunk = sock.recv(min(numbytes - bytes_recd, 2048))
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        chunks.append(chunk)
        bytes_recd = bytes_recd + len(chunk)
    return b''.join(chunks)

def vbus_login(sock, password, logger):
    reply = sock.recv(BUFSIZE)
    logger(reply.decode().rstrip())
    
    #Send Password
    sock.send(f"PASS {password}\r\n".encode())
    reply = sock.recv(BUFSIZE)
    assert(reply.rstrip() == b'+OK')
    logger(reply.decode().rstrip())
    
    sock.send("DATA\r\n".encode())
    reply = sock.recv(BUFSIZE)
    logger(reply.decode().rstrip())

def protocolversion(id):
    # Value	Description
    # 0x10 or 16 decimal	Protocol version 1.0
    # 0x20 or 32 decimal	Protocol version 2.0
    # 0x30 or 48 decimal	Protocol version 3.0
    # 0x31 or 49 decimal	Protocol version 3.1
    versions = {
        b'\x10' : '1.0',
        b'\x20' : '2.0',
        b'\x30' : '3.0',
        b'\x31' : '3.1',
    }
    return versions[id]

def recv_header_pt1(logger, sock):
    # Beginning of a VBus data stream
    # The first 6 bytes of a VBus data stream (starting with the SYNC-Byte) share the same structure for all protocol versions:

    # Offset	Description
    # 0	SYNC-Byte (0xAA or 170 decimal)
    # 1	Destination address (low-byte)
    # 2	Destination address (high-byte)
    # 3	Source address (low-byte)
    # 4	Source address (high-byte)
    # 5	Protocol version

    logger('Scanning for SYNC Byte 0xAA')
    while (reply := receive(sock, 1)) != b'\xaa':
        logger(f"Not SYNC - skipping {reply}")

    logger('Got SYNC Byte. Reading first part of header')
    reply = receive(sock, 5)
    (destination, source, pvraw) = struct.unpack('<HHc', reply[:5])
    pv = protocolversion(pvraw)
    logger(f'Destination 0x{destination:0>4x}')
    logger(f'Source 0x{source:0>4x}')
    logger(f'Protocol version {pv}')
    return destination,source,pv

def recv_header_pt2(logger, sock):
    reply = receive(sock, 4)
    # 6	Command (low-byte),            
    # 7	Command (high-byte),            
    # 8	Number of payload frames,            
    # 9	Checksum for offset 1-8
    header2 = struct.unpack('<Hbc', reply[:4])
    nframes = header2[1]
    logger(f"command=0x{header2[0]:0>4x} frames={nframes}")
    return nframes

def recv_frame(sock):
    # The payload is split into blocks of four bytes and transmitted together with its Septet-Byte and a checksum as a „frame“.
    # Offset	Description
    # i + 0	First payload byte, MSB is extracted to Septet-Bit 0
    # i + 1	Second payload byte, MSB is extracted to Septet-Bit 1
    # i + 2	Third payload byte, MSB is extracted to Septet-Bit 2
    # i + 3	Fourth payload byte, MSB is extracted to Septet-Bit 3
    # i + 4	Septet-Byte for offset (i + 0) to (i + 3)
    # i + 5	Checksum for offset (i + 0) to (i + 4)

    bytes_recvd = bytearray(receive(sock, 6))
    septett = bytes_recvd[4]
    for i in range(4):
        if septett & (1 << i):
            bytes_recvd[i] = bytes_recvd[i] | 0x80
    return bytes_recvd[:4]

def recv_frames(sock, nframes):
    frames = b''
    for i in range(nframes):
        frames += recv_frame(sock)
    return frames

def unpack_deltasolcs4_frames(frames):
    # http://danielwippermann.github.io/resol-vbus/#/vsf/bytes/00_0010_1122_10_0100
    # Structure: DFA (0x0010) <= DeltaSol CS4 (0x1122), command 0x0100 (00_0010_1122_10_0100)
    # 0		Temperature sensor 1	0.1	°C
    # 1		Temperature sensor 1	25.6	°C
    # 2		Temperature sensor 2	0.1	°C
    # 3		Temperature sensor 2	25.6	°C
    # 4		Temperature sensor 3	0.1	°C
    # 5		Temperature sensor 3	25.6	°C
    # 6		Temperature sensor 4	0.1	°C
    # 7		Temperature sensor 4	25.6	°C
    # 8		Pump speed relay 1	1	%
    # 10	Operating hours relay 1	1	h
    # 11	Operating hours relay 1	256	h
    # 12	Pump speed relay 2	1	%
    # 14	Operating hours relay 2	1	h
    # 15	Operating hours relay 2	256	h
    # 16	UnitType	1	
    # 17	System	1	
    # 20	ErrorMask	1	
    # 20	0x01	Sensor 1 defective	1	
    # 20	0x02	Sensor 2 defective	1	
    # 20	0x04	Sensor 3 defective	1	
    # 20	0x08	Sensor 4 defective	1	
    # 21	ErrorMask	256	
    # 22	System time	1	
    # 23	System time	256	
    # 24	Status mask	1	
    # 25	Status mask	256	
    # 26	Status mask	65536	
    # 27	Status mask	16777216	
    # 28	Heat quantity	1	Wh
    # 29	Heat quantity	256	Wh
    # 30	Heat quantity	65536	Wh
    # 31	Heat quantity	16777216	Wh
    # 32	SW Version	0.01	
    # 33	SW Version	2.56	
    # 36	Temperature sensor 5	0.1	°C
    # 37	Temperature sensor 5	25.6	°C
    # 38	Flow rate	1	l/h
    # 39	Flow rate	256	l/h

    temps = [None] * 5
    temps[:4] = struct.unpack('<hhhh', frames[:8])
    (pump1, hours1, pump2, hours2) = struct.unpack('<bxhbxh', frames[8:16])
    (unittype, system, errormask, timestamp ,status) = struct.unpack('<bbxxhhi', frames[16:28])
    (heat, version, temps[4], flowrate) = struct.unpack('<ihxxhh', frames[28:40])
    temps = [t*.1 for t in temps]
    return temps,pump1,timestamp,status

def main(ip, port, password, logger):
    
    logger(f"Connecting to {ip}:{port}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))    

    vbus_login(sock, password, logger)
    logger(f"Logged in")

    seenData = False
    while not seenData:

        destination, source, pv = recv_header_pt1(logger, sock)
        
        if pv == '1.0' and destination == DFA_ADDRESS and source == DELTASOL_CS4_ADDRESS:
            nframes = recv_header_pt2(logger, sock)
            frames = recv_frames(sock, nframes)
            logger([f'0x{x:0>2x}' for x in frames])
            temps, pump1, timestamp, status = unpack_deltasolcs4_frames(frames)

            print ()
            print (f"Collector Temperature : {temps[0]:.1f} \N{DEGREE SIGN}C")
            print (f"Water     Temperature : {temps[1]:.1f} \N{DEGREE SIGN}C")
            print (f"Pump                  : {pump1}%")
            print (f"Time                  : {timestamp//60}:{timestamp%60:02d}")
            print (f"Status                : {status}")
            print ()

            seenData = True
        else:
            logger('Not interested, reading next header')

    sock.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('ip_address',type=str,help="IP Address of the KM2")
    parser.add_argument('password',type=str,help="password of the KM2")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()    
    
    logger = lambda *largs : print("LOG: ", *largs) if args.verbose else lambda *largs : None
    
    main(args.ip_address, PORT, args.password, logger)


