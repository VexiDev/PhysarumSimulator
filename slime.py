from dotenv import load_dotenv
from particle import Particle
from city import City
import numpy as np
import threading
import pygame
import random
import time
import math
import os

# Load the .env file
load_dotenv()
FPS = int(os.getenv('FPS'))

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = int(os.getenv('SCREEN_WIDTH')), int(os.getenv('SCREEN_HEIGHT'))

PARTICLE_COUNT = int(os.getenv('PARTICLE_COUNT'))
RANDOM_PARTICLE_POSITIONS = os.getenv("RANDOM_PARTICLE_POSITIONS", 'False').lower() in ('true', '1', 't')
SPEED = float(os.getenv('SPEED'))


CONE_ANGLE = float(os.getenv('CONE_ANGLE'))
CONE_LENGTH = float(os.getenv('CONE_LENGTH'))

EDGE_FORCE = int(2*CONE_LENGTH+10) 
TRAIL_ATTRACTION = float(os.getenv('TRAIL_ATTRACTION')) # Strength of trail attraction

TRAIL_MAX_TIME = int(os.getenv('TRAIL_MAX_TIME'))  # Maximum trail time in seconds
TRAIL_MAX_FRAMES = TRAIL_MAX_TIME * int(os.getenv("FPS")) # do not change

CITY_COUNT = int(os.getenv('CITY_COUNT'))
CITY_RADIUS = int(os.getenv('CITY_RADIUS'))

DEBUG = os.getenv("DEBUG", 'False').lower() in ('true', '1', 't')
SHOW_PARTICLES = os.getenv("SHOW_PARTICLES", 'False').lower() in ('true', '1', 't')
SHOW_CITY = os.getenv("SHOW_CITIES", 'False').lower() in ('true', '1', 't')
SHOW_RADIUS = os.getenv("SHOW_RADIUS", 'False').lower() in ('true', '1', 't')


if DEBUG:
    print("DEBUG MODE ENABLED")

if SHOW_PARTICLES:
    print("SHOW_PARTICLES ENABLED")

if SHOW_CITY:
    print("SHOW_CITY ENABLED")

if SHOW_RADIUS:
    print("SHOW_RADIUS ENABLED")

if RANDOM_PARTICLE_POSITIONS:
    print("RANDOM_PARTICLE_POSITIONS ENABLED")

# Initial setup
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
elapsed_time = 0

px = EDGE_FORCE
py = SCREEN_HEIGHT-EDGE_FORCE

if RANDOM_PARTICLE_POSITIONS:
    particles = [
    Particle(
        random.randint(EDGE_FORCE, SCREEN_WIDTH - EDGE_FORCE),
        random.randint(EDGE_FORCE, SCREEN_HEIGHT - EDGE_FORCE),
        TRAIL_MAX_FRAMES
    ) for _ in range(PARTICLE_COUNT)
    ]
else:
    particles = [
    Particle(
        px,py,
        TRAIL_MAX_FRAMES
    ) for _ in range(PARTICLE_COUNT)
    ]


cities = [City() for _ in range(CITY_COUNT)]  # you can define NUMBER_OF_CITIES as per your requirement

city_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)

for city in cities:
    city_data += city.generate_city_data()
city_data = np.maximum(city_data, 0)

trail_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)

# update dx, dy from trail data including trail attraction and boundary repulsion   
cone_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)

def add_particles(px,py):
    global particles
    if RANDOM_PARTICLE_POSITIONS:
        for _ in range(PARTICLE_COUNT):
            particles.append(Particle(
                random.randint(EDGE_FORCE, SCREEN_WIDTH - EDGE_FORCE),
                random.randint(EDGE_FORCE, SCREEN_HEIGHT - EDGE_FORCE),
                TRAIL_MAX_FRAMES
            ))
    else:
        for _ in range(PARTICLE_COUNT):
            particles.append(Particle(
                px,py,
                TRAIL_MAX_FRAMES
            ))
        

def sim_update():
    # while True:
    global trail_data
    global city_data
    global cone_data
    global particles

    # update particle position from dx,dy
    for particle in particles:
        particle.update_position()

    # update trails array
    for particle in particles:
        particle.update_past_positions(trail_data)

    # update dx, dy from trail data including trail attraction and boundary repulsion   
    cone_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)
    for particle in particles:
        conem = particle.detect(trail_data, city_data)
        cone_data[int(particle.x-CONE_LENGTH):int(particle.x+CONE_LENGTH), int(particle.y-CONE_LENGTH):int(particle.y+CONE_LENGTH)] += conem

    # reduce the trail over time
    trail_data = np.maximum(trail_data - TRAIL_ATTRACTION/TRAIL_MAX_FRAMES, 0)

    # time.sleep(1/FPS)

# thread = threading.Thread(target=sim_update)

# thread.start()

running = True
counter = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if counter % 300 == 0:
        print('adding more particles')
        add_particles(px, py)
           
    # if counter % 500 == 0:
    #    print('resetting particles')
    #    for particle in particles:
    #        particle.reset(px, py, TRAIL_MAX_FRAMES)
    
    sim_update()

    screen.fill((0, 0, 0))

    # Use pygame.surfarray to draw the trails
    trail_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    trail_rgb = np.repeat(trail_data[:, :, np.newaxis], 3, axis=2)*255

    if SHOW_RADIUS == True:
        city_rgb = np.repeat(city_data[:, :, np.newaxis], 3, axis=2)
        city_rgb[:,:,0] = city_data * 255 # Red channel
        city_rgb[:,:,1] = city_data * 255 # Green channel
        city_rgb[:,:,2] = 0 # Blue channel
        trail_rgb += city_rgb

    if DEBUG == True:
        cone_rgb = np.repeat(cone_data[:, :, np.newaxis], 3, axis=2)
        trail_rgb += cone_rgb*50
        
    #if DEBUG == True or SHOW_RADIUS == True:
    trail_rgb = np.minimum(trail_rgb, 255)

    pygame.surfarray.blit_array(trail_surface, trail_rgb)
    screen.blit(trail_surface, (0, 0))

    # Use pygame.surfarray to draw the cone
    # cone_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    # pygame.surfarray.blit_array(cone_surface, cone_rgb)
    # screen.blit(cone_surface, (0, 0))


    # Draw simulation
    for idx,particle in enumerate(particles):
        
        
        if SHOW_CITY == True:
            for city in cities:
                # Draw the city center
                pygame.draw.circle(screen, (0, 172, 92), (int(city.x), int(city.y)), 6)
        
        if DEBUG == True:
            # Calculate the points for the cone
            direction = math.atan2(particle.dy, particle.dx)
            left_angle = direction - ((math.pi * (CONE_ANGLE/2))/180)
            right_angle = direction + ((math.pi * (CONE_ANGLE/2))/180)

            # Calculate the points of the lines
            left_line_start = (int(particle.x), int(particle.y))
            left_line_end = (int(particle.x + CONE_LENGTH * math.cos(left_angle)), int(particle.y + CONE_LENGTH * math.sin(left_angle)))
            right_line_start = (int(particle.x), int(particle.y))
            right_line_end = (int(particle.x + CONE_LENGTH * math.cos(right_angle)), int(particle.y + CONE_LENGTH * math.sin(right_angle)))

            # Draw the cone lines
            pygame.draw.line(screen, (0, 0, 255), left_line_start, left_line_end, 1)
            pygame.draw.line(screen, (0, 0, 255), right_line_start, right_line_end, 1)

        if SHOW_PARTICLES == True:
            # Draw the particle
            pygame.draw.circle(screen, (255, 0, 0), (int(particle.x), int(particle.y)), 2)
        
        if DEBUG == True:
            # Direction of the particle
            pygame.draw.line(screen, (0, 255, 0), (int(particle.x), int(particle.y)), (int(particle.x + particle.dx*10), int(particle.y + particle.dy*10)), 1)
            # Target of the particle
            if particle.target[0] is not None and particle.target[1] is not None:
                pygame.draw.line(screen, (255, 0, 255), (int(particle.x), int(particle.y)), (int(particle.target[0]+particle.x-CONE_LENGTH), int(particle.target[1]+particle.y-CONE_LENGTH)), 1)
        

    pygame.display.flip()
    clock.tick(FPS)
    # dt = clock.tick(FPS)
    # elapsed_time += dt

    # if elapsed_time >= 20000:
    #     print('resetting particles')
    #     for particle in particles:
    #         particle.reset(px, py, TRAIL_MAX_FRAMES)
    #     elapsed_time -= 20000

    counter += 1

pygame.quit()

