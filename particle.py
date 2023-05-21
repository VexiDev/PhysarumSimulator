from dotenv import load_dotenv
import numpy as np
import random
import math
import os

# Load the .env file
load_dotenv()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = int(os.getenv('SCREEN_WIDTH')), int(os.getenv('SCREEN_HEIGHT'))

PARTICLE_COUNT = int(os.getenv('PARTICLE_COUNT'))
RANDOM_PARTICLE_POSITIONS = os.getenv("RANDOM_PARTICLE_POSITIONS", 'False').lower() in ('true', '1', 't')
SPEED = float(os.getenv('SPEED'))

CONE_ANGLE = float(os.getenv('CONE_ANGLE'))
CONE_LENGTH = float(os.getenv('CONE_LENGTH'))

EDGE_FORCE = int(2*CONE_LENGTH+10) 
TRAIL_ATTRACTION = float(os.getenv('TRAIL_ATTRACTION')) # Strength of trail attraction
DETECTION_THRESHOLD = float(os.getenv('DETECTION_THRESHOLD')) # Strength of trail attraction
MIN_TRAIL_STRENGTH = float(os.getenv('MIN_TRAIL_STRENGTH')) # Strength of trail attraction

TRAIL_MAX_TIME = int(os.getenv('TRAIL_MAX_TIME'))  # Maximum trail time in seconds
TRAIL_MAX_FRAMES = TRAIL_MAX_TIME * 60 # do not change


class Particle:
    def __init__(self, x, y, trail_max_frames):
        self.id = random.randint(1, PARTICLE_COUNT+1)
        self.x = x
        self.y = y
        self.dx = random.uniform(-1, 1)
        self.dy = random.uniform(-1, 1)
        self.prev_dx = self.dx
        self.prev_dy = self.dy
        self.past_positions = np.full((1000, 2), fill_value=[self.x, self.y])
        self.target = [None, None]
        self.disable_detection = False
        self.trail_length =0
        #self.trail_index = 0
        # self.trail_length = trail_max_frames
        self.trail_strength = TRAIL_ATTRACTION

    def reset(self,x,y, trail_max_frames):
        if not RANDOM_PARTICLE_POSITIONS:
            self.x = x
            self.y = y
        else:
            self.x = random.randint(EDGE_FORCE, SCREEN_WIDTH - EDGE_FORCE)
            self.y = random.randint(EDGE_FORCE, SCREEN_HEIGHT - EDGE_FORCE)
        self.dx = random.uniform(-1, 1)
        self.dy = random.uniform(-1, 1)
        self.prev_dx = self.dx
        self.prev_dy = self.dy
        self.past_positions = np.full((1000, 2), fill_value=[self.x, self.y])
        self.target = [None, None]
        self.disable_detection = False
        self.trail_length=0
        #self.trail_index = 0
        #self.trail_length = trail_max_frames
        self.trail_strength = TRAIL_ATTRACTION

    def update_past_positions(self, trail_data):
        # Shift the old positions
        self.past_positions = np.roll(self.past_positions, -1, axis=0)
        
        # Add the new position
        self.past_positions[-1] = [self.x, self.y]

        # Update trail_data with the new position
        # x, y = self.past_positions[-1]  
        # if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
        #      # We assume the fade value to be 1 for the newest position
        #     trail_data[int(x), int(y)] = TRAIL_ATTRACTION #self.trail_strength

        val = self.trail_strength * self.trail_length
        # dv = self.trail_strength / (4*len(self.past_positions))
        dv = 0.001 
        for pos in self.past_positions[::-1]:
           x,y = pos
           if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
              # We assume the fade value to be 1 for the newest position
              if trail_data[int(x), int(y)] < val:
                trail_data[int(x), int(y)] = val
           val -= dv


        # Return the updated trail_data
        return trail_data

    def path_length(self):
        # Calculate the length of the path
        return np.sum(np.linalg.norm(np.diff(self.past_positions, axis=0), axis=1))

    def angle_between_vectors(self, dx1, dy1, dx2, dy2):
        # Calculate the angle between two vectors
        dot_product = dx1 * dx2 + dy1 * dy2
        magnitude_product = ((dx1**2 + dy1**2)**0.5) * ((dx2**2 + dy2**2)**0.5)
        try:
            return math.acos(dot_product / magnitude_product)
        except:
            return 0

    def detect(self, trail_data_in, city_data_in, px, py):

        trail_data = trail_data_in[int(self.x-CONE_LENGTH):int(self.x+CONE_LENGTH), int(self.y-CONE_LENGTH):int(self.y+CONE_LENGTH)].copy()

        cdat = city_data_in[int(self.x-CONE_LENGTH):int(self.x+CONE_LENGTH), int(self.y-CONE_LENGTH):int(self.y+CONE_LENGTH)]
        trail_data += cdat

        self.trail_strength = float(np.max(cdat))
        if self.trail_strength<MIN_TRAIL_STRENGTH:
            self.trail_strength=MIN_TRAIL_STRENGTH

        if self.disable_detection and self.trail_strength<0.4:
           self.disable_detection = False

        # Define the visibility cone
        # cone_mask = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH), dtype=np.float32)
        cone_mask = np.zeros((trail_data.shape[0], trail_data.shape[1]), dtype=np.float32)
        direction = math.atan2(self.dy, self.dx)
        left_angle = direction - ((math.pi * (CONE_ANGLE/2))/180)  # 30 degrees to the left
        right_angle = direction + ((math.pi * (CONE_ANGLE/2))/180)  # 30 degrees to the right

        # Generate cone points using polar coordinates
        for r in range(3,int(CONE_LENGTH+2)):  # 20 pixels deep
            for theta in np.linspace(left_angle, right_angle, 2*r + 1):  # 60 degrees wide
                x = int(CONE_LENGTH + r * math.cos(theta))
                y = int(CONE_LENGTH + r * math.sin(theta))
                if 0 <= x < cone_mask.shape[0] and 0 <= y < cone_mask.shape[1]:
                    cone_mask[x,y] = 1.0

        # Extract the visible trails
        visible_trails = trail_data * cone_mask
        try:
            max_intensity = np.max(visible_trails)
        except:
            print(visible_trails.shape)
        max_index = np.argmax(visible_trails)

        # Converting the index to coordinates
        num_rows, num_cols = visible_trails.shape
        row_index = max_index // num_cols
        col_index = max_index % num_cols

        # If the particle is not on a trail, follow the least faded trail
        if max_intensity > 0:

            max_intensity_indices = np.array(np.where(visible_trails == max_intensity)).T
            closest_index = min(max_intensity_indices, key=lambda index: np.linalg.norm([self.y - index[0], self.x - index[1]]))

            # Compute direction to the least faded section of the trail
            dir_x = closest_index[0] - CONE_LENGTH#self.x
            dir_y = closest_index[1] - CONE_LENGTH#self.y

            # break away from trails every probability
            if np.random.random()<0.4:
                # randomly pick a direction in a 90 degree cone
                #  current_angle = np.arctan2(dir_y, dir_x)  # get the current angle (in radians)
                #  delta_angle = np.random.uniform(-np.pi / 4, np.pi / 4)  # change within +/-45 degrees (in radians)
                #  new_angle = current_angle + delta_angle
                #  mag = np.sqrt(dir_x**2 + dir_y**2)
                #  dir_x = mag * np.cos(new_angle)
                #  dir_y = mag * np.sin(new_angle)
                dir_x = np.random.uniform()*2-1
                dir_y = np.random.uniform()*2-1

                

            magnitude = math.sqrt(dir_x ** 2 + dir_y ** 2)

            # Only change direction if the trail intensity is above a certain level and the trail is not newly created
            if max_intensity > DETECTION_THRESHOLD and self.disable_detection != True:
                self.dx += (dir_x / magnitude) * TRAIL_ATTRACTION
                self.dy += (dir_y / magnitude) * TRAIL_ATTRACTION
                self.target = closest_index  # Set the target attribute
                # print(f"Particle attracted to trail at {closest_index} with intensity {max_intensity}")

        # If the target exists and is not inside the viewing cone or the particle has reached the target, remove it
        if self.target[0] is not None and self.target[1] is not None:
            target_y, target_x = self.target
            distance_to_target = math.sqrt((self.x - target_x) ** 2 + (self.y - target_y) ** 2)
            if not cone_mask[int(target_y), int(target_x)] or distance_to_target < 1:
                # print(f"Particle lost sight of trail at {self.target}")
                self.target = [None,None]  # Reset the target attribute

        # if self.x < EDGE_FORCE:
        #     self.dx += (EDGE_FORCE - self.x) * 0.1
        # elif self.x > SCREEN_WIDTH - EDGE_FORCE:
        #     self.dx -= (self.x - (SCREEN_WIDTH - EDGE_FORCE)) * 0.1

        # if self.y < EDGE_FORCE:
        #     self.dy += (EDGE_FORCE - self.y) * 0.1
        # elif self.y > SCREEN_HEIGHT - EDGE_FORCE:
        #     self.dy -= (self.y - (SCREEN_HEIGHT - EDGE_FORCE)) * 0.1

        if self.x < EDGE_FORCE or self.x > SCREEN_WIDTH - EDGE_FORCE or self.y < EDGE_FORCE or self.y > SCREEN_HEIGHT - EDGE_FORCE:
            self.reset(px, py, TRAIL_MAX_FRAMES)
        
        # Normalize speed
        direction_magnitude = math.sqrt(self.dx ** 2 + self.dy ** 2)

        if direction_magnitude > 0:
            # Normalize the direction
            direction_dx = self.dx / direction_magnitude
            direction_dy = self.dy / direction_magnitude
            # Apply the desired speed
            self.dx = direction_dx * SPEED
            self.dy = direction_dy * SPEED
        
        return cone_mask
    
    def update_position(self):
        
        if self.trail_strength>0.999999:
            print(self.trail_strength)
            return
        self.x += self.dx
        self.y += self.dy
    
        return

