import cv2, pygame
import numpy as np
from pygame.locals import *

#pygame
pygame.init()
w, h = 320, 240
ws = pygame.display.set_mode((w*2, h+110))
pygame.display.set_caption('Video Stream')
font = pygame.font.SysFont("comicsans", 40)
clock = pygame.time.Clock()

#open camera
cap = cv2.VideoCapture(0)

#draw Text
def drawText(text, font, surface, x, y):
    textobj = font.render(text, 1, (0, 0, 0))
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

#detect if pixel is an edge
t = 20 #threshold
def detect(x, y, frame):
    #up
    global w, h, t
    if y > 0:
        if (np.int16(frame[x, y, 0]) - np.int16(frame[x, y-1, 0]))**2 + (np.int16(frame[x, y, 1]) - np.int16(frame[x, y-1, 1]))**2 + (np.int16(frame[x, y, 2]) - np.int16(frame[x, y-1, 2]))**2 > t**2:
            return True
    #left
    if x > 0:
        if (np.int16(frame[x, y, 0]) - np.int16(frame[x-1, y, 0]))**2 + (np.int16(frame[x, y, 1]) - np.int16(frame[x-1, y, 1]))**2 + (np.int16(frame[x, y, 2]) - np.int16(frame[x-1, y, 2]))**2 > t**2:
            return True
    #down
    if y < h-1:
        if (np.int16(frame[x, y, 0]) - np.int16(frame[x, y+1, 0]))**2 + (np.int16(frame[x, y, 1]) - np.int16(frame[x, y+1, 1]))**2 + (np.int16(frame[x, y, 2]) - np.int16(frame[x, y+1, 2]))**2 > t**2:
            return True
    #right
    if x < w-1:
        if (np.int16(frame[x, y, 0]) - np.int16(frame[x+1, y, 0]))**2 + (np.int16(frame[x, y, 1]) - np.int16(frame[x+1, y, 1]))**2 + (np.int16(frame[x, y, 2]) - np.int16(frame[x+1, y, 2]))**2 > t**2:
            return True
    return False

run = True
new_img = None
while run:
    #get frame
    ret, frame = cap.read()

    #manipulate image
    frame = cv2.resize(frame, (w, h))
    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = pygame.surfarray.make_surface(frame)

    #detection and save image to display later
    """
    new_img = []
    for y in range(h):
        row = []
        for x in range(w):
            row.append(detect(x, y, frame))
        new_img.append(row)
    """
    frame = frame.astype(np.int16)
    if new_img is None:
        new_img = np.empty(frame.shape[0:2])
    elif np.any(np.asarray(new_img.shape) - np.asarray(frame.shape[0:2])):
        new_img = np.empty(frame.shape[0:2])

    frame_1 = frame[1:w-1,1:h-1,:]
    new_img[1:w-1,1:h-1] = (
        (np.sum((frame_1 - frame[0:w-2,1:h-1,:]) ** 2, axis = 2) > t**2) |
        (np.sum((frame_1 - frame[2:w-0,1:h-1,:]) ** 2, axis = 2) > t**2) |
        (np.sum((frame_1 - frame[1:w-1,0:h-2,:]) ** 2, axis = 2) > t**2) |
        (np.sum((frame_1 - frame[1:w-1,2:h-0,:]) ** 2, axis = 2) > t**2))
    new_img = new_img.transpose()

    #display both images and threshold
    ws.blit(img, (0, 0))
    for y in range(h):
        for x in range(w):
            if new_img[y][x]:
                pygame.draw.rect(ws, (0, 0, 0), (x+w, y, 1, 1))
            else:
                pygame.draw.rect(ws, (255, 255, 255), (x+w, y, 1, 1))
    
    clock.tick()#to know the fps
    pygame.draw.rect(ws, (255, 255, 255), (0, h, w*2, 110))
    drawText("Threshold: %s" %t, font, ws, 20, h+10)
    drawText("FPS: %s"%int(clock.get_fps()), font, ws, 20, h+60)
    pygame.display.update()

    #input
    for e in pygame.event.get():
        if e.type == QUIT:
            run = False
        if e.type == KEYDOWN:
            if e.key == K_a:
                t += 1
            elif e.key == K_s:
                t -= 1

#release camera and quit
cap.release()
cv2.destroyAllWindows()
pygame.quit()
