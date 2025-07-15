import tkinter as tk
from tkinter import messagebox
import pygame
import sys
import random
import math

# --- Constants ---
PLAYER_LIVES = 3
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
ENEMY_WIDTH = 35
ENEMY_HEIGHT = 35
ENEMY_BULLET_COLOR = (173, 216, 230)  # Light blue

# --- Enemy Base Class ---
# (Classes unchanged up to here)

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
        self.shoot_cooldown = 2500  # 2.5 seconds in milliseconds
        self.last_shot_time = 0  # Track last shot time per enemy

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

    def update_entry(self):
        if self.path_index < len(self.path):
            self.rect.x, self.rect.y = map(int, self.path[self.path_index])
            self.path_index += 1
        else:
            self.in_formation = True

    def update_dive(self):
        pass

    def start_dive(self, player_x, player_y):
        pass

    def return_to_formation(self):
        self.returning = True
        self.path = self.generate_entry_path((self.rect.x, self.rect.y), self.target_pos)
        self.path_index = 0

class RedEnemy(Enemy):
    def __init__(self, sx, sy, tx, ty, round_num):
        super().__init__(sx, sy, tx, ty, {"color": (255, 0, 0), "points": 20})
        base_speed = 1 + 0.05 * round_num
        self.speed = random.uniform(max(0.5, base_speed - 0.5), base_speed + 0.5)  # Vary speed +-0.5
        self.shoot_cooldown = 4000  # 4 seconds cooldown
        self.last_shot_time = pygame.time.get_ticks() - random.randint(0, self.shoot_cooldown)
        self.zigzag = random.choice([True, False])
        self.zigzag_amplitude = 15
        self.zigzag_frequency = 0.1
        self.zigzag_phase = random.uniform(0, 2 * math.pi)

    def update_dive(self):
        self.rect.y += int(self.speed)
        if self.zigzag:
            # Zigzag horizontal movement using sine wave
            offset_x = int(self.zigzag_amplitude * math.sin(self.zigzag_frequency * self.rect.y + self.zigzag_phase))
            self.rect.x = self.target_pos[0] + offset_x

    def shoot(self, bullets):
        current_time = pygame.time.get_ticks()
        if self.in_formation and (current_time - self.last_shot_time) >= self.shoot_cooldown:
            bullet = pygame.Rect(self.rect.centerx - 2, self.rect.bottom, 4, 12)
            bullets.append((bullet, (0, 6), ENEMY_BULLET_COLOR))
            self.last_shot_time = current_time

class GreenEnemy(Enemy):
    def __init__(self, sx, sy, tx, ty, round_num):
        super().__init__(sx, sy, tx, ty, {"color": (0, 255, 0), "points": 35})
        self.hp = 2
        self.speed = min(1 + 0.03 * round_num, 1.8)
        self.center = (tx, ty)  # center for pattern
        self.pattern_type = random.choice(['circle', 'square', 'triangle', 'diamond'])
        self.pattern_points = self.generate_pattern_points(self.pattern_type, round_num)
        self.pattern_index = random.randint(0, len(self.pattern_points) - 1)
        self.shoot_cooldown = 4000
        self.last_shot_time = pygame.time.get_ticks() - random.randint(0, self.shoot_cooldown)

        # Add these for circular motion in update_dive
        self.phase_angle = 0
        self.phase_speed = 0.05  # You can adjust this for rotation speed
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise
        self.radius = 40 + round_num * 5  # Same as size for circular path radius
 
    def generate_pattern_points(self, pattern_type, round_num):
        size = 40 + round_num * 5
        if pattern_type == 'circle':
            # 20 points around circle
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
                (self.center[0] - s, self.center[1] + h/2),
                (self.center[0] + s, self.center[1] + h/2),
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
        if self.in_formation and self.pattern_points:
            # Move toward next point in pattern_points
            target = self.pattern_points[self.pattern_index]
            dx = target[0] - self.rect.centerx
            dy = target[1] - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 2:
                self.pattern_index = (self.pattern_index + 1) % len(self.pattern_points)
            else:
                step_x = self.speed * dx / dist
                step_y = self.speed * dy / dist
                self.rect.x += int(step_x)
                self.rect.y += int(step_y)

    def shoot(self, bullets):
        current_time = pygame.time.get_ticks()
        if self.in_formation and (current_time - self.last_shot_time) >= self.shoot_cooldown:
            left_bullet = pygame.Rect(self.rect.centerx - 4, self.rect.bottom, 4, 12)
            right_bullet = pygame.Rect(self.rect.centerx + 4, self.rect.bottom, 4, 12)
            bullets.append((left_bullet, (-3, 6), ENEMY_BULLET_COLOR))
            bullets.append((right_bullet, (3, 6), ENEMY_BULLET_COLOR))
            self.last_shot_time = current_time
    
    def update_dive(self):
        if self.in_formation:
        # Move in a circular path, direction determines clockwise or counterclockwise
            self.phase_angle += self.direction * self.phase_speed
            self.rect.x = int(self.center[0] + self.radius * math.cos(self.phase_angle))
            self.rect.y = int(self.center[1] + self.radius * math.sin(self.phase_angle))

    def take_hit(self):
        self.hp -= 1
        return self.hp <= 0

class PurpleEnemy(Enemy):
    def __init__(self, sx, sy, tx, ty, round_num):
        super().__init__(sx, sy, tx, ty, {"color": (128, 0, 255), "points": 30})
        self.speed = min(1 + 0.04 * round_num, 2.0)
        self.phase_angle = 0
        self.radius = 40  # example radius for circular motion
        self.center = (tx, ty)
        self.direction = 1  # clockwise or counterclockwise
        self.phase_speed = 0.05 * self.speed
        self.shoot_cooldown = 2500  # can adjust as needed
        self.last_shot_time = pygame.time.get_ticks() - random.randint(0, self.shoot_cooldown)

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
            # Circular motion for dive
            self.phase_angle += 0.05 * self.speed  # speed controls angular velocity
            self.rect.x = int(self.center[0] + self.radius * math.cos(self.phase_angle))
            self.rect.y = int(self.center[1] + self.radius * math.sin(self.phase_angle))
        elif self.path_index < len(self.path):
            # Following dive path
            self.rect.x, self.rect.y = map(int, self.path[self.path_index])
            self.path_index += int(2 * self.speed)
        else:
            if self.returning:
                self.in_formation = True
                self.returning = False

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
            # Circular motion for dive
            self.phase_angle += 0.05 * self.speed  # speed controls angular velocity
            self.rect.x = int(self.center[0] + self.radius * math.cos(self.phase_angle))
            self.rect.y = int(self.center[1] + self.radius * math.sin(self.phase_angle))

    def shoot(self, bullets, current_time):
        if self.in_formation and (current_time - self.last_shot_time) >= self.shoot_cooldown:
            left_bullet = pygame.Rect(self.rect.centerx - 4, self.rect.bottom, 4, 12)
            right_bullet = pygame.Rect(self.rect.centerx + 4, self.rect.bottom, 4, 12)
            bullets.append((left_bullet, (-3, 6), ENEMY_BULLET_COLOR))
            bullets.append((right_bullet, (3, 6), ENEMY_BULLET_COLOR))
            self.last_shot_time = current_time

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

# --- Enemy Shooting Handler with Current Time ---
def handle_enemy_shooting(enemies, enemy_bullets, current_time):
    for enemy in enemies:
        if hasattr(enemy, "shoot"):
            # Pass current_time to shoot method, or only enemy_bullets if shoot expects just that
            try:
                enemy.shoot(enemy_bullets, current_time)
            except TypeError:
                # fallback if enemy.shoot doesn't require current_time
                enemy.shoot(enemy_bullets)

def spawn_enemies(round_num):
    enemies = []
    cols = 5
    rows = 3
    spacing_x = ENEMY_WIDTH + 15
    spacing_y = ENEMY_HEIGHT + 15
    start_x = (SCREEN_WIDTH - (cols - 1) * spacing_x) // 2
    start_y = 50

    for row in range(rows):
        for col in range(cols):
            sx = random.randint(0, SCREEN_WIDTH)
            sy = -ENEMY_HEIGHT - random.randint(20, 100)

            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-10, 10)
            tx = start_x + col * spacing_x + offset_x
            ty = start_y + row * spacing_y + offset_y

            if row == 0:
                enemy = RedEnemy(sx, sy, tx, ty, round_num)
            elif row == 1:
                enemy = PurpleEnemy(sx, sy, tx, ty, round_num)
            else:
                enemy = GreenEnemy(sx, sy, tx, ty, round_num)

            enemies.append(enemy)
    return enemies

# --- Tkinter Menu and Game Start ---
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

    # Invincibility frame variables
    invincible = False
    invincible_start_time = 0
    invincible_duration = 3000  # 3 seconds in milliseconds
    flash_interval = 200        # flash toggle every 200 ms
    player_visible = True

    running = True
    while running:
        screen.fill(black)
        current_time = pygame.time.get_ticks()

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

        if keys[pygame.K_SPACE]:
            if current_time - last_shot_time >= shoot_cooldown:
                bullet = pygame.Rect(player.centerx - 2, player.top, 5, 15)
                bullets.append(bullet)
                last_shot_time = current_time

        # Handle invincibility and flashing
        if invincible:
            elapsed = current_time - invincible_start_time
            if elapsed > invincible_duration:
                invincible = False
                player_visible = True
            else:
                # Toggle visibility every flash_interval ms
                if (elapsed // flash_interval) % 2 == 0:
                    player_visible = True
                else:
                    player_visible = False
        else:
            player_visible = True

        handle_enemy_shooting(enemies, enemy_bullets, current_time)
        update_enemy_bullets(enemy_bullets)
        draw_enemy_bullets(screen, enemy_bullets)

        # Check for bullet-player collisions, only lose life if not invincible
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
            if not enemy.in_formation and not enemy.returning:
                enemy.update_entry()
            elif enemy.returning:
                enemy.update_entry()
                if enemy.path_index >= len(enemy.path):
                    enemy.in_formation = True
                    enemy.returning = False
            else:
                enemy.update_dive()

        in_formation_enemies = [e for e in enemies if e.in_formation]
        if in_formation_enemies:
            left = min(e.rect.left for e in in_formation_enemies)
            right = max(e.rect.right for e in in_formation_enemies)
            if right + formation_speed * formation_direction > SCREEN_WIDTH or left + formation_speed * formation_direction < 0:
                formation_direction *= -1
                for e in in_formation_enemies:
                    e.rect.y += 20
            else:
                for e in in_formation_enemies:
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

        # Draw player only if visible (for flashing)
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
