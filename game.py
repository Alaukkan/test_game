import os
import sys
import random
import math

import pygame

from scripts.utils import load_image, load_images, Animation, DamageNumbers
from scripts.entities import Player, Slime
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Test game")
        self.screen = pygame.display.set_mode((960*1.5, 600*1.5))
        self.display = pygame.Surface((160*1.2, 100*1.2), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((160*1.2, 100*1.2))

        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.assets = {
            'decor' : load_images('tiles/decor'),
            'grass' : load_images('tiles/grass'),
            'large_decor' : load_images('tiles/large_decor'),
            'stone' : load_images('tiles/stone'),
            'background' : load_image('background.png'),
            'clouds' : load_images('clouds'),
            'blue_slime/jump' : Animation(load_images('entities/blue_slime/jump'), img_dur=4, loop=False),
            'blue_slime/splash' : Animation(load_images('entities/blue_slime/splash'), img_dur=6, loop=False),
            'blue_slime/idle' : Animation(load_images('entities/blue_slime/idle'), img_dur=6),
            'blue_slime/death' : Animation(load_images('entities/blue_slime/death'), img_dur=6, loop=False),
            'player/idle' : Animation(load_images('entities/player/idle'), img_dur=6),
            'player/walk' : Animation(load_images('entities/player/run'), img_dur=6),
            'player/run' : Animation(load_images('entities/player/run'), img_dur=3),
            'player/attack_1' : Animation(load_images('entities/player/attack_1'), img_dur=5, loop=False),
            'player/attack_2' : Animation(load_images('entities/player/attack_2'), img_dur=5, loop=False),
            'player/attack_3' : Animation(load_images('entities/player/attack_3'), img_dur=5, loop=False),
            'player/jump' : Animation(load_images('entities/player/jump')),
            'player/dash' : Animation(load_images('entities/player/dash'), img_dur=4, loop=False),
            'player/fall' : Animation(load_images('entities/player/fall')),
            'player/slide' : Animation(load_images('entities/player/slide')),
            'player/wall_slide' : Animation(load_images('entities/player/wall_slide')),
            'experience/idle' : Animation(load_images('entities/experience')),
            'particle/leaf' : Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle' : Animation(load_images('particles/particle'), img_dur=6, loop=False),
        }

        self.sfx = {
            'jump' : pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash' : pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit' : pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot' : pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience' : pygame.mixer.Sound('data/sfx/ambience.wav'),
        }

        self.sfx['jump'].set_volume(0.1)
        self.sfx['dash'].set_volume(0.1)
        self.sfx['hit'].set_volume(0.3)
        self.sfx['shoot'].set_volume(0.1)
        self.sfx['ambience'].set_volume(0.1)

        self.clouds = Clouds(self.assets['clouds'], count=16)

        self.player = Player(self, (50, 50), (9, 16))

        self.tilemap = Tilemap(self, tile_size=16)

        self.level = 0
        self.load_level(self.level)

        pygame.font.init()

        self.screenshake = 0


    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            match spawner['variant']:
                case 0:
                    self.player.pos = spawner['pos']
                    self.player.air_time = 0
                case 1:
                    self.enemies.append(Slime(self, spawner['pos'], (14, 10)))

        self.projectiles = []
        self.particles = []
        self.sparks = []
        self.circles = []
        self.texts = []
        self.experiences = []
# arekkususanhahontounikirekutesekushiidesu
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30

        self.player.hp = self.player.max_hp


    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)

        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.fill((0, 0, 0, 0))
            
            self.display_2.blit(self.assets['background'], (0, 0))

            self.screenshake = max(0, self.screenshake - 1)

            damage = False

            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1

            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(self.level)

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 10
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 10
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            # self.clouds.update()
            # self.clouds.render(self.display_2, offset=render_scroll)

            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                if abs(enemy.pos[0] - self.player.pos[0]) > 120 or abs(enemy.pos[1] - self.player.pos[1]) > 100:
                    continue
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)
            if not self.dead:
                self.player.update(self.tilemap, ((self.movement[1] - self.movement[0]) * (2 if self.player.running else 1) if self.player.attacking < 30 - 5 * self.player.combo else 0, 0))
                self.player.render(self.display, offset=render_scroll)

            # [[x, y], direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.player.hp = max(0, self.player.hp - 4)
                        self.texts.append(DamageNumbers('-4', self.player.pos, color=(150, 0, 0)))
                        self.sfx['hit'].play()
                        self.screenshake = max(16, self.screenshake)
                                       

            for exp in self.experiences.copy():
                kill = exp.update(self.tilemap)
                if kill:
                    self.experiences.remove(exp)
                    continue
                exp.render(self.display, offset=render_scroll)
            for circle in self.circles:
                pygame.draw.circle(self.display_2, circle['color'], (circle['pos'][0] - render_scroll[0], circle['pos'][1] - render_scroll[1]), circle["radius"], width=circle["width"])
                circle['radius'] += 1
                circle['width'] = (201 - circle['radius']) % 20
                if circle['width'] <= 0:
                    self.circles.remove(circle)
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            display_mask = pygame.mask.from_surface(self.display)
            display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            # for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                # self.display_2.blit(display_silhouette, offset)

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)

            for text in self.texts.copy():
                kill = text.update()
                text.render(self.display, offset=render_scroll)
                if kill:
                    self.texts.remove(text)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        if self.player.jump():
                            self.sfx['jump'].play()
                    if event.key == pygame.K_x:
                        self.player.dash()
                    if event.key == pygame.K_c:
                        self.player.attack()
                    if event.key == pygame.K_v:
                        print(f'player exp: {self.player.exp}')
                    if event.key == pygame.K_LSHIFT and self.player.air_time < 10:
                        self.player.running = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_LSHIFT:
                        self.player.running = False

            if damage:
                self.display.blit(damage, self.player.pos)
                if self.player.hp == 0:
                    self.dead += 1

            max_hp_bar = pygame.Rect(10, 90, 50, 5)
            hp_bar = pygame.Rect(10, 90, self.player.hp / self.player.max_hp * 50, 5)
            pygame.draw.rect(self.display, (0, 0, 0), max_hp_bar)
            pygame.draw.rect(self.display, (150, 0, 0), hp_bar)
            
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))

            self.display_2.blit(self.display, (0, 0))

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 3, random.random() * self.screenshake - self.screenshake / 3)
            self.screen.blit(pygame.transform.scale(self.display_2, (self.screen.get_size())), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)

Game().run() 