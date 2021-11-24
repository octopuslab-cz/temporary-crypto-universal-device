import time
from machine import SPI, Pin, UART, I2C
from ST7735 import TFT, TFTColor
from assets.sysfont import sysfont
from assets.terminalfont import terminalfont

SPI_MISO_PIN = const(19)
SPI_CLK_PIN  = const(18)
SPI_MOSI_PIN = const(23)
SPI_CS0_PIN  = const(5)
cs = 26
dc = 25

posx = 3
posy = 3

spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(SPI_CLK_PIN), mosi=Pin(SPI_MOSI_PIN), miso=Pin(SPI_MISO_PIN))
tft=TFT(spi, dc, 16, cs)
tft.initr()
tft.rgb(True)
tft.rotation(3)

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = f(*args, **kwargs)
        delta = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

@timed_function
def box(x,y,val,valcol,label=".:."):
   tft.fillrect((x,y), (76, 35), tft.BLACK)
   tft.rect((x,y), (76, 35), tft.GRAY)
   tft.text((x+posx,y+3), label, TFT.GRAY, sysfont, 1)
   tft.text((x+posx,y+13), str(val), valcol, terminalfont, 2)

box(0, 0, "test", TFT.YELLOW, "label")

