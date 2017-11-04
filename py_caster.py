#! /usr/bin/env python
import math
import pygame

##############################################################
# Game parameters
##############################################################

TITLE         = "Py Caster"
FPS           = 30
SCREEN_SIZE   = (800, 600)
FILL_COLOR = (0, 0, 0)
FAR = 5.0
TOLERANCE     = 0.000001
FLOOR_TEXTURE = "Textures/goldlites.jpg"
CEIL_TEXTURE  = "Textures/brownstone.jpg"

##############################################################
# Projection parameters
##############################################################

FB_SIZE                = (320, 200)
DEG2RAD                = 3.1415926535897932384626433 / 180.0
RAD2DEG                = 180.0 / 3.1415926535897932384626433
FOV                    = 0.0
ANGLE_INCREMENT        = 0.0
HEIGHT_CLAMP_MULTIPLER = 10 # MUST BE AN INTEGER

##############################################################
# Player parameters
##############################################################

PLAYER_TURN_SPEED = 2.0 * DEG2RAD
PLAYER_MOVE_SPEED = 0.1

##############################################################
# Vector Classes
##############################################################

class vec(object):
    def __ini__(self):
        pass

    def length(self):
        return math.sqrt(self.dot(self))
    
    def distance(self, p):
        return p.sub(self).length()

class vec3(vec):
    def __init__(self, x = 0, y = 0, z = 0):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"
        
    def add(self, v):
        return vec3(self.x + v.x, self.y + v.y, self.z + v.z)

    def sub(self, v):
        return vec3(self.x - v.x, self.y - v.y, self.z - v.z)

    def scale(self, k):
        return vec3(self.x * k, self.y * k, self.z * k)
        
    def dot(self, v):
        return (self.x * v.x) + (self.y * v.y) + (self.z * v.z)
    
    def normalize(self):
        norm = self.length()
        if norm > 0:
            self.x /= norm
            self.y /= norm
            self.z /= norm
        return self

    def mix(self, v, t):
        return vec3((self.x * t) + (v.x * (1.0 - t)), (self.y * t) + (v.y * (1.0 - t)), (self.z * t) + (v.z * (1.0 - t)))

class vec2(vec):
    def __init__(self, x = 0, y = 0):
        self.x = x
        self.y = y

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    def add(self, v):
        return vec2(self.x + v.x, self.y + v.y)

    def sub(self, v):
        return vec2(self.x - v.x, self.y - v.y)

    def scale(self, k):
        return vec2(self.x * k, self.y * k)

    def dot(self, v):
        return (self.x * v.x) + (self.y * v.y)

    def normalize(self):
        norm = self.length()
        if norm > 0:
            self.x /= norm
            self.y /= norm
        return self

    def cross(self, v):
        return vec3(0.0, 0.0, (self.x * v.y) - (self.y * v.x))

    def mix(self, v, t):
        return vec2((self.x * t) + (v.x * (1.0 - t)), (self.y * t) + (v.y * (1.0 - t)))

##############################################################
# Ray Class
##############################################################

class Ray(object):
    def __init__(self, origin = vec2(0.0, 0.0), direction = vec2(0.0, 1.0)):
        self.o = origin
        self.d = direction.normalize()

    def __str__(self):
        return "Origin: " + str(self.o) + " :: Direction: " + str(self.d)

class Ray3d(Ray):
    def __init__(self, origin = vec3(0.0, 0.0, 0.0), direction = vec3(0.0, 0.0, 1.0)):
        self.o = origin
        self.d = direction.normalize()
    
##############################################################
# Intersection Class
##############################################################

class Intersection(object):
    def __init__(self, r, t, tex_coord = None):
        self.p = r.o.add(r.d.scale(t))
        self.d = r.o.distance(self.p)
        self.tc = tex_coord if tex_coord is not None else vec2(self.p.x, self.p.z)

##############################################################
# Line Segment Class
##############################################################

class LineSegment(object):
    def __init__(self, a, b, tca, tcb, texture):
        self.a = a
        self.b = b
        self.v = b.sub(a).normalize()
        self.n = vec2(-self.v.y, self.v.x)
        self.tca = tca
        self.tcb = tcb
        self.texture = pygame.image.load(texture)

    def intersect(self, r):
        def classifyPoint2D(point):
            v1 = point.sub(self.a).normalize()
            return v1.dot(self.n)

        def sign(n):
            if n == 0:
                return 0
            elif n > 0:
                return 1
            else:
                return -1

        def lerp(a, b, t):
            return (a * t) + (b * (1.0 - t))

        side = classifyPoint2D(r.o)
        v2 = self.b.sub(self.a)
        v3 = vec2(-r.d.y, r.d.x) if sign(side) > 0 else vec2(r.d.y, -r.d.x)
        det = v2.dot(v3)

        if abs(det) < TOLERANCE:
            return None
        else:
            v1 = r.o.sub(self.a)
            t1 = v2.cross(v1).length() / det
            t2 = v1.dot(v3) / det

            if t2 >= 0.0 and t2 <= 1.0 and t1 > 0.0:
                return Intersection(r, t1, lerp(self.tca, self.tcb, t2))
            else:
                return None

    def get_tex_column(self, s):
        w = self.texture.get_width()
        h = self.texture.get_height()
        _s = s * w if s >= 0.0 else (1.0 - (math.ceil(s) - s)) * w
        _s = int(_s % w)
        # Creating a subsurface is pretty fast in pygame, no copying of pixels is needed
        return self.texture.subsurface(pygame.Rect(_s, 0, 1, h))
    
##############################################################
# Plane3D class
##############################################################
    
class Plane3d(object):
    def __init__(self, texture):
        self.texture = pygame.image.load(texture)

    def sample_texture(self, st):
        w = self.texture.get_width()
        h = self.texture.get_height()
        s = st.x * w if st.x >= 0.0 else (1.0 - (math.ceil(st.x) - st.x)) * w
        s = int(s % w)
        t = st.y * h if st.y >= 0.0 else (1.0 - (math.ceil(st.y) - st.y)) * h
        t = int(t % h)
        return self.texture.subsurface(pygame.Rect(s, t, 1, 1))
    
##############################################################
# Main Function
##############################################################

def main():
    global FOV, ANGLE_INCREMENT

    # Local variables.
    done = False
    player_pos = vec2(0.0, 0.0)
    player_dir = vec2(-1.0, 0.0)
    plane = vec2(0.0, 0.66)
    arrow_keys = {pygame.K_UP: False, pygame.K_DOWN: False, pygame.K_LEFT: False, pygame.K_RIGHT: False}

    # Update global variables
    FOV = 2.0 * math.atan((plane.length() / player_dir.length())) * RAD2DEG
    ANGLE_INCREMENT = FOV / float(FB_SIZE[0])

    # Initialize Pygame.
    pygame.init()
    clock = pygame.time.Clock()
    screen  = pygame.display.set_mode(SCREEN_SIZE, pygame.HWSURFACE | pygame.DOUBLEBUF)
    frame_buffer = pygame.Surface(FB_SIZE, pygame.HWSURFACE)
    pygame.mouse.set_visible(False)
    pygame.key.set_repeat(17, 17)

    # Define walls, floor and ceiling.
    walls = [
        LineSegment(vec2(3.0, 3.0), vec2(3.0, -3.0), 0.0, 6.0, "Textures/metal.jpg"),
        LineSegment(vec2(3.0, -3.0), vec2(-3.0, -3.0), 0.0, 6.0, "Textures/metal.jpg"),
        LineSegment(vec2(-3.0, -3.0), vec2(-3.0, 3.0), 0.0, 6.0, "Textures/metal.jpg"),
        LineSegment(vec2(2.0, 2.0), vec2(3.0, 3.0), 0.0, 1.0, "Textures/diagmetal.jpg"),
        LineSegment(vec2(-2.0, 2.0), vec2(-3.0, 3.0), 0.0, 1.0, "Textures/diagmetal.jpg"),
        LineSegment(vec2(-2.0, 2.0), vec2(2.0, 2.0), 0.0, 4.0, "Textures/diagmetal.jpg")
    ]
    floor = Plane3d(FLOOR_TEXTURE)
    ceiln = Plane3d(CEIL_TEXTURE)

    # Main game loop.
    try:
        while(not done):
            fps = clock.get_fps() + 0.001
            pygame.display.set_caption(TITLE + ": " + str(int(fps)))
            
            # Input capture.
            for event in pygame.event.get():
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or event.type == pygame.QUIT:
                    done = True

                # Record wich keys were pressed and released this frame
                try:
                    if event.type == pygame.KEYDOWN:
                        arrow_keys[event.key] = True
                    if event.type == pygame.KEYUP:
                        arrow_keys[event.key] = False
                except KeyError:
                    pass
            
            # Camera movement
            if arrow_keys[pygame.K_UP]:
                player_pos = player_pos.add(player_dir.scale(PLAYER_MOVE_SPEED))

            if arrow_keys[pygame.K_DOWN]:
                player_pos = player_pos.sub(player_dir.scale(PLAYER_MOVE_SPEED))

            if arrow_keys[pygame.K_LEFT]:
                oldDirX = player_dir.x;
                player_dir.x = player_dir.x * math.cos(PLAYER_TURN_SPEED) - player_dir.y * math.sin(PLAYER_TURN_SPEED);
                player_dir.y = oldDirX * math.sin(PLAYER_TURN_SPEED) + player_dir.y * math.cos(PLAYER_TURN_SPEED);
                oldPlaneX = plane.x;
                plane.x = plane.x * math.cos(PLAYER_TURN_SPEED) - plane.y * math.sin(PLAYER_TURN_SPEED);
                plane.y = oldPlaneX * math.sin(PLAYER_TURN_SPEED) + plane.y * math.cos(PLAYER_TURN_SPEED);

            if arrow_keys[pygame.K_RIGHT]:
                oldDirX = player_dir.x;
                player_dir.x = player_dir.x * math.cos(-PLAYER_TURN_SPEED) - player_dir.y * math.sin(-PLAYER_TURN_SPEED);
                player_dir.y = oldDirX * math.sin(-PLAYER_TURN_SPEED) + player_dir.y * math.cos(-PLAYER_TURN_SPEED);
                oldPlaneX = plane.x;
                plane.x = plane.x * math.cos(-PLAYER_TURN_SPEED) - plane.y * math.sin(-PLAYER_TURN_SPEED);
                plane.y = oldPlaneX * math.sin(-PLAYER_TURN_SPEED) + plane.y * math.cos(-PLAYER_TURN_SPEED);

            # Render ceiling and floor.
            frame_buffer.fill(FILL_COLOR)

            # Render walls.
            angle = -FOV / 2.0
            depth_buffer = [0 for x in xrange(FB_SIZE[0])]
            for i in xrange(FB_SIZE[0]):
                # Generate camera ray
                camera_x = 2.0 * (float(i) / float(FB_SIZE[0])) - 1;
                r = Ray(vec2(player_pos.x, player_pos.y), player_dir.add(plane.scale(camera_x)))

                d = float('Inf')
                c = None
                p = None
                h = 0
                # Check each wall for an intersection
                for l in walls:
                    intersection = l.intersect(r)
                    if intersection is not None:
                        # If an intersection was found then keep it if it's closer than the previous one
                        if intersection.d < d:
                            d = intersection.d
                            c = l.get_tex_column(intersection.tc)
                            p = intersection.p
                            depth_buffer[i] = d

                if c is not None:
                    # If an intersection was found then compute the projected height of the wall in pixels
                    h = int(float(FB_SIZE[1]) / (d * math.cos(angle * DEG2RAD)))
                    # The height tends to infinity as we get close to the walls so it must be clamped
                    h = HEIGHT_CLAMP_MULTIPLER * FB_SIZE[1] if h > HEIGHT_CLAMP_MULTIPLER * FB_SIZE[1] else h
                    # Then scale the corresponding texture slice and blit it
                    scaled = pygame.transform.scale(c, (c.get_width(), h))
                    frame_buffer.blit(scaled, (i, -(h / 2) + (FB_SIZE[1] / 2)))

                    # Darken wall according to distance
                    _d = (d if d < FAR else FAR) / FAR
                    depth = 255 - int(_d * 255)
                    frame_buffer.fill((depth, depth, depth),
                                      pygame.Rect(i,
                                                  -(h / 2) + (FB_SIZE[1] / 2) if -(h / 2) + (FB_SIZE[1] / 2) >= 0 else 0,
                                                  1, 
                                                  scaled.get_height() if scaled.get_height() < FB_SIZE[1] else FB_SIZE[1] - 1),
                                      pygame.BLEND_MULT)

                # Floor casting and ceiling casting
                if p is not None and h > 0 and h < FB_SIZE[1]:
                    for j in xrange((h / 2) + (FB_SIZE[1] / 2), FB_SIZE[1] + 1): #FB_SIZE[1] - h + 1
                        det = (2.0 * j - FB_SIZE[1])
                        if det > 0.0:
                            cd = FB_SIZE[1] / det
                            weight = cd / (d * math.cos(angle * DEG2RAD))
                            st = vec2((weight * p.x) + ((1.0 - weight) * player_pos.x), (weight * p.y) + ((1.0 - weight) * player_pos.y))

                            # Sample floor and ceiling texture
                            ftex = floor.sample_texture(st)
                            ctex = ceiln.sample_texture(st)

                            # Draw floor and ceiling
                            frame_buffer.blit(ftex, (i, j))
                            frame_buffer.blit(ctex, (i, FB_SIZE[1] - j))

                            # Darken floor and ceiling according to distance
                            _d = (cd if cd < FAR else FAR) / FAR
                            depth = 255 - int(_d * 255)
                            frame_buffer.fill((depth, depth, depth), pygame.Rect(i, j, 1, 1), pygame.BLEND_MULT)
                            frame_buffer.fill((depth, depth, depth), pygame.Rect(i, FB_SIZE[1] - j, 1, 1), pygame.BLEND_MULT)

                angle += ANGLE_INCREMENT
                
            # Render framebuffer to the screen
            pygame.transform.scale(frame_buffer, SCREEN_SIZE, screen)

            # Update screen
            pygame.display.update()
            clock.tick(FPS)
            
    except KeyboardInterrupt:
        pass

    pygame.quit()

if __name__ == "__main__":
    main()

