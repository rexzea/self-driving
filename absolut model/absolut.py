import pygame
import random
import sys
import math

pygame.init()

SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 900
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)

CAR_WIDTH = 30
CAR_HEIGHT = 60
CAR_SPEED = 5
TURN_SPEED = 5

OBSTACLE_WIDTH = 60
OBSTACLE_HEIGHT = 60
OBSTACLE_SPEED = 3
NUM_OBSTACLES = 3

SENSOR_LENGTH = 200
NUM_SENSORS = 30

class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = CAR_SPEED  
        self.rect = pygame.Rect(x, y, CAR_WIDTH, CAR_HEIGHT)
        self.sensors = []
        self.sensor_readings = [SENSOR_LENGTH] * NUM_SENSORS
        self.turning = 0 
        self.safe_distance = SENSOR_LENGTH * 0.6
        
    def move(self, obstacles):
        self.update_sensors(obstacles)

        front_sensor = self.sensor_readings[1]
        left_sensor = self.sensor_readings[0]
        right_sensor = self.sensor_readings[2]
        
        self.turning = 0

        if front_sensor < self.safe_distance:
            if left_sensor > right_sensor and left_sensor > CAR_WIDTH * 2:
                self.turning = -1 
            elif right_sensor > left_sensor and right_sensor > CAR_WIDTH * 2:
                self.turning = 1   
            else:
                self.speed = max(1, self.speed - 0.5)
        else:
            if left_sensor < self.safe_distance * 0.5:
                self.turning = 1
            elif right_sensor < self.safe_distance * 0.5:
                self.turning = -1
            else:
                self.speed = min(CAR_SPEED, self.speed + 0.2)
        
        if self.turning != 0:
            self.x += TURN_SPEED * self.turning

        self.y -= self.speed  

        if self.y < -CAR_HEIGHT:
            self.y = SCREEN_HEIGHT
        
        self.x = max(0, min(self.x, SCREEN_WIDTH - CAR_WIDTH))
        
        self.rect.x = self.x
        self.rect.y = self.y

    def update_sensors(self, obstacles):
        self.sensors = []
        sensor_angles = [-50, -20, 0, 20, 50]  
        
        for i, angle in enumerate(sensor_angles):
            angle_rad = math.radians(angle)
            start_x = self.x + CAR_WIDTH/2
            start_y = self.y + CAR_HEIGHT/2
            end_x = start_x + math.sin(angle_rad) * SENSOR_LENGTH
            end_y = start_y - math.cos(angle_rad) * SENSOR_LENGTH

            self.sensors.append(((start_x, start_y), (end_x, end_y)))

            min_distance = SENSOR_LENGTH

            for obstacle in obstacles:
                obstacle_center_x = obstacle.rect.centerx
                obstacle_center_y = obstacle.rect.centery

                dx = obstacle_center_x - start_x
                dy = obstacle_center_y - start_y
                distance = math.sqrt(dx*dx + dy*dy)

                if distance < min_distance:
                    obstacle_angle = math.degrees(math.atan2(dx, -dy))
                    if abs(obstacle_angle - angle) < 30:
                        min_distance = distance - OBSTACLE_WIDTH/2
            
            self.sensor_readings[i] = max(0, min_distance)

    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, self.rect)
        pygame.draw.line(screen, YELLOW, 
                        (self.x + CAR_WIDTH/4, self.y + CAR_HEIGHT*0.8),
                        (self.x + CAR_WIDTH*3/4, self.y + CAR_HEIGHT*0.8), 3)

        for i, sensor in enumerate(self.sensors):
            intensity = min(255, int(255 * self.sensor_readings[i] / SENSOR_LENGTH))
            sensor_color = (255, intensity, intensity)  
            pygame.draw.line(screen, sensor_color, sensor[0], sensor[1], 3)

class Obstacle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x = random.randint(0, SCREEN_WIDTH - OBSTACLE_WIDTH)
        self.y = random.randint(-SCREEN_HEIGHT, -OBSTACLE_HEIGHT)
        self.rect = pygame.Rect(self.x, self.y, OBSTACLE_WIDTH, OBSTACLE_HEIGHT)
    
    def move(self):
        self.y += OBSTACLE_SPEED
        if self.y > SCREEN_HEIGHT:
            self.reset()
        self.rect.y = self.y
    
    def draw(self, screen):
        pygame.draw.rect(screen, RED, self.rect)
        pygame.draw.rect(screen, (200, 0, 0), 
                        (self.x + 5, self.y + 5, OBSTACLE_WIDTH - 10, OBSTACLE_HEIGHT - 10))

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Rexzea Self-Driving Car Simulation")
    clock = pygame.time.Clock()
    
    car = Car(SCREEN_WIDTH/2 - CAR_WIDTH/2, SCREEN_HEIGHT - CAR_HEIGHT - 20)
    obstacles = [Obstacle() for _ in range(NUM_OBSTACLES)]

    score = 0
    font = pygame.font.Font(None, 36)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    car = Car(SCREEN_WIDTH/2 - CAR_WIDTH/2, SCREEN_HEIGHT - CAR_HEIGHT - 20)
                    obstacles = [Obstacle() for _ in range(NUM_OBSTACLES)]
                    score = 0

        car.move(obstacles)
        for obstacle in obstacles:
            obstacle.move()

            if car.rect.colliderect(obstacle.rect):
                game_over_text = font.render(f"Game Over! Score: {score} - Press SPACE to restart", True, WHITE)
                screen.blit(game_over_text, (SCREEN_WIDTH/2 - game_over_text.get_width()/2, SCREEN_HEIGHT/2))
                pygame.display.flip()

                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                            waiting = False
                        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                            car = Car(SCREEN_WIDTH/2 - CAR_WIDTH/2, SCREEN_HEIGHT - CAR_HEIGHT - 20)
                            obstacles = [Obstacle() for _ in range(NUM_OBSTACLES)]
                            score = 0
                            waiting = False
                continue

        score += 1

        screen.fill(BLACK)
        
        for y in range(0, SCREEN_HEIGHT, 100):
            pygame.draw.rect(screen, GRAY, (SCREEN_WIDTH/2 - 5, y, 10, 50))

        car.draw(screen)
        for obstacle in obstacles:
            obstacle.draw(screen)

        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()