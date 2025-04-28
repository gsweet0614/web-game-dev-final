import pygame as pg
import sys as sys
import json
from enemy import Enemy
from world import World
from turret import Turret
from button import Button
import constants as c
import requests
import os
from dotenv import load_dotenv
load_dotenv()

#Adding Weather API
def get_weather_condition():
    API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    CITY = "Cincinnati"
    URL = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}"

    try:
        response = requests.get(URL)
        weather = response.json()
        weather_type = weather["weather"][0]["main"].lower()
        return weather_type
    except:
        return "clear"

#initialise pg
pg.init()

#create clock
clock = pg.time.Clock()

#create game window
screen = pg.display.set_mode((c.SCREEN_WIDTH + c.SIDE_PANEL, c.SCREEN_HEIGHT))
pg.display.set_caption("UC IT3049C Tower Defense")

#game variables
game_over = False
game_outcome = 0# -1 is loss & 1 is win
level_started = False
last_enemy_spawn = pg.time.get_ticks()
placing_turrets = False
selected_turret = None
toggle = False

#custom colors
retro_pink = (255, 72, 196)
retro_blue = (43, 209, 252)

#load images
#map
map_image = pg.image.load('level.png').convert_alpha()
#turret spritesheets
turret_spritesheets = []
for x in range(1, c.TURRET_LEVELS + 1):
  turret_sheet = pg.image.load(f'assets/turrets_{x}.png').convert_alpha()
  turret_spritesheets.append(turret_sheet)
#individual turret image for mouse cursor
cursor_turret = pg.image.load('assets/turretplacer.png').convert_alpha()
#enemies
enemy_images = {
  "weak": pg.image.load('assets/enemy_1.png').convert_alpha(),
  "medium": pg.image.load('assets/enemy_2.png').convert_alpha(),
  "strong": pg.image.load('assets/enemy_3.png').convert_alpha(),
  "elite": pg.image.load('assets/enemy_4.png').convert_alpha()
}
#buttons
buy_turret_image = pg.image.load('assets/buyTurret.png').convert_alpha()
cancel_image = pg.image.load('assets/Cancel.png').convert_alpha()
upgrade_turret_image = pg.image.load('assets/upgrade.png').convert_alpha()
begin_image = pg.image.load('assets/startRound.png').convert_alpha()
restart_image = pg.image.load('assets/Restart.png').convert_alpha()
fast_forward_image = pg.image.load('assets/speedUp.png').convert_alpha()
#gui
heart_image = pg.image.load("assets/heart.png").convert_alpha() #png image from pngtree.com
coin_image = pg.image.load("assets/coin.png").convert_alpha()
logo_image = pg.image.load("assets/logo.png").convert_alpha()

#weather
weather_icons = {
    "clear": pg.image.load("assets/sun.png").convert_alpha(),
    "clouds": pg.image.load("assets/cloud.png").convert_alpha(),
    "rain": pg.image.load("assets/rain.png").convert_alpha(),
    "snow": pg.image.load("assets/snow.png").convert_alpha(),
    "mist": pg.image.load("assets/cloud.png").convert_alpha(),
    "haze": pg.image.load("assets/cloud.png").convert_alpha(),
    "drizzle": pg.image.load("assets/rain.png").convert_alpha(),
}

weather_type = get_weather_condition()
print("Detected weather type:", weather_type)
weather_icon = weather_icons.get(weather_type, weather_icons["clear"])

#load sounds
shot_fx = pg.mixer.Sound('assets/concept.mp3') #shot sound
shot_fx.set_volume(0.0)

pg.mixer.music.load('assets/concept.mp3')
pg.mixer.music.set_volume(0.3)  
pg.mixer.music.play(-1) 


#load json data for level
with open('level.tmj') as file:
  world_data = json.load(file)

#load fonts for displaying text on the screen
text_font = pg.font.SysFont("Consolas", 24, bold = True)
large_font = pg.font.SysFont("Consolas", 36)
fun_font = pg.font.Font("assets/font.ttf", 24)
mine_font = pg.font.Font("assets/minecraft.ttf", 20)

#function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
  img = font.render(text, True, text_col)
  screen.blit(img, (x, y))

def display_data():
  # draw panel
  pg.draw.rect(screen, retro_pink, (c.SCREEN_WIDTH, 0, c.SIDE_PANEL, c.SCREEN_HEIGHT - 100))
  pg.draw.rect(screen, retro_blue, (c.SCREEN_WIDTH, 0, c.SIDE_PANEL, 400), 2)
  screen.blit(logo_image, (c.SCREEN_WIDTH, 400))

  # display data
  draw_text("LEVEL " + str(world.level), fun_font, retro_blue, c.SCREEN_WIDTH + 14, 10)
  screen.blit(heart_image, (c.SCREEN_WIDTH + 10, 75))
  draw_text(str(world.health), fun_font, retro_blue, c.SCREEN_WIDTH + 50, 70)
  screen.blit(coin_image, (c.SCREEN_WIDTH + 10, 127))
  draw_text(str(world.money), fun_font, retro_blue, c.SCREEN_WIDTH + 50, 120)

  # show weather info
  screen.blit(weather_icon, (c.SCREEN_WIDTH + 247, 350))
  draw_text("WEATHER IS " + weather_type.upper(), mine_font, retro_blue, c.SCREEN_WIDTH +  10, 355)



def create_turret(mouse_pos):
  mouse_tile_x = mouse_pos[0] // c.TILE_SIZE
  mouse_tile_y = mouse_pos[1] // c.TILE_SIZE
  #calculate the sequential number of the tile
  mouse_tile_num = (mouse_tile_y * c.COLS) + mouse_tile_x
  #check if that tile is grass
  if world.tile_map[mouse_tile_num] == 7:
    #check that there isn't already a turret there
    space_is_free = True
    for turret in turret_group:
      if (mouse_tile_x, mouse_tile_y) == (turret.tile_x, turret.tile_y):
        space_is_free = False
    #if it is a free space then create turret
    if space_is_free == True:
      new_turret = Turret(turret_spritesheets, mouse_tile_x, mouse_tile_y, shot_fx)
      turret_group.add(new_turret)
      #deduct cost of turret
      world.money -= c.BUY_COST

def select_turret(mouse_pos):
  mouse_tile_x = mouse_pos[0] // c.TILE_SIZE
  mouse_tile_y = mouse_pos[1] // c.TILE_SIZE
  for turret in turret_group:
    if (mouse_tile_x, mouse_tile_y) == (turret.tile_x, turret.tile_y):
      return turret

def clear_selection():
  for turret in turret_group:
    turret.selected = False

#create world
world = World(world_data, map_image)
world.process_data()
world.process_enemies()

#create groups
enemy_group = pg.sprite.Group()
turret_group = pg.sprite.Group()

#create buttons
turret_button = Button(c.SCREEN_WIDTH + 71, 230, buy_turret_image, True)
cancel_button = Button(c.SCREEN_WIDTH + 48, 220, cancel_image, True)
upgrade_button = Button(c.SCREEN_WIDTH + 70, 180, upgrade_turret_image, True)
begin_button = Button(c.SCREEN_WIDTH + 50, 280, begin_image, True)
restart_button = Button(310, 300, restart_image, True)
fast_forward_button = Button(c.SCREEN_WIDTH + 50, 280, fast_forward_image, False)
how_to_button = Button(c.SCREEN_WIDTH + 10, 230, buy_turret_image, True)

#game loop
run = True
while run:

  clock.tick(c.FPS)

  #########################
  # UPDATING SECTION
  #########################

  if game_over == False:
    #check if player has lost
    if world.health <= 0:
      game_over = True
      game_outcome = -1 #loss
    #check if player has won
    if world.level > c.TOTAL_LEVELS:
      game_over = True
      game_outcome = 1 #win

    #update groups
    enemy_group.update(world)
    turret_group.update(enemy_group, world)

    #highlight selected turret
    if selected_turret:
      selected_turret.selected = True

  #########################
  # DRAWING SECTION
  #########################

  #draw level
  world.draw(screen)

  #draw groups
  enemy_group.draw(screen)
  for turret in turret_group:
    turret.draw(screen)

  #draw how-to button
  how_to_button.draw(screen)

  display_data()

  if game_over == False:
    #check if the level has been started or not
    if level_started == False:
      if begin_button.draw(screen):
        level_started = True
    else:
      #fast forward option
      world.game_speed = 1
      if fast_forward_button.draw(screen):
        world.game_speed = 2
      #spawn enemies
      if pg.time.get_ticks() - last_enemy_spawn > c.SPAWN_COOLDOWN:
        if world.spawned_enemies < len(world.enemy_list):
          enemy_type = world.enemy_list[world.spawned_enemies]
          enemy = Enemy(enemy_type, world.waypoints, enemy_images)
          enemy_group.add(enemy)
          world.spawned_enemies += 1
          last_enemy_spawn = pg.time.get_ticks()

    #check if the wave is finished
    if world.check_level_complete() == True:
      world.money += c.LEVEL_COMPLETE_REWARD
      world.level += 1
      level_started = False
      last_enemy_spawn = pg.time.get_ticks()
      world.reset_level()
      world.process_enemies()

    #draw buttons
    #button for placing turrets
    #for the "turret button" show cost of turret and draw the button
    if turret_button.draw(screen):
      placing_turrets = True
    #if placing turrets then show the cancel button as well
    if placing_turrets == True:
      #show cursor turret
      cursor_rect = cursor_turret.get_rect()
      cursor_pos = pg.mouse.get_pos()
      cursor_rect.center = cursor_pos
      if cursor_pos[0] <= c.SCREEN_WIDTH:
        screen.blit(cursor_turret, cursor_rect)
      if cancel_button.draw(screen):
        placing_turrets = False
    #if a turret is selected then show the upgrade button
    if selected_turret:
      #if a turret can be upgraded then show the upgrade button
      if selected_turret.upgrade_level < c.TURRET_LEVELS:
        #show cost of upgrade and draw the button
        if upgrade_button.draw(screen):
          if world.money >= c.UPGRADE_COST:
            selected_turret.upgrade()
            world.money -= c.UPGRADE_COST
  else:
    pg.draw.rect(screen, retro_blue, (200, 200, 400, 200), border_radius = 30)
    if game_outcome == -1:
      draw_text("GAME OVER", mine_font, retro_pink, 310, 230)
    elif game_outcome == 1:
      draw_text("YOU WIN!", mine_font, retro_pink, 315, 230)
    #restart level
    if restart_button.draw(screen):
      game_over = False
      level_started = False
      placing_turrets = False
      selected_turret = None
      last_enemy_spawn = pg.time.get_ticks()
      world = World(world_data, map_image)
      world.process_data()
      world.process_enemies()
      #empty groups
      enemy_group.empty()
      turret_group.empty()

  #event handler
  for event in pg.event.get():
    #quit program
    if event.type == pg.QUIT:
      run = False
    #mouse click
    if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
      mouse_pos = pg.mouse.get_pos()
      #check if mouse is on the game area
      if mouse_pos[0] < c.SCREEN_WIDTH and mouse_pos[1] < c.SCREEN_HEIGHT:
        #clear selected turrets
        selected_turret = None
        clear_selection()
        if placing_turrets == True:
          #check if there is enough money for a turret
          if world.money >= c.BUY_COST:
            create_turret(mouse_pos)
        else:
          selected_turret = select_turret(mouse_pos)
          if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
              game_paused = True

  #update display
  pg.display.flip()

pg.quit()