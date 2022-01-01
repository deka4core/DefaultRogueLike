import pygame.transform

from entities import *
from lobby import *
from camera import Camera, camera_configure
from entities import Hero, monsters
from gui import hit_sprites, HealthBar
from monster_spawner import spawn_monsters

pygame.init()
screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)


def update_fps():
    fps = str(int(clock.get_fps()))
    fps_text = font.render(f'FPS: {fps}', True, pygame.Color("white"))
    return fps_text


def main():
    """
            Инициализация переменных
    """

    # Открытие меню
    Menu('background_menu.png', screen, load_image, clock)

    # Открываем лобби
    Lobby([533, 534, 535, 536, 573, 574, 575, 576, 1207, 1208], clock, screen)

    # Инициализация классов
    hero = Hero((int(TILE_SIZE * (3 * ROOM_SIZE[0] + ROOM_SIZE[0] // 2 - 1)),
                 int(TILE_SIZE * (3 * ROOM_SIZE[1] + ROOM_SIZE[1] // 2 - 1))), speed=HERO_SPEED, images=PLAYER_IMAGES,
                size=(45, 50))

    health_bar = HealthBar(screen, hero)

    map_ = Map([34, 6, 7, 8, 14, 15, 16, 22, 23, 24, 30])
    camera = Camera(camera_configure, len(spawned_rooms) * TILE_SIZE * 26, len(spawned_rooms) * TILE_SIZE * 26)
    spawn_monsters(MONSTERS_NUMBER)

    splashes = []
    hit_marks = []

    # Эмбиент
    pygame.mixer.music.load('data/sounds/dungeon_ambient_1.ogg')
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

    # Основной цикл
    running = True
    frame = 0  # счетчик кадра

    alpha_value = 0
    death_bckg = pygame.Surface(SIZE)

    pygame.mouse.set_visible(False)
    cooldown_tracker = 0
    while running:
        cooldown_tracker -= clock.get_time() if cooldown_tracker > 0 else 0
        frame = (frame + 1) % 11
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cooldown_tracker <= 0:
                    shoot_splash(event, hero, splashes, camera)
                    cooldown_tracker = SHOOT_COOLDOWN

        # Отрисовка
        screen.fill(BACKGROUND_COLOR)



        all_entities.update(frame)
        camera.update(hero)

        check_player_room(hero, map_)

        for e in all_sprites:
            screen.blit(e.image, camera.apply(e))

        screen.blit(hero.image, camera.apply(hero))

        for m in monsters:
            m.update_e(arr=monsters, frame=frame, hero_damage=hero.damage, arr_hit=hit_marks,
                       hero=hero, clock=clock, rooms=spawned_rooms)
            screen.blit(m.image, camera.apply(m))

        for splash in splashes:
            splash.move(splashes)
            screen.blit(splash.image, camera.apply(splash))

        for hit in hit_marks:
            hit.do_timer(clock=clock, arr=hit_marks)

        health_bar.update(hero.health_points)

        for title in titles:
            title.do_timer(clock=clock, arr=titles)
            screen.blit(title.image, (title.rect.x, title.rect.y))

        for hit in hit_sprites:
            screen.blit(hit.image, camera.apply(hit))

        if pygame.mouse.get_focused():
            pos = pygame.mouse.get_pos()
            screen.blit(load_image(CURSOR_IMAGE), pos)

        if not hero.is_alive:
            if alpha_value < 250:
                alpha_value += 1
                death_bckg.set_alpha(alpha_value)
                screen.blit(death_bckg, (0, 0))
            else:
                break

        # ФПС
        screen.blit(update_fps(), (WIDTH - 100, 25))
        pygame.display.flip()
        clock.tick(FPS)


main()
