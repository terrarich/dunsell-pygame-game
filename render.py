# -*- coding: utf-8 -*-
import pygame
import math
from config import (
    TILE, COL_BG, COL_FLOOR, COL_WALL, COL_GOLD, COL_RED, COL_UI, COL_DIM, COL_GREEN,
    LIGHT_RADIUS, LIGHT_SOFT, STATE_MENU, STATE_PLAY, STATE_DEAD, STATE_WIN, TREASURE_TYPES, draw_round_rect
)
from systems import update_particles, update_float_texts
from mapgen import world_to_tile

def draw_world(g):
    W, H = g.screen.get_width(), g.screen.get_height()
    g.screen.fill(COL_BG)

    start_tx = max(0, int(g.cam.x // TILE) - 2)
    end_tx = min(g.MAP_W, int((g.cam.x + W) // TILE) + 3)
    start_ty = max(0, int(g.cam.y // TILE) - 2)
    end_ty = min(g.MAP_H, int((g.cam.y + H) // TILE) + 3)

    for ty in range(start_ty, end_ty):
        for tx in range(start_tx, end_tx):
            r = pygame.Rect(tx * TILE - g.cam.x, ty * TILE - g.cam.y, TILE, TILE)
            if g.tiles[ty][tx] == 0:
                shade = (tx + ty) % 2
                col = (COL_FLOOR[0] + shade*3, COL_FLOOR[1] + shade*3, COL_FLOOR[2] + shade*3)
                pygame.draw.rect(g.screen, col, r)
            else:
                pygame.draw.rect(g.screen, COL_WALL, r)
                pygame.draw.line(g.screen, (COL_WALL[0]+10, COL_WALL[1]+10, COL_WALL[2]+10), (r.left, r.top), (r.right, r.top), 2)

    # Магазин
    shop_vis = g.shop_rect.move(-g.cam.x, -g.cam.y)
    draw_round_rect(g.screen, shop_vis, (35, 55, 80), radius=10, border=2, border_color=(90, 140, 200))
    pygame.draw.circle(g.screen, (120, 180, 255), (shop_vis.centerx, shop_vis.centery), 10)
    label = g.font.render("МАГАЗИН (E — продать)", True, (200, 230, 255))
    g.screen.blit(label, (shop_vis.x + 8, shop_vis.y - 22))

    # Выход
    if g.exit_rect:
        ex = g.exit_rect.move(-g.cam.x, -g.cam.y)
        if g.exit_open:
            draw_round_rect(g.screen, ex, (120, 255, 160), radius=6, border=2, border_color=(30, 60, 40))
            txt = g.font.render("ВХОД ОТКРЫТ", True, (20, 40, 30))
            g.screen.blit(txt, (ex.x + 6, ex.y - 22))
        else:
            draw_round_rect(g.screen, ex, (200, 60, 60), radius=6, border=2, border_color=(90, 20, 20))
            need = g.missing_gold()
            txt = g.font.render(f"ВХОД ЗАКРЫТ — нужно ещё: {need}", True, (255, 220, 220))
            g.screen.blit(txt, (ex.x - 20, ex.y - 22))

    # Сокровища
    for it in g.treasures:
        p = it["pos"] - g.cam
        t = TREASURE_TYPES[it["type"]]
        s = 6 + math.sin(pygame.time.get_ticks()/300 + p.x*0.01) * 2
        pygame.draw.circle(g.screen, (20,20,20), (int(p.x), int(p.y)+1), int(s)+2)
        pygame.draw.circle(g.screen, t["color"], (int(p.x), int(p.y)), int(s))
        pygame.draw.circle(g.screen, (255,255,255), (int(p.x), int(p.y - int(s/2))), 2)

    # Враги
    for e in g.enemies:
        p = e["pos"] - g.cam
        base_col = (180, 60, 60) if e["kind"] == "chaser" else (200, 130, 80)
        col = base_col if e["hp"] >= 2 else (240, 180, 120)
        pygame.draw.circle(g.screen, (10,10,10), (int(p.x), int(p.y)+2), 12)
        pygame.draw.circle(g.screen, col, (int(p.x), int(p.y)), 12)
        # HP
        w = 20
        hpw = int(w * (e["hp"]/3))
        pygame.draw.rect(g.screen, (30,30,30), pygame.Rect(p.x - w/2, p.y - 18, w, 4), border_radius=3)
        pygame.draw.rect(g.screen, (255,100,100), pygame.Rect(p.x - w/2, p.y - 18, hpw, 4), border_radius=3)

    # Снаряды
    for p in g.projectiles:
        pp = p["pos"] - g.cam
        c = (255, 240, 200) if not p["from_enemy"] else (255, 150, 150)
        pygame.draw.circle(g.screen, c, (int(pp.x), int(pp.y)), 3)

    # Игрок
    pp = g.player["pos"] - g.cam
    pygame.draw.circle(g.screen, (20,20,20), (int(pp.x), int(pp.y)+3), 14)
    pygame.draw.circle(g.screen, (30, 60, 80), (int(pp.x), int(pp.y)), 14)
    pygame.draw.circle(g.screen, (90, 200, 255), (int(pp.x), int(pp.y)), 12)
    pygame.draw.circle(g.screen, (255,255,255), (int(pp.x + g.player["dir"].x*6), int(pp.y + g.player["dir"].y*6)), 3)

def draw_lighting(g):
    if not g.settings["lighting"]:
        return
    overlay = pygame.Surface(g.screen.get_size(), pygame.SRCALPHA)
    center = (int(g.player["pos"].x - g.cam.x), int(g.player["pos"].y - g.cam.y))
    rings = 12
    for i in range(rings):
        rr = int(LIGHT_RADIUS + i * (LIGHT_SOFT / rings))
        alpha = min(220, i * 18)
        pygame.draw.circle(overlay, (0, 0, 0, alpha), center, rr)
    pygame.draw.rect(overlay, (0, 0, 0, 24), overlay.get_rect())
    g.screen.blit(overlay, (0, 0))

def draw_minimap(g):
    if not g.show_minimap:
        return
    W = g.screen.get_width()
    max_w = 280
    max_h = 220
    scale_x = max_w / g.MAP_W
    scale_y = max_h / g.MAP_H
    scale = min(scale_x, scale_y)
    mm_w = int(g.MAP_W * scale)
    mm_h = int(g.MAP_H * scale)

    panel = pygame.Surface((mm_w + 16, mm_h + 16), pygame.SRCALPHA)
    draw_round_rect(panel, panel.get_rect(), (0, 0, 0, 160), radius=10, border=2, border_color=(90, 140, 200))
    mm = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)

    for ty in range(g.MAP_H):
        for tx in range(g.MAP_W):
            if not g.visited[ty][tx]:
                continue
            rx = int(tx * scale)
            ry = int(ty * scale)
            r = pygame.Rect(rx, ry, max(1, int(scale)), max(1, int(scale)))
            if g.tiles[ty][tx] == 0:
                mm.fill((90, 95, 110, 200), r)
            else:
                mm.fill((50, 55, 70, 220), r)

    # Магазин
    stx, sty = g.shop_rect.x // TILE, g.shop_rect.y // TILE
    if 0 <= stx < g.MAP_W and 0 <= sty < g.MAP_H and g.visited[sty][stx]:
        pygame.draw.rect(mm, (120, 180, 255), pygame.Rect(int(stx*scale), int(sty*scale), int(2*scale), int(2*scale)))

    # Выход
    if g.exit_rect:
        etx, ety = g.exit_rect.x // TILE, g.exit_rect.y // TILE
        if 0 <= etx < g.MAP_W and 0 <= ety < g.MAP_H and g.visited[ety][etx]:
            col = (120, 255, 160) if g.exit_open else (200, 60, 60)
            pygame.draw.rect(mm, col, pygame.Rect(int(etx*scale), int(ety*scale), int(2*scale), int(2*scale)))

    # Игрок
    ptx, pty = world_to_tile(g.player["pos"].x, g.player["pos"].y)
    px = int(ptx * scale); py = int(pty * scale)
    pygame.draw.rect(mm, (255, 255, 255), pygame.Rect(px, py, max(2, int(scale)), max(2, int(scale))))

    panel.blit(mm, (8, 8))
    g.screen.blit(panel, (W - panel.get_width() - 16, 16))

def draw_ui(g):
    W = g.screen.get_width()
    panel = pygame.Surface((W, 48), pygame.SRCALPHA)
    draw_round_rect(panel, pygame.Rect(10, 6, W-20, 36), (0,0,0,120), radius=12)
    # HP
    for i in range(g.player["hp_max"]):
        x = 24 + i*20
        col = COL_RED if i < g.player["hp"] else (80,80,80)
        pygame.draw.circle(panel, col, (x, 24), 8)
    # Золото
    g_text = g.font.render(f"Золото: {g.gold}", True, COL_GOLD)
    panel.blit(g_text, (180, 14))
    # Инвентарь
    inv_val = sum(TREASURE_TYPES[it["type"]]["value"] for it in g.inventory)
    inv_text = g.font.render(f"В инвентаре: {len(g.inventory)} шт. (~{inv_val})", True, (200,230,255))
    panel.blit(inv_text, (330, 14))
    # Цель
    tgt = g.font.render(f"Цель: {g.TARGET_GOLD}", True, (200, 255, 200))
    panel.blit(tgt, (620, 14))
    g.screen.blit(panel, (0,0))

    # Плавающий текст
    for ft in g.float_texts:
        p = ft["pos"] - g.cam
        img = g.font.render(ft["text"], True, ft["color"])
        g.screen.blit(img, (p.x, p.y))

    # Подсказка у магазина
    if g.shop_rect.collidepoint(g.player["pos"].x, g.player["pos"].y):
        tip = g.font.render("E — продать всё из инвентаря", True, (220, 240, 255))
        g.screen.blit(tip, (20, 60))

    draw_minimap(g)
    draw_controls_help(g)

def draw_controls_help(g):
    if not g.show_controls: return
    W, H = g.screen.get_width(), g.screen.get_height()
    panel_w, panel_h = 520, 320
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    draw_round_rect(panel, panel.get_rect(), (0, 0, 0, 200), radius=12, border=2, border_color=(90, 140, 200))
    lines = [
        "Управление",
        "WASD — движение",
        "ЛКМ / Space — выстрел в точку курсора",
        "Shift — рывок",
        "E — продать предметы в магазине",
        "Tab — миникарта",
        "F1 — показать/скрыть справку",
        "R — начать заново (после смерти/победы)",
        "M — вернуться в меню (после смерти/победы)",
        "Esc — выйти из игры"
    ]
    for i, text in enumerate(lines):
        img = (g.font_mid if i == 0 else g.font).render(text, True, (230, 240, 255) if i == 0 else COL_UI)
        panel.blit(img, (24, 24 + i * 28))
    g.screen.blit(panel, (W//2 - panel_w//2, H//2 - panel_h//2))

# Новое: компоновка кнопок на экране смерти/победы

def compute_death_win_button_rects(g):
    W, H = g.screen.get_width(), g.screen.get_height()
    btn_w, btn_h = 220, 48
    gap = 20
    total_w = btn_w * 2 + gap
    x0 = W // 2 - total_w // 2
    y = H // 2 + 16
    return {
        "restart": pygame.Rect(x0, y, btn_w, btn_h),
        "menu": pygame.Rect(x0 + btn_w + gap, y, btn_w, btn_h),
    }

# Обновлено: оверлей смерти/победы с кнопками и исправленным цветом

def draw_death_or_win_overlay(g, title, buttons=None):
    W, H = g.screen.get_width(), g.screen.get_height()
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0,0,0,180))
    g.screen.blit(overlay, (0,0))

    is_dead = title.startswith("Ты пал")
    title_col = (255, 220, 220) if is_dead else (160, 255, 180)
    txt = g.font_big.render(title, True, title_col)
    g.screen.blit(txt, (g.screen.get_width() // 2 - txt.get_width() // 2, g.screen.get_height() // 2 - 72))

    if buttons is None:
        buttons = compute_death_win_button_rects(g)

    mx, my = pygame.mouse.get_pos()
    for key, rect in buttons.items():
        hovered = rect.collidepoint(mx, my)
        base_color = (40, 70, 100) if key == "restart" else (60, 50, 70)
        border_color = (120, 180, 255) if hovered else (90, 140, 200)
        draw_round_rect(g.screen, rect, base_color, radius=10, border=3, border_color=border_color)
        label = "ЗАНОВО (R)" if key == "restart" else "МЕНЮ (M)"
        img = g.font_mid.render(label, True, COL_UI)
        g.screen.blit(img, (rect.centerx - img.get_width() // 2, rect.centery - img.get_height() // 2))

    hint = g.font.render("Нажми R или кликни — начать заново. Нажми M — меню.", True, COL_DIM)
    g.screen.blit(hint, (W // 2 - hint.get_width() // 2, buttons["restart"].bottom + 12))

