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
SPEED = float(os.getenv('SPEED'))
EDGE_FORCE = int(os.getenv('EDGE_FORCE'))
TRAIL_ATTRACTION = float(os.getenv('TRAIL_ATTRACTION')) # Strength of trail attraction
TRAIL_MAX_TIME = int(os.getenv('TRAIL_MAX_TIME'))  # Maximum trail time in seconds
TRAIL_MAX_FRAMES = TRAIL_MAX_TIME * 60 # do not change

class Particle:
    def __init__(self, x, y, trail_max_frames):
        self.x = random.uniform(10, SCREEN_WIDTH - 10)
        self.y = random.uniform(10, SCREEN_HEIGHT - 10)
        self.dx = random.uniform(-1, 1)
        self.dy = random.uniform(-1, 1)
        self.prev_dx = self.dx
        self.prev_dy = self.dy
        self.past_positions = np.zeros((trail_max_frames, 2))
        self.trail_index = 0
        self.trail_length = trail_max_frames

    def update_past_positions(self):
        # Shift the old positions
        self.past_positions = np.roll(self.past_positions, -1, axis=0)
        
        # Add the new position
        self.past_positions[-1] = [self.x, self.y]

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
        cone_mask = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=bool)
        direction = math.atan2(self.dy, self.dx)
        left_angle = direction - math.pi / 6  # 30 degrees to the left
        right_angle = direction + math.pi / 6  # 30 degrees to the right

        # Generate cone points using polar coordinates
        for r in range(20):  # 20 pixels deep
            for theta in np.linspace(left_angle, right_angle, r + 1):  # 60 degrees wide
                x = int(self.x + r * math.cos(theta))
                y = int(self.y + r * math.sin(theta))
                if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                    cone_mask[y, x] = True

        # Extract the visible trails
        visible_trails = trail_data * cone_mask

        current_position = int(self.y), int(self.x)
        current_intensity = trail_data[current_position]
        trail_data[current_position] = 0

        max_intensity = np.max(visible_trails)

        # Reset the trail data at the particle's current position
        trail_data[current_position] = current_intensity

        if max_intensity > 0:
            max_intensity_indices = np.array(np.where(visible_trails == max_intensity)).T
            closest_index = min(max_intensity_indices, key=lambda index: np.linalg.norm([self.y - index[0], self.x - index[1]]))
            closest_index = closest_index[::-1]  # swap x and y

            # If the least faded section of the trail is not the particle itself
            if not np.array_equal(closest_index, np.array([self.x, self.y])):
                # Compute direction to the least faded section of the trail
                dir_x = closest_index[0] - self.x
                dir_y = closest_index[1] - self.y
                magnitude = math.sqrt(dir_x ** 2 + dir_y ** 2)

                print(f"dir_x: {dir_x}, dir_y: {dir_y}, magnitude: {magnitude}, max_intensity: {max_intensity}")

                # If the particle is close enough to the trail, follow it
                if magnitude > 0.4:  # Change this threshold as needed
                    self.dx = dir_x / magnitude
                    self.dy = dir_y / magnitude
                    self.target = closest_index  # Set the target attribute

        # If the target exists and is not inside the viewing cone, remove it
        if hasattr(self, 'target'):
            target_y, target_x = self.target
            if not cone_mask[int(target_y), int(target_x)]:
                del self.target  # Remove the target attribute

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

        self.update_past_positions()

        with open('output.txt', 'a') as file:
            print(f"#xy {self.x}, {self.y}", file=file)
            print(f"#dxdy {self.dx}, {self.dy}", file=file)

        return self.past_positions

