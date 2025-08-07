# -*- coding: utf-8 -*-
import pygame
import random
from config import (
    SCREEN_W, SCREEN_H, TILE, COL_GOLD, STATE_MENU, STATE_PLAY, STATE_DEAD, STATE_WIN,
    DIFFS, SIZES, TREASURE_TYPES
)
from mapgen import generate_new_floor
from systems import (
    clamp_camera, add_particles, add_float_text, mark_visited_radius,
    update_particles, update_float_texts
)

class Game:
    def __init__(self, screen, clock, font_small, font_mid, font_big):
        self.screen = screen
        self.clock = clock
        self.font = font_small
        self.font_mid = font_mid
        self.font_big = font_big

        # Настройки
        self.settings = {
            "size_name": "Средний",
            "map_w": 80,
            "map_h": 50,
            "difficulty": "Нормальная",
            "treasure_density": 0.015,
            "lighting": True
        }

        # Меню
        self.menu_items = []
        self.menu_sel = 0

        # Камера и интерфейс
        self.cam = pygame.Vector2(0, 0)
        self.show_controls = False
        self.show_minimap = False

        # Состояние игры
        self.state = STATE_MENU
        self.game_over = False
        self.win = False

        # Мир
        self.MAP_W, self.MAP_H = self.settings["map_w"], self.settings["map_h"]
        self.tiles = [[1 for _ in range(self.MAP_W)] for __ in range(self.MAP_H)]
        self.visited = [[False for _ in range(self.MAP_W)] for __ in range(self.MAP_H)]
        self.spawn_tx = self.spawn_ty = 0
        self.shop_rect = pygame.Rect(0, 0, TILE*6, TILE*4)
        self.exit_rect = None
        self.exit_open = False
        self.TARGET_GOLD = 500

        # Игрок
        self.player = {
            "pos": pygame.Vector2(0, 0),
            "speed": 170.0,
            "hp": 5,
            "hp_max": 5,
            "dash_cd": 0.0,
            "dash_time": 0.0,
            "dash_mult": 2.6,
            "hurt_cd": 0.0,
            "sell_cd": 0.0,
            "dir": pygame.Vector2(1, 0),
            "shoot_cd": 0.0,
            "fire_rate": 0.22,
            "proj_speed": 420.0,
            "recoil": 12.0,
        }

        # Объекты
        self.gold = 0
        self.inventory = []
        self.enemies = []
        self.treasures = []
        self.projectiles = []
        self.particles = []
        self.float_texts = []

        # Инициализация меню
        self._build_menu()

    def _build_menu(self):
        def change_size(delta):
            idx = next((i for i,(n,_,_) in enumerate(SIZES) if n == self.settings["size_name"]), 1)
            idx = (idx + delta) % len(SIZES)
            n, w, h = SIZES[idx]
            self.settings["size_name"] = n
            self.settings["map_w"] = w
            self.settings["map_h"] = h

        def change_diff(delta):
            keys = list(DIFFS.keys())
            idx = keys.index(self.settings["difficulty"])
            idx = (idx + delta) % len(keys)
            self.settings["difficulty"] = keys[idx]

        def change_density(delta):
            v = self.settings["treasure_density"]
            v += delta * 0.005
            v = max(0.008, min(0.030, v))
            self.settings["treasure_density"] = v

        def toggle_lighting():
            self.settings["lighting"] = not self.settings["lighting"]

        self.menu_items = [
            {"name": "Размер подземелья", "get": lambda: self.settings["size_name"],
             "left": lambda: change_size(-1), "right": lambda: change_size(+1)},
            {"name": "Сложность", "get": lambda: self.settings["difficulty"],
             "left": lambda: change_diff(-1), "right": lambda: change_diff(+1)},
            {"name": "Плотность сокровищ", "get": lambda: f"{self.settings['treasure_density']:.3f}",
             "left": lambda: change_density(-1), "right": lambda: change_density(+1)},
            {"name": "Освещение", "get": lambda: ("Вкл" if self.settings["lighting"] else "Выкл"),
             "left": lambda: toggle_lighting(), "right": lambda: toggle_lighting()},
            {"name": "НАЧАТЬ ИГРУ", "get": lambda: "", "left": lambda: None, "right": lambda: None},
        ]

    def new_run(self):
        # Применить размер
        self.MAP_W, self.MAP_H = self.settings["map_w"], self.settings["map_h"]

        # Сброс объектов
        self.enemies.clear()
        self.treasures.clear()
        self.projectiles.clear()
        self.particles.clear()
        self.float_texts.clear()
        self.gold = 0
        self.inventory.clear()
        self.game_over = False
        self.win = False
        self.exit_open = False

        # Генерация мира и объектов
        generate_new_floor(self)

        # Игрок и камеры
        diff = DIFFS[self.settings["difficulty"]]
        self.player["hp_max"] = diff["player_hp"]
        self.player["hp"] = self.player["hp_max"]
        self.player["dash_cd"] = 0.0
        self.player["dash_time"] = 0.0
        self.player["hurt_cd"] = 0.0
        self.player["sell_cd"] = 0.0
        self.player["shoot_cd"] = 0.0
        self.player["fire_rate"] = diff.get("player_fire_rate", self.player["fire_rate"])  # применяем баланс сложности
        self.player["dir"] = pygame.Vector2(1, 0)
        self.player["pos"] = pygame.Vector2(self.spawn_tx*TILE + TILE/2, self.spawn_ty*TILE + TILE/2)

        # Туман у старта
        self.visited = [[False for _ in range(self.MAP_W)] for __ in range(self.MAP_H)]
        mark_visited_radius(self, self.spawn_tx, self.spawn_ty, 2)

        clamp_camera(self)
        self.state = STATE_PLAY

    def missing_gold(self):
        return max(0, self.TARGET_GOLD - self.gold)

    def open_exit_if_ready(self):
        if not self.exit_open and self.gold >= self.TARGET_GOLD:
            self.exit_open = True
            add_particles(self, self.player["pos"], COL_GOLD, n=24, speed=150)
            add_float_text(self, "Выход открыт!", self.player["pos"]) 
