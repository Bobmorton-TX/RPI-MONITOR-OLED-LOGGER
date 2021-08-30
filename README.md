# RPI-MONITOR-OLED-LOGGER
Raspberry Pi monitor system stats and display to OLED and log to .csv file

**I am a python beginner, so please excuse coding mistakes - I am happy to learn**

Logging system stats and displaying these on a standard ssd1306 OLED Display. 
Rotary enoder to change scale of graphs and press to show addtional information (press again to return)
PIR motion detector to turn of screen
logging to .csv file which can be read by nextcloud analytics 

todo:
second OLED display on another I2c port

REQUIRED LIBARIES

luma.core
psutil
gpiozero
