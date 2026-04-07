
# ASTEROIDE SINGLEPLAYER v1.0
# This file coordinates world state, spawning, collisions, scoring, and progression.

import math
from random import uniform

import pygame as pg

import config as C
from sprites import Asteroid, ShieldPowerUp, Ship, UFO
from utils import Vec, rand_edge_pos, rand_unit_vec


class World:
    # Initialize the world state, entity groups, timers, and player progress.
    def __init__(self):
        """
        Inicializa o estado global do mundo do jogo.

        Nesta versão, também cria:
        - o grupo de power-ups;
        - o temporizador de surgimento do item de escudo.
        """
        self.ship = Ship(Vec(C.WIDTH / 2, C.HEIGHT / 2))
        self.bullets = pg.sprite.Group()
        self.ufo_bullets = pg.sprite.Group()
        self.asteroids = pg.sprite.Group()
        self.ufos = pg.sprite.Group()
        self.powerups = pg.sprite.Group()

        self.all_sprites = pg.sprite.Group(self.ship)

        self.score = 0
        self.lives = C.START_LIVES
        self.wave = 0
        self.wave_cool = C.WAVE_DELAY
        self.safe = C.SAFE_SPAWN_TIME
        self.ufo_timer = C.UFO_SPAWN_EVERY
        self.shield_timer = C.SHIELD_SPAWN_EVERY
        self.game_over = False  # Sinaliza fim de jogo para a cena principal

    def start_wave(self):
        # Spawn a new asteroid wave with difficulty based on the current round.
        self.wave += 1
        count = 3 + self.wave
        for _ in range(count):
            pos = rand_edge_pos()
            while (pos - self.ship.pos).length() < 150:
                pos = rand_edge_pos()
            ang = uniform(0, math.tau)
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX)
            vel = Vec(math.cos(ang), math.sin(ang)) * speed
            self.spawn_asteroid(pos, vel, "L")

    def spawn_asteroid(self, pos: Vec, vel: Vec, size: str):
        # Create an asteroid and register it in the world groups.
        a = Asteroid(pos, vel, size)
        self.asteroids.add(a)
        self.all_sprites.add(a)

    def spawn_ufo(self):
        # Spawn a single UFO at a screen edge and send it across the playfield.
        if self.ufos:
            return
        small = uniform(0, 1) < 0.5
        y = uniform(0, C.HEIGHT)
        x = 0 if uniform(0, 1) < 0.5 else C.WIDTH
        ufo = UFO(Vec(x, y), small)
        ufo.dir.xy = (1, 0) if x == 0 else (-1, 0)
        self.ufos.add(ufo)
        self.all_sprites.add(ufo)

    def ufo_try_fire(self):
        # Let every active UFO attempt to fire at the ship.
        for ufo in self.ufos:
            bullet = ufo.fire_at(self.ship.pos)
            if bullet:
                self.ufo_bullets.add(bullet)
                self.all_sprites.add(bullet)

    def try_fire(self):
        # Fire a player bullet when the bullet cap allows it.
        if len(self.bullets) >= C.MAX_BULLETS:
            return
        b = self.ship.fire()
        if b:
            self.bullets.add(b)
            self.all_sprites.add(b)

    def hyperspace(self):
        # Trigger the ship hyperspace action and apply its score penalty.
        self.ship.hyperspace()
        self.score = max(0, self.score - C.HYPERSPACE_COST)

    def update(self, dt: float, keys):
        """
        Atualiza toda a simulação do jogo a cada frame.

        Responsabilidades:
        - aplicar controle da nave;
        - atualizar sprites;
        - controlar área segura após respawn;
        - controlar surgimento e tiros de UFO;
        - controlar surgimento do item de escudo;
        - resolver colisões;
        - iniciar novas waves.
        """
        self.ship.control(keys, dt)
        self.all_sprites.update(dt)

        if self.safe > 0:
            self.safe -= dt
            self.ship.invuln = 0.5

        # Controla o surgimento periódico do item de escudo
        self.shield_timer -= dt
        if self.shield_timer <= 0 and not self.powerups:
            self.spawn_shield_powerup()
            self.shield_timer = C.SHIELD_SPAWN_EVERY

        # Comportamento dos UFOs
        if self.ufos:
            self.ufo_try_fire()
        else:
            self.ufo_timer -= dt

        if not self.ufos and self.ufo_timer <= 0:
            self.spawn_ufo()
            self.ufo_timer = C.UFO_SPAWN_EVERY

        self.handle_collisions()

        # Inicia nova wave quando não houver mais asteroides
        if not self.asteroids and self.wave_cool <= 0:
            self.start_wave()
            self.wave_cool = C.WAVE_DELAY
        elif not self.asteroids:
            self.wave_cool -= dt

    def handle_collisions(self):
        """
        Resolve as colisões entre os objetos do jogo.

        Trata:
        - tiro do jogador com asteroides;
        - tiro do UFO com asteroides;
        - nave com asteroides, UFOs e tiros inimigos;
        - nave com item de escudo;
        - tiro do jogador com UFO.
        """
        hits = pg.sprite.groupcollide(
            self.asteroids,
            self.bullets,
            False,
            True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast, _ in hits.items():
            self.split_asteroid(ast)

        ufo_hits = pg.sprite.groupcollide(
            self.asteroids,
            self.ufo_bullets,
            False,
            True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast, _ in ufo_hits.items():
            self.split_asteroid(ast)

        # Coleta do item de escudo
        for powerup in list(self.powerups):
            if (powerup.pos - self.ship.pos).length() < (powerup.r + self.ship.r):
                self.ship.shield_time = C.SHIELD_DURATION
                powerup.kill()

        # Colisões que causam dano à nave
        if self.ship.invuln <= 0 and self.safe <= 0:
            for ast in self.asteroids:
                if (ast.pos - self.ship.pos).length() < (ast.r + self.ship.r):
                    self.hit_ship()
                    break

            for ufo in self.ufos:
                if (ufo.pos - self.ship.pos).length() < (ufo.r + self.ship.r):
                    self.hit_ship()
                    break

            for bullet in self.ufo_bullets:
                if (bullet.pos - self.ship.pos).length() < (bullet.r + self.ship.r):
                    bullet.kill()
                    self.hit_ship()
                    break

        # Tiros do jogador acertando UFO
        for ufo in list(self.ufos):
            for b in list(self.bullets):
                if (ufo.pos - b.pos).length() < (ufo.r + b.r):
                    score = C.UFO_SMALL["score"] if ufo.small else C.UFO_BIG["score"]
                    self.score += score
                    ufo.kill()
                    b.kill()

    def split_asteroid(self, ast: Asteroid):
        # Destroy an asteroid, award score, and spawn its smaller fragments.
        self.score += C.AST_SIZES[ast.size]["score"]
        split = C.AST_SIZES[ast.size]["split"]
        pos = Vec(ast.pos)
        ast.kill()
        for s in split:
            dirv = rand_unit_vec()
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX) * 1.2
            self.spawn_asteroid(pos, dirv * speed, s)

    def ship_die(self):
        # Remove uma vida; sinaliza game over ou reposiciona a nave.
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True  # Game.run() detecta e muda de cena
            return
        self.ship.pos.xy = (C.WIDTH / 2, C.HEIGHT / 2)
        self.ship.vel.xy = (0, 0)
        self.ship.angle = -90
        self.ship.invuln = C.SAFE_SPAWN_TIME
        self.safe = C.SAFE_SPAWN_TIME

    def draw(self, surf: pg.Surface, font: pg.font.Font):
        """
        Desenha todos os sprites e a HUD do jogo.

        A HUD foi atualizada para exibir também o tempo restante
        do escudo quando ele estiver ativo.
        """
        for spr in self.all_sprites:
            spr.draw(surf)

        pg.draw.line(surf, (60, 60, 60), (0, 50), (C.WIDTH, 50), width=1)

        txt = f"SCORE {self.score:06d}   LIVES {self.lives}   WAVE {self.wave}"

        if self.ship.shield_time > 0:
            txt += f"   SHIELD {self.ship.shield_time:0.1f}s"

        label = font.render(txt, True, C.WHITE)
        surf.blit(label, (10, 10))


    def spawn_shield_powerup(self):
        """
        Cria um item de escudo em uma posição aleatória da tela.

        A posição é gerada afastada das bordas para facilitar visualização
        e coleta pelo jogador.
        """
        pos = Vec(
            uniform(80, C.WIDTH - 80),
            uniform(80, C.HEIGHT - 80),
        )

        powerup = ShieldPowerUp(pos)
        self.powerups.add(powerup)
        self.all_sprites.add(powerup)
        
    def hit_ship(self):
        """
        Trata o momento em que a nave recebe dano.

        Regras:
        - se houver escudo ativo, o escudo é consumido e a nave sobrevive;
        - se não houver escudo, aplica a lógica normal de perda de vida.
        """
        if self.ship.shield_time > 0:
            self.ship.shield_time = 0
            self.ship.invuln = C.SHIELD_HIT_INVULN
            return

        self.ship_die()