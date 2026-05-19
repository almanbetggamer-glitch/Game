"""
Grab Item Game — собирайте предметы за ограниченное время.
Управление: WASD / стрелки. SPACE — старт, R — рестарт, ESC — выход.
"""

import random
import sys

import pygame

# --- Константы окна и игры ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GAME_DURATION = 45  # секунд на раунд

# Размеры объектов
PLAYER_SIZE = 40
ITEM_SIZE = 28
PLAYER_SPEED = 6

# Цвета (RGB)
COLOR_BG = (30, 35, 55)
COLOR_PLAYER = (80, 200, 120)
COLOR_ITEM = (255, 200, 60)
COLOR_TEXT = (240, 240, 250)
COLOR_TEXT_DIM = (160, 165, 190)
COLOR_ACCENT = (100, 180, 255)
COLOR_GAME_OVER_BG = (20, 22, 40)

# Состояния игры
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"


def spawn_random_position(size: int) -> tuple[int, int]:
    """Случайная позиция внутри окна с отступом от краёв."""
    margin = 10
    max_x = SCREEN_WIDTH - size - margin
    max_y = SCREEN_HEIGHT - size - margin
    x = random.randint(margin, max(max_x, margin))
    y = random.randint(margin, max(max_y, margin))
    return x, y


class Player:
    """Игрок — зелёный квадрат с закруглённым видом (круг)."""

    def __init__(self) -> None:
        self.size = PLAYER_SIZE
        self.reset()

    def reset(self) -> None:
        self.x = SCREEN_WIDTH // 2 - self.size // 2
        self.y = SCREEN_HEIGHT // 2 - self.size // 2

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += PLAYER_SPEED

        self.x = max(0, min(SCREEN_WIDTH - self.size, self.x + dx))
        self.y = max(0, min(SCREEN_HEIGHT - self.size, self.y + dy))

    def draw(self, surface: pygame.Surface) -> None:
        center = (self.x + self.size // 2, self.y + self.size // 2)
        pygame.draw.circle(surface, COLOR_PLAYER, center, self.size // 2)
        pygame.draw.circle(surface, (50, 140, 90), center, self.size // 2, 2)


class Item:
    """Собираемый предмет — жёлтый ромб (через polygon)."""

    def __init__(self) -> None:
        self.size = ITEM_SIZE
        self.respawn()

    def respawn(self) -> None:
        self.x, self.y = spawn_random_position(self.size)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, surface: pygame.Surface) -> None:
        cx = self.x + self.size // 2
        cy = self.y + self.size // 2
        half = self.size // 2
        points = [
            (cx, cy - half),
            (cx + half, cy),
            (cx, cy + half),
            (cx - half, cy),
        ]
        pygame.draw.polygon(surface, COLOR_ITEM, points)
        pygame.draw.polygon(surface, (200, 150, 40), points, 2)


class GrabItemGame:
    """Основной класс игры: меню, геймплей, game over."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Grab Item Game")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("arial", 24)

        self.player = Player()
        self.item = Item()
        self.state = STATE_MENU
        self.score = 0
        self.time_left = float(GAME_DURATION)
        self.running = True

    def reset_round(self) -> None:
        """Сброс счёта, таймера и позиций для нового раунда."""
        self.score = 0
        self.time_left = float(GAME_DURATION)
        self.player.reset()
        self.item.respawn()

    def start_game(self) -> None:
        self.reset_round()
        self.state = STATE_PLAYING

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.state == STATE_MENU and event.key == pygame.K_SPACE:
                    self.start_game()
                elif self.state == STATE_GAME_OVER:
                    if event.key == pygame.K_r:
                        self.start_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

    def update_playing(self) -> None:
        keys = pygame.key.get_pressed()
        self.player.update(keys)

        # Таймер: вычитаем прошедшее время в секундах
        dt = self.clock.get_time() / 1000.0
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.state = STATE_GAME_OVER
            return

        # Сбор предмета при пересечении
        if self.player.rect.colliderect(self.item.rect):
            self.score += 1
            self.item.respawn()
            # Не спавнить предмет поверх игрока
            while self.player.rect.colliderect(self.item.rect):
                self.item.respawn()

    def draw_hud(self) -> None:
        """Счёт и оставшееся время во время игры."""
        score_surf = self.font_medium.render(f"Score: {self.score}", True, COLOR_TEXT)
        time_surf = self.font_medium.render(
            f"Time: {int(self.time_left)}s", True, COLOR_ACCENT
        )
        self.screen.blit(score_surf, (20, 15))
        self.screen.blit(time_surf, (SCREEN_WIDTH - time_surf.get_width() - 20, 15))

    def draw_centered_text_block(
        self,
        lines: list[tuple[str, pygame.font.Font, tuple[int, int, int]]],
        start_y: int,
        line_spacing: int = 12,
    ) -> None:
        total_height = sum(font.get_height() + line_spacing for _, font, _ in lines) - line_spacing
        y = start_y - total_height // 2
        for text, font, color in lines:
            surf = font.render(text, True, color)
            rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y + font.get_height() // 2))
            self.screen.blit(surf, rect)
            y += font.get_height() + line_spacing

    def draw_menu(self) -> None:
        self.draw_centered_text_block(
            [
                ("GRAB ITEM GAME", self.font_large, COLOR_ACCENT),
                ("Collect items before time runs out!", self.font_small, COLOR_TEXT_DIM),
                ("", self.font_small, COLOR_TEXT),
                ("Press SPACE to Start", self.font_medium, COLOR_TEXT),
                ("WASD / Arrows — Move", self.font_small, COLOR_TEXT_DIM),
                ("ESC — Quit", self.font_small, COLOR_TEXT_DIM),
            ],
            SCREEN_HEIGHT // 2,
        )

    def draw_game_over(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*COLOR_GAME_OVER_BG, 220))
        self.screen.blit(overlay, (0, 0))

        self.draw_centered_text_block(
            [
                ("GAME OVER", self.font_large, (255, 100, 100)),
                (f"Final Score: {self.score}", self.font_medium, COLOR_TEXT),
                ("", self.font_small, COLOR_TEXT),
                ("Press R to Restart", self.font_medium, COLOR_ACCENT),
                ("Press ESC to Quit", self.font_small, COLOR_TEXT_DIM),
            ],
            SCREEN_HEIGHT // 2,
        )

    def draw_playing(self) -> None:
        self.player.draw(self.screen)
        self.item.draw(self.screen)
        self.draw_hud()

    def draw(self) -> None:
        self.screen.fill(COLOR_BG)
        # Декоративная сетка на фоне
        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(self.screen, (40, 45, 70), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(self.screen, (40, 45, 70), (0, y), (SCREEN_WIDTH, y), 1)

        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_playing()
        elif self.state == STATE_GAME_OVER:
            self.draw_playing()
            self.draw_game_over()

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.handle_events()
            if self.state == STATE_PLAYING:
                self.update_playing()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


def main() -> None:
    game = GrabItemGame()
    game.run()


if __name__ == "__main__":
    main()
