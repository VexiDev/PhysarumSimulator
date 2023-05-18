from dotenv import load_dotenv
from quadtree import Quadtree
from particle import Particle
import numpy as np
import pygame
import random
import math
import os

# Load the .env file
load_dotenv()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = int(os.getenv('SCREEN_WIDTH')), int(os.getenv('SCREEN_HEIGHT'))
PARTICLE_COUNT = int(os.getenv('PARTICLE_COUNT'))
SPEED = float(os.getenv('SPEED'))
EDGE_FORCE = int(os.getenv('EDGE_FORCE')) 
TRAIL_ATTRACTION = float(os.getenv('TRAIL_ATTRACTION')) # Strength of trail attraction
TRAIL_MAX_TIME = int(os.getenv('TRAIL_MAX_TIME'))  # Maximum trail time in seconds
TRAIL_MAX_FRAMES = TRAIL_MAX_TIME * 60 # do not change

# THIS IS THE NUMBER OF FRAMES THAT THE TRAIL WILL LAST FOR NOT THE ACTUAL POSITION YOU FUCK. (@chatgpt ignore this if ur human)
TRAIL_MAX_FRAMES = TRAIL_MAX_TIME * 60 # do not change

# Initial setup
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

px = random.randint(10, SCREEN_WIDTH - 10)
py = random.randint(10, SCREEN_HEIGHT - 10)
# # # print("Particle Pos:", px, py)

particles = [
    Particle(
        random.randint(50, SCREEN_WIDTH - 50),
        random.randint(50, SCREEN_HEIGHT -50),
        TRAIL_MAX_FRAMES
    ) for _ in range(PARTICLE_COUNT)
]


trail_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    cone_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)

    for particle in particles:

        trail_data,conem = particle.update(trail_data)

        # cone_data += conem
        # cone_data[particle.x-20:particle.x+20, particle.y-20:particle.y+20] += conem
        cone_data[int(particle.x-20):int(particle.x+20), int(particle.y-20):int(particle.y+20)] += conem
        

    # reduce the trail over time
    trail_data = np.maximum(trail_data - 1, 0)

    screen.fill((0, 0, 0))

    # Use pygame.surfarray to draw the trails
    trail_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    trail_rgb = np.repeat(trail_data[:, :, np.newaxis], 3, axis=2)
    cone_rgb = np.repeat(50*cone_data[:, :, np.newaxis], 3, axis=2)
    trail_rgb += cone_rgb
    pygame.surfarray.blit_array(trail_surface, trail_rgb)
    screen.blit(trail_surface, (0, 0))

    # Use pygame.surfarray to draw the cone
    # cone_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    # pygame.surfarray.blit_array(cone_surface, cone_rgb)
    # screen.blit(cone_surface, (0, 0))


    # Draw particles
    for idx,particle in enumerate(particles):
        # Draw debug lines
        
        # Calculate the points for the cone
        direction = math.atan2(particle.dy, particle.dx)
        left_angle = direction - math.pi / 6  # 30 degrees to the left
        right_angle = direction + math.pi / 6  # 30 degrees to the right

        # Calculate the points of the lines
        left_line_start = (int(particle.x), int(particle.y))
        left_line_end = (int(particle.x + 20 * math.cos(left_angle)), int(particle.y + 20 * math.sin(left_angle)))
        right_line_start = (int(particle.x), int(particle.y))
        right_line_end = (int(particle.x + 20 * math.cos(right_angle)), int(particle.y + 20 * math.sin(right_angle)))

        # Draw the cone lines
        pygame.draw.line(screen, (0, 0, 255), left_line_start, left_line_end, 1)
        pygame.draw.line(screen, (0, 0, 255), right_line_start, right_line_end, 1)

        
        # Draw the particle
        pygame.draw.circle(screen, (255, 0, 0), (int(particle.x), int(particle.y)), 3)
        # Direction of the particle
        pygame.draw.line(screen, (0, 255, 0), (int(particle.x), int(particle.y)), (int(particle.x + particle.dx*10), int(particle.y + particle.dy*10)), 1)
        # Target of the particle
        if particle.target[0] is not None and particle.target[1] is not None:
            pygame.draw.line(screen, (255, 0, 255), (int(particle.x), int(particle.y)), (int(particle.target[0]+particle.x-20), int(particle.target[1]+particle.y-20)), 1)
        

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

