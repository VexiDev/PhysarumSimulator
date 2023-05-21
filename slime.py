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
SPEED = float(os.getenv('SPEED'))
RANDOM_PARTICLE_POSITIONS = os.getenv("RANDOM_PARTICLE_POSITIONS", 'False').lower() in ('true', '1', 't')
RESET_OLD = os.getenv("RESET_OLD", 'False').lower() in ('true', '1', 't')


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
pygame.display.set_caption("Particle Physarium Simulator")
clock = pygame.time.Clock()
elapsed_time = 0

# px = EDGE_FORCE+CITY_RADIUS+50
# py = SCREEN_HEIGHT-EDGE_FORCE-CITY_RADIUS-50

# px += random.randint(0, 50)
# py -= random.randint(0, 50)

#cities = [City(0,0) for _ in range(CITY_COUNT)]  # you can define NUMBER_OF_CITIES as per your requirement
# cities = [City(px,py), City(216, 168),City(316,313), City(500, 100)]  # you can define NUMBER_OF_CITIES as per your requirement

cities = []
while True:
    x = random.randint(EDGE_FORCE+CITY_RADIUS, SCREEN_WIDTH - EDGE_FORCE-CITY_RADIUS)
    y = random.randint(EDGE_FORCE+CITY_RADIUS, SCREEN_HEIGHT - EDGE_FORCE-CITY_RADIUS)
    new_city_ok = True
    for existing_cites in cities:
        if math.sqrt((x - existing_cites.x) ** 2 + (y - existing_cites.y) ** 2) < 2.5*CITY_RADIUS:
            new_city_ok = False
            break    
    if new_city_ok:
        cities.append(City(x,y))
    if len(cities) == CITY_COUNT:
        break

px = cities[0].x
py = cities[0].y

city_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)

for city in cities:
    city_data += city.generate_city_data()
city_data = np.maximum(city_data, 0)

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
        px+random.randint(0, 20),
        py-random.randint(0, 20),
        TRAIL_MAX_FRAMES
    ) for _ in range(PARTICLE_COUNT)
    ]

trail_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)

# update dx, dy from trail data including trail attraction and boundary repulsion   
cone_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)

def add_particle(px,py):
    global particles
    if RANDOM_PARTICLE_POSITIONS:
        particles.append(Particle(
            random.randint(EDGE_FORCE, SCREEN_WIDTH - EDGE_FORCE),
            random.randint(EDGE_FORCE, SCREEN_HEIGHT - EDGE_FORCE),
            TRAIL_MAX_FRAMES
        ))
    else:
        particles.append(Particle(
        px,
        py,
            TRAIL_MAX_FRAMES
        ))
        
def reset_particles(counter):
    to_reset = []
    if counter % 600 == 0:
        print('Pulsing.')
        diff = 0
        for particle in particles:
            # if the particles are not in the city center
            if particle.stopped == True:
                x = random.uniform(0, 1)
                if x > 0.3:
                    diff += 1
                    particle.stopped = False
                    particle.disable_detection = True
                    particle.dx = random.uniform(-1, 1)
                    particle.dy = random.uniform(-1, 1)

                    #particle.reset(particle.x,particle.y, TRAIL_MAX_FRAMES)
            else:
                to_reset.append(particle)

        print("Disabled:", diff, "Safe:", len(particles)-diff)
    
        for p in to_reset:
            # add_particle(px+random.randint(0, 20), py-random.randint(0, 20))
            p.reset(px, py, TRAIL_MAX_FRAMES)

def sim_update(counter):
    # while True:
    global trail_data
    global city_data
    global cone_data
    global particles

    if RESET_OLD == True:
        reset_particles(counter)

    # update particle position from dx,dy
    for p in particles:
        p.update_position()

   # compute relative path length
    L = []
    for p in particles:
        L.append(p.path_length()+0.001)
    L = np.array(L)
    L =  1-(L/np.sum(L))**4.
    for idx,p in enumerate(particles):
        p.trail_length = 1.0#L[idx]

    # update trails array
    for p in particles:
        p.update_past_positions(trail_data)

    # update dx, dy from trail data including trail attraction and boundary repulsion   
    cone_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)
    for particle in particles:
        conem = particle.detect(trail_data, city_data, px, py)
        cone_data[int(particle.x-CONE_LENGTH):int(particle.x+CONE_LENGTH), int(particle.y-CONE_LENGTH):int(particle.y+CONE_LENGTH)] += conem

    # reduce the trail over time
    #trail_data = np.maximum(trail_data - TRAIL_ATTRACTION/TRAIL_MAX_FRAMES, 0)
    trail_data = np.maximum(trail_data - 0.02, 0)

    # print(np.min(trail_data[np.nonzero(trail_data)]))
    # trail_data /= np.max(trail_data)
    # time.sleep(1/FPS)
    # for p in particles:
    #     print(p.path_length())

# thread = threading.Thread(target=sim_update)

# thread.start()

running = True
counter = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                SHOW_PARTICLES = not SHOW_PARTICLES  
            elif event.key == pygame.K_c: 
                SHOW_CITY = not SHOW_CITY  
            elif event.key == pygame.K_r: 
                SHOW_RADIUS = not SHOW_RADIUS  
            elif event.key == pygame.K_d: 
                DEBUG = not DEBUG  

    sim_update(counter)

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
        
    trail_rgb = np.minimum(trail_rgb, 255)

    pygame.surfarray.blit_array(trail_surface, trail_rgb)
    screen.blit(trail_surface, (0, 0))

    # Draw simulation
    for idx,particle in enumerate(particles):
        
        
        if SHOW_CITY == True:
            for city in cities:
                # Draw the city center
                pygame.draw.circle(screen, (0, 172, 92), (int(city.x), int(city.y)), 8)
        
        # Draw a boundary square based to represent the EDGE_FORCE boundary
        pygame.draw.rect(screen, (150, 150, 150), (EDGE_FORCE, EDGE_FORCE, SCREEN_WIDTH - EDGE_FORCE * 2, SCREEN_HEIGHT - EDGE_FORCE * 2), 1)

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

    counter += 1

pygame.quit()

