import pygame
import random
import math
import time
from enum import Enum

pygame.init()

# spesifikasi
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
LANE_WIDTH = 160
CAR_WIDTH = 40 
CAR_HEIGHT = 80
FPS = 60

# color
WHITE = (255, 255, 255)
BLUE = (30, 144, 255)
RED = (220, 20, 60)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)

class Direction(Enum):
    LEFT = -1
    STRAIGHT = 0
    RIGHT = 1

class CarState(Enum):
    CRUISING = 1
    OVERTAKING = 2
    RETURNING = 3

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Rexzea Self-Driving Car Simulation")
        self.clock = pygame.time.Clock()
        
        #game objects
        self.ai_car = AICar(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
        self.traffic = []
        self.game_over = False
        self.start_time = time.time()
        self.score = 0
        self.distance_traveled = 0
        
        #lane positions (5 lanes)
         #you can add :)
        self.lanes = [LANE_WIDTH * i + LANE_WIDTH for i in range(5)]
        
        #road markings
        self.road_marks = []
        self.initialize_road_marks()

    def initialize_road_marks(self):
        for y in range(-40, SCREEN_HEIGHT + 40, 40):
            self.road_marks.append(y)
    
    def spawn_traffic(self):
        if len(self.traffic) < 8 and random.random() < 0.02:
            lane = random.randint(1, 4)
            speed = random.uniform(2, 5)
            self.traffic.append(TrafficCar(self.lanes[lane] - CAR_WIDTH // 2, -CAR_HEIGHT, speed, lane))
    
    def draw_road(self):
        #road background
        pygame.draw.rect(self.screen, GRAY, (LANE_WIDTH, 0, LANE_WIDTH * 5, SCREEN_HEIGHT))
        
        #lane markings
        for x in self.lanes[1:0]:  # Don't draw on outer edges
            for y in self.road_marks:
                y_pos = (y + self.distance_traveled) % SCREEN_HEIGHT
                pygame.draw.rect(self.screen, YELLOW, (x - 1, y_pos, 2, 20))
        
        # road edges
        pygame.draw.rect(self.screen, WHITE, (LANE_WIDTH, 0, 5, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, WHITE, (LANE_WIDTH * 5, 0, 5, SCREEN_HEIGHT))
    
    def run(self):
        while not self.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            
            self.update()
            self.draw()
            self.clock.tick(FPS)
            self.distance_traveled += 1
        
        self.show_game_over()
        pygame.time.wait(2000)
    
    def update(self):
        # traffic
        self.spawn_traffic()
        for car in self.traffic[:]:
            car.update(self.distance_traveled)
            if car.y > SCREEN_HEIGHT:
                self.traffic.remove(car)
                self.score += 10
            elif car.y < -CAR_HEIGHT * 2:
                self.traffic.remove(car)
        
        # AI car
        self.ai_car.update(self.traffic, self.lanes)
        
        # check collisions
        self.check_collisions()
        
        # road markings
        for i in range(len(self.road_marks)):
            self.road_marks[i] = (self.road_marks[i] + 2) % SCREEN_HEIGHT
    
    def draw(self):
        self.screen.fill(BLACK)
        self.draw_road()
        
        # traffic
        for car in self.traffic:
            car.draw(self.screen)
        
        # AI car
        self.ai_car.draw(self.screen)
        
        # HUD
        self.draw_hud()
        
        pygame.display.flip()
    
    def draw_hud(self):
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        speed_text = font.render(f"Speed: {int(self.ai_car.speed * 10)} km/h", True, WHITE)
        state_text = font.render(f"State: {self.ai_car.state.name}", True, WHITE)
        
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(speed_text, (10, 50))
        self.screen.blit(state_text, (10, 90))
    
    def check_collisions(self):
        ai_car_rect = pygame.Rect(self.ai_car.x, self.ai_car.y, CAR_WIDTH, CAR_HEIGHT)
        for car in self.traffic:
            car_rect = pygame.Rect(car.x, car.y, CAR_WIDTH, CAR_HEIGHT)
            if ai_car_rect.colliderect(car_rect):
                self.game_over = True
    
    def show_game_over(self):
        font = pygame.font.Font(None, 74)
        text = font.render('Game Over!', True, WHITE)
        score_text = font.render(f'Final Score: {self.score}', True, WHITE)
        
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2,
                               SCREEN_HEIGHT // 2 - text.get_height()))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2,
                                     SCREEN_HEIGHT // 2 + text.get_height()))
        pygame.display.flip()

class AICar:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.speed = 60
        self.max_speed = 80
        self.min_speed = 40
        self.current_lane = 2  
        self.state = CarState.CRUISING
        self.sensor_range = 500
        self.side_sensor_range = 100
        self.lane_change_cooldown = 0
    
    def detect_traffic(self, traffic, lanes):
        sensors = {
            'front': [],
            'front_left': [],
            'front_right': [],
            'left': [],
            'right': []
        }
        
        for car in traffic:
            # front detection
            if abs(car.x - self.x) < LANE_WIDTH // 2:
                if car.y < self.y and car.y > self.y - self.sensor_range:
                    sensors['front'].append(car)
            
            # front left detection
            elif car.x < self.x and car.x > self.x - LANE_WIDTH:
                if car.y < self.y and car.y > self.y - self.sensor_range:
                    sensors['front_left'].append(car)
            
            # front right detection
            elif car.x > self.x and car.x < self.x + LANE_WIDTH:
                if car.y < self.y and car.y > self.y - self.sensor_range:
                    sensors['front_right'].append(car)
            
            # side detection
            if abs(car.y - self.y) < self.side_sensor_range:
                if car.x < self.x:
                    sensors['left'].append(car)
                elif car.x > self.x:
                    sensors['right'].append(car)
        
        return sensors
    
    def decide_action(self, sensors, lanes):
        if self.lane_change_cooldown > 0:
            self.lane_change_cooldown -= 1
            return
        
        # check if current lane is blocked
        if sensors['front']:
            closest_front = min(sensors['front'], key=lambda car: car.y)
            distance_to_front = self.y - closest_front.y
            
            if distance_to_front < self.sensor_range * 0.5:
                # look for overtaking opportunitiese (peluang untuk melewati)
                if not sensors['left'] and self.current_lane > 0:
                    self.change_lane('left')
                elif not sensors['right'] and self.current_lane < 4:
                    self.change_lane('right')
                else:
                    self.speed = max(closest_front.speed * 0.5, self.min_speed)
        else:
            # return to center if lanes if safe
            if self.current_lane < 2 and not sensors['right']:
                self.change_lane('right')
            elif self.current_lane > 2 and not sensors['left']:
                self.change_lane('left')
            
            # accelerate
            self.speed = min(self.speed + 0.1, self.max_speed)
    
    def change_lane(self, direction):
        if direction == 'left' and self.current_lane > 0:
            self.current_lane -= 1
            self.target_x = LANE_WIDTH * (self.current_lane + 1) - CAR_WIDTH // 2
            self.state = CarState.OVERTAKING
            self.lane_change_cooldown = 30
        elif direction == 'right' and self.current_lane < 4:
            self.current_lane += 1
            self.target_x = LANE_WIDTH * (self.current_lane + 1) - CAR_WIDTH // 2
            self.state = CarState.OVERTAKING
            self.lane_change_cooldown = 30
    
    def update(self, traffic, lanes):
        sensors = self.detect_traffic(traffic, lanes)
        self.decide_action(sensors, lanes)
        
        # lane changing
        if abs(self.x - self.target_x) > 2:
            self.x += (self.target_x - self.x) * 0.1
        else:
            self.x = self.target_x
            self.state = CarState.CRUISING
    
    def draw(self, screen):
        # car body
        pygame.draw.rect(screen, BLUE, (self.x, self.y, CAR_WIDTH, CAR_HEIGHT))
        
        # headlights
        pygame.draw.rect(screen, YELLOW, (self.x + 5, self.y, 5, 5))
        pygame.draw.rect(screen, YELLOW, (self.x + CAR_WIDTH - 10, self.y, 5, 5))
        
        # brake lights
        pygame.draw.rect(screen, RED, (self.x + 5, self.y + CAR_HEIGHT - 5, 5, 5))
        pygame.draw.rect(screen, RED, (self.x + CAR_WIDTH - 10, self.y + CAR_HEIGHT - 5, 5, 5))

class TrafficCar:
    def __init__(self, x, y, speed, lane):
        self.x = x
        self.y = y
        self.speed = speed
        self.lane = lane
        self.color = (random.randint(150, 255), random.randint(50, 150), random.randint(50, 150))
    
    def update(self, distance_traveled): #vriabl1
        relative_speed = self.speed
        self.y += (10 - relative_speed)  #relative to AI cars base speed!!!
    
    def draw(self, screen):
        #car body
        pygame.draw.rect(screen, self.color, (self.x, self.y, CAR_WIDTH, CAR_HEIGHT))
        #lights
        pygame.draw.rect(screen, YELLOW, (self.x + 5, self.y, 5, 5))
        pygame.draw.rect(screen, YELLOW, (self.x + CAR_WIDTH - 10, self.y, 5, 5))
        pygame.draw.rect(screen, RED, (self.x + 5, self.y + CAR_HEIGHT - 5, 5, 5))
        pygame.draw.rect(screen, RED, (self.x + CAR_WIDTH - 10, self.y + CAR_HEIGHT - 5, 5, 5))

if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
