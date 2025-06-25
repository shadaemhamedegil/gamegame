import pygame
import random
import sys
import math

pygame.init()
pygame.mixer.init()

# --------- الأصوات ---------
start_sound = pygame.mixer.Sound("game-music-loop-7-145285.mp3")
hit_sound = pygame.mixer.Sound("hit-flesh-02-266309.mp3")
win_sound = pygame.mixer.Sound("brass-fanfare-with-timpani-and-winchimes-reverberated-146260.mp3")
lose_sound = pygame.mixer.Sound("game-over-160612.mp3")

# --------- إعدادات عامة ---------
WIDTH, HEIGHT = 900, 650
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
BLUE = (0, 0, 255)
RED = (200, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)

clock = pygame.time.Clock()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("الهروب من المختبر")

font = pygame.font.SysFont("arial", 28)

# --------- الخلفيات ---------
backgrounds = {
    "easy": pygame.transform.scale(pygame.image.load("photo_2025-06-16_22-35-32.jpg"), (WIDTH, HEIGHT)),
    "middle": pygame.transform.scale(pygame.image.load("photo_2025-06-16_22-35-05.jpg"), (WIDTH, HEIGHT)),
    "hard": pygame.transform.scale(pygame.image.load("photo_2025-06-16_22-35-11.jpg"), (WIDTH, HEIGHT)),
}

# --------- الأسئلة ---------
questions_by_level = {
    "easy": ("5 + 3 = ?", "8"),
    "middle": ("9 * 4 = ?", "36"),
    "hard": ("7 * 9 - 3 = ?", "60")
}

# --------- الكلاس الأساسي المجرد للكائنات المتحركة ---------
class MovableObject:
    def __init__(self, pos, size):
        self._pos = list(pos)
        self._size = size

    @property
    def rect(self):
        return pygame.Rect(self._pos[0], self._pos[1], self._size, self._size)

    def draw(self, surface):
        raise NotImplementedError("This method must be overridden")

    def update(self):
        raise NotImplementedError("This method must be overridden")

# --------- كلاس اللاعب يرث من MovableObject ---------
class Player(MovableObject):
    def __init__(self, pos):
        super().__init__(pos, 45)
        self._images = {
            "down": pygame.transform.scale(pygame.image.load("mouseD.png"), (self._size, self._size)),
            "up": pygame.transform.scale(pygame.image.load("mouseU.png"), (self._size, self._size)),
            "left": pygame.transform.scale(pygame.image.load("mouseL.png"), (self._size, self._size)),
            "right": pygame.transform.scale(pygame.image.load("mouseR.png"), (self._size, self._size))
        }
        self._direction = "down"
        self._speed = 5

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        if value in self._images:
            self._direction = value

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        if value > 0:
            self._speed = value

    def move(self, dx, dy, walls):
        next_rect_x = pygame.Rect(self._pos[0] + dx, self._pos[1], self._size, self._size)
        if not any(next_rect_x.colliderect(w) for w in walls):
            self._pos[0] += dx

        next_rect_y = pygame.Rect(self._pos[0], self._pos[1] + dy, self._size, self._size)
        if not any(next_rect_y.colliderect(w) for w in walls):
            self._pos[1] += dy

        # منع الخروج من الشاشة
        self._pos[0] = max(0, min(WIDTH - self._size, self._pos[0]))
        self._pos[1] = max(0, min(HEIGHT - self._size, self._pos[1]))

    def draw(self, surface):
        surface.blit(self._images[self._direction], self._pos)

    def update(self):
        # لا حاجة لـ update داخل اللاعب حاليا، يمكن تطويرها مستقبلا
        pass

    @property
    def pos(self):
        return self._pos

# --------- كلاس العدو الأساسي (مجرد) يرث من MovableObject ---------
class Enemy(MovableObject):
    def __init__(self, pos, speed, image):
        super().__init__(pos, 40)
        self._speed = speed
        self._image = pygame.transform.scale(image, (self._size, self._size))

    def move_toward(self, target_pos):
        dx = target_pos[0] - self.rect.centerx
        dy = target_pos[1] - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        dx /= dist
        dy /= dist
        self._pos[0] += int(dx * self._speed)
        self._pos[1] += int(dy * self._speed)

    def draw(self, surface):
        surface.blit(self._image, self.rect)

    def update(self, target_pos):
        self.move_toward(target_pos)

# --------- عدوان مختلفان يرثون Enemy و يغيرون السلوك (تعددية - Polymorphism) ---------
class FastEnemy(Enemy):
    def __init__(self, pos, speed, image):
        super().__init__(pos, speed * 1.2, image)  # أسرع

    def update(self, target_pos):
        # يتحرك أسرع قليلاً مع سلوك ممكن تطويره لاحقاً
        self.move_toward(target_pos)

class ZigzagEnemy(Enemy):
    def __init__(self, pos, speed, image):
        super().__init__(pos, speed, image)
        self._zigzag_direction = 1
        self._zigzag_counter = 0

    def update(self, target_pos):
        # يتحرك باتجاه الهدف مع حركة زجزاج جانبية
        dx = target_pos[0] - self.rect.centerx
        dy = target_pos[1] - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        dx /= dist
        dy /= dist

        # حركة جانبية بسيطة
        perpendicular = (-dy, dx)  # متجه عمودي على اتجاه الحركة

        # تغيير الاتجاه الجانبي كل 30 تحديث
        if self._zigzag_counter >= 30:
            self._zigzag_direction *= -1
            self._zigzag_counter = 0

        self._zigzag_counter +=1

        self._pos[0] += int((dx + perpendicular[0]*0.3*self._zigzag_direction) * self._speed)
        self._pos[1] += int((dy + perpendicular[1]*0.3*self._zigzag_direction) * self._speed)

# --------- كلاس إدارة المستويات ---------
class LevelManager:
    def __init__(self):
        self._walls = []

    @property
    def walls(self):
        return self._walls

    def set_walls(self, level):
        self._walls.clear()
        if level == "easy":
            self._walls = [
                pygame.Rect(100, 150, 300, 20),
                pygame.Rect(300, 400, 20, 200),
                pygame.Rect(200, 500, 400, 20),
                pygame.Rect(100, 100, 20,100),
                pygame.Rect(600, 100, 20,300),
                pygame.Rect(150, 300, 200,20),
                pygame.Rect(600, 300, 200,20),
                pygame.Rect(500, 300, 300,20)
            ]
        elif level == "middle":
            self._walls = [
                pygame.Rect(200, 250, 300, 20),
                pygame.Rect(100, 350, 150, 20),
                pygame.Rect(450, 550, 200, 20),
                pygame.Rect(30, 200, 20, 400),
                pygame.Rect(300, 100, 20, 300),
                pygame.Rect(550,400,100,20),
                pygame.Rect(600,500,20,100),
                pygame.Rect(100, 150, 300,20),
                pygame.Rect(700, 100,20,300),
                pygame.Rect(650, 300, 200,20),
                pygame.Rect(150, 600, 200,20)
            ]
        elif level == "hard":
            self._walls = [
                pygame.Rect(100, 150, 750, 20),
                pygame.Rect(100, 150, 20, 100),
                pygame.Rect(200, 190, 20, 100),
                pygame.Rect(300, 150, 20, 100),
                pygame.Rect(400, 190, 20, 100),
                pygame.Rect(500, 150, 20, 100),
                pygame.Rect(600, 190, 20, 100),
                pygame.Rect(100, 280, 720, 20),
                pygame.Rect(100, 280, 20, 100),
                pygame.Rect(200, 360, 20, 100),
                pygame.Rect(300, 280, 20, 100),
                pygame.Rect(400, 360, 20, 100),
                pygame.Rect(500, 280, 20, 100),
                pygame.Rect(600, 360, 20, 100),
                pygame.Rect(100, 460, 720, 20),
                pygame.Rect(100, 580, 720, 20),
                pygame.Rect(100, 460, 20, 50),
                pygame.Rect(160, 550, 20, 60),
                pygame.Rect(230, 460, 20, 60),
                pygame.Rect(300, 550, 20, 30),
            ]

    def draw_walls(self, surface):
        for wall in self._walls:
            pygame.draw.rect(surface, WHITE, wall)

# --------- كلاس واجهة المستخدم ---------
class UI:
    def __init__(self):
        self._pause_img = pygame.transform.scale(pygame.image.load("pause.png"), (40, 40))
        self._resume_img = pygame.transform.scale(pygame.image.load("resume.png"), (40, 40))
        self._mute_img = pygame.transform.scale(pygame.image.load("mute.png"), (40, 40))
        self._home_img = pygame.transform.scale(pygame.image.load("home.png"), (40, 40))
        self._exit_img = pygame.transform.scale(pygame.image.load("button.png"), (40, 40))

        self.pause_rect = self._pause_img.get_rect(topleft=(10, 10))
        self.resume_rect = self._resume_img.get_rect(topleft=(60, 10))
        self.mute_rect = self._mute_img.get_rect(topleft=(110, 10))
        self.home_rect = self._home_img.get_rect(topleft=(160, 10))
        self.exit_rect = self._exit_img.get_rect(topleft=(210, 10))

    def draw_buttons(self, surface):
        surface.blit(self._pause_img, self.pause_rect)
        surface.blit(self._resume_img, self.resume_rect)
        surface.blit(self._mute_img, self.mute_rect)
        surface.blit(self._home_img, self.home_rect)
        surface.blit(self._exit_img, self.exit_rect)

# --------- كلاس اللعبة الرئيسية ---------
class Game:
    def __init__(self):
        self._level = None
        self._settings = {}
        self._background_img = None
        self._player = Player((WIDTH // 2, HEIGHT // 2))
        self._level_manager = LevelManager()
        self._ui = UI()
        self._enemies = []
        self._score = 0

        self._exit_rect = pygame.Rect(350, 0, 200, 20)
        self._door_open = False
        self._question_zone = pygame.Rect(400, 50, 100, 50)
        self._question = ""
        self._correct_answer = ""
        self._user_input = ""
        self._show_question = False

        self._paused = False
        self._muted = False

        self._game_over = False
        self._game_won = False

    def spawn_enemies(self, count, speed):
        self._enemies.clear()
        enemy_images = ["slime.png", "slime.png", "slime.png"]  # ملفات الصور يجب أن تكون موجودة
        enemy_classes = [Enemy, FastEnemy, ZigzagEnemy]

        for _ in range(count):
            side = random.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':
                pos = [random.randint(50, WIDTH - 50), 50]
            elif side == 'bottom':
                pos = [random.randint(50, WIDTH - 50), HEIGHT - 60]
            elif side == 'left':
                pos = [50, random.randint(50, HEIGHT - 50)]
            else:
                pos = [WIDTH - 60, random.randint(50, HEIGHT - 50)]

            enemy_class = random.choice(enemy_classes)
            img_file = random.choice(enemy_images)
            image = pygame.image.load(img_file)

            enemy_obj = enemy_class(pos, speed, image)
            self._enemies.append(enemy_obj)

    def detect_collision(self, rect1, rect2):
        return rect1.colliderect(rect2)

    def show_loading_screen(self):
        bg = pygame.transform.scale(pygame.image.load("photo_2025-06-19_17-23-41.jpg"), (WIDTH, HEIGHT))
        screen.blit(bg, (0, 0))
        title_font = pygame.font.SysFont("comicsansms", 64, bold=True)
        title_text = title_font.render("Escape from the Lab", True, WHITE)
        #screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 3))
        loading_font = pygame.font.SysFont("arial", 36)
        loading_text = loading_font.render("Loading...", True, BLUE)
        #screen.blit(loading_text, (WIDTH // 2 - loading_text.get_width() // 2, HEIGHT - 80))
        pygame.display.flip()
        pygame.time.wait(3000)

    def show_level_selection(self):
        selecting = True
        while selecting:
            bg = pygame.transform.scale(pygame.image.load("photo_2025-06-16_22-34-45.jpg"), (WIDTH, HEIGHT))
            screen.blit(bg, (0, 0))

            easy_btn = pygame.Rect(WIDTH // 2 - 100, 200, 200, 50)
            med_btn = pygame.Rect(WIDTH // 2 - 100, 300, 200, 50)
            hard_btn = pygame.Rect(WIDTH // 2 - 100, 400, 200, 50)

            pygame.draw.rect(screen, GREEN, easy_btn)
            pygame.draw.rect(screen, YELLOW, med_btn)
            pygame.draw.rect(screen, RED, hard_btn)

            screen.blit(font.render("Easy", True, BLACK), (easy_btn.x + 70, easy_btn.y + 10))
            screen.blit(font.render("Middle", True, BLACK), (med_btn.x + 70, med_btn.y + 10))
            screen.blit(font.render("Difficult", True, BLACK), (hard_btn.x + 70, hard_btn.y + 10))

            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    if easy_btn.collidepoint(mx, my):
                        return "easy", {"player_speed": 5, "enemy_speed": 2, "enemy_count": 2}
                    if med_btn.collidepoint(mx, my):
                        return "middle", {"player_speed": 4, "enemy_speed": 2.5, "enemy_count": 3}
                    if hard_btn.collidepoint(mx, my):
                        return "hard", {"player_speed": 4, "enemy_speed": 3, "enemy_count": 4}

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self._ui.pause_rect.collidepoint(event.pos):
                    self._paused = True
                elif self._ui.resume_rect.collidepoint(event.pos):
                    self._paused = False
                elif self._ui.mute_rect.collidepoint(event.pos):
                    self._muted = not self._muted
                    if self._muted:
                        pygame.mixer.pause()
                    else:
                        pygame.mixer.unpause()
                elif self._ui.home_rect.collidepoint(event.pos):
                    self._level, self._settings = self.show_level_selection()
                    self.reset_level()
                elif self._ui.exit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

            if not self._paused and self._show_question:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self._user_input == self._correct_answer:
                            self._door_open = True
                            self._show_question = False
                            self._user_input = ""
                        else:
                            self._user_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self._user_input = self._user_input[:-1]
                    elif event.unicode.isdigit():
                        self._user_input += event.unicode

    def update(self):
        if not self._paused:
            keys = pygame.key.get_pressed()
            dx = dy = 0
            if keys[pygame.K_LEFT]:
                dx = -self._settings["player_speed"]
                self._player.direction = "left"
            elif keys[pygame.K_RIGHT]:
                dx = self._settings["player_speed"]
                self._player.direction = "right"
            elif keys[pygame.K_UP]:
                dy = -self._settings["player_speed"]
                self._player.direction = "up"
            elif keys[pygame.K_DOWN]:
                dy = self._settings["player_speed"]
                self._player.direction = "down"

            self._player.move(dx, dy, self._level_manager.walls)

            player_rect = self._player.rect

            if player_rect.colliderect(self._question_zone) and not self._door_open:
                self._show_question = True

            for enemy in self._enemies:
                enemy.update(self._player.pos)
                if self.detect_collision(player_rect, enemy.rect):
                    hit_sound.play()
                    self._game_over = True

            if self._door_open and player_rect.colliderect(self._exit_rect):
                win_sound.play()
                self._game_won = True

            self._score += 1

    def draw(self):
        screen.blit(self._background_img, (0, 0))
        self._player.draw(screen)
        self._level_manager.draw_walls(screen)

        for enemy in self._enemies:
            enemy.draw(screen)

        if self._door_open:
            pygame.draw.rect(screen, GREEN, self._exit_rect)
        else:
            pygame.draw.rect(screen, RED, self._exit_rect)
            pygame.draw.rect(screen, YELLOW, self._question_zone)

        if self._show_question:
            q_text = font.render(self._question, True, BLACK)
            a_text = font.render(self._user_input, True, BLUE)
            screen.blit(q_text, (WIDTH // 2 - q_text.get_width() // 2, HEIGHT // 2 - 60))
            screen.blit(a_text, (WIDTH // 2 - a_text.get_width() // 2, HEIGHT // 2))

        score_text = font.render(f"Score: {self._score // 30}", True, BLACK)
        screen.blit(score_text, (10, HEIGHT - 40))

        self._ui.draw_buttons(screen)

    def reset_level(self):
        self._player = Player((WIDTH // 2, HEIGHT // 2))
        self._level_manager.set_walls(self._level)
        self._background_img = backgrounds[self._level]
        self._question, self._correct_answer = questions_by_level[self._level]
        self.spawn_enemies(self._settings["enemy_count"], self._settings["enemy_speed"])
        self._door_open = False
        self._user_input = ""
        self._show_question = False
        self._score = 0
        self._game_over = False
        self._game_won = False

        # ضبط سرعة اللاعب حسب المستوى
        self._player.speed = self._settings["player_speed"]

    def run(self):
     while True:  # تكرار اللعبة تلقائيًا بعد النهاية
        self.show_loading_screen()
        start_sound.play()
        self._level, self._settings = self.show_level_selection()
        self.reset_level()

        while not self._game_over and not self._game_won:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            clock.tick(30)

        # شاشة النهاية
        screen.fill(BLACK)
        end_font = pygame.font.SysFont("comicsansms", 60, bold=True)
        score_font = pygame.font.SysFont("arial", 40)
        end_text = end_font.render("I managed to escape" if self._game_won else "Game Over", True, GREEN if self._game_won else RED)
        screen.blit(end_text, (WIDTH // 2 - end_text.get_width() // 2, HEIGHT // 2 - 50))
        final_score = self._score // 30
        score_text = score_font.render(f"Final Score: {final_score}", True, WHITE)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 + 80))
        pygame.display.flip()

        pygame.mixer.stop()
        if self._game_won:
            win_sound.play()
        else:
            lose_sound.play()

        pygame.time.wait(3700)
       

# --------- بدء اللعبة ---------
if __name__ == "__main__":
    game = Game()
    game.run()