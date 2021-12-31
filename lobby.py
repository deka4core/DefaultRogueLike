import pygame
import sys
from map_generator import BorderTile, Tile, borders, default_tiles, all_sprites
from constants import TILE_SIZE, FPS, WIDTH, HEIGHT, HERO_SPEED, PLAYER_IMAGES
from camera import camera_configure, Camera
from entities import Hero, all_entities
import pytmx


class Lobby:
    def __init__(self, free_tiles, clock, screen):
        self.hero = Hero((WIDTH // 2, HEIGHT // 2), speed=HERO_SPEED, images=PLAYER_IMAGES, size=(57, 64))
        self.free_tiles = free_tiles
        self.surface = screen
        self.started = False
        pygame.init()
        self.map_ = pytmx.load_pygame('data/maps/lobby_map.tmx')
        camera = Camera(camera_configure, WIDTH, HEIGHT)
        self.start(clock, camera)

    def start(self, clock, camera):
        frame = 0
        while True:
            camera.update(self.hero, sides_minmax=[0, 0, HEIGHT, WIDTH])
            frame = (frame + 1) % 11
            all_entities.update(frame)
            self.surface.fill((104,144,35))
            self.draw_map()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.started = True
            for e in all_sprites:
                self.surface.blit(e.image, camera.apply(e))
            self.surface.blit(self.hero.image, camera.apply(self.hero))
            if self.started:
                for sprite in default_tiles:
                    sprite.kill()
                for sprite in borders:
                    sprite.kill()
                self.hero.kill()
                break
            pygame.display.flip()
            clock.tick(FPS)

    def is_free(self, position, layer) -> bool:
        return self.map_.tiledgidmap[self.map_.get_tile_gid(*position, layer)] in self.free_tiles

    def draw_map(self):
        for sprite in default_tiles:
            sprite.kill()
        for sprite in borders:
            sprite.kill()
        for y in range(self.map_.height):
            for x in range(self.map_.width):
                for i in range(0, 4):
                    image = self.map_.get_tile_image(x, y, layer=i)
                    if image:
                        image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
                        if not self.is_free((x, y), i):
                            BorderTile((x * TILE_SIZE, y * TILE_SIZE), image, borders)
                        else:
                            Tile((x * TILE_SIZE, y * TILE_SIZE), image, default_tiles)

    def terminate(self):
        pygame.mixer.music.stop()
        pygame.quit()
        sys.exit()