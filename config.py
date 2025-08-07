# -*- coding: utf-8 -*-
import pygame

# Экран и тайлы
SCREEN_W, SCREEN_H = 1024, 576
TILE = 24

# Палитра
COL_BG = (18, 18, 22)
COL_FLOOR = (40, 44, 52)
COL_WALL = (22, 24, 30)
COL_ACCENT = (90, 180, 255)
COL_GOLD = (255, 210, 64)
COL_RED = (255, 90, 90)
COL_GREEN = (120, 255, 160)
COL_UI = (230, 235, 240)
COL_DIM = (140, 150, 160)

# Освещение
LIGHT_RADIUS = 200
LIGHT_SOFT = 160

# Сложность
DIFFS = {
    "Лёгкая":   {"enemy_mult": 0.6, "enemy_speed": 0.8,  "player_hp": 7, "sell_mult": 1.25, "spitter_chance": 0.10, "target_mult": 0.75, "player_fire_rate": 0.18},
    "Нормальная":{"enemy_mult": 1.0, "enemy_speed": 1.0,  "player_hp": 5, "sell_mult": 1.0,  "spitter_chance": 0.25, "target_mult": 1.0,  "player_fire_rate": 0.22},
    "Сложная":  {"enemy_mult": 1.5, "enemy_speed": 1.15, "player_hp": 4, "sell_mult": 0.9,  "spitter_chance": 0.35, "target_mult": 1.2,  "player_fire_rate": 0.26},
}

# Размеры карт (пресеты)
SIZES = [
    ("Маленький", 60, 40),
    ("Средний", 80, 50),
    ("Большой", 110, 70),
]

# Типы сокровищ
TREASURE_TYPES = [
    {"name": "Монета",   "value": 10,  "color": (255, 215, 0),   "weight": 50},
    {"name": "Самоцвет", "value": 25,  "color": (80, 220, 255),  "weight": 30},
    {"name": "Кубок",    "value": 50,  "color": (255, 180, 60),  "weight": 15},
    {"name": "Идол",     "value": 100, "color": (255, 120, 120), "weight": 4},
    {"name": "Реликвия", "value": 200, "color": (200, 160, 255), "weight": 1},
]

# Состояния
STATE_MENU = "menu"
STATE_PLAY = "play"
STATE_DEAD = "dead"
STATE_WIN = "win"

# Утилита рисования
def draw_round_rect(surf, rect, color, radius=8, border=0, border_color=(0,0,0,0)):
    pygame.draw.rect(surf, border_color if border else color, rect, border_radius=radius)
    if border:
        inner = pygame.Rect(rect)
        inner.inflate_ip(-border*2, -border*2)
        pygame.draw.rect(surf, color, inner, border_radius=max(0, radius - border))
