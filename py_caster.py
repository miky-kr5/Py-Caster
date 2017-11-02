#! /usr/bin/env python
import math
import pygame

##############################################################
# Game parameters
##############################################################

TITLE         = "Py Caster"
FPS           = 30
SCREEN_SIZE   = (800, 600)
CEILING_COLOR = (75, 119, 208)
FLOOR_COLOR   = (229, 138, 132)
FOG_COLOR     = (128, 128, 128)
FOG_NEAR      = 1.0
FOG_FAR       = 5.0
TOLERANCE     = 0.000001
FLOOR_TEXTURE = "Textures/goldlites.jpg"
CEIL_TEXTURE  = "Textures/brownstone.jpg"

##############################################################
# Projection parameters
##############################################################

FB_SIZE                = (320, 200)
DEG2RAD                = 3.1415926535897932384626433 / 180.0
FOV                    = 66.84962236520761
ANGLE_INCREMENT        = FOV / float(FB_SIZE[0])
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
        self.tca = tca
        self.tcb = tcb
        self.texture = pygame.image.load(texture)

    def intersect(self, r):
        def classifyPoint2D(point):
            v1 = point.sub(self.a).normalize()
            v2 = vec2(self.v.y, -self.v.x)
            return v1.dot(v2)

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
        v2 = self.b.sub(self.a) if sign(side) > 0 else self.a.sub(self.b)
        v3 = vec2(-r.d.y, r.d.x)
        det = v2.dot(v3)

        if abs(det) < TOLERANCE:
            return None
        else:
            v1 = r.o.sub(self.a) if sign(side) > 0 else self.a.sub(r.o)
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
    def __init__(self, texture, floor = True):
        self.n = vec3(0.0, 1.0, 0.0) if floor else vec3(0.0, -1.0, 0.0)
        self.y = -0.5 if floor else 0.5
        self.texture = pygame.image.load(texture)

    def intersect(self, r):
        d = r.d.dot(self.n)
        if abs(d) > TOLERANCE:
            t = self.n.dot(vec3(0.0, self.y, 0.0).sub(r.o)) / d
            return Intersection(r, t)
        else:
            return None

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
    # Local variables.
    done = False
    player_pos = vec2(0.0, 0.0)
    player_dir = vec2(-1.0, 0.0)
    plane = vec2(0.0, 0.66)
    arrow_keys = {pygame.K_UP: False, pygame.K_DOWN: False, pygame.K_LEFT: False, pygame.K_RIGHT: False}

    # Initialize Pygame.
    pygame.init()
    clock = pygame.time.Clock()
    screen  = pygame.display.set_mode(SCREEN_SIZE, pygame.HWSURFACE | pygame.DOUBLEBUF)
    frame_buffer = pygame.Surface(FB_SIZE, pygame.HWSURFACE)
    pygame.mouse.set_visible(False)
    pygame.key.set_repeat(17, 17)

    # Define walls, floor and ceiling.
    walls = [LineSegment(vec2(-3.0, 3.0), vec2(3.0, 3.0), -3.0, 3.0, "Textures/metal.jpg"),
             LineSegment(vec2(3.0, 3.0), vec2(3.0, -3.0), 0.0, 6.0, "Textures/metal.jpg"),
             LineSegment(vec2(3.0, -3.0), vec2(-3.0, -3.0), 0.0, 6.0, "Textures/metal.jpg"),
             LineSegment(vec2(-3.0, -3.0), vec2(-3.0, 3.0), 0.0, 6.0, "Textures/metal.jpg"),
             LineSegment(vec2(2.0, 2.0), vec2(3.0, 3.0), 0.0, 1.0, "Textures/diagmetal.jpg"),
             LineSegment(vec2(-2.0, 2.0), vec2(-3.0, 3.0), 0.0, 1.0, "Textures/diagmetal.jpg"),
             LineSegment(vec2(-2.0, 2.0), vec2(2.0, 2.0), 0.0, 4.0, "Textures/diagmetal.jpg")
    ]
    floor = Plane3d(FLOOR_TEXTURE)
    ceiln = Plane3d(CEIL_TEXTURE, False)

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
                player_pos = player_pos.sub(player_dir.scale(PLAYER_MOVE_SPEED))

            if arrow_keys[pygame.K_DOWN]:
                player_pos = player_pos.add(player_dir.scale(PLAYER_MOVE_SPEED))

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
            frame_buffer.fill(CEILING_COLOR, pygame.Rect(0, 0, FB_SIZE[0], FB_SIZE[1] / 2))
            frame_buffer.fill(FLOOR_COLOR, pygame.Rect(0, FB_SIZE[1] / 2, FB_SIZE[0], FB_SIZE[1] / 2))

            # Render walls.
            angle = -FOV / 2.0
            for i in xrange(FB_SIZE[0]):
                # Generate camera ray
                camera_x = 2.0 * (float(i) / float(FB_SIZE[0])) - 1;
                r = Ray(vec2(player_pos.x, player_pos.y), vec2(player_dir.x + plane.x * camera_x, player_dir.y + plane.y * camera_x))

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

                if d < float('Inf') and c is not None:
                    # If an intersection was found then compute the projected height of the wall in pixels
                    h = int(float(FB_SIZE[1]) / (d * math.cos(angle * DEG2RAD)))
                    # The height tends to infinity as we get close to the walls so it must be clamped
                    h = HEIGHT_CLAMP_MULTIPLER * FB_SIZE[1] if h > HEIGHT_CLAMP_MULTIPLER * FB_SIZE[1] else h
                    # Then scale the corresponding texture slice and blit it
                    scaled = pygame.transform.scale(c, (c.get_width(), h))
                    frame_buffer.blit(scaled, (i, -(h / 2) + (FB_SIZE[1] / 2)))

                # Floor casting and ceiling casting
                if p is not None and h > 0 and h < FB_SIZE[1]:
                    for j in xrange(1, FB_SIZE[1] - h):
                        # Compute wall height in world space
                        h_world = float((h + j)) / float(FB_SIZE[1])

                        # Take player position and starting floor intersection point to 3D space
                        o3d = vec3(player_pos.x, 0.0, player_pos.y)
                        p3d = vec3(p.x, -h_world/2.0, p.y)
                        
                        # Compute floor ray
                        fr = Ray3d(o3d, p3d.sub(o3d))

                        # Compute ceiling starting intersection point and ceiling ray
                        p3d = vec3(p.x, h_world/2.0, p.y)
                        cr = Ray3d(o3d, p3d.sub(o3d))

                        # Compute floor and ceiling intersections
                        fip = floor.intersect(fr)
                        cip = ceiln.intersect(cr)
                        
                        # Get floor and ceiling textures
                        ftex = floor.sample_texture(fip.tc)
                        ctex = ceiln.sample_texture(cip.tc)

                        # Blit floor and ceiling colors to the framebuffer
                        frame_buffer.blit(ftex, (i, ((h + j) / 2) + (FB_SIZE[1] / 2)))
                        frame_buffer.blit(ctex, (i, -((h + j) / 2) + (FB_SIZE[1] / 2)))
                        
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

