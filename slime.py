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

particles = [
    Particle(
        random.uniform(10, SCREEN_WIDTH - 10),
        random.uniform(10, SCREEN_HEIGHT - 10),
        TRAIL_MAX_FRAMES
    ) for _ in range(PARTICLE_COUNT)
]


trail_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)

# quadtree = Quadtree((SCREEN_WIDTH/2, SCREEN_HEIGHT/2, SCREEN_WIDTH/2, SCREEN_HEIGHT/2), 4)

#add an active particles list here that stores all the particles that are currently active so that we can update their past positions

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    

    new_trails = []
    for particle in particles:
        # Update the particle's position
        past_positions = particle.update(trail_data)
            
        # Store the particle's past positions to be added to the trail data later
        for i in range(particle.trail_length):
            y, x = map(int, particle.past_positions[particle.trail_length - 1 - i])
            if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                new_trails.append((y, x, TRAIL_MAX_FRAMES - i))

    # Update the trail data with the new trails
    for y, x, value in new_trails:
        trail_data[y, x] = value


    # reduce the trail over time
    trail_data = np.maximum(trail_data - 1, 0)

    screen.fill((0, 0, 0))

    # Use pygame.surfarray to draw the trails
    trail_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    trail_rgb = np.repeat(trail_data[:, :, np.newaxis], 3, axis=2)
    pygame.surfarray.blit_array(trail_surface, trail_rgb)
    screen.blit(trail_surface, (0, 0))

    # Draw particles
    for idx,particle in enumerate(particles):
        # Draw debug lines
        # Direction of the particle
        pygame.draw.line(screen, (0, 255, 0), (int(particle.x), int(particle.y)), (int(particle.x + particle.dx*20), int(particle.y + particle.dy*20)), 1)
        
        # Calculate the points for the cone
        direction = math.atan2(particle.dy, particle.dx)
        left_angle = direction - math.pi / 6  # 30 degrees to the left
        right_angle = direction + math.pi / 6  # 30 degrees to the right

        # Calculate the points of the lines
        left_line_start = (int(particle.x), int(particle.y))
        left_line_end = (int(particle.x + 20 * math.cos(left_angle)), int(particle.y + 20 * math.sin(left_angle)))
        right_line_start = (int(particle.x), int(particle.y))
        right_line_end = (int(particle.x + 20 * math.cos(right_angle)), int(particle.y + 20 * math.sin(right_angle)))

        # Draw the lines
        pygame.draw.line(screen, (0, 0, 255), left_line_start, left_line_end, 1)
        pygame.draw.line(screen, (0, 0, 255), right_line_start, right_line_end, 1)

        
        # Draw the particle
        pygame.draw.circle(screen, (255, 0, 0), (int(particle.x), int(particle.y)), 3)
        # Target of the particle
        if hasattr(particle, 'target'):
            pygame.draw.line(screen, (255, 0, 255), (int(particle.x), int(particle.y)), (int(particle.target[0]), int(particle.target[1])), 1)
        

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

