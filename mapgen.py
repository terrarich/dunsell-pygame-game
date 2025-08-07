# -*- coding: utf-8 -*-
import pygame
import random
import math
from config import TILE, TREASURE_TYPES, DIFFS

def in_bounds(g, tx, ty):
    return 0 <= tx < g.MAP_W and 0 <= ty < g.MAP_H

def world_to_tile(x, y):
    return int(x // TILE), int(y // TILE)

def is_wall_at_world(g, x, y):
    tx, ty = world_to_tile(x, y)
    if not in_bounds(g, tx, ty): return True
    return g.tiles[ty][tx] == 1

def collide_move(g, pos, move, radius=10):
    new = pos + move
    test = pygame.Vector2(new.x, pos.y)
    if (is_wall_at_world(g, test.x - radius, test.y) or
        is_wall_at_world(g, test.x + radius, test.y) or
        is_wall_at_world(g, test.x, test.y - radius) or
        is_wall_at_world(g, test.x, test.y + radius)):
        test.x = pos.x
    test2 = pygame.Vector2(test.x, new.y)
    if (is_wall_at_world(g, test2.x - radius, test2.y) or
        is_wall_at_world(g, test2.x + radius, test2.y) or
        is_wall_at_world(g, test2.x, test2.y - radius) or
        is_wall_at_world(g, test2.x, test2.y + radius)):
        test2.y = pos.y
    return test2

def carve_random_walk(g, steps, rooms, room_size):
    g.tiles = [[1 for _ in range(g.MAP_W)] for __ in range(g.MAP_H)]
    cx, cy = g.MAP_W // 2, g.MAP_H // 2

    # Комнаты
    for _ in range(rooms):
        rw = random.randint(room_size, room_size + 5)
        rh = random.randint(room_size, room_size + 5)
        rx = max(2, min(g.MAP_W - rw - 2, cx + random.randint(-12, 12)))
        ry = max(2, min(g.MAP_H - rh - 2, cy + random.randint(-8, 8)))
        for yy in range(ry, ry + rh):
            for xx in range(rx, rx + rw):
                g.tiles[yy][xx] = 0

    x, y = cx, cy
    for _ in range(steps):
        g.tiles[y][x] = 0
        dir = random.choice([(1,0), (-1,0), (0,1), (0,-1)])
        x = max(1, min(g.MAP_W - 2, x + dir[0]))
        y = max(1, min(g.MAP_H - 2, y + dir[1]))
        g.tiles[y][x] = 0

    # Сглаживание
    for _ in range(2):
        for yy in range(1, g.MAP_H - 1):
            for xx in range(1, g.MAP_W - 1):
                n = 0
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        if g.tiles[yy+dy][xx+dx] == 1:
                            n += 1
                if n <= 3:
                    g.tiles[yy][xx] = 0

    # Стартовая комната
    for sy in range(cy - 4, cy + 5):
        for sx in range(cx - 5, cx + 6):
            if in_bounds(g, sx, sy):
                g.tiles[sy][sx] = 0

    # Магазин у спавна
    g.shop_rect.x = (cx - 3) * TILE
    g.shop_rect.y = (cy - 2) * TILE
    return cx, cy

def spawn_treasures_by_density(g, density):
    g.treasures.clear()
    floor_tiles = [(tx, ty) for ty in range(g.MAP_H) for tx in range(g.MAP_W) if g.tiles[ty][tx] == 0]
    random.shuffle(floor_tiles)
    num = int(len(floor_tiles) * density)
    weights = [t["weight"] for t in TREASURE_TYPES]
    i = 0
    for (tx, ty) in floor_tiles:
        if i >= num: break
        if (abs(tx - g.spawn_tx) + abs(ty - g.spawn_ty)) <= 6:
            continue
        g.treasures.append({
            "pos": pygame.Vector2(tx * TILE + TILE / 2, ty * TILE + TILE / 2),
            "type": random.choices(range(len(TREASURE_TYPES)), weights=weights)[0]
        })
        i += 1

def spawn_enemies_scaled(g, base_num, diff):
    g.enemies.clear()
    target_num = max(4, int(base_num * diff["enemy_mult"]))
    tries = 0
    while len(g.enemies) < target_num and tries < target_num * 200:
        tries += 1
        tx = random.randrange(2, g.MAP_W - 2)
        ty = random.randrange(2, g.MAP_H - 2)
        if g.tiles[ty][tx] == 0:
            if (abs(tx - g.spawn_tx) + abs(ty - g.spawn_ty)) > 8:
                kind = "chaser"
                if random.random() < diff["spitter_chance"]:
                    kind = "spitter"
                g.enemies.append({
                    "pos": pygame.Vector2(tx * TILE + TILE / 2, ty * TILE + TILE / 2),
                    "hp": 3 if kind == "chaser" else 2,
                    "t": random.random() * 10.0,
                    "kind": kind,
                    "state": "wander",
                    "atk_cd": random.uniform(0.0, 1.2),
                })

def spawn_exit_far(g):
    g.exit_rect = None
    best = None
    best_d = -1
    for _ in range(1200):
        tx = random.randrange(1, g.MAP_W - 1)
        ty = random.randrange(1, g.MAP_H - 1)
        if g.tiles[ty][tx] == 0:
            d = abs(tx - g.spawn_tx) + abs(ty - g.spawn_ty)
            if d > best_d:
                best_d = d
                best = (tx, ty)
    if best:
        g.exit_rect = pygame.Rect(best[0] * TILE, best[1] * TILE, TILE * 2, TILE * 2)

def generate_new_floor(g):
    # Генерация тайлов
    steps = g.MAP_W * g.MAP_H // 2
    rooms = 7
    room_size = 6
    g.spawn_tx, g.spawn_ty = carve_random_walk(g, steps, rooms, room_size)

    # Настройки сложности
    diff = DIFFS[g.settings["difficulty"]]

    # Цель по золоту
    base_target = int((g.MAP_W * g.MAP_H) * 0.12)
    g.TARGET_GOLD = max(200, int(base_target * diff["target_mult"]))

    # Сокровища, враги, выход
    spawn_treasures_by_density(g, g.settings["treasure_density"])
    base_enemies = max(8, (g.MAP_W * g.MAP_H) // 160)
    spawn_enemies_scaled(g, base_enemies, diff)
    spawn_exit_far(g)
