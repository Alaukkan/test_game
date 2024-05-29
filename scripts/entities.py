import math
import random
import pygame

from scripts.particle import Particle
from scripts.spark import Spark
from scripts.utils import DamageNumbers

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up' : False, 'down' : False, 'right' : False, 'left' : False}

        self.action = ''
        self.anim_offset = (-4, -1)
        self.flip = False
        self.set_action('idle')

        self.last_movement = [0, 0]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up' : False, 'down' : False, 'right' : False, 'left' : False}
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        
        self.last_movement = movement

        if self.collisions['up'] or self.collisions['down']:
            self.velocity[1] = 0
        
        self.animation.update()

    def render_hp_bar(self, surf, hp, max_hp, anim_offset, offset=(0, 0)):
        max_hp_bar = pygame.Rect(self.pos[0] - offset[0] + anim_offset[0], self.pos[1] - offset[1] + anim_offset[1], 12, 2)
        hp_bar = pygame.Rect(self.pos[0] - offset[0] + anim_offset[0], self.pos[1] - offset[1] + anim_offset[1], hp / max_hp * 12, 2)
        pygame.draw.rect(self.game.display, (0, 0, 0), max_hp_bar)
        pygame.draw.rect(self.game.display, (150, 0, 0), hp_bar)

    def render(self, surf, anim_offset, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + anim_offset[0], self.pos[1] - offset[1] + anim_offset[1]))

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.anim_offset = (-4, 0)
        self.air_time = 0
        self.jumps = 1
        self.running = False
        self.wall_slide = False
        self.attacking = 0
        self.dashing = 0
        self.max_hp = 16
        self.hp = self.max_hp
        self.immunity = 60
        self.exp = 0
        self.combo = 0
        self.damage = 5

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.air_time += 1
        self.immunity = max(0, self.immunity - 1)

        if self.air_time > 120 and self.velocity[1] > 4.7:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1

        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1

        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 1)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
            
        if not self.wall_slide:
            if self.attacking > 30 - 5 * self.combo:
                self.set_action(f'attack_{self.combo + 1}')
            elif abs(self.dashing) > 50:
                self.set_action('dash')
            elif self.air_time > 4: 
                if self.velocity[1] > 0:
                    self.set_action('fall')
                else:
                    self.set_action('jump')
            elif movement[0] != 0:
                if self.running:
                    self.set_action('run')
                else:
                    self.set_action('walk')
            else:
                self.set_action('idle')

        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                # self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            # self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))

        if self.attacking > 0:
            self.attacking = max(0, self.attacking - 1)
        elif self.combo:
            self.combo = 0
        if self.combo == 2 and self.attacking < 30 - 5 * self.combo:
            self.combo = 0

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
    
    def render(self, surf, offset=(0, 0)):
        if self.attacking < 30 - 5 * self.combo:
            super().render(surf, self.anim_offset, offset=offset)
        else:
            super().render(surf, (-16, -16) if not self.flip else (-24, -16), offset=offset)
        
    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
            self.velocity[1] = -2.5
            self.air_time = 5
            self.jumps = max(0, self.jumps - 1)
            return True

        elif self.jumps and self.air_time < 10:
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 5
            return True
    
    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60

    def attack(self):
        if self.dashing < 50 and self.air_time < 4 and not self.wall_slide and self.attacking < 30 - 5 * self.combo:
            if self.attacking:
                self.combo = min(2, self.combo + 1)
            self.attacking = 45
            self.damage = 5 if self.combo < 2 else 8
            self.game.screenshake = max(16, self.game.screenshake)
            for i in range(3):
                self.game.sparks.append(Spark((self.rect().bottomright[0] - (20 if self.flip else -12), self.rect().bottomright[1] - random.randint(0, 7)), random.random() * math.pi / 6 + (math.pi if self.flip else 0), 1 + random.random() * 0.5))
        if False:
            self.game.sparks.append(Spark((self.rect().bottomright[0] - (20 if self.flip else -12), self.rect().bottomright[1]), 0, 2 + random.random() * 0.5))
            self.game.sparks.append(Spark((self.rect().bottomright[0] - (20 if self.flip else -12), self.rect().bottomright[1]), math.pi, 2 + random.random() * 0.5))

class Slime(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'blue_slime', pos, size)
        self.anim_offset = (1, -6)
        self.jumping = 0
        self.ground_time = 0
        self.damage = 3
        self.max_hp = 11
        self.hp = self.max_hp
        self.immunity = 20
        self.dead = 0
        self.exp = 2

    def update(self, tilemap, movement=(0, 0)):
        if not self.dead:
            if abs(self.jumping) > 20:
                self.velocity[0] = abs(self.jumping) / self.jumping * 0.5
                if self.jumping < 0:
                    self.jumping = min(0, self.jumping + 1)
                else:
                    self.jumping = max(0, self.jumping - 1)
            elif self.ground_time > 5 and random.random() < (0.01 if abs(self.game.player.pos[0] - self.pos[0]) > 5 * 16 else 0.05) and self.game.player.pos[0] != self.pos[0]:
                self.jumping = abs(self.game.player.pos[0] - self.pos[0]) // (self.game.player.pos[0] - self.pos[0]) * 60
                self.velocity[0] = self.jumping / abs(self.jumping) * 2
                self.velocity[1] = -2
                self.ground_time = 0
            else:
                self.velocity[0] = 0

        super().update(tilemap, movement=movement)

        if self.dead:
            self.set_action('death')
            self.dead += 1
            if self.dead >= 30:
                return True
            return False

        if self.collisions['down']:
            self.ground_time += 1

        if abs(self.jumping) > 20:
            self.set_action('jump')
        elif self.ground_time < 5:
             self.set_action('splash')
        else:
            self.set_action('idle')

        if self.immunity:
            self.immunity = max(0, self.immunity - 1)
        if self.game.player.attacking >= 40 and not self.immunity:
            e_mask = pygame.mask.from_surface(pygame.transform.flip(self.animation.img(), self.flip, False))
            p_mask = pygame.mask.from_surface(pygame.transform.flip(self.game.player.animation.img(), self.game.player.flip, False))
            offset = (-17, -16) if not self.game.player.flip else (0, -16)
            # if self.game.player.attacking >= 25:
                # print(f"enemy: {self.pos}  player: {self.game.player.pos}")
                # print(e_mask.overlap_area(p_mask, (int(self.pos[0] - self.game.player.pos[0] + offset[0]), int(self.pos[1] - self.game.player.pos[1] + offset[1]))))
            if e_mask.overlap_area(p_mask, (int(self.pos[0] - self.game.player.pos[0] + offset[0]), int(self.pos[1] - self.game.player.pos[1] + offset[1]))) > 2:
                self.game.circles.append({"radius" : 5, "width" : 5, 'pos' : self.rect().center, 'color' : (255, 255, 255)})
                self.game.texts.append(DamageNumbers(str(self.game.player.damage), self.pos))
                self.hp = max(0, self.hp - self.game.player.damage)
                self.game.sfx['hit'].play()
                self.immunity = 20
                if self.hp == 0:
                    self.dead += 1
                    for i in range(self.exp):
                        self.game.experiences.append(Experience(self.game, self.pos))

        if abs(self.game.player.dashing) < 50 and not self.game.player.immunity:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.player.immunity = 20
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                self.game.player.velocity[0] = 2 if self.game.player.flip else -2
                for i in range(5):
                    angle = random.random() * math.pi - (math.atan((self.game.player.pos[1] - self.pos[1]) / (self.game.player.pos[0] - self.pos[0])) if self.game.player.pos[0] != self.pos[0] else 0)
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random(), color=(100, 200, 255)))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.player.hp = max(0, self.game.player.hp - self.damage)
                self.game.texts.append(DamageNumbers(str(self.damage), self.game.player.pos, color=(150, 0, 0)))
                if self.game.player.hp == 0:
                    self.game.dead += 1
                    for i in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.game.player.rect().center, angle, 2 + random.random()))
                        self.game.particles.append(Particle(self.game, 'particle', self.game.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
 
        if self.velocity[1] == 5:
            return True

    def render(self, surf, offset=(0, 0)):
        super().render(surf, self.anim_offset, offset=offset)
        if self.hp < self.max_hp:
            self.render_hp_bar(surf, self.hp, self.max_hp, self.anim_offset, offset=(offset[0] - 2, offset[1] + 2))

class Experience(PhysicsEntity):
    def __init__(self, game, pos, size=(3, 3), exp=1):
        super().__init__(game, 'experience', pos, size)
        self.anim_offset = (0, 0)
        self.exp = exp
        angle = math.pi / 2 * random.random() + math.pi * 5/4
        velocity = random.random() * 0.5 + 1
        self.velocity = [math.cos(angle) * velocity, math.sin(angle) * velocity]
        self.hit_ground = False

    def update(self, tilemap, movement=(0, 0)):
        if self.collisions['down']:
            self.velocity[0] = 0
            self.hit_ground = True
        if self.hit_ground:
            if abs(self.game.player.pos[0] - self.pos[0]) < 32 and abs(self.game.player.pos[1] + 8 - self.pos[1]) < 16:
                if self.game.player.pos[0] - self.pos[0] != 0 and self.game.player.pos[1] - self.pos[1] != 0:
                    self.velocity[0] = 16 / (self.game.player.pos[0] - self.pos[0]) if abs(self.game.player.pos[0] - self.pos[0]) > 8 else 2
                    self.velocity[1] = 1 / (self.game.player.pos[1] - self.pos[1]) if abs(self.game.player.pos[1] + 8 - self.pos[1]) > 4 else 0
        super().update(tilemap, movement)
        if abs(self.game.player.pos[0] - self.pos[0]) < 16 and abs(self.game.player.pos[1] - self.pos[1]) < 16:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.player.exp += self.exp
                return True

    def render(self, surf, offset=(0, 0)):
        super().render(surf, self.anim_offset, offset=offset)