# ASTEROIDE SINGLEPLAYER v1.0
# This file coordinates world state, spawning, collisions, scoring, and progression.

import math
from random import uniform

import pygame as pg

import config as C
from sprites import Asteroid, ShieldPowerUp, Ship, TripleShotPowerUp, UFO
from utils import Vec, rand_edge_pos, rand_unit_vec


class World:
    # Initialize the world state, entity groups, timers, and player progress.
    def __init__(self):
        """
        Inicializa o estado global do mundo do jogo.

        Nesta versão, além da base do jogo, também controla:
        - power-up de escudo;
        - power-up de tiro triplo;
        - estado do combo de destruição;
        - pontuação, wave e vidas.
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
        self.triple_shot_timer = C.TRIPLE_SHOT_SPAWN_EVERY
        self.game_over = False

        # Estado da mecânica de combo
        self.combo_hits = 0
        self.combo_multiplier = 1
        self.combo_timer = 0.0

    def start_wave(self):
        """Cria uma nova wave de asteroides com dificuldade crescente."""
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
        """Cria um asteroide e o registra nos grupos do mundo."""
        asteroid = Asteroid(pos, vel, size)
        self.asteroids.add(asteroid)
        self.all_sprites.add(asteroid)

    def spawn_ufo(self):
        """Cria um único UFO em uma das bordas da tela."""
        if self.ufos:
            return

        small = uniform(0, 1) < 0.5
        y = uniform(0, C.HEIGHT)
        x = 0 if uniform(0, 1) < 0.5 else C.WIDTH

        ufo = UFO(Vec(x, y), small)
        ufo.dir.xy = (1, 0) if x == 0 else (-1, 0)

        self.ufos.add(ufo)
        self.all_sprites.add(ufo)

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

    def spawn_triple_shot_powerup(self):
        """
        Cria um item de tiro triplo em uma posição aleatória da tela.
        """
        pos = Vec(
            uniform(80, C.WIDTH - 80),
            uniform(80, C.HEIGHT - 80),
        )

        powerup = TripleShotPowerUp(pos)
        self.powerups.add(powerup)
        self.all_sprites.add(powerup)

    def ufo_try_fire(self):
        """Permite que cada UFO ativo tente atirar na nave."""
        for ufo in self.ufos:
            bullet = ufo.fire_at(self.ship.pos)
            if bullet:
                self.ufo_bullets.add(bullet)
                self.all_sprites.add(bullet)

    def try_fire(self):
        """Dispara tiros da nave se o limite de projéteis permitir."""
        if len(self.bullets) >= C.MAX_BULLETS:
            return

        new_bullets = self.ship.fire()
        for bullet in new_bullets:
            self.bullets.add(bullet)
            self.all_sprites.add(bullet)

    def hyperspace(self):
        """Aciona o hyperspace da nave e aplica a penalidade de pontuação."""
        self.ship.hyperspace()
        self.score = max(0, self.score - C.HYPERSPACE_COST)

    def reset_combo(self):
        """
        Reinicia o estado do combo.

        Isso ocorre quando:
        - o tempo entre destruições excede a janela permitida;
        - a nave perde vida;
        - o jogo decide encerrar o combo por segurança.
        """
        self.combo_hits = 0
        self.combo_multiplier = 1
        self.combo_timer = 0.0

    def register_combo_hit(self) -> int:
        """
        Registra a destruição de um asteroide pelo jogador.

        Regras:
        - se o jogador ainda estiver dentro da janela do combo, incrementa a sequência;
        - se o combo já tiver expirado, inicia uma nova sequência;
        - o multiplicador é limitado por COMBO_MAX_MULTIPLIER.
        """
        if self.combo_timer > 0:
            self.combo_hits += 1
        else:
            self.combo_hits = 1

        self.combo_multiplier = min(self.combo_hits, C.COMBO_MAX_MULTIPLIER)
        self.combo_timer = C.COMBO_WINDOW
        return self.combo_multiplier

    def update(self, dt: float, keys):
        """
        Atualiza toda a simulação do jogo a cada frame.

        Responsabilidades:
        - aplicar controle da nave;
        - atualizar sprites;
        - controlar área segura após respawn;
        - controlar surgimento e tiros de UFO;
        - controlar surgimento dos power-ups;
        - controlar expiração do combo;
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

        # Controla o surgimento periódico do item de tiro triplo
        self.triple_shot_timer -= dt
        if self.triple_shot_timer <= 0 and not self.powerups:
            self.spawn_triple_shot_powerup()
            self.triple_shot_timer = C.TRIPLE_SHOT_SPAWN_EVERY

        # Controla o tempo do combo
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.reset_combo()

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
        - nave com itens (power-ups);
        - tiro do jogador com UFO.
        """
        hits = pg.sprite.groupcollide(
            self.asteroids,
            self.bullets,
            False,
            True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for asteroid, _ in hits.items():
            self.split_asteroid(asteroid, by_player=True)

        ufo_hits = pg.sprite.groupcollide(
            self.asteroids,
            self.ufo_bullets,
            False,
            True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for asteroid, _ in ufo_hits.items():
            self.split_asteroid(asteroid, by_player=False)

        # Coleta de itens (power-ups)
        for powerup in list(self.powerups):
            if (powerup.pos - self.ship.pos).length() < (powerup.r + self.ship.r):
                if isinstance(powerup, ShieldPowerUp):
                    self.ship.shield_time = C.SHIELD_DURATION
                elif isinstance(powerup, TripleShotPowerUp):
                    self.ship.triple_shot_time = C.TRIPLE_SHOT_DURATION
                powerup.kill()

        # Colisões que causam dano à nave
        if self.ship.invuln <= 0 and self.safe <= 0:
            for asteroid in self.asteroids:
                if (asteroid.pos - self.ship.pos).length() < (asteroid.r + self.ship.r):
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
            for bullet in list(self.bullets):
                if (ufo.pos - bullet.pos).length() < (ufo.r + bullet.r):
                    score = C.UFO_SMALL["score"] if ufo.small else C.UFO_BIG["score"]
                    self.score += score
                    ufo.kill()
                    bullet.kill()

    def split_asteroid(self, asteroid: Asteroid, by_player: bool = True):
        """
        Destrói um asteroide, soma pontuação e cria fragmentos menores.

        Se a destruição vier do jogador, o combo é atualizado e o multiplicador
        é aplicado na pontuação daquele asteroide.
        """
        base_score = C.AST_SIZES[asteroid.size]["score"]

        if by_player:
            multiplier = self.register_combo_hit()
        else:
            multiplier = 1

        self.score += base_score * multiplier

        split = C.AST_SIZES[asteroid.size]["split"]
        pos = Vec(asteroid.pos)
        asteroid.kill()

        for size in split:
            dirv = rand_unit_vec()
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX) * 1.2
            self.spawn_asteroid(pos, dirv * speed, size)

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

    def ship_die(self):
        """
        Remove uma vida da nave.

        Ao perder vida, o combo atual é encerrado para evitar manter a
        sequência após erro do jogador.
        """
        self.reset_combo()
        self.lives -= 1

        if self.lives <= 0:
            self.game_over = True
            return

        self.ship.pos.xy = (C.WIDTH / 2, C.HEIGHT / 2)
        self.ship.vel.xy = (0, 0)
        self.ship.angle = -90
        self.ship.invuln = C.SAFE_SPAWN_TIME
        self.safe = C.SAFE_SPAWN_TIME

    def draw(self, surf: pg.Surface, font: pg.font.Font):
        """
        Desenha todos os sprites e a HUD do jogo.

        A HUD exibe:
        - score;
        - vidas;
        - wave;
        - tempo restante do escudo, se ativo;
        - tempo restante do tiro triplo, se ativo;
        - combo atual, se houver sequência em andamento.
        """
        for spr in self.all_sprites:
            spr.draw(surf)

        pg.draw.line(surf, (60, 60, 60), (0, 50), (C.WIDTH, 50), width=1)

        txt = f"SCORE {self.score:06d}   LIVES {self.lives}   WAVE {self.wave}"

        if self.ship.shield_time > 0:
            txt += f"   SHIELD {self.ship.shield_time:0.1f}s"

        if self.ship.triple_shot_time > 0:
            txt += f"   TRIPLE {self.ship.triple_shot_time:0.1f}s"

        if self.combo_hits > 1 and self.combo_timer > 0:
            txt += f"   COMBO x{self.combo_multiplier}"

        label = font.render(txt, True, C.WHITE)
        surf.blit(label, (10, 10))