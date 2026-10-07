import pygame
import random
import math
from array import array

from game.beat import (
    Note,
    LANES,
    LANE_KEYS,
    LANE_LABELS,
    LANE_COLORS
)

WIDTH, HEIGHT = 480, 640
FPS = 60
HIT_Y = HEIGHT - 80
HIT_WINDOW = 30
BG = (15, 10, 25)
LANE_W = WIDTH // LANES

# Task 3: BPM settings
BPM = 120
BEAT_INTERVAL = 60 / BPM


class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        # Task 1: Sound effects
        self.hit_sounds = {
            "PERFECT": self.make_sound(880, 0.10),
            "GREAT": self.make_sound(660, 0.10),
            "OK": self.make_sound(440, 0.10),
        }

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption("Rhythm Tap")

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(
            "monospace",
            26,
            bold=True
        )

        self.big_font = pygame.font.SysFont(
            "monospace",
            44,
            bold=True
        )

        self.reset()

    def make_sound(self, frequency, duration):
        """Generate a short beep sound."""
        sample_rate = 44100
        samples = int(sample_rate * duration)

        buffer = array("h")

        for i in range(samples):
            value = int(
                32767
                * 0.25
                * math.sin(
                    2 * math.pi * frequency * i / sample_rate
                )
            )

            buffer.append(value)

        return pygame.mixer.Sound(
            buffer=buffer.tobytes()
        )

    def reset(self):
        self.notes = []

        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.misses = 0

        # Task 3: BPM-synchronized spawning
        self.beat_timer = 0.0

        self.speed = 5
        self.frame = 0

        self.feedback = []

        self.game_over = False

    def spawn_note(self):
        lane = random.randint(
            0,
            LANES - 1
        )

        # Task 2: Randomly create normal or hold note
        is_hold = random.random() < 0.25

        self.notes.append(
            Note(
                lane,
                y=-30,
                speed=self.speed,
                hold=is_hold
            )
        )

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_r:
                    self.reset()

                elif not self.game_over:

                    for i, key in enumerate(LANE_KEYS):

                        if event.key == key:
                            self.start_note(i)

            # Detect when player releases a key
            if event.type == pygame.KEYUP:

                for i, key in enumerate(LANE_KEYS):

                    if event.key == key:
                        self.release_note(i)

        return True

    def start_note(self, lane):

        # Find closest note
        best = None
        best_dist = 9999

        for note in self.notes:

            if (
                note.lane == lane
                and not note.hit
                and not note.missed
            ):

                dist = abs(
                    note.y
                    + Note.HEIGHT // 2
                    - HIT_Y
                )

                if dist < best_dist:
                    best_dist = dist
                    best = note

        lane_x = (
            lane * LANE_W
            + LANE_W // 2
        )

        if best and best_dist <= HIT_WINDOW:

            # HOLD NOTE
            if best.hold:

                best.holding = True

                self.feedback.append(
                    [
                        "HOLD!",
                        (255, 200, 100),
                        30,
                        lane_x,
                        HIT_Y - 30
                    ]
                )

            # NORMAL NOTE
            else:

                self.process_normal_hit(
                    best,
                    best_dist,
                    lane_x
                )

        else:

            self.combo = 0

            self.feedback.append(
                [
                    "MISS",
                    (220, 60, 60),
                    40,
                    lane_x,
                    HIT_Y - 30
                ]
            )

    def release_note(self, lane):

        for note in self.notes:

            if (
                note.lane == lane
                and note.hold
                and note.holding
                and not note.hit
            ):

                # Released before 1 second
                if note.hold_progress < note.hold_duration:

                    note.holding = False
                    note.missed = True

                    self.misses += 1
                    self.combo = 0

                    lane_x = (
                        lane * LANE_W
                        + LANE_W // 2
                    )

                    self.feedback.append(
                        [
                            "MISS",
                            (220, 60, 60),
                            40,
                            lane_x,
                            HIT_Y - 30
                        ]
                    )

    def process_normal_hit(
        self,
        note,
        best_dist,
        lane_x
    ):

        note.hit = True

        if best_dist < 8:

            grade, pts = "PERFECT", 300
            col = (255, 220, 0)

        elif best_dist < 18:

            grade, pts = "GREAT", 200
            col = (100, 220, 100)

        else:

            grade, pts = "OK", 100
            col = (180, 180, 255)

        self.combo += 1

        self.max_combo = max(
            self.max_combo,
            self.combo
        )

        self.score += pts * max(
            1,
            self.combo // 5
        )

        # Task 1: Play sound
        self.hit_sounds[grade].play()

        self.feedback.append(
            [
                grade,
                col,
                40,
                lane_x,
                HIT_Y - 30
            ]
        )

    def update(self):

        if self.game_over:
            return

        self.frame += 1

        # ==========================================
        # TASK 3: BPM-SYNCHRONIZED NOTE SPAWNING
        # 120 BPM = one note every 0.5 seconds
        # ==========================================

        self.beat_timer += 1 / FPS

        if self.beat_timer >= BEAT_INTERVAL:

            self.beat_timer -= BEAT_INTERVAL

            self.spawn_note()

        # Gradually increase speed
        if self.frame % 600 == 0:

            self.speed = min(
                10,
                self.speed + 0.5
            )

        # Update notes
        for note in self.notes:

            note.update()

            # Successful hold note
            if (
                note.hold
                and note.hit
            ):

                lane_x = (
                    note.lane * LANE_W
                    + LANE_W // 2
                )

                self.combo += 1

                self.max_combo = max(
                    self.max_combo,
                    self.combo
                )

                self.score += 300

                self.hit_sounds["PERFECT"].play()

                self.feedback.append(
                    [
                        "HOLD PERFECT",
                        (255, 220, 0),
                        40,
                        lane_x,
                        HIT_Y - 30
                    ]
                )

            # Missed note
            if (
                not note.hit
                and not note.missed
                and note.y >
                HIT_Y
                + HIT_WINDOW
                + Note.HEIGHT
            ):

                note.missed = True

                self.misses += 1

                self.combo = 0

        # Remove old notes
        self.notes = [
            n for n in self.notes
            if not (
                n.hit
                or (
                    n.missed
                    and n.y > HEIGHT + 10
                )
            )
        ]

        # Update feedback
        self.feedback = [
            [
                t,
                c,
                ttl - 1,
                x,
                y
            ]
            for t, c, ttl, x, y
            in self.feedback
            if ttl > 1
        ]

        if self.misses >= 15:
            self.game_over = True

    def draw(self):

        self.screen.fill(BG)

        # Lane dividers
        for i in range(LANES + 1):

            pygame.draw.line(
                self.screen,
                (40, 40, 60),
                (
                    i * LANE_W,
                    0
                ),
                (
                    i * LANE_W,
                    HEIGHT
                ),
                1
            )

        # Hit line
        pygame.draw.line(
            self.screen,
            (80, 80, 100),
            (
                0,
                HIT_Y
            ),
            (
                WIDTH,
                HIT_Y
            ),
            2
        )

        # Hit buttons
        for i in range(LANES):

            lx = (
                i * LANE_W
                + LANE_W // 2
            )

            pygame.draw.rect(
                self.screen,
                LANE_COLORS[i],
                pygame.Rect(
                    lx - Note.WIDTH // 2,
                    HIT_Y - 12,
                    Note.WIDTH,
                    24
                ),
                border_radius=6
            )

            lbl = self.font.render(
                LANE_LABELS[i],
                True,
                (20, 20, 20)
            )

            self.screen.blit(
                lbl,
                (
                    lx
                    - lbl.get_width() // 2,
                    HIT_Y - 10
                )
            )

        # Notes
        for note in self.notes:

            if note.hit:
                continue

            lx = (
                note.lane * LANE_W
                + LANE_W // 2
            )

            rect = note.get_rect(lx)

            pygame.draw.rect(
                self.screen,
                LANE_COLORS[note.lane],
                rect,
                border_radius=5
            )

            # Show HOLD text
            if note.hold:

                hold_text = self.font.render(
                    "HOLD",
                    True,
                    (20, 20, 20)
                )

                self.screen.blit(
                    hold_text,
                    (
                        lx
                        - hold_text.get_width() // 2,
                        int(note.y) + 25
                    )
                )

        # Feedback
        for text, color, ttl, x, y in self.feedback:

            surf = self.font.render(
                text,
                True,
                color
            )

            alpha = min(
                255,
                ttl * 7
            )

            surf.set_alpha(alpha)

            self.screen.blit(
                surf,
                (
                    x
                    - surf.get_width() // 2,
                    y
                )
            )

        # HUD
        sc = self.font.render(
            f"Score: {self.score}",
            True,
            (220, 220, 220)
        )

        co = self.font.render(
            f"Combo: {self.combo}x",
            True,
            (255, 220, 80)
        )

        mi = self.font.render(
            f"Misses: {self.misses}/15",
            True,
            (220, 100, 100)
        )

        bpm_text = self.font.render(
            f"BPM: {BPM}",
            True,
            (180, 180, 255)
        )

        self.screen.blit(
            sc,
            (10, 10)
        )

        self.screen.blit(
            co,
            (10, 40)
        )

        self.screen.blit(
            mi,
            (WIDTH - 170, 10)
        )

        # Task 3: Display BPM
        self.screen.blit(
            bpm_text,
            (WIDTH - 150, 40)
        )

        # Game over
        if self.game_over:

            ov = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            ov.fill(
                (0, 0, 0, 160)
            )

            self.screen.blit(
                ov,
                (0, 0)
            )

            msg = self.big_font.render(
                "GAME OVER",
                True,
                (220, 60, 60)
            )

            sc_msg = self.font.render(
                f"Final Score: {self.score}  "
                f"Max Combo: {self.max_combo}x",
                True,
                (200, 200, 200)
            )

            restart = self.font.render(
                "Press R to Restart",
                True,
                (160, 160, 160)
            )

            self.screen.blit(
                msg,
                (
                    WIDTH // 2
                    - msg.get_width() // 2,
                    HEIGHT // 2 - 70
                )
            )

            self.screen.blit(
                sc_msg,
                (
                    WIDTH // 2
                    - sc_msg.get_width() // 2,
                    HEIGHT // 2
                )
            )

            self.screen.blit(
                restart,
                (
                    WIDTH // 2
                    - restart.get_width() // 2,
                    HEIGHT // 2 + 50
                )
            )

        pygame.display.flip()

    def run(self):

        running = True

        while running:

            running = self.handle_events()

            self.update()

            self.draw()

            self.clock.tick(FPS)

        pygame.quit()
