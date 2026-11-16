import math
import random
import sys
from dataclasses import dataclass, field

import pygame


WIDTH, HEIGHT = 960, 640
FPS = 60
GAME_SECONDS = 60

NIGHT = (8, 14, 29)
NAVY = (14, 24, 47)
NAVY_LIGHT = (27, 44, 76)
COURT = (178, 104, 49)
COURT_LIGHT = (214, 142, 73)
COURT_DARK = (125, 64, 36)
PAINT = (126, 54, 43)
WHITE = (247, 244, 232)
BLACK = (18, 19, 24)
ORANGE = (225, 91, 24)
ORANGE_LIGHT = (251, 131, 43)
GOLD = (255, 207, 72)
GREEN = (83, 204, 123)
RED = (228, 86, 86)
SKIN = (214, 151, 105)
SKIN_LIGHT = (239, 184, 137)
JERSEY = (25, 82, 155)
JERSEY_LIGHT = (50, 124, 209)

COURT_TOP = 142
COURT_BOTTOM = HEIGHT - 38
HOOP_X = 800
HOOP_Y = 238
RIM_RADIUS = 19
BALL_RADIUS = 13


def draw_text(surface, font, text, color, position, anchor="topleft"):
    image = font.render(text, True, color)
    rect = image.get_rect()
    setattr(rect, anchor, position)
    surface.blit(image, rect)


@dataclass
class Ball:
    x: float
    y: float
    vx: float
    vy: float
    active: bool = True
    scored: bool = False
    previous_y: float = 0
    trail: list[tuple[float, float]] = field(default_factory=list)

    def update(self, dt: float) -> None:
        self.previous_y = self.y
        self.trail.append((self.x, self.y))
        if len(self.trail) > 9:
            self.trail.pop(0)
        self.vy += 840 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt


class ShootingGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("3-Point Shooting | Downtown Arena")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.Font(None, 34)
        self.score_font = pygame.font.Font(None, 64)
        self.big_font = pygame.font.Font(None, 48)
        self.body_font = pygame.font.Font(None, 27)
        self.small_font = pygame.font.Font(None, 21)
        self.tiny_font = pygame.font.Font(None, 17)
        self.restart_button = pygame.Rect(WIDTH - 170, 24, 140, 42)
        self.random = random.Random(7)
        self.running = True
        self.reset()

    def reset(self) -> None:
        self.score = 0
        self.shots = 0
        self.balls: list[Ball] = []
        self.aim_angle = 52.0
        self.power = 0.0
        self.charging = False
        self.time_left = float(GAME_SECONDS)
        self.game_over = False
        self.message = "HOLD SPACE TO CHARGE"
        self.message_color = WHITE
        self.message_timer = 3.0
        self.flash_timer = 0.0
        self.player_anim = 0.0
        self.crowd_phase = 0.0

    @property
    def player_pos(self) -> tuple[int, int]:
        return (150, COURT_BOTTOM - 55)

    def shoot(self) -> None:
        if self.game_over:
            return
        px, py = self.player_pos
        radians = math.radians(self.aim_angle)
        speed = 430 + self.power * 520
        self.balls.append(
            Ball(
                px + 28,
                py - 70,
                math.cos(radians) * speed,
                -math.sin(radians) * speed,
                previous_y=py - 70,
            )
        )
        self.shots += 1
        self.message = "SHOT IN THE AIR"
        self.message_color = WHITE
        self.message_timer = 0.7
        self.power = 0
        self.player_anim = 0.28

    def score_ball(self, ball: Ball) -> None:
        ball.scored = True
        ball.active = False
        self.score += 3
        self.message = "SWISH!  +3 POINTS"
        self.message_color = GOLD
        self.message_timer = 1.4
        self.flash_timer = 0.18

    def update_ball(self, ball: Ball, dt: float) -> None:
        if not ball.active:
            return
        ball.update(dt)

        rim_y = HOOP_Y
        passed_down = ball.previous_y < rim_y <= ball.y
        inside_rim = HOOP_X - RIM_RADIUS + 3 < ball.x < HOOP_X + RIM_RADIUS - 3
        near_rim = math.hypot(ball.x - HOOP_X, ball.y - HOOP_Y) < 52
        if ball.vy > 0 and ((passed_down and inside_rim) or (near_rim and ball.y < HOOP_Y + 45)):
            self.score_ball(ball)
            return

        distance = math.hypot(ball.x - HOOP_X, ball.y - HOOP_Y)
        if distance < BALL_RADIUS + RIM_RADIUS and ball.vy > 0:
            ball.vy = -abs(ball.vy) * 0.68
            ball.vx *= 0.82
            ball.y = HOOP_Y - BALL_RADIUS - RIM_RADIUS

        backboard = pygame.Rect(HOOP_X + 40, HOOP_Y - 70, 10, 112)
        if backboard.collidepoint(ball.x + BALL_RADIUS, ball.y):
            ball.vx = -abs(ball.vx) * 0.75
            ball.x = backboard.left - BALL_RADIUS

        if ball.y > COURT_BOTTOM - BALL_RADIUS or ball.x > WIDTH + 50 or ball.x < -50:
            ball.active = False

    def update(self, dt: float) -> None:
        self.crowd_phase += dt
        self.player_anim = max(0, self.player_anim - dt)
        self.flash_timer = max(0, self.flash_timer - dt)
        if not self.game_over:
            self.time_left = max(0, self.time_left - dt)
            if self.time_left <= 0:
                self.game_over = True
                self.message = "BUZZER!  TIME'S UP"
                self.message_color = GOLD
                self.message_timer = 99

        if self.charging and not self.game_over:
            self.power = min(1.0, self.power + dt * 0.9)
        for ball in self.balls:
            self.update_ball(ball, dt)
        self.balls = [ball for ball in self.balls if ball.active]
        self.message_timer = max(0, self.message_timer - dt)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.reset()
            elif event.key == pygame.K_LEFT and not self.game_over:
                self.aim_angle = min(72, self.aim_angle + 2)
            elif event.key == pygame.K_RIGHT and not self.game_over:
                self.aim_angle = max(35, self.aim_angle - 2)
            elif event.key == pygame.K_SPACE and not self.game_over:
                self.charging = True
        elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            if self.charging:
                self.charging = False
                self.shoot()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.restart_button.collidepoint(event.pos):
                self.reset()

    def draw(self) -> None:
        self.screen.fill(NIGHT)
        self.draw_stadium()
        self.draw_header()
        self.draw_court()
        self.draw_hoop()
        self.draw_player()
        for ball in self.balls:
            self.draw_ball(ball)
        self.draw_overlay()
        if self.flash_timer:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 228, 130, round(self.flash_timer * 220)))
            self.screen.blit(flash, (0, 0))
        pygame.display.flip()

    def draw_stadium(self) -> None:
        for y in range(COURT_TOP):
            blend = y / COURT_TOP
            color = tuple(round(NIGHT[i] * (1 - blend) + NAVY[i] * blend) for i in range(3))
            pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))
        pygame.draw.rect(self.screen, NAVY, (0, 91, WIDTH, 51))
        pygame.draw.line(self.screen, (44, 68, 107), (0, 94), (WIDTH, 94), 2)
        pygame.draw.line(self.screen, (5, 9, 20), (0, 140), (WIDTH, 140), 4)

        for row, y in enumerate((106, 122, 136)):
            for x in range(-20, WIDTH + 20, 25):
                sway = math.sin(self.crowd_phase * 1.8 + x * 0.04 + row) * 2
                head = (x + row * 6, round(y + sway))
                color = (54 + (x * 3) % 35, 69 + (x * 5) % 35, 103 + (x * 7) % 35)
                pygame.draw.circle(self.screen, color, head, 5 if row < 2 else 4)
                pygame.draw.line(self.screen, color, (head[0], head[1] + 5), (head[0], head[1] + 11), 3)

        pygame.draw.rect(self.screen, (8, 12, 24), (0, 0, WIDTH, 18))
        for x in range(20, WIDTH, 72):
            pygame.draw.circle(self.screen, (255, 216, 127), (x, 17), 3)

    def draw_header(self) -> None:
        panel = pygame.Surface((WIDTH, 88), pygame.SRCALPHA)
        panel.fill((7, 13, 27, 240))
        self.screen.blit(panel, (0, 0))
        pygame.draw.line(self.screen, (51, 72, 112), (0, 87), (WIDTH, 87), 2)

        draw_text(self.screen, self.title_font, "DOWNTOWN ARENA", WHITE, (28, 17))
        draw_text(self.screen, self.tiny_font, "3-POINT SHOOTOUT  /  ROUND 01", (136, 164, 201), (30, 51))
        pygame.draw.line(self.screen, GOLD, (30, 73), (118, 73), 3)

        pygame.draw.rect(self.screen, (18, 31, 57), (332, 12, 235, 65), border_radius=10)
        pygame.draw.rect(self.screen, (49, 74, 112), (332, 12, 235, 65), 2, border_radius=10)
        draw_text(self.screen, self.tiny_font, "PLAYER SCORE", (155, 179, 213), (449, 20), "midtop")
        draw_text(self.screen, self.score_font, f"{self.score:02d}", GOLD, (449, 42), "midtop")

        seconds = max(0, math.ceil(self.time_left))
        timer_color = RED if seconds <= 10 else WHITE
        draw_text(self.screen, self.tiny_font, "TIME REMAINING", (155, 179, 213), (622, 19))
        draw_text(self.screen, self.big_font, f"{seconds:02d}", timer_color, (622, 35))
        pygame.draw.rect(self.screen, (50, 64, 93), self.restart_button, border_radius=8)
        pygame.draw.rect(self.screen, (92, 113, 149), self.restart_button, 1, border_radius=8)
        draw_text(self.screen, self.small_font, "RESTART  [R]", WHITE, self.restart_button.center, "center")

    def draw_court(self) -> None:
        pygame.draw.rect(self.screen, COURT_DARK, (0, COURT_TOP, WIDTH, COURT_BOTTOM - COURT_TOP))
        for y in range(COURT_TOP, COURT_BOTTOM, 13):
            tone = COURT if (y // 13) % 2 else COURT_LIGHT
            pygame.draw.rect(self.screen, tone, (0, y, WIDTH, 7))
        for x in range(-100, WIDTH + 100, 72):
            pygame.draw.line(self.screen, (154, 82, 43), (x, COURT_TOP), (x + 80, COURT_BOTTOM), 1)

        pygame.draw.rect(self.screen, (229, 164, 94), (0, COURT_TOP, WIDTH, 10))
        pygame.draw.rect(self.screen, COURT_DARK, (0, COURT_BOTTOM - 10, WIDTH, 10))
        pygame.draw.line(self.screen, WHITE, (0, COURT_BOTTOM), (WIDTH, COURT_BOTTOM), 4)
        pygame.draw.line(self.screen, WHITE, (WIDTH - 3, COURT_TOP), (WIDTH - 3, COURT_BOTTOM), 4)
        pygame.draw.line(self.screen, WHITE, (3, COURT_TOP), (3, COURT_BOTTOM), 4)

        paint_rect = pygame.Rect(HOOP_X - 140, HOOP_Y + 18, 140, COURT_BOTTOM - HOOP_Y - 18)
        pygame.draw.rect(self.screen, PAINT, paint_rect)
        pygame.draw.rect(self.screen, (236, 191, 131), paint_rect, 3)
        pygame.draw.rect(self.screen, WHITE, paint_rect, 4)
        pygame.draw.circle(self.screen, WHITE, (HOOP_X - 70, HOOP_Y + 116), 58, 4)
        pygame.draw.line(self.screen, WHITE, (HOOP_X - 140, HOOP_Y + 116), (HOOP_X, HOOP_Y + 116), 3)
        pygame.draw.arc(self.screen, WHITE, (HOOP_X - 385, HOOP_Y - 185, 630, 640), math.radians(270), math.radians(90), 4)
        pygame.draw.circle(self.screen, (231, 183, 117), (HOOP_X - 70, HOOP_Y + 116), 4)

        for x in range(0, WIDTH, 80):
            pygame.draw.line(self.screen, (241, 181, 104), (x, COURT_BOTTOM - 6), (x + 45, COURT_BOTTOM - 6), 2)

    def draw_hoop(self) -> None:
        pole_x = HOOP_X + 65
        pygame.draw.rect(self.screen, (26, 34, 48), (pole_x, HOOP_Y - 65, 17, COURT_BOTTOM - HOOP_Y + 65))
        pygame.draw.rect(self.screen, (66, 78, 93), (pole_x - 8, COURT_BOTTOM - 10, 33, 10), border_radius=3)
        pygame.draw.line(self.screen, (112, 127, 145), (pole_x + 8, HOOP_Y - 65), (HOOP_X + 44, HOOP_Y - 42), 8)

        backboard = pygame.Rect(HOOP_X + 35, HOOP_Y - 73, 10, 112)
        pygame.draw.rect(self.screen, (225, 238, 241), backboard)
        pygame.draw.rect(self.screen, (86, 102, 117), backboard, 2)
        pygame.draw.rect(self.screen, (250, 252, 248), (HOOP_X + 32, HOOP_Y - 38, 6, 48))
        pygame.draw.rect(self.screen, RED, (HOOP_X + 1, HOOP_Y - 31, 35, 31), 3)

        pygame.draw.ellipse(self.screen, (104, 45, 22), (HOOP_X - RIM_RADIUS - 1, HOOP_Y - 1, RIM_RADIUS * 2 + 2, 11))
        pygame.draw.ellipse(self.screen, ORANGE_LIGHT, (HOOP_X - RIM_RADIUS, HOOP_Y - 5, RIM_RADIUS * 2, 10), 4)
        for offset in (-14, -8, -2, 5, 11, 16):
            pygame.draw.line(self.screen, (232, 236, 226), (HOOP_X + offset, HOOP_Y + 4), (HOOP_X + offset // 2, HOOP_Y + 37), 2)
        pygame.draw.arc(self.screen, (232, 236, 226), (HOOP_X - 17, HOOP_Y + 18, 34, 24), 0, math.pi, 2)

    def draw_player(self) -> None:
        px, py = self.player_pos
        lift = round(math.sin(self.player_anim * 18) * 5) if self.player_anim else 0
        shadow = pygame.Surface((110, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (25, 27, 29, 100), (0, 0, 100, 17))
        self.screen.blit(shadow, (px - 50, py + 30))

        pygame.draw.line(self.screen, BLACK, (px - 10, py - 8), (px - 23, py + 38), 11)
        pygame.draw.line(self.screen, BLACK, (px + 10, py - 8), (px + 24, py + 38), 11)
        pygame.draw.line(self.screen, (29, 39, 51), (px - 23, py + 34), (px - 35, py + 39), 8)
        pygame.draw.line(self.screen, (29, 39, 51), (px + 24, py + 34), (px + 37, py + 39), 8)

        jersey = pygame.Rect(px - 25, py - 87 - lift, 50, 62)
        pygame.draw.rect(self.screen, JERSEY, jersey, border_radius=9)
        pygame.draw.rect(self.screen, JERSEY_LIGHT, (px - 20, py - 84 - lift, 8, 56), border_radius=4)
        pygame.draw.line(self.screen, WHITE, (px - 16, py - 83 - lift), (px - 10, py - 26 - lift), 3)
        pygame.draw.line(self.screen, WHITE, (px + 16, py - 83 - lift), (px + 10, py - 26 - lift), 3)
        draw_text(self.screen, self.small_font, "3", WHITE, (px, py - 61 - lift), "center")

        pygame.draw.circle(self.screen, SKIN, (px, py - 105 - lift), 18)
        pygame.draw.arc(self.screen, BLACK, (px - 18, py - 121 - lift, 36, 27), math.pi, math.tau, 5)
        pygame.draw.line(self.screen, SKIN_LIGHT, (px - 15, py - 35 - lift), (px - 31, py - 8), 9)
        pygame.draw.line(self.screen, SKIN_LIGHT, (px + 15, py - 35 - lift), (px + 31, py - 61 - lift), 9)
        pygame.draw.circle(self.screen, SKIN_LIGHT, (px + 31, py - 61 - lift), 6)
        pygame.draw.line(self.screen, (243, 244, 239), (px - 22, py - 82 - lift), (px - 30, py - 59 - lift), 4)

        if not self.balls and not self.game_over:
            radians = math.radians(self.aim_angle)
            start = (px + 33, py - 68 - lift)
            end = (px + int(math.cos(radians) * 155), py - 70 - int(math.sin(radians) * 155))
            pygame.draw.line(self.screen, (255, 232, 144), start, end, 2)
            pygame.draw.circle(self.screen, (255, 232, 144), end, 4)

    def draw_ball(self, ball: Ball) -> None:
        for index, (trail_x, trail_y) in enumerate(ball.trail):
            alpha = round(18 + index * 6)
            trail = pygame.Surface((BALL_RADIUS * 3, BALL_RADIUS * 3), pygame.SRCALPHA)
            pygame.draw.circle(trail, (255, 185, 86, alpha), (BALL_RADIUS * 1.5, BALL_RADIUS * 1.5), max(2, index // 2))
            self.screen.blit(trail, (round(trail_x - BALL_RADIUS * 1.5), round(trail_y - BALL_RADIUS * 1.5)))

        center = (round(ball.x), round(ball.y))
        pygame.draw.circle(self.screen, (122, 43, 16), center, BALL_RADIUS + 2)
        pygame.draw.circle(self.screen, ORANGE_LIGHT, center, BALL_RADIUS)
        pygame.draw.arc(self.screen, BLACK, (center[0] - BALL_RADIUS, center[1] - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2), math.radians(25), math.radians(205), 2)
        pygame.draw.arc(self.screen, BLACK, (center[0] - BALL_RADIUS, center[1] - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2), math.radians(205), math.radians(385), 2)
        pygame.draw.line(self.screen, BLACK, (center[0] - 10, center[1] + 4), (center[0] + 10, center[1] - 4), 2)

    def draw_overlay(self) -> None:
        if self.charging:
            bar = pygame.Rect(28, HEIGHT - 79, 245, 17)
            pygame.draw.rect(self.screen, (46, 34, 32), bar, border_radius=9)
            pygame.draw.rect(self.screen, GOLD if self.power < 0.8 else RED, (bar.left, bar.top, round(bar.width * self.power), bar.height), border_radius=9)
            draw_text(self.screen, self.small_font, "SHOT POWER", WHITE, (28, HEIGHT - 107))
            draw_text(self.screen, self.tiny_font, f"{round(self.power * 100):02d}%", WHITE, (281, HEIGHT - 80), "midleft")

        controls = "← / → AIM     HOLD SPACE + RELEASE TO SHOOT"
        draw_text(self.screen, self.small_font, controls, (240, 218, 180), (28, 111))
        if self.message_timer > 0:
            draw_text(self.screen, self.body_font, self.message, self.message_color, (WIDTH // 2, 112), "midtop")
        if self.game_over:
            panel = pygame.Surface((470, 208), pygame.SRCALPHA)
            panel.fill((8, 14, 29, 242))
            pygame.draw.rect(panel, (87, 107, 145, 255), panel.get_rect(), 2, border_radius=14)
            self.screen.blit(panel, panel.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            draw_text(self.screen, self.big_font, "FINAL BUZZER", GOLD, (WIDTH // 2, HEIGHT // 2 - 66), "center")
            draw_text(self.screen, self.body_font, f"{self.score} POINTS  /  {self.shots} SHOTS", WHITE, (WIDTH // 2, HEIGHT // 2 - 15), "center")
            draw_text(self.screen, self.small_font, "PRESS R OR CLICK RESTART TO PLAY AGAIN", (180, 201, 230), (WIDTH // 2, HEIGHT // 2 + 38), "center")

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    ShootingGame().run()
