import tkinter as tk
from tkinter import messagebox
import pygame
import sys
import random
import math

PLAYER_LIVES = 3
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 720
ENEMY_WIDTH = 35
ENEMY_HEIGHT = 35
ENEMY_BULLET_COLOR = (173, 216, 230)  #light-blue

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def show_game_over(score, round_number):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Game Over", f"Game Over! Your score: {score}\nYou reached round {round_number}.")
    root.destroy()
    sys.exit()

def create_wave(round_num):
    return spawn_enemies(round_num)

class Asteroid:
    def __init__(self, start_x, start_y):
        self.rect = pygame.Rect(start_x, start_y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.color = (105, 105, 105)  #dark-grey
        self.hp = 2
        self.speed = random.uniform(0.5, 1.5)
        self.power_up_drop_chance = 0.1
        self.in_formation = False
        self.returning = False

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.x = random.randint(0, SCREEN_WIDTH - ENEMY_WIDTH)
            self.rect.y = -ENEMY_HEIGHT
            self.hp = 2

    def take_hit(self):
        self.hp -= 1
        return self.hp <= 0

    def try_drop_power_up(self):
        return random.random() < self.power_up_drop_chance

class Enemy:
    def __init__(self, start_x, start_y, target_x, target_y, enemy_type):
        self.rect = pygame.Rect(start_x, start_y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.color = enemy_type["color"]
        self.points = enemy_type["points"]
        self.in_formation = False
        self.returning = False
        self.path = self.generate_entry_path((start_x, start_y), (target_x, target_y))
        self.path_index = 0
        self.target_pos = (target_x, target_y)
        self.shoot_cooldown = 2500 
        self.last_shot_time = 0

        self.attack_delay = random.randint(0, 2000)
        self.spawn_time = pygame.time.get_ticks()

    def generate_entry_path(self, start, end):
        control1 = (random.randint(50, SCREEN_WIDTH - 50), random.randint(100, 250))
        control2 = (random.randint(50, SCREEN_WIDTH - 50), random.randint(250, 400))
        steps = 100
        path = []
        for t in range(steps + 1):
            t /= steps
            x = (
                (1 - t) ** 3 * start[0]
                + 3 * (1 - t) ** 2 * t * control1[0]
                + 3 * (1 - t) * t ** 2 * control2[0]
                + t ** 3 * end[0]
            )
            y = (
                (1 - t) ** 3 * start[1]
                + 3 * (1 - t) ** 2 * t * control1[1]
                + 3 * (1 - t) * t ** 2 * control2[1]
                + t ** 3 * end[1]
            )
            path.append((x, y))
        return path

    def update_dive(self):
        pass

    def start_dive(self, player_x, player_y):
        pass

    def return_to_formation(self):
        self.returning = True
        self.path = self.generate_entry_path((self.rect.x, self.rect.y), self.target_pos)
        self.path_index = 0

    def bounce_on_edges(self):
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            if hasattr(self, "direction"):
                self.direction *= -1
                self.rect.x = clamp(self.rect.x, 0, SCREEN_WIDTH - ENEMY_WIDTH)

        if self.rect.top <= 0:
            if hasattr(self, "vertical_speed"):
                self.vertical_speed *= -1
            else:
                self.rect.y = 1

class RedEnemy(Enemy):
    def __init__(self, sx, sy, tx, ty, round_num):
        super().__init__(sx, sy, tx, ty, {"color": (255, 0, 0), "points": 20})
        self.charging_up = False
        self.charge_path = []
        self.charge_index = 0

        base_speed = 1.5 + 0.04 * round_num
        self.speed = random.uniform(max(0.3, base_speed - 0.2), base_speed + 0.3)

        self.shoot_cooldown = 5000
        self.last_shot_time = pygame.time.get_ticks() - random.randint(0, self.shoot_cooldown)

        self.zigzag = random.choice([True, False])
        self.zigzag_amplitude = 15
        self.zigzag_frequency = 0.08
        self.zigzag_phase = random.uniform(0, 2 * math.pi)

    def update(self):
        if not self.in_formation and not self.returning:
            if self.path_index < len(self.path):
                self.rect.x, self.rect.y = map(int, self.path[self.path_index])
                self.path_index += 1
            else:
                self.in_formation = True
            return

        if self.returning:
            if self.path_index < len(self.path):
                self.rect.x, self.rect.y = map(int, self.path[self.path_index])
                self.path_index += 1
            else:
                self.in_formation = True
                self.returning = False
            return

        if self.charging_up:
            if self.charge_index < len(self.charge_path):
                self.rect.x, self.rect.y = map(int, self.charge_path[self.charge_index])
                self.charge_index += 2
            else:
                self.return_to_formation()
                self.charging_up = False
            return

        self.rect.y += int(self.speed)

        if self.zigzag:
            offset_x = int(self.zigzag_amplitude * math.sin(self.zigzag_frequency * self.rect.y + self.zigzag_phase))
            self.rect.x = self.target_pos[0] + offset_x

        self.bounce_on_edges()

        if self.rect.bottom >= SCREEN_HEIGHT:
            self.charging_up = True
            self.charge_path = self.generate_entry_path(
                (self.rect.x, self.rect.y),
                (self.target_pos[0], self.target_pos[1] + 30)
            )
            self.charge_index = 0

    def update_dive(self):
        if self.charging_up:
            if self.charge_index < len(self.charge_path):
                self.rect.x, self.rect.y = map(int, self.charge_path[self.charge_index])
                self.charge_index += 2
            else:
                self.return_to_formation()
                self.charging_up = False
            return

        if not hasattr(self, 'pos_x'):
            self.pos_x = float(self.rect.x)
            self.pos_y = float(self.rect.y)

        self.pos_y += self.speed

        if self.zigzag:
            offset_x = self.zigzag_amplitude * math.sin(self.zigzag_frequency * self.pos_y + self.zigzag_phase)
            self.rect.x = int(self.pos_x + offset_x)
        else:
            self.rect.x = int(self.pos_x)

        self.rect.y = int(self.pos_y)

        self.bounce_on_edges()

        if self.rect.bottom >= SCREEN_HEIGHT:
            self.charging_up = True
            self.charge_path = self.generate_entry_path(
                (self.rect.x, self.rect.y),
                (self.target_pos[0], self.target_pos[1] + 30)
            )
            self.charge_index = 0

    def update_entry(self):
        if self.path_index < len(self.path):
            self.rect.x, self.rect.y = map(int, self.path[self.path_index])
            self.path_index += 1
        else:
            self.in_formation = True

    def shoot(self, bullets):
        current_time = pygame.time.get_ticks()
        if current_time - self.spawn_time >= self.attack_delay:
            if self.in_formation and (current_time - self.last_shot_time) >= self.shoot_cooldown:
                bullet = pygame.Rect(self.rect.centerx - 2, self.rect.bottom, 4, 12)
                bullets.append((bullet, (0, 6), ENEMY_BULLET_COLOR))
                self.last_shot_time = current_time

class GreenEnemy(Enemy):
    def __init__(self, sx, sy, tx, ty, round_num, pattern_type):
        super().__init__(sx, sy, tx, ty, {"color": (0, 255, 0), "points": 35})
        self.hp = 2
        self.speed = min(1 + 0.03 * round_num, 1.8)
        self.center = (tx, ty)
        self.pattern_type = pattern_type
        self.pattern_points = self.generate_pattern_points(pattern_type, round_num)
        self.pattern_index = random.randint(0, len(self.pattern_points) - 1)
        self.shoot_cooldown = 4000
        self.last_shot_time = pygame.time.get_ticks() - random.randint(0, self.shoot_cooldown)
        self.phase_angle = 0
        self.phase_speed = 0.05
        self.direction = 1
        self.radius = 40 + round_num * 5

    def update(self):
        if not self.in_formation and not self.returning:
            if self.path_index < len(self.path):
                self.rect.x, self.rect.y = map(int, self.path[self.path_index])
                self.path_index += 1
            else:
                self.in_formation = True
                if self.pattern_points:
                    distances = [
                        math.hypot(self.rect.centerx - px, self.rect.centery - py) 
                        for (px, py) in self.pattern_points
                    ]
                    closest_index = distances.index(min(distances))
                    self.pattern_index = closest_index
                    self.rect.center = (int(self.pattern_points[closest_index][0]), int(self.pattern_points[closest_index][1]))
            return

        if self.returning:
            if self.path_index < len(self.path):
                self.rect.x, self.rect.y = map(int, self.path[self.path_index])
                self.path_index += 1
            else:
                self.in_formation = True
                self.returning = False
            return

        if self.pattern_type == 'circle':
            self.phase_angle += self.direction * self.phase_speed
            self.rect.centerx = int(self.center[0] + self.radius * math.cos(self.phase_angle))
            self.rect.centery = int(self.center[1] + self.radius * math.sin(self.phase_angle))
        else:
            if not self.pattern_points:
                return
            target = self.pattern_points[self.pattern_index]
            dx = target[0] - self.rect.centerx
            dy = target[1] - self.rect.centery
            dist = math.hypot(dx, dy)

            if dist < self.speed:
                self.rect.center = (int(target[0]), int(target[1]))
                self.pattern_index = (self.pattern_index + 1) % len(self.pattern_points)
            else:
                move_x = self.speed * dx / dist
                move_y = self.speed * dy / dist
                self.rect.centerx += int(move_x)
                self.rect.centery += int(move_y)

        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)

    def generate_pattern_points(self, pattern_type, round_num):
        size = 40 + round_num * 5
        if pattern_type == 'circle':
            points = []
            for i in range(20):
                angle = 2 * math.pi * i / 20
                x = self.center[0] + size * math.cos(angle)
                y = self.center[1] + size * math.sin(angle)
                points.append((x, y))
            return points
        elif pattern_type == 'square':
            s = size
            return [
                (self.center[0] - s, self.center[1] - s),
                (self.center[0] + s, self.center[1] - s),
                (self.center[0] + s, self.center[1] + s),
                (self.center[0] - s, self.center[1] + s),
            ]
        elif pattern_type == 'triangle':
            s = size
            h = s * math.sqrt(3) / 2
            return [
                (self.center[0], self.center[1] - h),
                (self.center[0] - s, self.center[1] + h / 2),
                (self.center[0] + s, self.center[1] + h / 2),
            ]
        elif pattern_type == 'diamond':
            s = size
            return [
                (self.center[0], self.center[1] - s),
                (self.center[0] + s, self.center[1]),
                (self.center[0], self.center[1] + s),
                (self.center[0] - s, self.center[1]),
            ]
        return []
    
    def update_dive(self):
        if not self.in_formation:
            return

        if self.pattern_type == 'circle':
            self.phase_angle += self.direction * self.phase_speed
            self.rect.centerx = int(self.center[0] + self.radius * math.cos(self.phase_angle))
            self.rect.centery = int(self.center[1] + self.radius * math.sin(self.phase_angle))
        else:
            if not self.pattern_points:
                return

            target = self.pattern_points[self.pattern_index]
            dx = target[0] - self.rect.centerx
            dy = target[1] - self.rect.centery
            dist = math.hypot(dx, dy)

            if dist < self.speed:
                self.rect.center = (int(target[0]), int(target[1]))
                self.pattern_index = (self.pattern_index + 1) % len(self.pattern_points)
            else:
                move_x = self.speed * dx / dist
                move_y = self.speed * dy / dist
                self.rect.centerx += int(move_x)
                self.rect.centery += int(move_y)

        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        if self.rect.top < 0:
            self.rect.top = 0
        elif self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def update_entry(self):
        if self.path_index < len(self.path):
            self.rect.x, self.rect.y = map(int, self.path[self.path_index])
            self.path_index += 1
        else:
            if not self.in_formation:
                self.in_formation = True
                if self.pattern_points:
                    distances = [
                        math.hypot(self.rect.centerx - px, self.rect.centery - py) 
                        for (px, py) in self.pattern_points
                    ]
                    closest_index = distances.index(min(distances))
                    self.pattern_index = closest_index
                    self.rect.center = (int(self.pattern_points[closest_index][0]), int(self.pattern_points[closest_index][1]))

    def shoot(self, bullets):
        current_time = pygame.time.get_ticks()
        if self.in_formation and (current_time - self.last_shot_time) >= self.shoot_cooldown:
            left_bullet = pygame.Rect(self.rect.centerx - 4, self.rect.bottom, 4, 12)
            right_bullet = pygame.Rect(self.rect.centerx + 4, self.rect.bottom, 4, 12)
            bullets.append((left_bullet, (-3, 6), ENEMY_BULLET_COLOR))
            bullets.append((right_bullet, (3, 6), ENEMY_BULLET_COLOR))
            self.last_shot_time = current_time

    def take_hit(self):
        self.hp -= 1
        return self.hp <= 0

class PurpleEnemy(Enemy):
    def __init__(self, sx, sy, tx, ty, round_num, direction=1):
        super().__init__(sx, sy, tx, ty, {"color": (128, 0, 255), "points": 30})
        self.speed = min(1 + 0.04 * round_num, 2.0)
        self.phase_angle = 0
        self.radius = 40
        self.center = (tx, ty)
        self.phase_speed = 0.05 * self.speed
        self.shoot_cooldown = 2500
        self.last_shot_time = pygame.time.get_ticks() - random.randint(0, self.shoot_cooldown)
        self.direction = direction
        self.zigzag_phase = random.uniform(0, 2 * math.pi)
        self.player_ref = None

    def update(self):
        if not self.in_formation and not self.returning:
            if self.path_index < len(self.path):
                self.rect.x, self.rect.y = map(int, self.path[self.path_index])
                self.phase_angle = 0
                self.center = (self.rect.x, self.rect.y)
                self.path_index += int(1 * self.speed)
            else:
                self.in_formation = True
            return

        if self.returning:
            if self.path_index < len(self.path):
                self.rect.x, self.rect.y = map(int, self.path[self.path_index])
                self.path_index += 1
            else:
                self.in_formation = True
                self.returning = False
            return

        if not hasattr(self, 'base_y'):
            self.base_y = self.rect.y

        self.rect.x += int(self.speed * self.direction)

        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            if hasattr(self, 'player_ref'):
                self.start_dive(self.player_ref.centerx, self.player_ref.centery)
            return

        zigzag_amplitude = 30
        zigzag_frequency = 0.05
        offset = int(zigzag_amplitude * math.sin(zigzag_frequency * self.rect.x + self.zigzag_phase))
        self.rect.y = self.base_y + offset

    def start_dive(self, player_x, player_y):
        self.returning = False
        steps = 60
        path = []
        dx = (player_x - self.rect.x) / steps
        dy = ((SCREEN_HEIGHT + 100) - self.rect.y) / steps
        for i in range(steps):
            path.append((self.rect.x + dx * i, self.rect.y + dy * i))
        for i in range(steps):
            path.append((self.rect.x + dx * (steps - i - 1), SCREEN_HEIGHT + 100 - dy * i))
        self.path = path
        self.path_index = 0
        self.in_formation = False

    def update_entry(self):
        if self.path_index < len(self.path):
            self.rect.x, self.rect.y = map(int, self.path[self.path_index])
            self.phase_angle = 0
            self.center = (self.rect.x, self.rect.y)
            self.path_index += int(1 * self.speed)
        else:
            self.in_formation = True

    def update_dive(self):
        if self.in_formation:
            if not hasattr(self, 'base_y'):
                self.base_y = self.rect.y

            self.rect.x += int(self.speed * self.direction)

            if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
                self.start_dive(self.player_ref.centerx, self.player_ref.centery)
                return

            zigzag_amplitude = 30
            zigzag_frequency = 0.05
            offset = int(zigzag_amplitude * math.sin(zigzag_frequency * self.rect.x + self.zigzag_phase))
            self.rect.y = self.base_y + offset

    def take_hit(self):
        self.hp -= 1
        return self.hp <= 0

def update_enemy_bullets(enemy_bullets):
    for bullet in enemy_bullets[:]:
        rect, (dx, dy), _ = bullet
        rect.x += dx
        rect.y += dy
        if rect.top > SCREEN_HEIGHT:
            enemy_bullets.remove(bullet)

def draw_enemy_bullets(screen, enemy_bullets):
    for rect, _, color in enemy_bullets:
        pygame.draw.rect(screen, color, rect)

def check_bullet_player_collisions(player, enemy_bullets):
    for bullet in enemy_bullets[:]:
        rect, _, _ = bullet
        if rect.colliderect(player):
            enemy_bullets.remove(bullet)
            return True
    return False

def handle_enemy_shooting(enemies, enemy_bullets, current_time):
    for enemy in enemies:
        if hasattr(enemy, "shoot"):
            try:
                enemy.shoot(enemy_bullets, current_time)
            except TypeError:
                enemy.shoot(enemy_bullets)

def spawn_enemies(round_num):
    enemies = []
    cols = 8
    rows = 4
    spacing_x = ENEMY_WIDTH + 25
    spacing_y = ENEMY_HEIGHT + 25
    start_x = (SCREEN_WIDTH - (cols - 1) * spacing_x) // 2
    start_y = 80
    min_distance = ENEMY_WIDTH + 10

    def is_far_enough(x, y, existing_rects):
        for rect in existing_rects:
            if math.hypot(rect.centerx - x, rect.centery - y) < min_distance:
                return False
        return True

    placed_rects = []

    green_patterns = ['circle', 'square', 'triangle', 'diamond']
    random.shuffle(green_patterns)

    green_count = 0
    purple_toggle = True

    for row in range(rows):
        for col in range(cols):
            for _ in range(30):
                sx = random.randint(0, SCREEN_WIDTH)
                sy = -ENEMY_HEIGHT - random.randint(20, 100)

                offset_x = random.randint(-20, 20)
                offset_y = random.randint(-10, 10)
                tx = start_x + col * spacing_x + offset_x
                ty = start_y + row * spacing_y + offset_y

                if is_far_enough(tx, ty, placed_rects):
                    if row == 2:
                        red_positions = [1, 3, 5, 7]
                        if col in red_positions:
                            enemy = RedEnemy(sx, sy, tx, ty, round_num)
                        else:
                            break
                    elif row == 0:
                        enemy = RedEnemy(sx, sy, tx, ty, round_num)
                    elif row == 1:
                        direction = -1 if purple_toggle else 1
                        enemy = PurpleEnemy(sx, sy, tx, ty, round_num, direction)
                        purple_toggle = not purple_toggle
                    else:
                        if green_count < len(green_patterns):
                            pattern = green_patterns[green_count]
                            green_count += 1
                        else:
                            pattern = random.choice(green_patterns)
                        enemy = GreenEnemy(sx, sy, tx, ty, round_num, pattern)

                    enemies.append(enemy)
                    placed_rects.append(pygame.Rect(tx, ty, ENEMY_WIDTH, ENEMY_HEIGHT))
                    break

    return enemies

def start_game():
    window.destroy()
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("From Beyond")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 30)

    black = (0, 0, 0)
    white = (255, 255, 255)
    player = pygame.Rect(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT - 70, 40, 40)
    player_speed = 6
    bullets = []
    enemy_bullets = []
    bullet_speed = 10
    shoot_cooldown = 500
    last_shot_time = pygame.time.get_ticks()

    power_shot_ready = True
    item_ready = True
    force_field_ready = True

    round_number = 1
    enemies = spawn_enemies(round_number)
    formation_direction = 1
    formation_speed = 1.5

    lives = PLAYER_LIVES
    score = 0
    diving_enemies = []

    invincible = False
    invincible_start_time = 0
    invincible_duration = 3000
    flash_interval = 200
    player_visible = True

    running = True
    while running:
        screen.fill(black)
        current_time = pygame.time.get_ticks()

        MIN_PLAYER_Y = 300

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.left > 0:
            player.x -= player_speed
        if keys[pygame.K_RIGHT] and player.right < SCREEN_WIDTH:
            player.x += player_speed
        if keys[pygame.K_UP] and player.top > 0:
            player.y -= player_speed
        if keys[pygame.K_DOWN] and player.bottom < SCREEN_HEIGHT:
            player.y += player_speed

        player.y = max(player.y, MIN_PLAYER_Y)

        if keys[pygame.K_SPACE]:
            if current_time - last_shot_time >= shoot_cooldown:
                bullet = pygame.Rect(player.centerx - 2, player.top, 5, 15)
                bullets.append(bullet)
                last_shot_time = current_time

        if invincible:
            elapsed = current_time - invincible_start_time
            if elapsed > invincible_duration:
                invincible = False
                player_visible = True
            else:
                if (elapsed // flash_interval) % 2 == 0:
                    player_visible = True
                else:
                    player_visible = False
        else:
            player_visible = True

        handle_enemy_shooting(enemies, enemy_bullets, current_time)
        update_enemy_bullets(enemy_bullets)
        draw_enemy_bullets(screen, enemy_bullets)

        if check_bullet_player_collisions(player, enemy_bullets):
            if not invincible:
                lives -= 1
                invincible = True
                invincible_start_time = current_time
                if lives <= 0:
                    running = False
                else:
                    player.x = SCREEN_WIDTH // 2 - 20
                    player.y = SCREEN_HEIGHT - 70

        if keys[pygame.K_z] and power_shot_ready:
            print("Power shot activated!")
            power_shot_ready = False

        if keys[pygame.K_x] and item_ready:
            print("Item used!")
            item_ready = False

        if keys[pygame.K_c] and force_field_ready:
            print("Force-field activated!")
            force_field_ready = False

        for bullet in bullets[:]:
            bullet.y -= bullet_speed
            if bullet.bottom < 0:
                bullets.remove(bullet)

        for enemy in enemies:
            if isinstance(enemy, PurpleEnemy):
                enemy.player_ref = player

            enemy.update()

        in_formation_enemies = [e for e in enemies if e.in_formation]
        if in_formation_enemies:
            left = min(e.rect.left for e in in_formation_enemies)
            right = max(e.rect.right for e in in_formation_enemies)
            if right + formation_speed * formation_direction > SCREEN_WIDTH or left + formation_speed * formation_direction < 0:
                formation_direction *= -1
                for e in in_formation_enemies:
                    if not isinstance(e, GreenEnemy):
                        e.rect.y += 20 
            else:
                for e in in_formation_enemies:
                    if not isinstance(e, GreenEnemy):
                        e.rect.x += formation_speed * formation_direction

            if len(diving_enemies) < 3:
                potential_divers = [e for e in in_formation_enemies if random.random() < 0.002]
                for diver in potential_divers:
                    diver.start_dive(player.centerx, player.centery)
                    diving_enemies.append(diver)
                    if len(diving_enemies) >= 3:
                        break

            for diver in diving_enemies[:]:
                if diver.path_index >= len(diver.path):
                    diver.return_to_formation()
                    diving_enemies.remove(diver)

            for bullet in bullets[:]:
                for e in enemies[:]:
                    if bullet.colliderect(e.rect):
                        bullets.remove(bullet)
                        if isinstance(e, GreenEnemy):
                            if e.take_hit():
                                enemies.remove(e)
                                score += e.points
                        else:
                            enemies.remove(e)
                            score += e.points
                        break

            for e in enemies:
                if e.rect.colliderect(player):
                    if not invincible:
                        lives -= 1
                        invincible = True
                        invincible_start_time = current_time
                        if lives <= 0:
                            running = False
                        else:
                            player.x = SCREEN_WIDTH // 2 - 20
                            player.y = SCREEN_HEIGHT - 70
                        break

            if not enemies:
                round_number += 1
                enemies = spawn_enemies(round_number)
                formation_speed += 0.2

        if player_visible:
            pygame.draw.rect(screen, white, player)

        for bullet in bullets:
            pygame.draw.rect(screen, white, bullet)
        for e in enemies:
            pygame.draw.rect(screen, e.color, e.rect)

        for i in range(lives):
            pygame.draw.rect(screen, white, (10 + i * 30, SCREEN_HEIGHT - 35, 25, 25))

        score_surf = font.render(f"Score: {score}", True, white)
        screen.blit(score_surf, (SCREEN_WIDTH - 180, SCREEN_HEIGHT - 35))

        round_surf = font.render(f"Round: {round_number}", True, white)
        screen.blit(round_surf, (10, SCREEN_HEIGHT - 60))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Game Over", f"Game Over! Your score: {score}")
    root.destroy()
    sys.exit()

def show_about():
    messagebox.showinfo("About", "From Beyond - Galaga Style.\nEnjoy your challenge!")

def exit_program():
    window.destroy()

window = tk.Tk()
window.title("Welcome Menu")
window.geometry("500x400")
window.resizable(False, False)

label = tk.Label(window, text="Welcome to From Beyond!", font=("Impact", 22))
label.pack(pady=20)

start_button = tk.Button(window, text="Start", width=20, command=start_game)
start_button.pack(pady=5)

about_button = tk.Button(window, text="About", width=20, command=show_about)
about_button.pack(pady=5)

exit_button = tk.Button(window, text="Exit", width=20, command=exit_program)
exit_button.pack(pady=5)

window.mainloop()