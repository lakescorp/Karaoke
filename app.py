import sounddevice
import threading
import soundfile as sf
import json
import os
import time
import pygame
import queue
import sounddevice as sd
import numpy

from os import listdir
from os.path import isfile, join

clear = lambda: os.system('cls')

DATA_TYPE = os.getenv('DATA_TYPE')

DATA_PATH = os.getenv('DATA_PATH')

CONSOLE_LYRICS = int(os.getenv('CONSOLE_LYRICS'))==1

data = None

song1 = None
song2 = None

songIndex = -1

printingLyrics = True

out1 = None
out2 = None

# Config
BLOCKSIZE = int(os.getenv('BLOCKSIZE'))
BUFFERSIZE = int(os.getenv('BUFFERSIZE'))

# Begin: PyGame

pygame.init()

black = (0, 0, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)
blue = (0, 0, 128)
grey = (200,200,200)

infoScreen = pygame.display.Info()

X = infoScreen.current_w
Y = infoScreen.current_h

display_surface = pygame.display.set_mode((X, Y), flags=pygame.HIDDEN)

pygame.display.set_caption('Lyrics')

font = pygame.font.Font('freesansbold.ttf', 32)

# End: PyGame

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class myThread(threading.Thread):
    def __init__(self,filename,device):
        threading.Thread.__init__(self)        
        self.filename = filename
        self.device = device
        self.isPaused = False
        self.isFinsished = False
        self.isReady = False
        self.q = queue.Queue(maxsize=BUFFERSIZE)
        self.event = threading.Event()

    def callback(self,outdata, frames, time, status):
        assert frames == BLOCKSIZE
        if status.output_underflow:
            #print('Output underflow: increase blocksize?', file=sys.stderr)
            raise sd.CallbackAbort
        assert not status
        try:
            data = self.q.get_nowait()
        except queue.Empty as e:
            #print('Buffer is empty: increase buffersize?', file=sys.stderr)
            raise sd.CallbackAbort from e
        if len(data) < len(outdata):
            outdata[:len(data)] = data
            outdata[len(data):].fill(0)
            raise sd.CallbackStop
        else:
            outdata[:] = data  

    def pause(self):
        self.isPaused = not self.isPaused

    def finish(self):
        self.isFinsished = not self.isFinsished

    def run(self):
        try:
            with sf.SoundFile(self.filename) as f:
                for _ in range(BUFFERSIZE):
                    data = f.read(BLOCKSIZE)
                    if not len(data):
                        break
                    self.q.put_nowait(data)  # Pre-fill queue
                stream = sd.OutputStream(
                    samplerate=f.samplerate, blocksize=BLOCKSIZE,
                    device=self.device, channels=f.channels,
                    callback=self.callback, finished_callback=self.event.set)
                with stream:
                    timeout = BLOCKSIZE * BUFFERSIZE / f.samplerate
                    self.isReady = True
                    while len(data) and not self.isFinsished:     
                        if self.isPaused:
                            self.q.put(numpy.zeros((BLOCKSIZE,2)), timeout=timeout)
                        else:
                            data = f.read(BLOCKSIZE)
                            self.q.put(data, timeout=timeout)
                    self.event.wait()  # Wait until playback is finished
        except Exception as e:
            #print(type(e).__name__ + ': ' + str(e))
            quit()
     
def get_devices(): 
    devices = sounddevice.query_devices()
    index = 1
    realIndex = 0
    realIndexList = []
    for device in devices:
        if device['hostapi'] == 0:
            if device['max_input_channels'] == 0:
                print(str(index)+'.',device["name"])
                realIndexList.append(realIndex)
                index+=1
        realIndex += 1
    return realIndexList

def loadData():
    global data
    data = {
        "songs":[]
    }

    onlyfiles = [f for f in listdir(DATA_PATH) if isfile(join(DATA_PATH, f))]

    for elem in onlyfiles:
        namePath = DATA_PATH + '\\' + elem
        f = open(namePath, mode="r", encoding='utf-8')
        miDat = json.load(f)
        data["songs"].append(miDat)
        f.close()

def selectOutput():
    realIndexList = get_devices()

    print()

    global out1,out2
    while out1 == None or out2 == None:
        if out1 == None:
            out1a = input("Select output for singer: ")
            out1a = int(out1a)-1

            if out1a >= 0 and out1a < len(realIndexList):
                out1 = realIndexList[out1a]
            else:
                out1 = None

        if out2 == None:
            out2a = input("Select output for instrumental: ")
            out2a = int(out2a)-1

            if out2a >= 0 and out2a < len(realIndexList):
                out2 = realIndexList[out2a]
            else:
                out2 = None
    clear()

def selectSong():
    selection = None
    while selection is None:
        index = 1
        for cancion in data["songs"]:
            print(str(index)+'.',cancion["title"],"-",cancion["artist"])
            index += 1
        print()
        try:
            selection = int(input("Select a song (0 to exit): "))-1
        except:
            selection = -1
        if selection == -1:
            quit()
        if selection+1 <= 0 or selection+1 >= index:
            selection = None

    global songIndex
    songIndex = selection

    clear()
    global song1,song2
    song1 = data["songs"][songIndex]["songpath"]
    song2 = data["songs"][songIndex]["karaokepath"]

def loadLyrics():
    letras = []
    f = open(data["songs"][songIndex]["lyricspath"], mode="r", encoding="utf-8")
    for x in f:
        line = x.split("[")[1].split("]")
        if line[1] != "\n":
            minutes = int(line[0].split(":")[0])
            seconds = float(line[0].split(":")[1])
            total = 60*minutes+seconds
            letras.append([total,line[1].encode('utf-8')])
    f.close()
    return letras

def writeText(line,pos):
    text = font.render(line[:-1], True, green if pos==2 else white, black)
    textRect = text.get_rect()
    textRect.center = (X // 2, (Y * pos) // 4)
    display_surface.blit(text, textRect)

def writeTitle(title,pos):
    text = font.render(title, True, grey, black)
    textRect = text.get_rect()
    textRect.center = (X // 2, (Y * pos) // 4)
    display_surface.blit(text, textRect)


def pyGameUpdate():
    pygame.display.update()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        elif event.type == pygame.KEYDOWN:
            global printingLyrics
            if printingLyrics and event.key == pygame.K_ESCAPE:
                stopAll()      
                printingLyrics = False


def printLyrics():   
    lyrics = loadLyrics()
    index = 0
    interval = 0
    if CONSOLE_LYRICS:
        clear()
        print('\n\n\n')

    firstLine = lyrics[0][1].decode('utf-8')
    
    if CONSOLE_LYRICS:
        print(firstLine)

    songTitle = data["songs"][songIndex]["title"]+" - "+data["songs"][songIndex]["artist"]

    # PyGame
    display_surface = pygame.display.set_mode((X, Y), flags=pygame.SHOWN|pygame.FULLSCREEN|pygame.NOFRAME)
    pyGameUpdate()
    display_surface.fill(black)
    writeText(firstLine,3)
    writeTitle(songTitle,0.2)
    pyGameUpdate()
    
    global printingLyrics
    printingLyrics = True

    playAll()
    
    while not thread1.isReady and not thread2.isReady:
        pass

    currentTime = time.perf_counter()

    lastLine1 = None
    nextLine = firstLine

    while index < len(lyrics) and printingLyrics:
        interval = time.perf_counter() - currentTime 
        
        if lyrics[index][0] < interval:
            if CONSOLE_LYRICS:
                clear()
            display_surface.fill(black)
            writeTitle(songTitle,0.2)
            if index != 0:
                if CONSOLE_LYRICS:
                    print(lastLine1)
                writeText(lastLine1,1)
            elif CONSOLE_LYRICS:
                print('\n')

            mainLine = nextLine
            if CONSOLE_LYRICS:
                print(bcolors.OKGREEN + mainLine + bcolors.ENDC)
            
            writeText(mainLine,2)
            lastLine1 = mainLine

            if index < len(lyrics)-1:
                lastLine = lyrics[index+1][1].decode('utf-8')
                if CONSOLE_LYRICS:
                    print(lastLine)
                writeText(lastLine,3)
                nextLine = lastLine
            index += 1
        pyGameUpdate()


def playAll():
    play1()
    play2()

def play1():
    global thread1
    thread1 = myThread(song1,out1)
    thread1.start()
    
def play2():
    global thread2
    thread2 = myThread(song2,out2)
    thread2.start()
    
def stopAll():
    stop1()
    stop2()     

def stop1():
    thread1.finish()
    
def stop2():
    thread2.finish()

def pauseAll():
    pause1()
    pause2()

def pause1():
    thread1.pause()

def pause2():
    thread2.pause()

loadData()
selectOutput()
while True:
    selectSong()
    printLyrics()
    while thread1.is_alive() or thread2.is_alive():
        time.sleep(0.5)
    display_surface = pygame.display.set_mode((X, Y), flags=pygame.HIDDEN)

input()