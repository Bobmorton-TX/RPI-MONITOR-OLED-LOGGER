![20210830_115347_1](https://user-images.githubusercontent.com/86124810/131322382-cdbdfdbc-bf28-4490-aec2-b5c496411592.gif)
# RPI-MONITOR-OLED-LOGGER
Raspberry Pi monitor system stats and display to OLED and log to .csv file

**I am a python beginner, so please excuse coding mistakes - I am happy to learn**

- Logging system stats and displaying these on a standard ssd1306 OLED Display.

- Rotary enoder to change scale of graphs and press to show addtional information (press again to return)

- PIR motion detector to turn of screen

- logging to .csv file which can be read by nextcloud analytics 

![20210830_113800 (2)](https://user-images.githubusercontent.com/86124810/131321424-e9cf35bd-c79c-491b-a09a-e1b805cc6496.jpg)





**REQUIRED LIBARIES**

- python3

- luma.core (https://github.com/rm-hull/luma.core)

- psutil

- gpiozero

**How to use**

- install libaries
- connect display, PIR, Encoder to GPIO (use ports specified or change in code accordingly)
- run script

-- run as system service (this currently gives an error and does not work)

**todo:**

- second OLED display on another I2c port



