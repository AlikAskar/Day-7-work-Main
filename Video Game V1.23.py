import tkinter as tk
from tkinter import messagebox
import pygame
import sys
import random
import math

# --- Constants ---
PLAYER_LIVES = 3
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
ENEMY_WIDTH = 25  # Smaller enemy size
ENEMY_HEIGHT = 25
PLAYER_WIDTH = 30  # Smaller player size
PLAYER_HEIGHT = 30

# --- Enemy types ---
BEE = {"color": (255, 255, 0), "points": 30}
BUTTERFLY = {"color": (0, 0, 255), "points": 40}
BOSS = {"color": (128, 0, 128), "points": 50}
RED = {"color": (255, 0, 0), "points": 60}

# --- Enemy class ---
class Enemy:
    def __init__(self, start_x, start_y, target_x, target_y, enemy_type):
        self.rect = pygame.Rect(start_x, start_y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.color = enemy_type["color"]
        self.points = enemy_type["points"]
        self.in_formation = False
        self.returning = False
        self.path = self.generate_entry_path((start_x, start_y), (target_x, target_y))
        self.path_index = 0
        self.original_pos = (target_x, target_y)  # Fixed original formation position
        self.target_pos = (target_x, target_y)    # Moves with formation

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

    def start_dive(self, player_x, player_y):
        self.returning = False
        dive_target = (player_x, SCREEN_HEIGHT + 100)
        self.path = self.generate_entry_path((self.rect.x, self.rect.y), dive_target)
        self.path_index = 0
        self.in_formation = False

    def return_to_formation(self):
        self.returning = True
        self.path = self.generate_entry_path((self.rect.x, self.rect.y), self.original_pos)
        self.path_index = 0

    def update_dive(self):
        if self.path_index < len(self.path):
            self.rect.x, self.rect.y = map(int, self.path[self.path_index])
            self.path_index += 1
        else:
            if self.returning:
                self.in_formation = True
                self.returning = False

# --- Formation movement patterns ---

def pattern_simple(speed, time, state):
    direction = state.get("direction", 1)
    state["direction"] = direction
    return speed * direction, 0

def pattern_sine(speed, time, state):
    amplitude = 50
    freq = 0.01
    dx = amplitude * math.sin(freq * time)
    dx_prev = state.get("prev_dx", 0)
    state["prev_dx"] = dx
    return dx - dx_prev, 0

def pattern_circle(speed, time, state):
    radius = 30
    freq = 0.01
    angle = freq * time
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    prev_pos = state.get("prev_pos", (0, 0))
    dx = x - prev_pos[0]
    dy = y - prev_pos[1]
    state["prev_pos"] = (x, y)
    return dx, dy

patterns = [pattern_simple, pattern_sine, pattern_circle]

def create_wave():
    enemies = []
    start_y = 80
    rows = 5
    cols = 6

    x_spacing = ENEMY_WIDTH + 20
    y_spacing = ENEMY_HEIGHT + 20

    formation_width = cols * x_spacing - 20
    left_offset = (SCREEN_WIDTH - formation_width) // 2

    for row in range(rows):
        for col in range(cols):
            x = left_offset + col * x_spacing
            y = start_y + row * y_spacing

            if row == 0:
                enemy_type = BOSS
            elif row == 1:
                enemy_type = RED
            elif row == 2:
                enemy_type = BUTTERFLY
            else:
                enemy_type = BEE

            enemy = Enemy(random.randint(-400, SCREEN_WIDTH + 400), -100, x, y, enemy_type)
            enemies.append(enemy)

    return enemies

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def start_game():
    window.destroy()
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("From Beyond")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 30)

    black = (0, 0, 0)
    white = (255, 255, 255)

    player = pygame.Rect(SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2, SCREEN_HEIGHT - 70, PLAYER_WIDTH, PLAYER_HEIGHT)
    player_speed = 5
    bullets = []
    bullet_speed = 10
    shoot_cooldown = 500
    last_shot_time = pygame.time.get_ticks()

    enemies = create_wave()
    formation_speed = 1.5

    lives = PLAYER_LIVES
    score = 0
    diving_enemies = []

    wave_count = 0
    round_count = 1
    max_divers = 3

    player_alive = True
    waiting_for_respawn = False
    enemies_returning = False

    current_pattern = 0
    pattern_state = {"direction": 1, "time": 0, "prev_dx": 0, "prev_pos": (0, 0)}

    while True:
        screen.fill(black)
        current_time = pygame.time.get_ticks()
        pattern_state["time"] += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if waiting_for_respawn:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    if lives > 0:
                        player_alive = True
                        waiting_for_respawn = False
                        player.x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
                        bullets.clear()
                        diving_enemies.clear()
                    else:
                        pygame.quit()
                        import tkinter as tk2
                        root = tk2.Tk()
                        root.withdraw()
                        messagebox.showinfo("Game Over", f"Game Over! Your score: {score}\nYou reached Round: {round_count}")
                        root.destroy()
                        sys.exit()

        keys = pygame.key.get_pressed()

        if player_alive and not waiting_for_respawn and not enemies_returning:
            if keys[pygame.K_LEFT] and player.left > 0:
                player.x -= player_speed
            if keys[pygame.K_RIGHT] and player.right < SCREEN_WIDTH:
                player.x += player_speed
            if keys[pygame.K_SPACE]:
                if current_time - last_shot_time >= shoot_cooldown:
                    bullet = pygame.Rect(player.centerx - 2, player.top, 5, 15)
                    bullets.append(bullet)
                    last_shot_time = current_time

        for bullet in bullets[:]:
            bullet.y -= bullet_speed
            if bullet.bottom < 0:
                bullets.remove(bullet)

        for enemy in enemies:
            if enemies_returning:
                if not enemy.in_formation and not enemy.returning:
                    enemy.return_to_formation()
                enemy.update_dive()
            else:
                if not enemy.in_formation and not enemy.returning:
                    enemy.update_entry()
                elif enemy.returning or not enemy.in_formation:
                    enemy.update_dive()

        if enemies_returning:
            if all(e.in_formation for e in enemies):
                enemies_returning = False
                waiting_for_respawn = True

        # Formation movement
        if player_alive and not waiting_for_respawn and not enemies_returning:
            in_formation_enemies = [e for e in enemies if e.in_formation]
            if in_formation_enemies:
                dx, dy = patterns[current_pattern](formation_speed, pattern_state["time"], pattern_state)

                min_x = min(e.rect.left for e in in_formation_enemies)
                max_x = max(e.rect.right for e in in_formation_enemies)
                min_y = min(e.rect.top for e in in_formation_enemies)
                max_y = max(e.rect.bottom for e in in_formation_enemies)

                # Clamp movement to keep formation inside screen
                if min_x + dx < 0:
                    dx = -min_x
                    if current_pattern == 0:
                        pattern_state["direction"] *= -1
                elif max_x + dx > SCREEN_WIDTH:
                    dx = SCREEN_WIDTH - max_x
                    if current_pattern == 0:
                        pattern_state["direction"] *= -1

                max_allowed_y = SCREEN_HEIGHT - 150
                if max_y + dy > max_allowed_y:
                    dy = max_allowed_y - max_y
                if min_y + dy < 50:
                    dy = 50 - min_y

                for e in in_formation_enemies:
                    e.rect.x += dx
                    e.rect.y += dy
                    # Clamp individual enemy inside screen just in case
                    e.rect.x = clamp(e.rect.x, 0, SCREEN_WIDTH - ENEMY_WIDTH)
                    e.rect.y = clamp(e.rect.y, 50, max_allowed_y)
                    e.target_pos = (e.rect.x, e.rect.y)  # This moves but original_pos remains fixed

                if (dx == 0 or dy == 0) and current_pattern != 0:
                    pattern_state["time"] = 0

        # Start dives
        if player_alive and not waiting_for_respawn and not enemies_returning:
            if len(diving_enemies) < max_divers:
                potential_divers = [e for e in enemies if e.in_formation and e not in diving_enemies]
                random.shuffle(potential_divers)
                needed = max_divers - len(diving_enemies)
                for diver in potential_divers[:needed]:
                    diver.start_dive(player.centerx, player.centery)
                    diving_enemies.append(diver)

        # Handle diving enemies returning
        for diver in diving_enemies[:]:
            if diver.path_index >= len(diver.path) and not diver.returning:
                if diver.rect.y > SCREEN_HEIGHT:
                    diver.rect.y = -ENEMY_HEIGHT - random.randint(0, 100)
                    diver.path_index = 0
                    diver.return_to_formation()
                else:
                    diver.return_to_formation()
            elif diver.path_index >= len(diver.path) and diver.returning:
                diver.in_formation = True
                diver.returning = False
                if diver in diving_enemies:
                    diving_enemies.remove(diver)

        # Collision detection
        if player_alive and not enemies_returning:
            for bullet in bullets[:]:
                for e in enemies[:]:
                    if bullet.colliderect(e.rect):
                        bullets.remove(bullet)
                        enemies.remove(e)
                        score += e.points
                        if e in diving_enemies:
                            diving_enemies.remove(e)
                        break

            for e in enemies:
                if e.rect.colliderect(player):
                    lives -= 1
                    player_alive = False
                    enemies_returning = True
                    waiting_for_respawn = False
                    bullets.clear()
                    diving_enemies.clear()
                    break

        # New waves
        if not enemies and not waiting_for_respawn and not enemies_returning:
            wave_count += 1
            if wave_count % 5 == 0:
                round_count += 1
                max_divers += 2
            enemies = create_wave()
            formation_speed += 0.2
            current_pattern = (current_pattern + 1) % len(patterns)
            pattern_state = {"direction": 1, "time": 0, "prev_dx": 0, "prev_pos": (0, 0)}

        # Drawing
        pygame.draw.rect(screen, white, player)
        for bullet in bullets:
            pygame.draw.rect(screen, white, bullet)
        for e in enemies:
            pygame.draw.rect(screen, e.color, e.rect)

        for i in range(lives):
            pygame.draw.rect(screen, white, (10 + i * 30, SCREEN_HEIGHT - 35, 25, 25))

        status_text = f"Score: {score}  Round: {round_count}  Wave: {wave_count}"
        if enemies_returning:
            status_text += "  Enemies returning to formation..."
        elif waiting_for_respawn:
            status_text += "  PRESS ENTER TO RESPAWN"

        score_surf = font.render(status_text, True, white)
        screen.blit(score_surf, (SCREEN_WIDTH - 460, SCREEN_HEIGHT - 35))

        pygame.display.flip()
        clock.tick(60)

# --- Tkinter menu ---
def show_about():
    messagebox.showinfo("About", "From Beyond - Galaga Style.\nEnjoy your classic challenge!")

def exit_program():
    window.destroy()

window = tk.Tk()
window.title("Welcome Menu")
window.geometry("600x500")
window.resizable(False, False)

label = tk.Label(window, text="Welcome to From Beyond!", font=("Impact", 22))
label.pack(pady=20)

start_button = tk.Button(window, text="Start", width=20, command=start_game)
start_button.pack(pady=5)

about_button = tk.Button(window, text="About", width=20, command=show_about)
about_button.pack(pady=5)

exit_button = tk.Button(window, text="Exit", width=20, command=exit_program)
exit_button.pack(pady=5)

controls_label = tk.Label(
    window,
    text="Controls:\nArrow Keys = Move\nSpace Bar = Shoot\nEnter = Respawn",
    font=("Arial", 12),
    justify="center"
)
controls_label.pack(side="bottom", pady=20)

window.mainloop()
