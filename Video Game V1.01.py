import tkinter as tk
from tkinter import messagebox
import pygame
import sys
import random

# --- Constants ---
PLAYER_LIVES = 3
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
ENEMY_WIDTH = 35
ENEMY_HEIGHT = 35

# --- Enemy types ---
BEE = {"color": (255, 255, 0), "points": 30}
BUTTERFLY = {"color": (0, 0, 255), "points": 40}
BOSS = {"color": (128, 0, 128), "points": 50}

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
        self.target_pos = (target_x, target_y)

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
        self.path = self.generate_entry_path((self.rect.x, self.rect.y), self.target_pos)
        self.path_index = 0

    def update_dive(self):
        if self.path_index < len(self.path):
            self.rect.x, self.rect.y = map(int, self.path[self.path_index])
            self.path_index += 1
        else:
            if self.returning:
                self.in_formation = True
                self.returning = False

def create_wave():
    enemies = []
    start_y = 80
    rows = 5
    cols = 6

    for row in range(rows):
        for col in range(cols):
            x = 70 + col * (ENEMY_WIDTH + 10)
            y = start_y + row * (ENEMY_HEIGHT + 10)

            # Assign type by row (classic Galaga pattern)
            if row == 0:
                enemy_type = BOSS
            elif row in [1, 2]:
                enemy_type = BUTTERFLY
            else:
                enemy_type = BEE

            enemy = Enemy(random.randint(-400, SCREEN_WIDTH + 400), -100, x, y, enemy_type)
            enemies.append(enemy)

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
    bullet_speed = 10
    shoot_cooldown = 500
    last_shot_time = pygame.time.get_ticks()

    enemies = create_wave()
    formation_direction = 1
    formation_speed = 1.5

    lives = PLAYER_LIVES
    score = 0
    diving_enemies = []

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
        if keys[pygame.K_SPACE]:
            if current_time - last_shot_time >= shoot_cooldown:
                bullet = pygame.Rect(player.centerx - 2, player.top, 5, 15)
                bullets.append(bullet)
                last_shot_time = current_time

        # Update bullets
        for bullet in bullets[:]:
            bullet.y -= bullet_speed
            if bullet.bottom < 0:
                bullets.remove(bullet)

        # Update enemies
        for enemy in enemies:
            if not enemy.in_formation and not enemy.returning:
                enemy.update_entry()
            elif enemy.returning or not enemy.in_formation:
                enemy.update_dive()

        # Move formation
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

        # Start dives
        if len(diving_enemies) < 3:
            potential_divers = [e for e in in_formation_enemies if random.random() < 0.002]
            for diver in potential_divers:
                diver.start_dive(player.centerx, player.centery)
                diving_enemies.append(diver)
                if len(diving_enemies) >= 3:
                    break

        # Handle returning
        for diver in diving_enemies[:]:
            if diver.path_index >= len(diver.path):
                diver.return_to_formation()
                diving_enemies.remove(diver)

        # Check collisions
        for bullet in bullets[:]:
            for e in enemies[:]:
                if bullet.colliderect(e.rect):
                    bullets.remove(bullet)
                    enemies.remove(e)
                    score += e.points
                    break

        # Player collision
        for e in enemies:
            if e.rect.colliderect(player):
                lives -= 1
                if lives <= 0:
                    running = False
                else:
                    player.x = SCREEN_WIDTH // 2 - 20
                    break

        # New wave if cleared
        if not enemies:
            enemies = create_wave()
            formation_speed += 0.2  # Increase difficulty

        # Draw
        pygame.draw.rect(screen, white, player)
        for bullet in bullets:
            pygame.draw.rect(screen, white, bullet)
        for e in enemies:
            pygame.draw.rect(screen, e.color, e.rect)

        for i in range(lives):
            pygame.draw.rect(screen, white, (10 + i * 30, SCREEN_HEIGHT - 35, 25, 25))

        score_surf = font.render(f"Score: {score}", True, white)
        screen.blit(score_surf, (SCREEN_WIDTH - 180, SCREEN_HEIGHT - 35))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    import tkinter as tk2
    root = tk2.Tk()
    root.withdraw()
    messagebox.showinfo("Game Over", f"Game Over! Your score: {score}")
    root.destroy()
    sys.exit()

# --- Tkinter menu ---
def show_about():
    messagebox.showinfo("About", "From Beyond - Galaga Style.\nEnjoy your classic challenge!")

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
