# -*- coding: utf-8 -*-
import pygame
from config import SCREEN_W, SCREEN_H, STATE_MENU, STATE_PLAY, STATE_DEAD, STATE_WIN
from game_state import Game
from systems import (
    clamp_camera, update_particles, update_float_texts,
    handle_input, pick_up_items, enemy_ai_and_collisions,
    update_projectiles, update_visited_by_player, check_exit
)
from render import (
    draw_world, draw_lighting, draw_ui,
    draw_death_or_win_overlay
)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Treasure Dungeons — многомодульная версия")
    clock = pygame.time.Clock()

    font_small = pygame.font.SysFont("consolas", 18)
    font_mid = pygame.font.SysFont("consolas", 24, bold=False)
    font_big = pygame.font.SysFont("consolas", 36, bold=True)

    game = Game(screen, clock, font_small, font_mid, font_big)

    running = True
    dt = 0.016

    while running:
        dt = clock.tick(60) / 1000.0
        events = pygame.event.get()

        # Общие события (выход)
        for e in events:
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False

        # Состояние: меню
        if game.state == STATE_MENU:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_UP:
                        game.menu_sel = (game.menu_sel - 1) % len(game.menu_items)
                    elif e.key == pygame.K_DOWN:
                        game.menu_sel = (game.menu_sel + 1) % len(game.menu_items)
                    elif e.key == pygame.K_LEFT:
                        game.menu_items[game.menu_sel]["left"]()
                    elif e.key == pygame.K_RIGHT:
                        game.menu_items[game.menu_sel]["right"]()
                    elif e.key == pygame.K_RETURN:
                        game.new_run()

            # Рендер меню
            screen.fill((16, 18, 24))
            title = font_big.render("Treasure Dungeons", True, (200, 230, 255))
            screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 80))

            desc = font_mid.render("Выбери настройки и нажми Enter, чтобы начать", True, (140, 150, 160))
            screen.blit(desc, (SCREEN_W//2 - desc.get_width()//2, 120))

            base_y = 180
            for i, it in enumerate(game.menu_items):
                is_sel = (i == game.menu_sel)
                name = it["name"]
                val = it["get"]()
                text = f"{name}: {val}" if val != "" else name
                img = font_mid.render(text, True, (230, 235, 240) if is_sel else (140, 150, 160))
                x = SCREEN_W//2 - img.get_width()//2
                y = base_y + i * 40
                if is_sel:
                    pygame.draw.rect(screen, (40, 70, 100), pygame.Rect(x-14, y-4, img.get_width()+28, img.get_height()+8), border_radius=8)
                screen.blit(img, (x, y))

            pygame.display.flip()
            continue

        # Состояние: игра
        if game.state == STATE_PLAY:
            handle_input(game, dt, events)
            update_visited_by_player(game)

            clamp_camera(game)
            pick_up_items(game)
            enemy_ai_and_collisions(game, dt)
            update_projectiles(game, dt)
            update_particles(game, dt)
            update_float_texts(game, dt)
            check_exit(game)

            if game.game_over:
                game.state = STATE_DEAD
            elif game.win:
                game.state = STATE_WIN

            draw_world(game)
            draw_lighting(game)
            draw_ui(game)
            pygame.display.flip()
            continue

        # Состояния: смерть / победа
        if game.state in (STATE_DEAD, STATE_WIN):
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_r:
                        game.new_run()
                    elif e.key == pygame.K_m:
                        game.state = STATE_MENU

            draw_world(game)
            draw_lighting(game)
            if game.state == STATE_DEAD:
                draw_death_or_win_overlay(game, "Ты пал…")
            else:
                draw_death_or_win_overlay(game, "Ты выбрался с сокровищами!")
            pygame.display.flip()
            continue

    pygame.quit()

if __name__ == "__main__":
    main()
