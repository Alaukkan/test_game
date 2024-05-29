import os
import pygame

BASE_IMG_PATH = "data/images/"

def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_images(path):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name))
    return images

class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        return self.images[int(self.frame / self.img_duration)]

class DamageNumbers:
    def __init__(self, text, pos, ticks=40, color=(255, 255, 255), size=7, font='Arial'):
        self.pos = list(pos)
        self.start_height = pos[1]
        self.font = pygame.font.SysFont(font, size)
        self.text = text
        self.color = color
        self.ticks = ticks
    
    def update(self):
        self.pos[1] -= int(self.ticks % 2)
        self.ticks = max(0, self.ticks - 1)
        if self.ticks == 0:
            return True


    def render(self, surf, offset=(0, 0)):
        render_pos = (self.pos[0] - offset[0], self.pos[1] - offset[1])
        text_surf = self.font.render('- ' + self.text, False, self.color)
        surf.blit(text_surf, render_pos)
