import cv2, pygame, socket, pickle, threading
import numpy as np
from pygame.locals import *
import multiprocessing

#detect if pixel is an edge
def detect(x, y, frame, t, w, h):
    #up
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

def divide_work(quarter, frame, w, h, threads, t):
    #socket recv
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.1.1", 5560))

    new_img = []
    #get quarter
    height = int(h/threads)
    starty = int(h*quarter/threads)
    for y in range(height):
        row = []
        for x in range(w):
            row.append(detect(x, y+starty, frame, t, w, h))
        new_img.append(row)

    sock.sendall(pickle.dumps([quarter, new_img]))
    sock.close()

if __name__ == '__main__':
    #threshold number and threads number
    t = 20
    threads = 10
    run = True

    #pygame
    pygame.init()
    w, h = 160, 120
    ws = pygame.display.set_mode((w*2, h+160))
    pygame.display.set_caption('Video Stream')
    font = pygame.font.SysFont("comicsans", 40)
    clock = pygame.time.Clock()

    #socket
    connected = 0
    conn_thread = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 5560))
    sock.listen(h)
    exit_event = threading.Event()
    def allow():
        global run, sock, connected, exit_event
        while True:
            if exit_event.is_set():
                break
            conn, addr = sock.accept()
            conn_thread.append(conn)

    al = threading.Thread(target=allow)
    al.start()

    #open camera
    cap = cv2.VideoCapture(0)

    #draw Text
    def drawText(text, font, surface, x, y):
        textobj = font.render(text, 1, (0, 0, 0))
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    #threading results
    threading_results = []
    for th in range(h):
        threading_results.append([])


    
    rgb = True
    while run:
        #get frame
        ret, frame = cap.read()

        #manipulate image
        frame = cv2.resize(frame, (w, h))
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        if rgb:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = pygame.surfarray.make_surface(frame)

        #detection and save image to display later with threads
        new_img = []
        thread = []
        for th in range(threads):
            #init and start
            thread.append(multiprocessing.Process(target=divide_work, args=(th, frame, w, h, threads, t)))
            thread[th].start()
        for th in range(threads):
            result = pickle.loads(conn_thread[th].recv(10240))
            threading_results[result[0]] = result[1]
        for th in range(threads):
            #join when done and get result
            thread[th].join()
            new_img.append(threading_results[th])
            
        #display both images and threshold
        ws.blit(img, (0, 0))
        for l in range(threads):
            for y in range(int(h/threads)):
                for x in range(w):
                    if new_img[l][y][x]:
                        pygame.draw.rect(ws, (255, 255, 255), (x+w, y++int(h/threads*l), 1, 1))
                    else:
                        pygame.draw.rect(ws, (0, 0, 0), (x+w, y+int(h/threads*l), 1, 1))
            
        clock.tick()#to know the fps
        pygame.draw.rect(ws, (255, 255, 255), (0, h, w*2, 160))
        drawText("Threshold: %s" %t, font, ws, 20, h+10)
        drawText("Threads: %s"%threads, font, ws, 20, h+60)
        drawText("FPS: %s"%int(clock.get_fps()), font, ws, 20, h+110)
        pygame.display.update()

        #clean connections
        conn_thread.clear()

        #input
        for e in pygame.event.get():
            if e.type == QUIT:
                run = False
            if e.type == KEYDOWN:
                if e.key == K_a:
                    t += 1
                elif e.key == K_s:
                    t -= 1
                elif e.key == K_r:
                    if rgb:
                        rgb = False
                    else:
                        rgb = True
                elif e.key == K_t:
                    if not threads == h:
                        threads += 10
                        while not h%threads == 0:
                            if not threads == h:
                                threads += 10
                            else:
                                while not h%threads == 0:
                                    threads -= 10
                elif e.key == K_y:
                    if not threads == 10:
                        threads -= 10
                        while not h%threads == 0:
                            threads -= 10
                            if not threads == 10:
                                threads -= 10
                            else:
                                while not h%threads == h:
                                    threads += 10
    
    #release camera and quit
    exit_event.set()
    al.join()
    sock.close()
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()
