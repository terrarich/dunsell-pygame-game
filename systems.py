# -*- coding: utf-8 -*-
import pygame
import random
import math
from config import (
    TILE, COL_GOLD, COL_RED, LIGHT_RADIUS, LIGHT_SOFT, TREASURE_TYPES, DIFFS
)
from mapgen import world_to_tile, in_bounds, collide_move, is_wall_at_world

# Плавающий текст и частицы
def add_float_text(g, text, pos, color=(230,230,230)):
    g.float_texts.append({
        "text": text,
        "pos": pygame.Vector2(pos),
        "vy": -22,
        "time": 0.0,
        "color": color,
        "life": 1.2
    })

def update_float_texts(g, dt):
    i = 0
    while i < len(g.float_texts):
        ft = g.float_texts[i]
        ft["time"] += dt
        ft["pos"].y += ft["vy"] * dt
        if ft["time"] > ft["life"]:
            g.float_texts.pop(i); continue
        i += 1

def add_particles(g, pos, color, n=10, speed=70):
    for _ in range(n):
        ang = random.random() * math.tau
        v = pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(0.2, 1.0) * speed
        g.particles.append({
            "pos": pygame.Vector2(pos),
            "vel": v,
            "life": random.uniform(0.4, 0.9),
            "color": color,
            "size": random.randint(2, 4)
        })

def update_particles(g, dt):
    i = 0
    while i < len(g.particles):
        prt = g.particles[i]
        prt["life"] -= dt
        if prt["life"] <= 0:
            g.particles.pop(i); continue
        prt["pos"] += prt["vel"] * dt
        prt["vel"] *= 0.92
        i += 1

# Камера
def clamp_camera(g):
    g.cam.x = max(0, min(g.player["pos"].x - g.screen.get_width()/2, g.MAP_W * TILE - g.screen.get_width()))
    g.cam.y = max(0, min(g.player["pos"].y - g.screen.get_height()/2, g.MAP_H * TILE - g.screen.get_height()))

# Туман войны
def mark_visited_radius(g, tx, ty, r=1):
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            x = tx + dx
            y = ty + dy
            if in_bounds(g, x, y):
                g.visited[y][x] = True

def update_visited_by_player(g):
    tx, ty = world_to_tile(g.player["pos"].x, g.player["pos"].y)
    if in_bounds(g, tx, ty):
        mark_visited_radius(g, tx, ty, r=2)

# Игровые системы
def pick_up_items(g):
    i = 0
    while i < len(g.treasures):
        it = g.treasures[i]
        if (it["pos"] - g.player["pos"]).length_squared() < (12+10)**2:
            g.inventory.append({"type": it["type"]})
            t = TREASURE_TYPES[it["type"]]
            add_particles(g, it["pos"], t["color"], n=12, speed=110)
            add_float_text(g, f"+{t['value']}", it["pos"], t["color"])
            g.treasures.pop(i)
        else:
            i += 1

def sell_all(g):
    diff = DIFFS[g.settings["difficulty"]]
    if not g.inventory:
        return
    value = sum(TREASURE_TYPES[it["type"]]["value"] for it in g.inventory)
    value = int(value * diff["sell_mult"])
    if value > 0:
        g.gold += value
        add_particles(g, g.player["pos"], COL_GOLD, n=24, speed=150)
        add_float_text(g, f"+{value} золота", g.player["pos"], COL_GOLD)
        g.inventory.clear()
        g.open_exit_if_ready()

def fire_projectile(g, target_pos):
    if g.player["shoot_cd"] > 0:
        return
    src = pygame.Vector2(g.player["pos"])
    dir = (target_pos - src)
    if dir.length() == 0:
        return
    dir = dir.normalize()
    vel = dir * g.player["proj_speed"]
    g.projectiles.append({
        "pos": pygame.Vector2(src + dir * 14),
        "vel": vel,
        "life": 1.2,
        "dmg": 1,
        "from_enemy": False
    })
    # отдача
    g.player["pos"] = collide_move(g, g.player["pos"], -dir * g.player["recoil"], radius=10)
    add_particles(g, src + dir * 10, (220, 240, 255), n=6, speed=90)
    g.player["shoot_cd"] = g.player["fire_rate"]

def update_projectiles(g, dt):
    i = 0
    while i < len(g.projectiles):
        p = g.projectiles[i]
        p["life"] -= dt
        if p["life"] <= 0:
            g.projectiles.pop(i); continue
        new_pos = p["pos"] + p["vel"] * dt
        if is_wall_at_world(g, new_pos.x, new_pos.y):
            add_particles(g, p["pos"], (255, 230, 160) if not p["from_enemy"] else (255, 120, 120), n=8, speed=120)
            g.projectiles.pop(i); continue
        p["pos"] = new_pos

        if p["from_enemy"]:
            if (p["pos"] - g.player["pos"]).length_squared() < (10+4)**2:
                if g.player["hurt_cd"] <= 0:
                    g.player["hp"] -= p["dmg"]
                    g.player["hurt_cd"] = 0.9
                    add_float_text(g, f"-{p['dmg']} HP", g.player["pos"], COL_RED)
                    if g.player["hp"] <= 0:
                        g.game_over = True
                g.projectiles.pop(i); continue
        else:
            hit = False
            for e in g.enemies[:]:
                if (p["pos"] - e["pos"]).length_squared() < (12+4)**2:
                    e["hp"] -= p["dmg"]
                    add_particles(g, e["pos"], (255, 200, 160), n=10, speed=120)
                    add_float_text(g, f"-{p['dmg']}", e["pos"], (255, 150, 150))
                    if e["hp"] <= 0:
                        if random.random() < 0.33:
                            weights = [t["weight"] for t in TREASURE_TYPES]
                            g.treasures.append({
                                "pos": pygame.Vector2(e["pos"]),
                                "type": random.choices(range(len(TREASURE_TYPES)), weights=weights)[0]
                            })
                        g.enemies.remove(e)
                    hit = True
                    break
            if hit:
                g.projectiles.pop(i); continue
        i += 1

def enemy_ai_and_collisions(g, dt):
    ppos = pygame.Vector2(g.player["pos"])
    diff = DIFFS[g.settings["difficulty"]]
    for e in g.enemies[:]:
        e["t"] += dt
        to_p = ppos - e["pos"]
        dist = to_p.length()
        if dist < 240:
            e["state"] = "chase"
        elif dist > 300:
            e["state"] = "wander"

        if e["state"] == "chase":
            if dist > 1:
                to_p.scale_to_length(65 * diff["enemy_speed"])
                desired = to_p
            else:
                desired = pygame.Vector2()
        else:
            desired = pygame.Vector2(math.cos(e["t"]*0.8), math.sin(e["t"]*0.7)) * (40 * diff["enemy_speed"])

        e["pos"] = collide_move(g, e["pos"], desired * dt, radius=10)

        # Плевок
        if e["kind"] == "spitter":
            e["atk_cd"] -= dt
            if e["atk_cd"] <= 0 and dist < 320:
                dir = (ppos - e["pos"])
                if dir.length() > 0:
                    dir = dir.normalize()
                    vel = dir * 260.0
                    g.projectiles.append({
                        "pos": pygame.Vector2(e["pos"]),
                        "vel": vel,
                        "life": 2.0,
                        "dmg": 1,
                        "from_enemy": True
                    })
                    e["atk_cd"] = random.uniform(0.9, 1.4)

        # Контактный урон
        if (e["pos"] - ppos).length_squared() < (10+12)**2:
            if g.player["hurt_cd"] <= 0:
                g.player["hp"] -= 1
                g.player["hurt_cd"] = 0.9
                add_float_text(g, "-1 HP", g.player["pos"], COL_RED)
                push = (ppos - e["pos"])
                if push.length() > 0:
                    push.scale_to_length(120)
                    g.player["pos"] = collide_move(g, g.player["pos"], push * dt, radius=10)
                if g.player["hp"] <= 0:
                    g.game_over = True

def handle_input(g, dt, events):
    keys = pygame.key.get_pressed()
    move = pygame.Vector2(0, 0)
    if keys[pygame.K_w]: move.y -= 1
    if keys[pygame.K_s]: move.y += 1
    if keys[pygame.K_a]: move.x -= 1
    if keys[pygame.K_d]: move.x += 1
    if move.length_squared() > 0:
        move = move.normalize()
        g.player["dir"] = move

    speed = g.player["speed"]
    if g.player["dash_time"] > 0:
        speed *= g.player["dash_mult"]
    g.player["pos"] = collide_move(g, g.player["pos"], move * speed * dt, radius=10)

    for e in events:
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            mx, my = pygame.mouse.get_pos()
            world_target = pygame.Vector2(mx + g.cam.x, my + g.cam.y)
            fire_projectile(g, world_target)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                mx, my = pygame.mouse.get_pos()
                world_target = pygame.Vector2(mx + g.cam.x, my + g.cam.y)
                fire_projectile(g, world_target)
            if e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                moving = keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]
                if g.player["dash_cd"] <= 0 and g.player["dash_time"] <= 0 and moving:
                    g.player["dash_time"] = 0.18
                    g.player["dash_cd"] = 0.9
            if e.key == pygame.K_e and g.player["sell_cd"] <= 0:
                if g.shop_rect.collidepoint(g.player["pos"].x, g.player["pos"].y) and len(g.inventory) > 0:
                    sell_all(g)
                    g.player["sell_cd"] = 0.3
            if e.key == pygame.K_F1:
                g.show_controls = not g.show_controls
            if e.key == pygame.K_TAB:
                g.show_minimap = not g.show_minimap

    # Тики кулдаунов
    g.player["dash_cd"] = max(0.0, g.player["dash_cd"] - dt)
    g.player["dash_time"] = max(0.0, g.player["dash_time"] - dt)
    g.player["hurt_cd"] = max(0.0, g.player["hurt_cd"] - dt)
    g.player["sell_cd"] = max(0.0, g.player["sell_cd"] - dt)
    g.player["shoot_cd"] = max(0.0, g.player["shoot_cd"] - dt)

def check_exit(g):
    if not g.exit_rect or not g.exit_open: return
    if g.exit_rect.collidepoint(g.player["pos"].x, g.player["pos"].y):
        g.win = True
