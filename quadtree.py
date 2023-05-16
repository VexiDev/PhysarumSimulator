# Quadtree class
class Quadtree:
    def __init__(self, boundary, n):
        self.boundary = boundary
        self.capacity = n
        self.points = []
        self.divided = False

    def subdivide(self):
        x, y, w, h = self.boundary
        self.northwest = Quadtree((x - w/2, y - h/2, w/2, h/2), self.capacity)
        self.northeast = Quadtree((x + w/2, y - h/2, w/2, h/2), self.capacity)
        self.southwest = Quadtree((x - w/2, y + h/2, w/2, h/2), self.capacity)
        self.southeast = Quadtree((x + w/2, y + h/2, w/2, h/2), self.capacity)
        self.divided = True

    def insert(self, point):
        if not self.boundary[0] - self.boundary[2] < point[0] < self.boundary[0] + self.boundary[2] or not self.boundary[1] - self.boundary[3] < point[1] < self.boundary[1] + self.boundary[3]:
            return False
        if len(self.points) < self.capacity:
            self.points.append(point)
            return True
        if not self.divided:
            self.subdivide()
        return (self.northwest.insert(point) or self.northeast.insert(point) or self.southwest.insert(point) or self.southeast.insert(point))

    def query(self, point, radius):
        x, y, w, h = self.boundary
        if point[0] > x + radius or point[0] < x - radius or point[1] > y + radius or point[1] < y - radius:
            return []
        else:
            points_in_radius = [p for p in self.points if ((p[0]-point[0])**2 + (p[1]-point[1])**2) < radius**2]
            if self.divided:
                points_in_radius += self.northwest.query(point, radius)
                points_in_radius += self.northeast.query(point, radius)
                points_in_radius += self.southwest.query(point, radius)
                points_in_radius += self.southeast.query(point, radius)
            return points_in_radius

    def clear(self):
        self.points = []
        if self.divided:
            self.northwest.clear()
            self.northeast.clear()
            self.southwest.clear()
            self.southeast.clear()
        self.divided = False
