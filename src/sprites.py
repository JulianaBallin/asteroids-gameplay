# ASTEROIDE SINGLEPLAYER v1.0
# Este arquivo define as entidades interativas do jogo e seus comportamentos locais.

import math
from random import uniform

import pygame as pg

import config as C
from utils import Vec, angle_to_vec, draw_circle, draw_poly, wrap_pos


class Bullet(pg.sprite.Sprite):
    """Projétil disparado pela nave do jogador."""

    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = C.BULLET_TTL
        self.r = C.BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        """Move o projétil, aplica wrap na tela e reduz seu tempo de vida."""
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """Desenha o projétil na tela."""
        draw_circle(surf, self.pos, self.r)


class UfoBullet(pg.sprite.Sprite):
    """Projétil disparado pelo UFO."""

    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = C.UFO_BULLET_TTL
        self.r = C.BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        """Move o projétil, aplica wrap na tela e reduz seu tempo de vida."""
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """Desenha o projétil do UFO na tela."""
        draw_circle(surf, self.pos, self.r)


class Asteroid(pg.sprite.Sprite):
    """Asteroide com formato irregular e tamanho variável."""

    def __init__(self, pos: Vec, vel: Vec, size: str):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.size = size
        self.r = C.AST_SIZES[size]["r"]
        self.poly = self._make_poly()
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def _make_poly(self):
        """Gera o contorno irregular do asteroide."""
        steps = 12 if self.size == "L" else 10 if self.size == "M" else 8
        pts = []

        for i in range(steps):
            ang = i * (360 / steps)
            jitter = uniform(0.75, 1.2)
            r = self.r * jitter
            v = Vec(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
            pts.append(v * r)

        return pts

    def update(self, dt: float):
        """Move o asteroide e aplica wrap na tela."""
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """Desenha o contorno do asteroide."""
        pts = [self.pos + p for p in self.poly]
        pg.draw.polygon(surf, C.WHITE, pts, width=1)


class Ship(pg.sprite.Sprite):
    """Nave do jogador."""

    def __init__(self, pos: Vec):
        """
        Inicializa a nave com seus estados principais.

        shield_time:
            controla por quanto tempo o escudo temporário permanece ativo.
        triple_shot_time:
            controla por quanto tempo o tiro triplo permanece ativo.
        """
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(0, 0)
        self.angle = -90.0
        self.cool = 0.0
        self.invuln = 0.0
        self.shield_time = 0.0
        self.triple_shot_time = 0.0
        self.alive = True
        self.r = C.SHIP_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def control(self, keys: pg.key.ScancodeWrapper, dt: float):
        """Aplica rotação, aceleração e atrito com base nas teclas pressionadas."""
        if keys[pg.K_LEFT]:
            self.angle -= C.SHIP_TURN_SPEED * dt
        if keys[pg.K_RIGHT]:
            self.angle += C.SHIP_TURN_SPEED * dt
        if keys[pg.K_UP]:
            self.vel += angle_to_vec(self.angle) * C.SHIP_THRUST * dt

        self.vel *= C.SHIP_FRICTION

    def fire(self) -> list[Bullet]:
        """Cria projéteis da nave se o cooldown permitir."""
        if self.cool > 0:
            return []

        bullets = []
        dirv = angle_to_vec(self.angle)
        pos = self.pos + dirv * (self.r + 6)

        # Tiro principal
        vel = self.vel + dirv * C.SHIP_BULLET_SPEED
        bullets.append(Bullet(pos, vel))

        # Tiros extras se o power-up estiver ativo
        if self.triple_shot_time > 0:
            for offset in [-20, 20]:
                side_dir = angle_to_vec(self.angle + offset)
                side_vel = self.vel + side_dir * C.SHIP_BULLET_SPEED
                bullets.append(Bullet(pos, side_vel))

        self.cool = C.SHIP_FIRE_RATE
        return bullets

    def hyperspace(self):
        """Teletransporta a nave para uma posição aleatória e zera sua velocidade."""
        self.pos = Vec(uniform(0, C.WIDTH), uniform(0, C.HEIGHT))
        self.vel.xy = (0, 0)
        self.invuln = 1.0

    def update(self, dt: float):
        """
        Atualiza o estado da nave a cada frame.

        Responsabilidades:
        - reduzir o cooldown do tiro;
        - reduzir o tempo de invulnerabilidade;
        - reduzir o tempo do escudo temporário;
        - reduzir o tempo do tiro triplo;
        - mover a nave;
        - manter a nave dentro da tela usando wrap.
        """
        if self.cool > 0:
            self.cool -= dt

        if self.invuln > 0:
            self.invuln -= dt

        if self.shield_time > 0:
            self.shield_time -= dt

        if self.triple_shot_time > 0:
            self.triple_shot_time -= dt

        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """
        Desenha a nave e seus efeitos visuais temporários.

        Efeitos:
        - círculo piscando para indicar invulnerabilidade;
        - círculo maior para indicar que o escudo temporário está ativo;
        - triângulo invertido no topo para indicar tiro triplo.
        """
        dirv = angle_to_vec(self.angle)
        left = angle_to_vec(self.angle + 140)
        right = angle_to_vec(self.angle - 140)

        p1 = self.pos + dirv * self.r
        p2 = self.pos + left * self.r * 0.9
        p3 = self.pos + right * self.r * 0.9

        draw_poly(surf, [p1, p2, p3])

        # Indica o power-up de tiro triplo ativo
        if self.triple_shot_time > 0:
            p_top = self.pos + dirv * (self.r + 4)
            p_l = self.pos + dirv * (self.r + 2) + angle_to_vec(self.angle + 90) * 4
            p_r = self.pos + dirv * (self.r + 2) + angle_to_vec(self.angle - 90) * 4
            draw_poly(surf, [p_top, p_l, p_r])

        # Indica a invulnerabilidade inicial ou após respawn
        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            draw_circle(surf, self.pos, self.r + 6)

        # Indica que o escudo temporário está ativo
        if self.shield_time > 0 and int(self.shield_time * 12) % 2 == 0:
            draw_circle(surf, self.pos, self.r + 12)


class ShieldPowerUp(pg.sprite.Sprite):
    """Item coletável que concede escudo temporário para a nave."""

    def __init__(self, pos: Vec):
        """
        Inicializa o item de escudo em uma posição fixa da tela.
        """
        super().__init__()
        self.pos = Vec(pos)
        self.ttl = C.SHIELD_PICKUP_TTL
        self.r = C.SHIELD_PICKUP_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        self.rect.center = self.pos

    def update(self, dt: float):
        """
        Atualiza o item de escudo.

        O item fica disponível por tempo limitado. Se o tempo acabar,
        ele é removido da tela.
        """
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()

        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """
        Desenha o item de escudo no estilo minimalista do jogo.
        """
        draw_circle(surf, self.pos, self.r)

        top = self.pos + Vec(0, -self.r + 2)
        right = self.pos + Vec(self.r - 2, 0)
        bottom = self.pos + Vec(0, self.r - 2)
        left = self.pos + Vec(-self.r + 2, 0)

        draw_poly(surf, [top, right, bottom, left])


class TripleShotPowerUp(pg.sprite.Sprite):
    """Item coletável que concede tiro triplo temporário para a nave."""

    def __init__(self, pos: Vec):
        """
        Inicializa o item de tiro triplo em uma posição fixa da tela.
        """
        super().__init__()
        self.pos = Vec(pos)
        self.ttl = C.TRIPLE_SHOT_PICKUP_TTL
        self.r = C.TRIPLE_SHOT_PICKUP_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        self.rect.center = self.pos

    def update(self, dt: float):
        """
        O item fica disponível por tempo limitado.
        """
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()

        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """
        Desenha o item de tiro triplo (um triângulo).
        """
        draw_circle(surf, self.pos, self.r)

        p1 = self.pos + Vec(0, -self.r + 3)
        p2 = self.pos + Vec(self.r - 3, self.r - 3)
        p3 = self.pos + Vec(-self.r + 3, self.r - 3)

        draw_poly(surf, [p1, p2, p3])


class UFO(pg.sprite.Sprite):
    """Inimigo do tipo disco voador."""

    def __init__(self, pos: Vec, small: bool):
        super().__init__()
        self.pos = Vec(pos)
        self.small = small
        profile = C.UFO_SMALL if small else C.UFO_BIG
        self.r = profile["r"]
        self.aim = profile["aim"]
        self.speed = C.UFO_SPEED
        self.cool = C.UFO_FIRE_EVERY
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        self.dir = Vec(1, 0) if uniform(0, 1) < 0.5 else Vec(-1, 0)

    def update(self, dt: float):
        """Move o UFO, reduz o cooldown de tiro e remove ao sair da tela."""
        self.pos += self.dir * self.speed * dt
        self.cool -= dt

        if self.pos.x < -self.r * 2 or self.pos.x > C.WIDTH + self.r * 2:
            self.kill()

        self.rect.center = self.pos

    def fire_at(self, target_pos: Vec) -> UfoBullet | None:
        """Dispara em direção à nave com precisão baseada no tipo do UFO."""
        if self.cool > 0:
            return None

        aim_vec = Vec(target_pos) - self.pos
        if aim_vec.length_squared() == 0:
            aim_vec = self.dir.normalize()
        else:
            aim_vec = aim_vec.normalize()

        max_error = (1.0 - self.aim) * 60.0
        shot_dir = aim_vec.rotate(uniform(-max_error, max_error))
        self.cool = C.UFO_FIRE_EVERY
        spawn_pos = self.pos + shot_dir * (self.r + 6)
        vel = shot_dir * C.UFO_BULLET_SPEED
        return UfoBullet(spawn_pos, vel)

    def draw(self, surf: pg.Surface):
        """Desenha o corpo do UFO."""
        w, h = self.r * 2, self.r
        rect = pg.Rect(0, 0, w, h)
        rect.center = self.pos
        pg.draw.ellipse(surf, C.WHITE, rect, width=1)

        cup = pg.Rect(0, 0, w * 0.5, h * 0.7)
        cup.center = (self.pos.x, self.pos.y - h * 0.3)
        pg.draw.ellipse(surf, C.WHITE, cup, width=1)
