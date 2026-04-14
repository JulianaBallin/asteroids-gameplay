# ASTEROIDE SINGLEPLAYER v1.0
# This file stores the gameplay, rendering, and balancing constants.

WIDTH = 960
HEIGHT = 720
FPS = 60

START_LIVES = 3
SAFE_SPAWN_TIME = 2.0
WAVE_DELAY = 2.0

SHIP_RADIUS = 15
SHIP_TURN_SPEED = 220.0
SHIP_THRUST = 220.0
SHIP_FRICTION = 0.995
SHIP_FIRE_RATE = 0.2
SHIP_BULLET_SPEED = 420.0
HYPERSPACE_COST = 250

AST_VEL_MIN = 30.0
AST_VEL_MAX = 90.0
AST_SIZES = {
    "L": {"r": 46, "score": 20, "split": ["M", "M"]},
    "M": {"r": 24, "score": 50, "split": ["S", "S"]},
    "S": {"r": 12, "score": 100, "split": []},
}

BULLET_RADIUS = 2
BULLET_TTL = 1.0
MAX_BULLETS = 8

UFO_SPAWN_EVERY = 15.0
UFO_SPEED = 80.0
UFO_FIRE_EVERY = 1.2
UFO_BULLET_SPEED = 260.0
UFO_BULLET_TTL = 1.8
UFO_BIG = {"r": 18, "score": 200, "aim": 0.2}
UFO_SMALL = {"r": 12, "score": 1000, "aim": 0.6}

WHITE = (240, 240, 240)
GRAY = (120, 120, 120)
BLACK = (0, 0, 0)

RANDOM_SEED = None

# Duração do fade-in da tela de game over (segundos)
GAME_OVER_FADE_DURATION = 1.5

# Configurações da mecânica de escudo temporário
SHIELD_DURATION = 6.0          # Tempo que o escudo fica ativo após coleta
SHIELD_SPAWN_EVERY = 12.0      # Intervalo para surgir um novo item de escudo
SHIELD_PICKUP_TTL = 8.0        # Tempo de vida do item na tela
SHIELD_PICKUP_RADIUS = 10      # Raio do item coletável
SHIELD_HIT_INVULN = 1.0        # Pequena invulnerabilidade após o escudo quebrar

# Configurações da mecânica de tiro triplo
TRIPLE_SHOT_DURATION = 10.0    # Duração do tiro triplo após coleta
TRIPLE_SHOT_SPAWN_EVERY = 20.0 # Intervalo para surgir o item de tiro triplo
TRIPLE_SHOT_PICKUP_TTL = 8.0   # Tempo de vida do item na tela
TRIPLE_SHOT_PICKUP_RADIUS = 10 # Raio do item coletável

# Configurações da mecânica de raio laser
LASER_DURATION = 8.0           # Duração do laser após coleta
LASER_SPAWN_EVERY = 25.0       # Intervalo para surgir o item de laser
LASER_PICKUP_TTL = 8.0         # Tempo de vida do item na tela
LASER_PICKUP_RADIUS = 10       # Raio do item coletável
LASER_RANGE = 400.0            # Alcance máximo do raio laser

# Configurações da mecânica de combo de destruição
COMBO_WINDOW = 2.0             # Janela máxima entre destruições para manter o combo
COMBO_MAX_MULTIPLIER = 5       # Multiplicador máximo permitido