import random
from constants import *
import pygame
import pytmx

spawned_rooms = list()  # список установленных комнат
all_sprites = pygame.sprite.Group()  # группа всех спрайтов
all_entities = pygame.sprite.Group()  # группа всех живых объектов
borders = pygame.sprite.Group()  # группа границ
ROOM_MAPS = []  # список карт всех комнат
screen = pygame.display.set_mode(SIZE)


def more(x, y):
    return x > y


def less(x, y):
    return x < y


def room_at(x, y):
    return spawned_rooms[x][y][0]


def check_room(x, y):
    return spawned_rooms[x][y] != 0


def build_passage_to(position, map_position, door, map):
    x, y = position
    map_x, map_y = map_position
    if not door.is_builded():
        for tile in door.nf_tiles:
            x1, y1 = tile
            image = map.get_tile_image(2, 2, layer=0)
            image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
            Tile((x1 * TILE_SIZE + map_x, map_y + (y1 * TILE_SIZE)), image)
        for tile in door.borders_tiles:
            image = map.get_tile_image(0, 0, layer=0)
            image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
            x1, y1 = tile
            BorderTile((x1 * TILE_SIZE + map_x, map_y + (y1 * TILE_SIZE)), image)
        door.build_passage()
    image = map.get_tile_image(1, 1, layer=0)
    image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
    Tile((x * TILE_SIZE + map_x, y * TILE_SIZE + map_y), image)


# При запуске
def start():
    global ROOM_MAPS, spawned_rooms
    ROOM_MAPS = [pytmx.load_pygame(f'{MAPS_DIR}/map{i}.tmx') for i in range(1, 5)]
    spawned_rooms = [[0] * MAP_MAX_WIDTH for i in range(MAP_MAX_HEIGHT)]
    newRoom = Room(ROOM_SIZE, ROOM_MAPS[2])

    # Ставим начальную карту в координаты (3, 3)
    spawned_rooms[3][3] = (newRoom, 3 * TILE_SIZE * ROOM_SIZE[0], 3 * TILE_SIZE * ROOM_SIZE[1])

    # Добавляем определенное кол-во комнат
    for i in range(ROOM_NUMBER):
        place_one_room()

    # Соединяет все комнаты между собой
    for x in range(len(spawned_rooms)):
        for y in range(len(spawned_rooms[0])):
            if spawned_rooms[x][y] != 0:
                room = spawned_rooms[x][y][0]
                connect_room(room, (x, y))


# Генерация комнат
def place_one_room():
    vacantPlaces = set()  # свободные места
    for x in range(len(spawned_rooms)):
        for y in range(len(spawned_rooms[0])):
            if spawned_rooms[x][y] == 0:
                continue

            max_x = len(spawned_rooms) - 1
            max_y = len(spawned_rooms[0]) - 1

            if x > 0 and spawned_rooms[x - 1][y] == 0:
                vacantPlaces.add((x - 1, y))
            if y > 0 and spawned_rooms[x][y - 1] == 0:
                vacantPlaces.add((x, y - 1))
            if x < max_x and spawned_rooms[x + 1][y] == 0:
                vacantPlaces.add((x + 1, y))
            if y < max_y and spawned_rooms[x][y + 1] == 0:
                vacantPlaces.add((x, y + 1))

    # Выбираем случайную комнату и конвертируем координаты в настоящие
    newRoom = Room(ROOM_SIZE, ROOM_MAPS[2])
    vacantPlaces = list(vacantPlaces)
    position = random.choice(vacantPlaces)
    width, height = ROOM_SIZE
    room_x, room_y = position[0] * TILE_SIZE * width, position[1] * TILE_SIZE * height
    # Выставляем комнату на её место в списке
    spawned_rooms[position[0]][position[1]] = (newRoom, room_x, room_y)


# соединить комнаты проходом
def connect_room(room, position):
    # макс.индекс комнаты по X и Y
    max_x = len(spawned_rooms) - 1
    max_y = len(spawned_rooms[0]) - 1
    room_x, room_y = position

    neighbours = list()  # список всех возможных дверей (1-DU, 2-UD, 3-RL, 4-LR)

    # Добавление всех возможных проходов
    if not room.DoorD.is_open() and less(room_y, max_y) and check_room(room_x, room_y + 1) and \
            not room_at(room_x, room_y + 1).DoorU.is_open():
        neighbours.append(1)
    if not room.DoorU.is_open() and more(room_y, 0) and check_room(room_x, room_y - 1) and \
            not room_at(room_x, room_y - 1).DoorD.is_open():
        neighbours.append(2)
    if not room.DoorR.is_open() and less(room_x, max_x) and check_room(room_x + 1, room_y) and \
            not room_at(room_x + 1, room_y).DoorL.is_open():
        neighbours.append(3)
    if not room.DoorL.is_open() and more(room_x, 0) and check_room(room_x - 1, room_y) and \
            not room_at(room_x - 1, room_y).DoorR.is_open():
        neighbours.append(4)

    # Применение изменений
    if neighbours:
        for select_direction in neighbours:
            if select_direction == 1:
                room.DoorD.change_state()
                if check_room(room_x, room_y + 1):
                    room_at(room_x, room_y + 1).DoorU.change_state()
            elif select_direction == 2:
                room.DoorU.change_state()
                if check_room(room_x, room_y - 1):
                    room_at(room_x, room_y - 1).DoorD.change_state()
            elif select_direction == 3:
                room.DoorR.change_state()
                if check_room(room_x + 1, room_y):
                    room_at(room_x + 1, room_y).DoorL.change_state()
            elif select_direction == 4:
                room.DoorL.change_state()
                if check_room(room_x - 1, room_y):
                    room_at(room_x - 1, room_y).DoorR.change_state()


class Door:
    """            Класс двери            """
    def __init__(self, free_tiles_coords, not_free_tiles_coords=None, borders=None):
        self.opened = False
        self.f_tiles = free_tiles_coords
        self.nf_tiles = not_free_tiles_coords
        self.borders_tiles = borders
        self.already_done = False

    def is_open(self):
        return self.opened

    def change_state(self):
        self.opened = True

    def build_passage(self):
        self.already_done = True

    def is_builded(self):
        return self.already_done


class Room:
    """            Класс комнаты            """
    def __init__(self, size, map):
        self.x, self.y = size
        self.map = map
        self.DoorU = Door([(8, 0), (9, 0)], [(8, -1), (9, -1), (8, -2), (9, -2)],
                          [(7, -1), (10, -1), (7, -2), (10, -2)])
        self.DoorD = Door([(8, 9), (9, 9)], [(8, 10), (9, 10), (8, 11), (9, 11)],
                          [(7, 10), (10, 10), (7, 11), (10, 11)])
        self.DoorR = Door([(19, 4), (19, 5)], [(20, 4), (20, 5), (21, 4), (21, 5)],
                          [(20, 3), (20, 6), (21, 3), (21, 6)])
        self.DoorL = Door([(0, 4), (0, 5)], [(-1, 4), (-1, 5), (-2, 4), (-2, 5)],
                          [(-1, 3), (-1, 6), (-2, 3), (-2, 6)])


start()


class Tile(pygame.sprite.Sprite):
    """           Класс тайла                """
    def __init__(self, position, image):
        super().__init__(all_sprites)
        self.x, self.y = position
        self.image = image
        self.rect = pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)


class BorderTile(Tile):
    """    Класс тайла на который нельзя наступать       """
    def __init__(self, position, image):
        super().__init__(position, image)
        borders.add(self)


class Map:
    """                 Класс карты                       """

    def __init__(self, free_tiles):
        maps = spawned_rooms
        self.free_tiles = free_tiles
        self.sort_tiles(maps)

    # узнаем ID тайла из тайлсета
    def get_tile_id(self, position, map):
        return map.tiledgidmap[map.get_tile_gid(*position, layer=0)]

    # можно ли наступать на клетку
    def is_free(self, position, map):
        return self.get_tile_id(position, map) in self.free_tiles

    # Сортировка тайлов и проходов
    def sort_tiles(self, maps):
        for row in maps:
            for item in row:
                if item != 0:
                    map_class, map_x, map_y = item
                    dup, ddown, dleft, dright = map_class.DoorU, map_class.DoorD, map_class.DoorL, map_class.DoorR
                    map = map_class.map
                    print(map.width, map.height)
                    for y in range(map.height):
                        for x in range(map.width):
                            if dup.is_open() and (x, y) in dup.f_tiles:
                                build_passage_to(position=(x, y), map_position=(map_x, map_y), door=dup, map=map)
                            elif ddown.is_open() and (x, y) in ddown.f_tiles:
                                build_passage_to(position=(x, y), map_position=(map_x, map_y), door=ddown, map=map)
                            elif dleft.is_open() and (x, y) in dleft.f_tiles:
                                build_passage_to(position=(x, y), map_position=(map_x, map_y), door=dleft, map=map)
                            elif dright.is_open() and (x, y) in dright.f_tiles:
                                build_passage_to(position=(x, y), map_position=(map_x, map_y), door=dright, map=map)
                            else:
                                image = map.get_tile_image(x, y, layer=0)
                                image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
                                if not self.is_free((x, y), map):
                                    BorderTile((x * TILE_SIZE + map_x, y * TILE_SIZE + map_y), image)
                                else:
                                    Tile((x * TILE_SIZE + map_x, y * TILE_SIZE + map_y), image)
