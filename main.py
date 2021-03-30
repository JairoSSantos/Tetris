import pygame as pg
import numpy as np
from random import randint
from time import time
import tkinter as tk
from tkinter.simpledialog import askstring
import pandas as pd

root = tk.Tk()
root.withdraw()

def verify_events():
    global run
    for event in pg.event.get():
        if event.type == pg.QUIT: quit()
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE: run = not run

def nrange(x0 ,xi=None, dx=1):
    if not xi: xi = x0; x0 = 0
    while x0 < xi: yield x0; x0 += dx

def ddtime():
    global start
    sec = time() - start
    min = 0
    while sec > 60:
        min += 1
        sec -= 60
    return f'{int(min)}:{int(sec)}'

def update_dataframe():
    global record
    dataframe = pd.read_csv('register.csv')
    scores = dataframe['pontuação'].tolist()
    try: record = dataframe.sort_values('pontuação').loc[scores.index(sorted(scores)[-1])].to_dict()
    except IndexError: record = None

def save_player(score):
    global start
    time_end = ddtime()
    player_name = askstring('Voçê perdeu!',
        f'Voçê perdeu!\nSua pontuação foi {score}; Tempo de duração foi {time_end}\nDigite seu nome:')
    dataframe = pd.read_csv('register.csv')
    dataframe = dataframe.append({'nome':player_name, 'pontuação':score, 'tempo':time_end}, ignore_index=True)
    dataframe.to_csv('register.csv', index=False)
    start = time()

class BlockTypes:
    type1 = [
        np.array([[0, 1], [1, 0], [1, 1], [2, 1]]),
        np.array([[0, 0], [0, 1], [0, 2], [1, 1]]),
        np.array([[0, 0], [1, 0], [2, 0], [1, 1]]),
        np.array([[0, 1], [1, 0], [1, 1], [1, 2]])
    ]

    type2 = [
        np.array([[0, 0], [1, 0], [0, 1], [1, 1]])
    ]

    type3 = [
        np.array([[0, 0], [0, 1], [0, 2], [0, 3]]),
        np.array([[0, 0], [1, 0], [2, 0], [3, 0]])
    ]

    type4 = [
        np.array([[0, 0], [0, 1], [1, 1], [2, 1]]),
        np.array([[0, 0], [0, 1], [0, 2], [1, 0]]),
        np.array([[0, 0], [1, 0], [2, 0], [2, 1]]),
        np.array([[0, 2], [1, 0], [1, 1], [1, 2]])
    ]

    type5 = [
        np.array([[0, 0], [1, 0], [2, 0], [0, 1]]),
        np.array([[0, 0], [1, 0], [1, 1], [1, 2]]),
        np.array([[2, 0], [0, 1], [1, 1], [2, 1]]),
        np.array([[0, 0], [0, 1], [0, 2], [1, 2]])
    ]

    type6 = [
        np.array([[1, 0], [2, 0], [0, 1], [1, 1]]),
        np.array([[0, 0], [0, 1], [1, 1], [1, 2]])
    ]

    type7 = [
        np.array([[0, 0], [1, 0], [1, 1], [2, 1]]),
        np.array([[0, 1], [0, 2], [1, 1], [1, 0]])
    ]

    alltypes = [type1, type2, type3, type4, type5, type6, type7]

    colors = {-1:(50,50,50), 1:(0,0,225), 2:(255,0,0),
        3:(0,200,0), 4:(150,0,150), 5:(255,255,0), 6:(255,0,100), 7:(0,255,200)}

class Block:
    def __init__(self, pos, index):
        self.position = np.array(pos)
        self.colorid = int(index)+1
        self.btype = BlockTypes.alltypes[index]
        self.type_idd = 0

    def change_id(self, idd=1):
        self.type_idd += idd
        if self.type_idd > len(self.btype)-1: self.type_idd = 0
        elif self.type_idd < 0: self.type_idd = len(self.btype)-1

    def get_shape(self): return self.btype[self.type_idd] + self.position

    def move(self, *args):
        self.position += np.array(args)

class Game:
    def __init__(self, pos, size, scale, delay):
        self.position = pos
        self.surface = pg.Surface(size)
        self.scale = scale
        self.width, self.height = int(size[0]/self.scale), int(size[1]/self.scale)

        self.delay = delay
        self.delay_value = delay

        self.field = np.zeros((self.width, self.height))

        self.falling_blocks = []
        self.next_block = randint(0, len(BlockTypes.alltypes)-1)
        self.add_new_block()

        self.keys = {pg.K_UP:[0, 0], pg.K_DOWN:[0, 0], pg.K_RIGHT:[0, 0], pg.K_LEFT:[0, 0]} # key_code:[released, pressing]

        self.score = 0
        self.lost = False

    def add_new_block(self):
        self.falling_blocks.append(Block([randint(0, self.width-6), 0], self.next_block))
        self.next_block = randint(0, len(BlockTypes.alltypes)-1)

    def draw(self, root, update):
        if not self.lost:
            self.surface.fill(pg.SRCALPHA)
            if update:
                self.delay -= 1
                pressed_keys = pg.key.get_pressed()
                for k in self.keys.keys():
                    self.keys[k][0] = 0
                    if pressed_keys[k] and not self.keys[k][1]: self.keys[k] = [1, 1]
                    elif not pressed_keys[k]: self.keys[k][1] = 0

            for block in self.falling_blocks:
                if self.keys[pg.K_UP][0]:
                    block.change_id()
                    if self.verify_collision(block): block.change_id(-1)

                dx, dy = self.keys[pg.K_RIGHT][1] - self.keys[pg.K_LEFT][1], self.keys[pg.K_DOWN][1]
                block.move(dx, dy)
                if self.verify_collision(block): block.move(-dx, -dy)
                if self.ground(block): self.froze(block)
                elif self.delay < 0:
                    self.delay = self.delay_value
                    block.move(0, 1)
                    if self.ground(block): self.froze(block)

            for x, y in block.get_shape():
                pg.draw.rect(self.surface, BlockTypes.colors[block.colorid],
                    [x*self.scale, y*self.scale, self.scale, self.scale])

            ysremov = 0
            for y in nrange(self.height):
                for x in nrange(self.width):
                    if self.field[x][y] < 0: self.field[x][y] = 0
                    if not self.field[x][y]:
                        if y+1 >= self.height: self.field[x][y] = -1
                        elif self.field[x][y+1] > 0: self.field[x][y] = -1
                    else:
                        pg.draw.rect(self.surface, BlockTypes.colors[self.field[x][y]],
                            [x*self.scale, y*self.scale, self.scale, self.scale])
                    pg.draw.rect(self.surface, (10,10,10),
                        [x*self.scale, y*self.scale, self.scale, self.scale], 1)

                remove = True
                for i in self.field.T[y]:
                    if i <= 0: remove = False; break
                if remove: self.remove(y); ysremov += 5
            self.score += ysremov**2

            self.lost = np.sum(np.clip(self.field.T[0], 0, 1)) > 0

        root.blit(self.surface, self.position)

    def froze(self, block):
        for x, y in block.get_shape(): self.field[x][y] = block.colorid
        self.falling_blocks.remove(block)
        self.add_new_block()

    def ground(self, block):
        gnd = False
        for x, y in block.get_shape():
            if self.field[x][y] == -1: gnd = True; break
        return gnd

    def remove(self, y):
        self.field = np.array(list(np.zeros((1, self.width))) + list(self.field.T[:y]) + list(self.field.T[y+1:])).T
        # self.score += 10

    def verify_collision(self, block):
        collide = False
        for x, y in block.get_shape():
            if not (0 <= x < self.width) or not (0 <= y < self.height) or self.field[x][y] > 0: collide = True; break
        return collide

if __name__ == '__main__':
    global run, record, start

    pg.init()
    pg.display.set_caption('Tetris')

    pad = 20
    size = width, height = 800+pad*2, 650+pad
    pref_size = 300, height-pad
    game_size = width-pref_size[0]-pad*2, height-pad
    game_pos = pad//2, pad//2
    pref_pos = game_size[0]+int(pad*3/2), pad//2
    pref_rect = pg.Rect(pref_pos, pref_size)

    screen = pg.display.set_mode(size)
    scale = 25
    game = Game([pad//2, pad//2], game_size, scale, 10)
    clock = pg.time.Clock()
    font = pg.font.SysFont('calibre', 20)

    update_dataframe()

    start = time()
    run = True
    while True:
        clock.tick(15)

        verify_events()

        screen.fill((0,0,0))
        game.draw(screen, run)
        pg.draw.rect(screen, (100,100,100), [game_pos, game_size], 3)
        pg.draw.rect(screen, (100,100,100), pref_rect, 2)

        rects = [pg.Rect(pref_pos[0]+x*scale, pref_pos[1]+y*scale, scale, scale)
            for x, y in BlockTypes.alltypes[game.next_block][0]]
        rectall = rects[0].unionall(rects[0:])
        rectall.centerx = pref_rect.centerx
        rectall.y += pad
        for x, y in BlockTypes.alltypes[game.next_block][0]:
            for i, color in enumerate([BlockTypes.colors[game.next_block+1], (10,10,10)]):
                pg.draw.rect(screen, color, [rectall.x+x*scale, rectall.y+y*scale, scale, scale], i)

        ddy = 0
        values = [f'Pontuação:', str(game.score), 'Tempo de jogo:', ddtime()]
        if record: values += ['Recorde:', '{0} - {1}'.format(record['nome'], record['pontuação'])]
        for i, strs in enumerate(values):
            text = font.render(strs, False, (255,255,255))
            text_rect = text.get_rect()
            text_rect.centerx = pref_rect.centerx
            text_rect.y = rectall.bottom + pad//2*(i + 1) + ddy
            ddy += text_rect.height
            screen.blit(text, text_rect)

        if game.lost:
            save_player(game.score)
            game = Game([pad//2, pad//2], game_size, scale, 10)
            update_dataframe()

        pg.display.flip()
