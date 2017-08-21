#!/usr/bin/python3
#Follow me in instgram : _.brbr
#Follow me in Facebook : https://www.facebook.com/albaraa.alhamidi
import socket
from colorama import Fore
import sys
import subprocess
from datetime import datetime

#clear Terminal

subprocess.call("clear",shell=True)
print("      ##################################################")
print("      #         Thank You For work My scrip  ❤️         #")
print("      #        https://github.com/bara-alhamidi        #")
print("      #              gift to all my friends            #")
print("      ##################################################")

#input website or ip to scan

website=input("[+] Enter website or IP to scan : ")
website=website.replace("http://","")
website=website.replace("https://","")
website=website.replace("/","")
website=website.replace(" ","")

#get ip host

try:
   ips=socket.gethostbyname(website)
except socket.gaierror:
    print (Fore.LIGHTRED_EX,'[!] Hostname could not be resolved. Exiting....')
    sys.exit()
except socket.error:
    print (Fore.LIGHTRED_EX,'[!] Your Not connect internet')
    sys.exit()
except IOError:
    print(Fore.LIGHTRED_EX,"[!] Error .....")
    sys.exit()
else:
    print(Fore.LIGHTBLUE_EX, "-" * 70)
    print(Fore.LIGHTGREEN_EX,"[+] Please wait, scanning IP {}".format(ips))
    print(Fore.LIGHTBLUE_EX,"-" * 70)
time1=datetime.now()

#connect host and scan port

try:
    for port in range(10, 1024):
        scan = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rules=scan.connect_ex((ips,port))
        if rules == 0:
            print(Fore.LIGHTBLUE_EX,"[*] Port {} =====> Open".format(port))
        scan.close()
#if press ctrl+C to exit
except KeyboardInterrupt:
    print(Fore.LIGHTRED_EX,"[!] You pressed Ctrl+C to exit... ")
    sys.exit()
except socket.gaierror:
    print (Fore.LIGHTRED_EX,'[!] Hostname could not be resolved. Exiting')
    sys.exit()
#not connct internet
except socket.error:
    print (Fore.LIGHTRED_EXs,"[!] Your Not connect internet")
    sys.exit()
else:
    time2 = datetime.now()
    total = time2 - time1

    # finish script

    print(Fore.LIGHTYELLOW_EX, '[+] Scanning Completed in : {}'.format(total))
    print(Fore.LIGHTBLUE_EX, "-" * 70)
