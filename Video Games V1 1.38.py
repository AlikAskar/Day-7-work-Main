import tkinter as tk
from tkinter import messagebox
import pygame
import sys
import random
import math
import time

# --- Constants ---
PLAYER_LIVES = 3
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
ENEMY_WIDTH = 30
ENEMY_HEIGHT = 30
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 30

# --- Enemy types ---
BEE = {"color": (255, 255, 0), "points": 30, "can_shoot": False}
BUTTERFLY = {"color": (0, 0, 255), "points": 40, "can_shoot": True}
BOSS = {"color": (128, 0, 128), "points": 50, "can_shoot": True}
RED = {"color": (255, 0, 0), "points": 60, "can_shoot": True}

class Enemy:
    def __init__(self, start_x, start_y, target_x, target_y, enemy_type):
        self.rect = pygame.Rect(start_x, start_y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.color = enemy_type["color"]
        self.points = enemy_type["points"]
        self.can_shoot = enemy_type["can_shoot"]
        self.type = enemy_type
        self.in_formation = False
        self.returning = False
        self.looping = False
        self.path = self.generate_entry_path((start_x, start_y), (target_x, target_y))
        self.path_index = 0
        self.original_pos = (target_x, target_y)
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
            self.rect.x, self.rect.y = self.original_pos

    def start_dive(self, player_x, player_y):
        self.returning = False
        self.looping = False
        if self.type == BUTTERFLY:
            offset_x = random.choice([-150, 150])
            dive_target = (player_x + offset_x, SCREEN_HEIGHT + 100)
        else:
            dive_target = (player_x, SCREEN_HEIGHT + 100)
        self.path = self.generate_entry_path((self.rect.x, self.rect.y), dive_target)
        self.path_index = 0
        self.in_formation = False

    def loop_from_bottom(self):
        self.looping = True
        start = (self.rect.x, -100)
        self.path = self.generate_entry_path((self.rect.x, SCREEN_HEIGHT + 50), start)
        self.path_index = 0

    def return_to_formation(self):
        self.returning = True
        start = (random.randint(0, SCREEN_WIDTH), -100)
        self.path = self.generate_entry_path(start, self.original_pos)
        self.path_index = 0

    def update_dive(self):
        if self.path_index < len(self.path):
            self.rect.x, self.rect.y = map(int, self.path[self.path_index])
            self.path_index += 1
        else:
            if self.looping:
                self.return_to_formation()
                self.looping = False
            elif not self.returning and self.rect.bottom >= SCREEN_HEIGHT:
                self.loop_from_bottom()
            elif self.returning:
                self.in_formation = True
                self.returning = False
                self.rect.x, self.rect.y = self.original_pos

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

def show_game_over(score, round_count):
    over = tk.Tk()
    over.title("Game Over")
    over.geometry("500x400")
    over.configure(bg="black")

    title = tk.Label(over, text="GAME OVER", font=("Impact", 40), fg="red", bg="black")
    title.pack(pady=30)

    score_label = tk.Label(over, text=f"Final Score: {score}\nRound Reached: {round_count}",
                           font=("Arial", 18), fg="white", bg="black")
    score_label.pack(pady=20)

    def back_to_menu():
        over.destroy()
        show_menu()

    button = tk.Button(over, text="Return to Menu", font=("Arial", 16), bg="gray", fg="white", command=back_to_menu)
    button.pack(pady=30)

    over.mainloop()

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
    enemy_bullets = []
    bullet_speed = 10
    enemy_bullet_speed = 6
    shoot_cooldown = 500
    enemy_shoot_interval = 2000  # Slower shooting
    last_shot_time = pygame.time.get_ticks()
    last_enemy_shoot_time = pygame.time.get_ticks()

    enemies = create_wave()
    formation_speed = 1.5

    lives = PLAYER_LIVES
    score = 0
    diving_enemies = []

    wave_count = 0
    round_count = 1
    max_divers = 3

    player_alive = True
    invincible = False
    invincible_start_time = 0
    enemies_returning = False
    paused = False

    pattern_state = {"direction": 1}

    while True:
        screen.fill(black)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                paused = not paused

        # Respawn invincibility logic
        if invincible and current_time - invincible_start_time >= 3000:
            invincible = False

        keys = pygame.key.get_pressed()
        if player_alive and not enemies_returning and not paused and not invincible:
            if keys[pygame.K_LEFT] and player.left > 0:
                player.x -= player_speed
            if keys[pygame.K_RIGHT] and player.right < SCREEN_WIDTH:
                player.x += player_speed
            if keys[pygame.K_UP] and player.top > SCREEN_HEIGHT - 200:
                player.y -= player_speed
            if keys[pygame.K_DOWN] and player.bottom < SCREEN_HEIGHT - 30:
                player.y += player_speed
            if keys[pygame.K_SPACE] and current_time - last_shot_time >= shoot_cooldown:
                bullet = pygame.Rect(player.centerx - 2, player.top, 5, 15)
                bullets.append(bullet)
                last_shot_time = current_time

        # Update bullets
        for bullet in bullets[:]:
            bullet.y -= bullet_speed
            if bullet.bottom < 0:
                bullets.remove(bullet)

        for eb in enemy_bullets[:]:
            eb.y += enemy_bullet_speed
            if eb.top > SCREEN_HEIGHT:
                enemy_bullets.remove(eb)
            elif eb.colliderect(player) and not invincible:
                lives -= 1
                player_alive = False
                bullets.clear()
                diving_enemies.clear()
                enemy_bullets.clear()
                if lives > 0:
                    player.x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
                    player.y = SCREEN_HEIGHT - 70
                    player_alive = True
                    invincible = True
                    invincible_start_time = pygame.time.get_ticks()
                else:
                    pygame.quit()
                    time.sleep(0.5)
                    show_game_over(score, round_count)
                    return
                break

        # Update enemies
        for enemy in enemies:
            if not enemy.in_formation and not enemy.returning:
                enemy.update_entry()
            elif enemy.returning or not enemy.in_formation:
                enemy.update_dive()

        # Move formation
        in_formation_enemies = [e for e in enemies if e.in_formation]
        if in_formation_enemies:
            dx = formation_speed * pattern_state["direction"]
            min_x = min(e.rect.left for e in in_formation_enemies)
            max_x = max(e.rect.right for e in in_formation_enemies)

            if min_x + dx < 0 or max_x + dx > SCREEN_WIDTH:
                pattern_state["direction"] *= -1
                dx = formation_speed * pattern_state["direction"]

            for e in in_formation_enemies:
                e.rect.x += dx
                e.original_pos = (e.rect.x, e.rect.y)

        # Divers logic
        if player_alive and not enemies_returning and len(diving_enemies) < max_divers:
            potential_divers = [e for e in enemies if e.in_formation and e not in diving_enemies]
            random.shuffle(potential_divers)
            needed = max_divers - len(diving_enemies)
            for diver in potential_divers[:needed]:
                diver.start_dive(player.centerx, player.centery)
                diving_enemies.append(diver)

        for diver in diving_enemies[:]:
            if diver.can_shoot and random.randint(0, 1000) < 5:
                bullet = pygame.Rect(diver.rect.centerx - 2, diver.rect.bottom, 5, 15)
                enemy_bullets.append(bullet)
            if diver.path_index >= len(diver.path) and not diver.returning and not diver.looping:
                diver.return_to_formation()
            elif diver.path_index >= len(diver.path) and diver.returning:
                diver.in_formation = True
                diver.returning = False
                diving_enemies.remove(diver)

        # Random formation shooters
        if player_alive and not paused and current_time - last_enemy_shoot_time >= enemy_shoot_interval:
            shooters = [e for e in in_formation_enemies if e.can_shoot]
            if shooters:
                shooter = random.choice(shooters)
                bullet = pygame.Rect(shooter.rect.centerx - 2, shooter.rect.bottom, 5, 15)
                enemy_bullets.append(bullet)
            last_enemy_shoot_time = current_time

        # Handle collisions
        if player_alive:
            for bullet in bullets[:]:
                for e in enemies[:]:
                    if bullet.colliderect(e.rect):
                        bullets.remove(bullet)
                        enemies.remove(e)
                        score += e.points
                        if e in diving_enemies:
                            diving_enemies.remove(e)
                        break

        if not enemies:
            wave_count += 1
            if wave_count % 5 == 0:
                round_count += 1
                max_divers += 2
            enemies = create_wave()
            formation_speed += 0.2
            pattern_state = {"direction": 1}

        # Draw
        if invincible and (current_time // 300) % 2 == 0:
            # Flicker effect
            pass
        else:
            pygame.draw.rect(screen, white, player)

        for bullet in bullets:
            pygame.draw.rect(screen, white, bullet)
        for eb in enemy_bullets:
            pygame.draw.rect(screen, (255, 0, 0), eb)
        for e in enemies:
            pygame.draw.rect(screen, e.color, e.rect)

        for i in range(lives):
            pygame.draw.rect(screen, white, (10 + i * 30, SCREEN_HEIGHT - 35, 25, 25))

        status_text = f"Score: {score}  Round: {round_count}  Wave: {wave_count}"
        score_surf = font.render(status_text, True, white)
        screen.blit(score_surf, (SCREEN_WIDTH - 460, SCREEN_HEIGHT - 35))

        pygame.display.flip()
        clock.tick(60)

def show_about():
    messagebox.showinfo("About", "From Beyond - Galaga Style.\nEnjoy your classic challenge!\nCreated by Keenan, Rassul, Max, and Nate.")

def exit_program():
    window.destroy()

def show_menu():
    global window
    window = tk.Tk()
    window.title("Welcome Menu")
    window.geometry("700x600")
    window.configure(bg="black")
    window.resizable(False, False)

    label = tk.Label(window, text="FROM BEYOND", font=("Impact", 42), fg="red", bg="black")
    label.pack(pady=30)

    subtitle = tk.Label(window, text="Galaga-style Arcade Shooter", font=("Arial", 18), fg="white", bg="black")
    subtitle.pack(pady=10)

    start_button = tk.Button(window, text="Start Game", width=20, height=2, font=("Arial", 14), command=start_game, bg="gray", fg="white")
    start_button.pack(pady=10)

    about_button = tk.Button(window, text="About", width=20, height=2, font=("Arial", 14), command=show_about, bg="gray", fg="white")
    about_button.pack(pady=10)

    exit_button = tk.Button(window, text="Exit", width=20, height=2, font=("Arial", 14), command=exit_program, bg="gray", fg="white")
    exit_button.pack(pady=10)

    controls_label = tk.Label(
        window,
        text="Controls:\nArrows = Move (↑↓ limited)\nSpace = Shoot\nP = Pause/Resume\nEnemies may shoot back!",
        font=("Arial", 12),
        fg="white",
        bg="black",
        justify="center"
    )
    controls_label.pack(side="bottom", pady=30)

    window.mainloop()

if __name__ == "__main__":
    show_menu()
