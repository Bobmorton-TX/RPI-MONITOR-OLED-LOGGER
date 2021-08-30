# -*- coding: utf-8 -*-
# Copyright (c) 2021 Bobmorton-TX and contributors
# Incorparates demo code by Richard Hull and contributors https://github.com/rm-hull/luma.examples
# Incorparates code from Sebastian @ https://indibit.de/raspberry-pi-cpu-auslastung-als-diagramm-auf-oled-display/
# See LICENSE.rst for details.

import asyncio
import time
from datetime import datetime
import psutil
from psutil._common import bytes2human
from luma.core.render import canvas                     # Oled rendering
from luma.core.virtual import viewport, snapshot
from PIL import ImageFont
from demo_opts import get_device                        # easy device selection cmd line
import csv                                              # csv export functions
import configparser                                     # config importer
configfile = 'ROL-CONF.ini'                             # location of config file

# Inputs
from gpiozero import Button, RotaryEncoder, MotionSensor
button = Button(14, hold_time=1)                        # Button
rotor = RotaryEncoder(15, 18, wrap=True, max_steps=30)  # Encoder
pir = MotionSensor(22)                                  # Motion Sensor

# second screen
# from luma.core.interface.serial import i2c
# from luma.oled.device import ssd1306, ssd1309, ssd1325, ssd1331, sh1106, ws0010
# serial = i2c(port=3, address=0x3C)
# deviceB = ssd1306(serial, width=128, height=32)

## variables

cpuList = [1]               # cpu data list
netList = [1]               # network total data list
scaledata = [1]             # scale for charts
history_length = 3600       # data collection time
control_output = [0]        # control unit outputs
chartlength = 108           # chart display length
offtimer = [0]              # display off timer       
timeout = 120               # time out in seconds
csvfile = ""                # csv file location
writeout_timer = [0]        # write to csv when = csvscale
csvscale = [600]            # write to csv in seconds
datacollecttimer = [1]      # datacollect in seconds

# Fonts
font1 = ImageFont.truetype('FreeSans.ttf', 9)
font2 = ImageFont.truetype('FreeSans.ttf', 12)

# scroll functions
def scroll_right(virtual, pos): 
    x, y = pos
    if virtual.width > device.width:
        while x < virtual.width - device.width:
            virtual.set_position((x, y))
            x += 1
        x -= 1
        print(x)
    return (x, y)

def scroll_left(virtual, pos):
    x, y = pos
    while x >= 0:
        virtual.set_position((x, y))
        x -= 1
    x = 0
    return (x, y)

def move_right(virtual, pos): 
    x, y = pos
    x = virtual.width - device.width
    virtual.set_position((x, y))    
    x -= 1
    return (x, y)

def move_left(virtual, pos):
    x, y = pos
    x = 0
    virtual.set_position((x, y))
    return (x, y)

# Python program to get average of a list
def avg(data,LEN):
    for i in range((len(data) + LEN - 1) // LEN):
        sublist = data[i*LEN:(i+1)*LEN]
        yield sum(sublist) / len(sublist) 

def timer():
    offtimer[0] = 0
    # print(f'motion detected')

def csvwrite(row):
    # open the file in the write mode
    # f = open('/home/ubuntu/scripts/OLED/HMON/csvtest.csv', 'a', newline='')
    f = open(csvfile, 'a', newline='') # todo via config.file

    # create the csv writer
    writer = csv.writer(f)

    # write a row to the csv file
    writer.writerow(row)

    # close the file
    f.close()


# Button inputs
async def control(delay, signal: asyncio.Event):
    
    while True:
        # Encoder input
        steps = rotor.steps
        stepchk = scaledata[0]
        if steps == 0:          # avoid div by 0
            steps =1
        scaledata[0] = abs(steps)

        control_output[0] = 0        
        if button.is_pressed:
            control_output[0] = 1
            # print(f'knopf pressed')
            signal.set()
                             
        if button.is_held:
            control_output[0] = 2
            # print(f'knopf long pressed')
            signal.set()
            await asyncio.sleep(0.5) # avoid double long press input
        else:
            await asyncio.sleep(delay)
        
        if stepchk != scaledata[0]:
            signal.set()

       
# Collect system info and store in variable
async def data_collect(delay, values, signal: asyncio.Event):
    global uptime, dfpercent, dffree, dftotal, elapsed, nets, netr, mem, mem_free, mem_used, memo, df, cpu_val, tempo
    elapsed, nets, netr, mem, mem_free, mem_used, memo, cpu_val, tempo = 1, 1, 1, 1, 1, 1, 1, 1, 1
    df = 1
    dffree = 1
    dftotal = 1
    dfpercent = 1
    uptime = 1
    
    
    while True:
        # get network data for interval
        tot_before = psutil.net_io_counters()
        await asyncio.sleep(1)
        # time.sleep(delay)
        tot_after = psutil.net_io_counters()
        nets = (tot_after.bytes_sent - tot_before.bytes_sent)
        netr = (tot_after.bytes_recv - tot_before.bytes_recv)

        # Uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        elapsed = datetime.now() - boot_time
        uptimestr = time.strftime('%H:%M:%S', time.gmtime(elapsed.total_seconds()))

        #disk
        df = psutil.disk_usage("/")
        dfpercent = str("{0:0.1f}%".format(df.percent))
        dffree = bytes2human(df.free,)
        dftotal = bytes2human(df.total)

        # CPU+MEM Auslastung auslesen
        cpu_val = psutil.cpu_percent(interval=0)
        mem = psutil.virtual_memory()
        mem_used = (mem.total - mem.available) * 100.0 / mem.total
        mem_free = mem.available
        memo = mem.total


        # Temperatur
        temp = psutil.sensors_temperatures()["cpu_thermal"][0]
        tempo = round(temp.current, 1)

        # fill lists
        cpuList.append(cpu_val) 
        if len(cpuList) > history_length:
            cpuList.pop(0)

        netList.append(nets + netr)
        if len(netList) > history_length:
            netList.pop(0)        
        
        # save to csv
        writeout_timer[0] = writeout_timer[0] + 1 
        if writeout_timer[0] == csvscale[0]:
            # csvwrite(list((datetime.now(), list(avg(cpuList[-5:],5),))))
            csvwrite(list((datetime.now(), round(list(avg(cpuList[-csvscale[0]:],csvscale[0]))[0],1), tempo, list(avg(netList[-csvscale[0]:],csvscale[0]))[0], mem_free, dffree)))

            writeout_timer[0] = 0
        # print(f' csv timer {writeout_timer[0]}')
        signal.set()            # signal that loop is completed
  

async def ausgabe(delay, btn_input, pos, signal: asyncio.Event):
    await signal.wait()         # waiting for either data update or button press
    with canvas(virtual) as draw:
        # debug stuff
        #  print(f'ausgabe button {control_output[0]}')    
        
        # ## change scale on button press
        # if btn_input[0] == 1:
        #     if scaledata[0] == 1:
        #         scaledata[0] = 5
        #     elif scaledata[0] == 5:
        #         scaledata[0] = 1

        ## offtimer

        pir.when_motion = timer
        if offtimer[0] >= timeout:
            device.hide()
            # datacollecttimer[0] = 60    # only collect every minute
            # csvscale[0] = 10             # write to csv every 10 min             
            # deviceB.hide()
        else:
            device.show()
            # datacollecttimer[0] = 1     # collect data every second
            # csvscale[0] = 600             # write to csv every 10 min 
            # deviceB.show()   
        offtimer[0] = offtimer[0] +1
        # print(f'offtimer is {offtimer[0]}')
         
        ###  CPU Diagram   # get last 110 steps of data list
        cpuListavg = list(avg(cpuList,scaledata[0]))    
        if len(cpuListavg) < chartlength:
            liststart = 0
        else:
            liststart = len(cpuListavg) - len(cpuListavg[-chartlength:])

        # draw axis
        draw.line((25, 43, 25, 63), fill=255)            # Y
        draw.line((22, 43, 25, 43), fill=255)            # mark top of axis
        
        # cpuscale = float(max(cpuList[liststart:len(cpuListavg)]))
        cpuscale = max((cpuListavg[liststart:]))
        
        # label axis
        # draw.text((0, 43), f'{round(max(cpuList[liststart:len(cpuListavg)]))} %', font=font1, fill=255) 
        draw.text((0, 43), f'{round(cpuscale)} %', font=font1, fill=255) 
        draw.text((0, 52), "CPU", font=font1, fill=255)


        # CPU chart
               
        X = 26                                            # start of chartdraw

                      
        for n in range(liststart, len(cpuListavg)):
                        
            Y = float(20 / cpuscale * cpuListavg[n]) # tbd avoid divion by 0
            if len(cpuList) == 0:
                draw.line((X, 63 - Y, X, 63 - Y), fill=255)
            else:
                y2 = float(20 / cpuscale * cpuListavg[n-1])
                draw.line((X - 1 , 63 - y2, X, 63 - Y), fill=255)
            # draw.line((X, 63, X, 63 - Y), fill=255) # Balken diagram
            X = X + 1
            

        # NET STATS output

        netListavg = list(avg(netList,scaledata[0]))
        if len(netListavg) < chartlength:
            liststart = 0
        else:
            liststart = len(netListavg) - len(netListavg[-chartlength:])

        X = 26
        # nscale = max(netList[liststart:len(netListavg)])
        nscale = max((netListavg[liststart:]))
        # print(f'netscale {nscale}')

        # Net Diagram
        # draw lables
        draw.text((0, 21), f'{(bytes2human(round(nscale,0)))}', font=font1, fill=255)
        draw.text((0, 29), "NET", font=font1, fill=255)
        # draw axis
        draw.line((22, 21, 25, 21), fill=255)           # mark highest point
        draw.line((25, 21, 25, 41), fill=255)            # Y

        # draw chart

        for n in range(liststart, len(netListavg)):
            if nscale < 1:      # avoid division by 0
                nscale = 1

            Y = float(20 / nscale * netListavg[n])
            draw.line((X, 41, X, 41 - Y), fill=255)
            X = X + 1          

        # draw values to display
        draw.text((0, 0), "C: " + str(cpu_val) + " %", font=font1, fill=255)
        draw.text((42, 0), "M: " + str(bytes2human(mem_free)), font=font1, fill=255)
        draw.text((82, 0), "Tx: " + str(bytes2human(nets)), font=font1, fill=255)
        draw.text((82, 8), "Rx: " + str(bytes2human(netr)), font=font1, fill=255)
        # draw scale information
        draw.rectangle((42, 11, 72, 20), fill="white")
        draw.text((44, 11), f'{scaledata[0]} sec', font=font1, fill="black")
        # draw cpu temp
        draw.text((0, 8), str(tempo) + " °C", font=font1, fill=255)            
        # render uptime and IP
        uptimestr = time.strftime('%d', time.gmtime(elapsed.total_seconds())) + " days " + time.strftime('%H:%M:%S', time.gmtime(elapsed.total_seconds()))
        # debug time        
        # print(uptimestr)
        # print('%d:%H:%M:%S',elapsed)
        draw.text((135, 0), "Up: " + str(uptimestr), font=font1, fill=255)
        draw.text((135, 10), " IP:" + str(psutil.net_if_addrs()['eth0'][0].address), font=font1, fill=255)
        # disk usage
        draw.text((135, 20), text=f'DISK', font=font2, fill="white")
        draw.text((135, 35), text=f'Used {dfpercent}', font=font1, fill="white")
        draw.text((135, 45), text=f'Free: {dffree}', font=font1, fill="white")
        draw.text((135, 55), text=f'Total: {dftotal}', font=font1, fill="white")

        #mem test
        draw.text((200, 20), text=f'MEM', font=font2, fill="white")
        draw.text((200, 35), text="{0:0.1f}%".format(round(mem_used, 1)), font=font1, fill="white")
        draw.text((200, 45), text=f'{bytes2human(mem_free)}', font=font1, fill="white")
        draw.text((200, 55), text=f'{bytes2human(memo)}', font=font1, fill="white")
    
        ## scroll display on button long press
        x, y = pos
 
        if btn_input[0] == 2:
            if x == 0:
                draw.text((0, 10), text=f'Btn {btn_input}', font=font2, fill="white")
                pos = move_right(virtual, pos)
                # virtual.set_position((127, 0))
                # x = 127
                control_output[0] = 0
                # print(f'butn pressed  {btn_input} x {x}')
            elif x > 1:        
                draw.text((0, 10), text=f'Btn L {btn_input}', font=font2, fill="white")
                pos = move_left(virtual, pos)
                # virtual.set_position((0, 0))
                # x = 0
                control_output[0] = 0
        
        if btn_input[0] == 1:
            offtimer[0] = 0     # wake up on button press
 
    # second screen output           
    # with canvas(deviceB) as draw:
    #     draw.text((0, 0), "Up: " + str(uptimestr), font=font2, fill=255)
    #     draw.text((0, 10), " IP:" + str(psutil.net_if_addrs()['eth0'][0].address), font=font2, fill=255)
 

    signal.clear()
    return pos
    

async def main():
    global btn
    # btn = 0 # not needed?
    pos = (0, 0)
    # h = 0 # not needed?
    values = 1
    signal = asyncio.Event()
    task2 = asyncio.create_task(control(0.10, signal))
    task1 = asyncio.create_task(data_collect(1, values, signal))
    
    
    
    while True:

        task3 = asyncio.create_task(ausgabe(0, control_output, pos, signal))
        pos = await task3
        # h = h +1 # not needed?
        # btn = 0 # not needed?

        
        # print(f'h wert {h} button wert {btn}')      
            
if __name__ == '__main__':
    # get config
    config = configparser.ConfigParser()    
    config.read(configfile)
    csvfile = config.get('Oled-config', 'csvpath2')
    
    try:
        device = get_device()                   # device selector default to ssd1306
        virtual = viewport(device, width=device.width * 2, height=device.height)
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

