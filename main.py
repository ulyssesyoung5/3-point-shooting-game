import asyncio
import math
from dataclasses import dataclass

import pygame


WIDTH, HEIGHT = 960, 640
FPS = 60
GAME_SECONDS = 60

SKY = (28, 39, 68)
COURT = (194, 123, 67)
COURT_LIGHT = (216, 151, 87)
PAINT = (126, 67, 48)
WHITE = (247, 244, 232)
BLACK = (24, 21, 24)
ORANGE = (235, 111, 32)
GOLD = (255, 207, 72)
GREEN = (83, 204, 123)
RED = (228, 86, 86)

COURT_TOP = 150
COURT_BOTTOM = HEIGHT - 38
HOOP_X = 800
HOOP_Y = 238
RIM_RADIUS = 18
BALL_RADIUS = 12


@dataclass
class Ball:
    x: float
    y: float
    vx: float
    vy: float
    active: bool = True
    scored: bool = False
    previous_y: float = 0

    def update(self, dt: float) -> None:
        self.previous_y = self.y
        self.vy += 840 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt


class ShootingGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("3-Point Shooting")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.Font(None, 42)
        self.score_font = pygame.font.Font(None, 64)
        self.body_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        self.restart_button = pygame.Rect(WIDTH - 170, 24, 140, 42)
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
        self.message = "Hold SPACE to charge, release to shoot"
        self.message_color = WHITE
        self.message_timer = 3.0

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
        self.message = "Nice shot!"
        self.message_color = WHITE
        self.message_timer = 0.7
        self.power = 0

    def score_ball(self, ball: Ball) -> None:
        ball.scored = True
        ball.active = False
        self.score += 3
        self.message = "SWISH! +3"
        self.message_color = GOLD
        self.message_timer = 1.4

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

        # A small, forgiving collision with the rim and backboard.
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
        if not self.game_over:
            self.time_left = max(0, self.time_left - dt)
            if self.time_left <= 0:
                self.game_over = True
                self.message = "Time's up!"
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
        self.screen.fill(SKY)
        self.draw_header()
        self.draw_court()
        self.draw_hoop()
        self.draw_player()
        for ball in self.balls:
            self.draw_ball(ball)
        self.draw_overlay()
        pygame.display.flip()

    def draw_header(self) -> None:
        pygame.draw.rect(self.screen, (19, 27, 49), (0, 0, WIDTH, 112))
        title = self.title_font.render("3-POINT SHOOTING", True, WHITE)
        self.screen.blit(title, (28, 22))
        score = self.score_font.render(f"{self.score}", True, GOLD)
        self.screen.blit(score, (385, 15))
        label = self.small_font.render("POINTS", True, (170, 184, 209))
        self.screen.blit(label, (389, 78))
        seconds = max(0, math.ceil(self.time_left))
        timer_color = RED if seconds <= 10 else WHITE
        timer = self.title_font.render(f"{seconds:02d}s", True, timer_color)
        self.screen.blit(timer, (670, 28))
        pygame.draw.rect(self.screen, (55, 69, 98), self.restart_button, border_radius=8)
        restart = self.small_font.render("RESTART [R]", True, WHITE)
        self.screen.blit(restart, restart.get_rect(center=self.restart_button.center))

    def draw_court(self) -> None:
        pygame.draw.rect(
            self.screen, COURT, (0, COURT_TOP, WIDTH, COURT_BOTTOM - COURT_TOP)
        )
        pygame.draw.rect(
            self.screen,
            COURT_LIGHT,
            (0, COURT_TOP, WIDTH, 18),
        )
        pygame.draw.line(self.screen, WHITE, (0, COURT_BOTTOM), (WIDTH, COURT_BOTTOM), 4)
        pygame.draw.line(self.screen, WHITE, (WIDTH - 3, COURT_TOP), (WIDTH - 3, COURT_BOTTOM), 4)
        pygame.draw.rect(
            self.screen,
            PAINT,
            (HOOP_X - 140, HOOP_Y + 18, 140, COURT_BOTTOM - HOOP_Y - 18),
        )
        pygame.draw.rect(
            self.screen,
            WHITE,
            (HOOP_X - 140, HOOP_Y + 18, 140, COURT_BOTTOM - HOOP_Y - 18),
            4,
        )
        pygame.draw.circle(
            self.screen, WHITE, (HOOP_X - 70, HOOP_Y + 116), 58, 4
        )
        pygame.draw.arc(
            self.screen,
            WHITE,
            (HOOP_X - 385, HOOP_Y - 185, 630, 640),
            math.radians(270),
            math.radians(90),
            4,
        )
        for x in range(20, WIDTH, 80):
            pygame.draw.line(self.screen, (211, 139, 78), (x, COURT_BOTTOM - 6), (x + 45, COURT_BOTTOM - 6), 2)

    def draw_hoop(self) -> None:
        backboard = pygame.Rect(HOOP_X + 35, HOOP_Y - 73, 10, 112)
        pygame.draw.rect(self.screen, WHITE, backboard)
        pygame.draw.rect(self.screen, BLACK, backboard, 2)
        pygame.draw.line(self.screen, BLACK, (HOOP_X + 35, HOOP_Y - 31), (HOOP_X + 35, HOOP_Y + 25), 3)
        pygame.draw.line(self.screen, BLACK, (HOOP_X + 35, HOOP_Y - 31), (HOOP_X + 2, HOOP_Y - 31), 3)
        pygame.draw.ellipse(
            self.screen, ORANGE, (HOOP_X - RIM_RADIUS, HOOP_Y - 5, RIM_RADIUS * 2, 10)
        )
        for offset in (-12, -6, 0, 6, 12):
            pygame.draw.line(
                self.screen,
                WHITE,
                (HOOP_X + offset, HOOP_Y + 4),
                (HOOP_X + offset // 2, HOOP_Y + 35),
                2,
            )
        pygame.draw.arc(
            self.screen,
            WHITE,
            (HOOP_X - 13, HOOP_Y + 18, 26, 22),
            0,
            math.pi,
            2,
        )

    def draw_player(self) -> None:
        px, py = self.player_pos
        pygame.draw.circle(self.screen, (234, 187, 145), (px, py - 102), 17)
        pygame.draw.rect(self.screen, (50, 93, 169), (px - 22, py - 85, 44, 58), border_radius=8)
        pygame.draw.line(self.screen, (234, 187, 145), (px - 14, py - 35), (px - 24, py + 4), 8)
        pygame.draw.line(self.screen, (234, 187, 145), (px + 14, py - 35), (px + 24, py + 4), 8)
        pygame.draw.line(self.screen, (50, 40, 35), (px - 10, py + 4), (px - 23, py + 39), 8)
        pygame.draw.line(self.screen, (50, 40, 35), (px + 10, py + 4), (px + 23, py + 39), 8)
        if not self.balls and not self.game_over:
            radians = math.radians(self.aim_angle)
            end = (px + int(math.cos(radians) * 155), py - 70 - int(math.sin(radians) * 155))
            pygame.draw.line(self.screen, (255, 235, 145), (px + 28, py - 70), end, 2)
            pygame.draw.circle(self.screen, (255, 235, 145), end, 4)

    def draw_ball(self, ball: Ball) -> None:
        pygame.draw.circle(self.screen, ORANGE, (round(ball.x), round(ball.y)), BALL_RADIUS)
        pygame.draw.arc(
            self.screen,
            BLACK,
            (round(ball.x) - BALL_RADIUS, round(ball.y) - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2),
            math.radians(20),
            math.radians(200),
            2,
        )
        pygame.draw.line(
            self.screen,
            BLACK,
            (round(ball.x) - 10, round(ball.y) + 4),
            (round(ball.x) + 10, round(ball.y) - 4),
            2,
        )

    def draw_overlay(self) -> None:
        if self.charging:
            bar = pygame.Rect(28, HEIGHT - 85, 230, 18)
            pygame.draw.rect(self.screen, (62, 47, 42), bar, border_radius=9)
            pygame.draw.rect(
                self.screen,
                GOLD,
                (bar.left, bar.top, round(bar.width * self.power), bar.height),
                border_radius=9,
            )
            text = self.small_font.render("POWER", True, WHITE)
            self.screen.blit(text, (28, HEIGHT - 112))
        controls = self.small_font.render("LEFT/RIGHT aim  |  SPACE shoot", True, WHITE)
        self.screen.blit(controls, (28, 120))
        if self.message_timer > 0:
            message = self.body_font.render(self.message, True, self.message_color)
            self.screen.blit(message, message.get_rect(center=(WIDTH // 2, 126)))
        if self.game_over:
            panel = pygame.Surface((440, 190), pygame.SRCALPHA)
            panel.fill((12, 17, 31, 235))
            self.screen.blit(panel, panel.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            finished = self.title_font.render("GAME OVER", True, GOLD)
            result = self.body_font.render(f"Final score: {self.score} points", True, WHITE)
            prompt = self.small_font.render("Press R or click RESTART to play again", True, WHITE)
            self.screen.blit(finished, finished.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 48)))
            self.screen.blit(result, result.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            self.screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 42)))

    async def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
            await asyncio.sleep(0)
        pygame.quit()


if __name__ == "__main__":
    asyncio.run(ShootingGame().run())
