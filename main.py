# (O)CU(L)D – octopus crypto universal ligtning device
# https://www.octopusengine.org/octopus-crypto-device/
# ESP32 + Micropython + OctopusLab modules
# TFT 1.8", NFC-RFID, KeyPad 4x4/5x4
# 2021/11

from time import sleep, sleep_ms, ticks_ms
from machine import SPI, Pin, UART, I2C
from utils.octopus_lib import w # need connection for FTP
from utils.octopus_decor import octopus_debug
from utils.pinout import set_pinout
from ST7735 import TFT, TFTColor
from lib.rgb import color565
from assets.sysfont import sysfont
from assets.terminalfont import terminalfont
from uQR import QRCode
from keypad.i2ckeypad import I2CKeypad
from components.rfid import PN532_UART
import _thread

pinout = set_pinout()

print("CRYPTO UNIVERSAL DEVICE - HW basic test")
print("--- i2c keypad expander16 init >")

i2c = I2C(0, scl=Pin(pinout.I2C_SCL_PIN), sda=Pin(pinout.I2C_SDA_PIN), freq=400000)

KP_ADDRESS = 0x25
KP_DELAY = 250
KP_INTERRUPT = 39
kp = I2CKeypad(i2c, KP_ADDRESS, 16)


COIN_INTERRUPT = 35
coin = Pin(COIN_INTERRUPT, Pin.IN)


print("--- spi.TFT 128x160 init >")
# spi = SPI(1, baudrate=10000000, polarity=1, phase=0, sck=Pin(pinout.SPI_CLK_PIN), mosi=Pin(pinout.SPI_MOSI_PIN))
# ss = Pin(pinout.SPI_CS0_PIN, Pin.OUT)
cs = 26  # Pin(26, Pin.OUT) #R_D2
dc = 25  # Pin(25, Pin.OUT) #R_D1
rst = 27 # Pin(27, Pin.OUT) #PWM1(17) > DEv3(27)

print("--- TFT 128x160px init >")
spi = SPI(2, baudrate=20000000, polarity=0, phase=0, sck=Pin(pinout.SPI_CLK_PIN), mosi=Pin(pinout.SPI_MOSI_PIN), miso=Pin(pinout.SPI_MISO_PIN))
tft=TFT(spi, dc, 16, cs)   # tft(dc,rst,cs)

tft.initr()
tft.rgb(True)

posx = 3
posy = 3

def box(x,y,val,valcol,label=".:."):
   tft.fillrect((x,y), (76, 35), tft.BLACK)
   tft.rect((x,y), (76, 35), tft.GRAY)
   tft.text((x+posx,y+3), label, TFT.GRAY, sysfont, 1)
   tft.text((x+posx,y+13), str(val), valcol, terminalfont, 2)


def qrcode(code="OctopusLAB"):
    xq, yq = 10, 10
    qr = QRCode()
    qr.add_data(code)
    matrix = qr.get_matrix()
    print("code: ", code)
    print("matrix: ", len(matrix), len(matrix[0]))

    for y in range(len(matrix)*2):               # Scaling the bitmap by 2
      for x in range(len(matrix[0])*2):          # because my screen is tiny.
         value = not matrix[int(y/2)][int(x/2)]  # Inverting the values because
         #screen.pixel(xq+x, yq+y, value)        # black is `True` in the matrix.
         if value: tft.pixel((xq+x, yq+y),tft.WHITE)
         

def tftprinttest():
    tft.fill(TFT.BLACK)
    v = 30
    tft.text((0, v), "octopus LAB (1)", TFT.RED, sysfont, 1, nowrap=True)
    v += sysfont["Height"]
    tft.text((0, v), "octopus LAB (2)", TFT.YELLOW, terminalfont, 2, nowrap=True)
    v += sysfont["Height"] * 2
    tft.text((0, v), "octopus LAB (3)", TFT.GREEN, sysfont, 3, nowrap=True)
    v += sysfont["Height"] * 3
    tft.text((0, v), str(1234.567)+ " (4)", TFT.BLUE, sysfont, 4, nowrap=True)
    sleep_ms(3000)
    tft.fill(TFT.BLACK)
    v = 0
    fh = sysfont["Height"]
    tft.text((0, v), "sysfont", TFT.WHITE, sysfont)
    v += fh 
    tft.text((0, v), "terminalfont", TFT.WHITE, terminalfont)
    
    v += fh  * 3
    tft.text((0, v), hex(8675309), TFT.GREEN, terminalfont)
    v += fh 
    tft.text((0, v), " Print HEX!", TFT.GREEN, terminalfont)
    v += fh  * 2
    tft.text((0, v), "Sketch has been", TFT.WHITE, terminalfont)
    v += fh 
    tft.text((0, v), "running for: ", TFT.WHITE, terminalfont)
    v += fh 
    tft.text((0, v), str(ticks_ms() / 1000), TFT.PURPLE, terminalfont, 2)
    v += fh *2
    tft.text((0, v), " seconds.", TFT.WHITE, sysfont)
    sleep(3)

# @octopus_debug
def test_main():
    tft.fill(TFT.BLACK)
    tft.rotation(0)
    """ ok
    print("--- bmp image ---")
    #bmpimage('test128x160.bmp')
    bmpimage('assets/ek3.bmp')
    sleep(1)
    #bmpimage('assets/esp32doit.bmp')
    """
    tft.fill(TFT.BLACK)
    tft.rotation(3) # 1
    tft.text((0, 0), "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur adipiscing ante sed nibh tincidunt feugiat. Maecenas enim massa, fringilla sed malesuada et, malesuada sit amet turpis. Sed porttitor neque ut ante pretium vitae malesuada nunc bibendum. Nullam aliquet ultrices massa eu hendrerit. Ut sed nisi lorem. In vestibulum purus a tortor imperdiet posuere. ", TFT.WHITE, sysfont, 1)
    sleep_ms(2000)

    #tft.rotation(1)
    #tftprinttest()
    sleep(1)


def read_keypad(kp):
    global coins
    print("Starting Keypad reader thread")
    displayNum = ""
    lastKeyPress = 0
    keyDelay = KP_DELAY

    while True:
        try:
            key = kp.getKey()
        except OSError as e:
            print("Error while get key")
            print(e)
            key = None

        if key and ticks_ms() > lastKeyPress+keyDelay:
            lastKeyPress = ticks_ms()
            print(key)
            # ToDo action for "*"
            if key == '#': # Enter
                print("final number: ", displayNum)
            else:
                displayNum += str(key)
            #d7.show((8-len(displayNum))*" " + displayNum)

            if key == 'C': # Clear
                displayNum = ""
                coins = 0


coins = 0
coin_lastint = 0
def coin_interrupt(pin):
    global coin_lastint
    global coins
    if coin_lastint + 28 > ticks_ms():
        return

    coin_lastint = ticks_ms()
    coins+=10


print("color-fill test")
tft.fill(color565(255,0,0))
sleep(0.3)
tft.fill(color565(0,255,0))
sleep(0.3)
tft.fill(color565(0,0,255))
sleep(0.3)
 

# test_main()

tft.rotation(3)
tft.fill(TFT.BLACK)
tft.text((posx-1,2), "CRYPTO UNIVERS. DEVICE", TFT.WHITE, terminalfont,1)
tft.text((posx-1,112), "status EDU_KIT ::: 12:23 :::", TFT.WHITE, sysfont,1)
tft.text((6,90), "Agama21", TFT.MAROON, terminalfont,2)
#box(3,12,"23.6" + chr(223)+"C",TFT.YELLOW,"temperature")
box(posx,12,"-",TFT.YELLOW,"input box")
box(posx+78,12,0,TFT.GREEN,"counter")
box(posx,12+37,0,TFT.YELLOW,"Coins")
box(posx+78,12+37,"LNURL",TFT.YELLOW,"BTC")


print("--- uart PN32 init >")
uart = UART(2, 115200)
#UART1:
#uart.init(baudrate=115200, tx=pinout.TXD1, rx=pinout.RXD1, timeout=100)
#UART2:
uart.init(baudrate=115200, tx=pinout.PWM1_PIN, rx=pinout.PWM2_PIN, timeout=100)
pn532 = PN532_UART(uart, debug=False)
ic, ver, rev, support = pn532.firmware_version
print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))
# Configure PN532 to communicate with MiFare cards
pn532.SAM_configuration()

print("Setting up COIN acceptor interrupt")
coin.irq(coin_interrupt, Pin.IRQ_RISING)

print("Waiting for KEY-PAD - RFID/NFC card...")
_thread.start_new_thread(read_keypad, [kp])

j = 0
while True:
    # Check if a card is available to read
    uid = pn532.read_passive_target(timeout=1)
    print(".", end="")
    if uid is not None:
        card_id = ""
        for i in uid:
           card_id += str(hex(i))[2:]

        print("Found card with UID:", card_id)
        tft.text((2,112), "CARD ID: " + card_id + " "*10, TFT.WHITE, sysfont,1)
        #piezzo.beep()
        
    pn532.power_down()
    box(3+78,12,str(j),TFT.GREEN,"counter")
    box(posx,12+37,coins,TFT.YELLOW,"Coins")
    j += 1
    sleep(0.2)

