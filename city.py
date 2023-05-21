import numpy as np
import random
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = int(os.getenv('SCREEN_WIDTH')), int(os.getenv('SCREEN_HEIGHT'))
EDGE_FORCE = int(os.getenv('CONE_LENGTH')) + 10
CITY_RADIUS = int(os.getenv('CITY_RADIUS'))

class City:
    def __init__(self, x, y):
        # self.x = random.randint(EDGE_FORCE+CITY_RADIUS, SCREEN_WIDTH - EDGE_FORCE-CITY_RADIUS)
        # self.y = random.randint(EDGE_FORCE+CITY_RADIUS, SCREEN_HEIGHT - EDGE_FORCE-CITY_RADIUS)
        self.x = x
        self.y = y
        print(f"City at ({self.x}, {self.y})")

    def generate_city_data(self):
        city_data = np.zeros((SCREEN_WIDTH, SCREEN_HEIGHT), dtype=np.float32)
        for i in range(SCREEN_WIDTH):
            for j in range(SCREEN_HEIGHT):
                distance = np.sqrt((i - self.x) ** 2 + (j - self.y) ** 2)
                if distance < CITY_RADIUS:
                    city_data[i, j] = (1. - distance / CITY_RADIUS)

        return np.maximum(city_data,0)
