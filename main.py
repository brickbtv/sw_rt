import time
from typing import Tuple

import pygame
import math
from vector3d.vector import Vector


SCREEN = (1024, 768)
FOV = math.pi / 2.0


class Light:
    def __init__(self, pos: Vector, intensity: int):
        self.pos = pos
        self.intensity = intensity


class Geometry:
    def ray_intersect(self, orig: Vector, direction: Vector, t0: float):
        pass

    def diffuse_color(self):
        pass

    def specular(self):
        pass

    def albedo(self):
        pass


class Material:
    def __init__(self, albedo, diffuse, specular):
        self.albedo = albedo
        self.diffuse = diffuse
        self.specular = specular


class Sphere(Geometry):
    def __init__(self, pos: Vector, radius: int, material: Material):
        self.pos = pos
        self.radius = radius
        self.sqr_radius = radius*radius
        self.material = material

    def ray_intersect(self, orig: Vector, direction: Vector, t0: float):
        L = self.pos - orig
        tca = L*direction
        d2 = L*L - tca*tca
        if d2 > self.sqr_radius:
            return (False, 0)

        thc = math.sqrt(self.sqr_radius - d2)
        t0 = tca - thc
        t1 = tca + thc
        if t0 < 0:
            t0 = t1
        if t0 < 0:
            return (False, 0)

        return (True, t0)

    def diffuse_color(self):
        return self.material.diffuse

    def specular(self):
        return self.material.specular

    def albedo(self):
        return self.material.albedo


def scene_intersect(orig: Vector, direction: Vector, objects: Tuple[Geometry]):
    obj_distance = 100000000
    hit = None
    N = None
    obj_hit = None

    for obj in objects:
        res, obj_dist = obj.ray_intersect(orig, direction, obj_distance)
        if res and obj_dist < obj_distance:
            obj_distance = obj_dist
            hit = orig + direction * obj_distance
            N = (hit - obj.pos).normalize()
            obj_hit = obj

    return obj_distance < 10000, hit, N, obj_hit


def cast_ray(orig: Vector, direction: Vector, objects: Tuple[Geometry], lights: Tuple[Light], depth=0):
    c = None

    res, hit, N, obj_hit = scene_intersect(orig, direction, objects)
    if depth > 4 or not res:
        return (128, 200, 255)

    refl_dir = reflect(direction, N).normalize()
    refl_orig = hit-N*0.001 if refl_dir*N < 0 else hit + N*0.001
    refl_color = cast_ray(refl_orig, refl_dir, objects, lights, depth + 1)

    obj_to_render = obj_hit

    if hit:
        diffuse_light_intens = 0
        specular_light_intens = 0
        for light in lights:
            light_dir = (light.pos - hit).normalize()
            diffuse_light_intens += light.intensity * max(0.0, light_dir*N)
            specular_light_intens += pow(max(0.0, -reflect(-light_dir, N)*direction), obj_to_render.specular()) * light.intensity

        c = obj_to_render.diffuse_color() * diffuse_light_intens * obj_to_render.albedo().x + Vector(1.0, 1.0, 1.0)*specular_light_intens*255 * obj_to_render.albedo().y + Vector(*refl_color)*obj_to_render.albedo().z

        if c.x > 255:
            c.x = 255
        if c.y > 255:
            c.y = 255
        if c.z > 255:
            c.z = 255

    return (int(c.x), int(c.y), int(c.z))


def reflect(i: Vector, n: Vector) -> Vector:
    return i - n*2.0*(i*n)


def render(screen: pygame.Surface, objects: Tuple[Geometry], lights: Tuple[Light]):
    screen.lock()

    for j in range(-int(SCREEN[1]/2), int(SCREEN[1]/2)):
        for i in range(-int(SCREEN[0]/2), int(SCREEN[0]/2)):
            x =  (2 * (i + 0.5)) / (SCREEN[0] - 1) * math.tan(FOV / 2.0)*int(SCREEN[0])/SCREEN[1]
            y = -(2 * (j + 0.5)) / (SCREEN[1] - 1) * math.tan(FOV / 2.0)
            direction = Vector(x, y, -1).normalize()

            screen.set_at((i+int(SCREEN[0]/2), j+int(SCREEN[1]/2)), cast_ray(Vector(0,0,0), direction, tuple(objects), tuple(lights)))
        pygame.display.flip()
    screen.unlock()


def main():
    objects = [Sphere(Vector(-3, 0, -16), 4, Material(Vector(0.0, 0.4, 0.9),(Vector(255, 255, 255)), 50)),
               Sphere(Vector(9, 1, -16), 7, Material(Vector(0.9, 0.1, 0.2), Vector(255, 128, 255), 10)),
               Sphere(Vector(-8, 5, -16), 2, Material(Vector(0.4, 0.5, 0.4), Vector(0, 128, 0), 100))]
    lights = [Light(Vector(-20, 20, 20), 1.5), Light(Vector(30, 50, -25), 1.3), Light(Vector(30, 20, 30), 0.7)]

    pygame.init()

    pygame.display.set_caption("SW RT")

    screen = pygame.display.set_mode((int(SCREEN[0]), int(SCREEN[1])))

    while True:
        st = time.time()
        render(screen, objects, lights)
        print(time.time() - st)
        pygame.display.flip()
        objects[0].pos.x += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return


if __name__ == "__main__":
    main()
