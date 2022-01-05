import math
import random

import pygame

from constants import IDLE, RUN, TILE_SIZE, SPLASH_IMAGE, PLAYER_SHOOT_COOLDOWN, DEFAULT_ENEMY_DAMAGE, ROOM_SIZE, \
    SHOTTER_SHOOT_COOLDOWN, SANDBULLET_IMG
from gui import Hit, Title
from map_generator import borders, door_borders
from mixer import death_fall_sound, death_wave_sound, swish_attack_sounds
from static_func import load_image

all_entities = pygame.sprite.Group()  # Группа всех живых объектов
splash_sprites = pygame.sprite.Group()  # Группа всех пуль игрока
sand_bullet = pygame.sprite.Group()  # Группа всех пуль врагов

titles = []


class Entity(pygame.sprite.Sprite):
    """               Класс всех энтити                 """

    def __init__(self, position, speed, images_idle, images_run, size):
        super().__init__(all_entities)
        self.health_points = 100

        # Позиция и скорость (вектор скорости)
        self.x, self.y = position
        self.speed = speed
        self.x_vel, self.y_vel = 0, 0
        self.damage = 5

        # Номер кадра анимации // Графика
        self.count_image = 0
        self.image_size = size
        self.images_idle = images_idle
        self.images_run = images_run
        self.image = pygame.transform.scale(load_image(self.images_idle[0]), size)
        self.rect = self.image.get_rect().move(self.x, self.y)
        self.state = IDLE

        # Флаг направления спрайта
        self.look_right = False

    # Получить позицию
    def get_position(self) -> tuple:
        return self.x, self.y

    # Сменить позицию на ...
    def set_position(self, position: tuple) -> None:
        self.x, self.y = position
        self.rect = self.image.get_rect().move(self.x, self.y)

    # Изменить положение анимаций на ...
    def change_state(self, state: int) -> None:
        if self.state != state:
            self.state = state
            self.count_image = 0

    # Смена спрайта анимации в зависимости от состояния
    def play_animation(self) -> None:
        self.count_image += 0.05
        if int(self.count_image) >= max(len(self.images_idle), len(self.images_run)):
            self.count_image = 0

        # Устанавливаем номер кадра
        if self.state == RUN:
            self.image = pygame.transform.scale(load_image(self.images_run[int(self.count_image)]), self.image_size)
        elif self.state == IDLE:
            self.image = pygame.transform.scale(load_image(self.images_idle[0]),
                                                self.image_size)  # Todo: немного переделать get по индексу

        # Если не смотрит в нужную сторону - разворачиваем
        if not self.look_right:
            self.image = pygame.transform.flip(self.image, True, False)

    # Проверка на коллизию по оси X
    def collide_x(self) -> bool:
        next_rect = pygame.Rect(self.rect.x + self.x_vel + 2, self.rect.y + 2,
                                TILE_SIZE - 4, TILE_SIZE - 4)
        for border in borders:
            if next_rect.colliderect(border.rect):
                return False
        for border in door_borders:
            if next_rect.colliderect(border.rect):
                return False
        return True

    # Проверка на коллизию по оси Y
    def collide_y(self) -> bool:
        next_rect = pygame.Rect(self.rect.x + 2, self.rect.y + self.y_vel + 2,
                                TILE_SIZE - 4, TILE_SIZE - 4)
        for border in borders:
            if next_rect.colliderect(border.rect):
                return False
        for border in door_borders:
            if next_rect.colliderect(border.rect):
                return False
        return True

    # Получить урон
    def get_damage(self, damage: int, arr_hit: list, color: str) -> None:
        self.health_points -= damage
        Hit(damage=damage, coords=(self.rect.x, self.rect.y), color=color)


class Hero(Entity):
    """                 Класс главного героя       """

    def __init__(self, position, speed, images_idle, images_run, size=(TILE_SIZE, TILE_SIZE)):
        super().__init__(position, speed, images_idle, images_run, size)
        self.is_alive = True
        self.coins = 0
        self.health_points = 100
        self.cooldown_tracker = 0

    # Обновление положений
    def update(self) -> None:
        # Если жив
        if self.health_points > 0:
            # Проверка нажатых клавиш, изменение вектора направления и проигрывание анимации
            if pygame.key.get_pressed()[pygame.K_w]:
                self.change_state(RUN)
                self.y_vel = -self.speed
            if pygame.key.get_pressed()[pygame.K_s]:
                self.change_state(RUN)
                self.y_vel = self.speed
            if pygame.key.get_pressed()[pygame.K_a]:
                self.change_state(RUN)
                # Поворот изображения в сторону ходьбы
                self.look_right = False
                self.x_vel = -self.speed
            if pygame.key.get_pressed()[pygame.K_d]:
                self.change_state(RUN)
                self.look_right = True
                self.x_vel = self.speed

            # Сброс векторов направления, если ни одна клавиша не зажата
            if not (pygame.key.get_pressed()[pygame.K_w] or pygame.key.get_pressed()[pygame.K_s]):
                self.y_vel = 0
            if not (pygame.key.get_pressed()[pygame.K_d] or pygame.key.get_pressed()[pygame.K_a]):
                self.x_vel = 0

            # IDLE Сброс всех анимаций при остановке
            if not (pygame.key.get_pressed()[pygame.K_d] or pygame.key.get_pressed()[pygame.K_a]) and \
                    not (pygame.key.get_pressed()[pygame.K_w] or pygame.key.get_pressed()[pygame.K_s]):
                self.change_state(IDLE)
            # Проигрываем анимацию
            self.play_animation()

            # Проверка на коллизию. Если проходит, то перемещаем игрока
            if self.collide_x():
                self.rect.x += self.x_vel
            if self.collide_y():
                self.rect.y += self.y_vel
        else:
            if self.is_alive:
                self.image = pygame.transform.rotate(self.image, -90)
                self.death()

    # Смерть игрока
    def death(self):
        pygame.mixer.Sound.play(death_fall_sound)
        pygame.mixer.Sound.play(death_wave_sound)
        self.is_alive = False

    def update_cooldown(self, clock):
        self.cooldown_tracker -= clock.get_time() if self.cooldown_tracker > 0 else 0

    # Стрельба по КД
    def shoot_splash(self, event, camera):
        if self.cooldown_tracker <= 0:
            pygame.mixer.Sound.play(random.choice(swish_attack_sounds))
            mx, my = event.pos
            mx, my = abs(camera.state.x) + mx, abs(camera.state.y) + my
            Splash((self.rect.x, self.rect.y), 20, images=SPLASH_IMAGE, need_pos=(mx, my),
                   tiles_group=splash_sprites)
            self.cooldown_tracker = PLAYER_SHOOT_COOLDOWN


class Enemy(Entity):
    """                                   Класс врага                                            """

    def __init__(self, position, speed: int, images_idle, images_run, room_index: tuple, size=(TILE_SIZE, TILE_SIZE)):
        super().__init__(position, speed, images_idle, images_run, size)

        self.damaged_from = None
        self.change_K = 1
        self.health_points = 20
        self.damage = DEFAULT_ENEMY_DAMAGE
        self.room_index = room_index
        self.size = size

        self.timer = 0  # Таймер для КД

    # Проверка на пробитие и смена кадра
    def update_enemy(self, arr: list, arr_hit: list, hero: Hero, clock, rooms: list):
        player_pos = (hero.rect.x, hero.rect.y)
        self.play_animation()
        self.check_damage(hero, arr_hit)

        if self.health_points <= 0:
            self.destruct(rooms, arr)

        self.move_to_player(player_pos, rooms)
        self.do_timer(clock)
        self.attack(hero, arr_hit)

    # Если задет снарядом игрока
    def collide_splash(self) -> bool:
        for splash in splash_sprites:
            if self.rect.colliderect(splash.rect):
                if splash != self.damaged_from:
                    self.damaged_from = splash
                    return True
        return False

    # Атакуем героя если рядом и прошел КД
    def attack(self, hero: Hero, arr_hit: list) -> None:
        if self.rect.colliderect(hero.rect):
            if self.timer > 600:
                hero.get_damage(self.damage, arr_hit, 'red')
                self.timer = 0

    # Проверяем под атакой ли существо?
    def check_damage(self, hero: Hero, arr_hit: list) -> None:
        if self.collide_splash():
            self.get_damage(hero.damage, arr_hit, 'green')

    # Обновляем счетчик КД
    def do_timer(self, clock: pygame.time.Clock):
        self.timer += clock.get_time()

    # Передвигаемся до игрока
    def move_to_player(self, player_pos: tuple, rooms: list) -> None:
        first_ind, second_ind = self.room_index
        room, room_x, room_y = rooms[first_ind][second_ind]
        px, py = player_pos
        # Если игрок в комнате
        if (room_x < px < room_x + (ROOM_SIZE[0] - 5) * TILE_SIZE) and \
                (room_y < py < room_y + (ROOM_SIZE[1] - 5) * TILE_SIZE):
            px, py = player_pos
            dx, dy = px - self.rect.x, py - self.rect.y
            length = math.hypot(dx, dy)
            if 0 < abs(length) < 500:
                self.x_vel = dx / length
                self.y_vel = dy / length
                if self.collide_x():
                    self.rect.x += self.x_vel * self.speed
                    self.look_right = False if self.x_vel >= 0 else True
                    self.change_state(state=RUN)
                if self.collide_y():
                    self.rect.y += self.y_vel * self.speed
                    self.change_state(state=RUN)
            else:
                self.change_state(state=IDLE)

    # Деструктор при смерти
    def destruct(self, rooms: list, arr: list):
        first_ind, second_ind = self.room_index
        lst = rooms[first_ind][second_ind][0].mobs
        del lst[lst.index(self)]
        if len(lst) == 0:
            rooms[first_ind][second_ind][0].have_monsters = False
            titles.append(Title(titles))
        del arr[arr.index(self)]
        self.kill()


class Splash(Entity):
    """                                          Снаряд игрока                                                """

    def __init__(self, position: tuple, speed: int, images: list, need_pos: tuple, tiles_group,
                 size=(TILE_SIZE - 8, TILE_SIZE - 8)):
        super().__init__(position, speed, images, images, size)
        tiles_group.add(self)
        # Mouse_x mouse_y
        self.need_pos = need_pos
        mx, my = need_pos
        # Delta_x delta_y
        dx, dy = mx - self.rect.x + TILE_SIZE // 2, my - self.rect.y
        # Траектория полета
        length = math.hypot(dx, dy)
        self.dx = dx / length
        self.dy = dy / length
        if dx < 0:
            self.image = pygame.transform.flip(self.image, True, False)

    # Передвижение снаряда
    def move(self):
        if not self.collide():
            self.rect.x += self.dx * self.speed
            self.rect.y += self.dy * self.speed
        else:
            self.kill()

    # Проверка коллизии
    def collide(self) -> bool:
        for border in borders:
            if self.rect.colliderect(border.rect):
                return True
        for border in door_borders:
            if self.rect.colliderect(border.rect):
                return True
        return False


class ShootingEnemy(Enemy):
    """                                         Стреляющий враг                                   """

    def __init__(self, position, speed: int, images, room_index: tuple):
        super().__init__(position, speed, images, images, room_index)

    # Стрельба по КД
    def shoot(self, hero: Hero, arr_hit: list, rooms: list) -> None:
        first_ind, second_ind = self.room_index
        room, room_x, room_y = rooms[first_ind][second_ind]
        px, py = hero.rect.x, hero.rect.y
        # Если игрок в комнате - стреляем
        if (room_x < px < room_x + (ROOM_SIZE[0] - 5) * TILE_SIZE) and \
                (room_y < py < room_y + (ROOM_SIZE[1] - 5) * TILE_SIZE):
            needed_pos = (hero.rect.x, hero.rect.y)
            if self.timer > SHOTTER_SHOOT_COOLDOWN:
                SandBullet((self.rect.x, self.rect.y), 7, images=SANDBULLET_IMG, need_pos=needed_pos,
                           arr_hit=arr_hit, hero=hero, tile_group=sand_bullet)
                self.timer = 0

    # Проверка на пробитие и смена кадра
    def update_enemy(self, arr, arr_hit: list, hero, clock, rooms: list):
        self.check_damage(hero, arr_hit)
        self.play_animation()

        if self.health_points <= 0:
            self.destruct(rooms, arr)

        self.do_timer(clock)
        self.shoot(hero, arr_hit, rooms)


class SandBullet(Splash):
    def __init__(self, position: tuple, speed: int, images: list, need_pos: tuple, arr_hit: list, tile_group, hero,
                 size=(TILE_SIZE - 20, TILE_SIZE - 20)):
        super().__init__(position, speed, images, need_pos, tile_group, size)
        self.arr_hit = arr_hit
        self.hero = hero
        self.image = pygame.transform.flip(self.image, True, False)

    def collide(self) -> bool:
        for border in borders:
            if self.rect.colliderect(border.rect):
                return True
        for border in door_borders:
            if self.rect.colliderect(border.rect):
                return True
        if self.rect.colliderect(self.hero.rect):
            self.hero.get_damage(self.damage, self.arr_hit, 'red')
            return True
        return False
