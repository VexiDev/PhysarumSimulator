from dotenv import load_dotenv
import numpy as np
import random
import math
import sys
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

class Particle:
    def __init__(self, x, y, trail_max_frames):
        self.id = random.randint(1, PARTICLE_COUNT+1)
        self.x = x
        self.y = y
        self.dx = random.uniform(-1, 1)
        self.dy = random.uniform(-1, 1)
        self.prev_dx = self.dx
        self.prev_dy = self.dy
        self.past_positions = np.full((trail_max_frames, 2), fill_value=[self.x, self.y])
        self.target = [None, None]
        self.trail_index = 0
        self.trail_length = trail_max_frames
        self.updates = 0

    def update_past_positions(self, trail_data):
        # Shift the old positions
        self.past_positions = np.roll(self.past_positions, -1, axis=0)
        
        # Add the new position
        self.past_positions[-1] = [self.x, self.y]

        # Update trail_data with the new position
        x, y = self.past_positions[-1]
        if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
            # We assume the fade value to be 1 for the newest position
            trail_data[int(x), int(y)] = TRAIL_MAX_FRAMES

        # Return the updated trail_data
        return trail_data

    def angle_between_vectors(self, dx1, dy1, dx2, dy2):
        # Calculate the angle between two vectors
        dot_product = dx1 * dx2 + dy1 * dy2
        magnitude_product = ((dx1**2 + dy1**2)**0.5) * ((dx2**2 + dy2**2)**0.5)
        try:
            return math.acos(dot_product / magnitude_product)
        except:
            return 0

    def update(self, trail_data):
        # Define the visibility cone
        cone_mask = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH), dtype=np.float32)
        direction = math.atan2(self.dy, self.dx)
        left_angle = direction - math.pi / 6  # 30 degrees to the left
        right_angle = direction + math.pi / 6  # 30 degrees to the right

        # Generate cone points using polar coordinates
        for r in range(3,22):  # 20 pixels deep
            for theta in np.linspace(left_angle, right_angle, r + 1):  # 60 degrees wide
                x = int(self.x + r * math.cos(theta))
                y = int(self.y + r * math.sin(theta))
                if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                    cone_mask[x,y] = 1.0

        # Extract the visible trails
        visible_trails = trail_data * cone_mask

        # Ignore the trail points that are directly behind the particle
        # back_mask = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH), dtype=bool)
        # back_direction = math.atan2(-self.dy, -self.dx)
        # back_left_angle = back_direction - math.pi / 6  # 30 degrees to the left
        # back_right_angle = back_direction + math.pi / 6  # 30 degrees to the right
        # for r in range(10):  # 10 pixels deep behind the particle
        #     for theta in np.linspace(back_left_angle, back_right_angle, r + 1):  # 60 degrees wide
        #         x = int(self.x + r * math.cos(theta))
        #         y = int(self.y + r * math.sin(theta))
        #         if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
        #             back_mask[y, x] = True
        # visible_trails = visible_trails * ~back_mask

        max_intensity = np.max(visible_trails)
        max_index = np.argmax(visible_trails)

        # Converting the index to coordinates
        num_rows, num_cols = visible_trails.shape
        row_index = max_index // num_cols
        col_index = max_index % num_cols

        # If the particle is not on a trail, follow the least faded trail
        if max_intensity > 0:
            max_intensity_indices = np.array(np.where(visible_trails == max_intensity)).T
            closest_index = min(max_intensity_indices, key=lambda index: np.linalg.norm([self.y - index[0], self.x - index[1]]))
            #closest_index = closest_index[::-1]  # swap x and y

            # Compute direction to the least faded section of the trail
            dir_x = closest_index[0] - self.x
            dir_y = closest_index[1] - self.y
            magnitude = math.sqrt(dir_x ** 2 + dir_y ** 2)

            # Only change direction if the trail intensity is above a certain level and the trail is not newly created
            if max_intensity > TRAIL_ATTRACTION:
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

        if self.x < EDGE_FORCE:
            self.dx += (EDGE_FORCE - self.x) * 0.1
        elif self.x > SCREEN_WIDTH - EDGE_FORCE:
            self.dx -= (self.x - (SCREEN_WIDTH - EDGE_FORCE)) * 0.1

        if self.y < EDGE_FORCE:
            self.dy += (EDGE_FORCE - self.y) * 0.1
        elif self.y > SCREEN_HEIGHT - EDGE_FORCE:
            self.dy -= (self.y - (SCREEN_HEIGHT - EDGE_FORCE)) * 0.1

        # Normalize speed
        direction_magnitude = math.sqrt(self.dx ** 2 + self.dy ** 2)

        if direction_magnitude > 0:
            # Normalize the direction
            direction_dx = self.dx / direction_magnitude
            direction_dy = self.dy / direction_magnitude
            # Apply the desired speed
            self.dx = direction_dx * SPEED
            self.dy = direction_dy * SPEED

        self.x += self.dx
        self.y += self.dy

        trail_data = self.update_past_positions(trail_data)

        self.updates += 1

        # with open('output.txt', 'a') as file:
        #     print(f"#xy {self.x}, {self.y}", file=file)
        #     print(f"#dxdy {self.dx}, {self.dy}", file=file)
    
        return trail_data,cone_mask

