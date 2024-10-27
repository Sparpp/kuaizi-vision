import random
import cv2
import keyboard
import time
from cvzone.HandTrackingModule import HandDetector
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame 

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

def load_images(folderpath, scale=1.0):
    overlaylist = []
    filelist = os.listdir(folderpath)
    for filename in filelist:
        imgpath = os.path.join(folderpath, filename)
        image = pygame.image.load(imgpath).convert_alpha()
        image = pygame.transform.scale_by(image, scale)
        overlaylist.append(image)
    return overlaylist

def getWebcamImage(cap, hd, screen, bot_images):
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    hands, _ = hd.findHands(frame)
    total_finger_count = 0
    left_count = 0
    right_count = 0

    for hand in hands:
        fingers_up = hd.fingersUp(hand)

        if fingers_up == [0, 0, 1, 0, 0]:
            doBotExpressions(4, screen, bot_images, False, True, False, False)

        count = fingers_up.count(1)
        total_finger_count += count
        if hand["type"] == "Left":
            right_count += count
        else:
            left_count += count

    return left_count, right_count, frame

def processGameState(my_font, screen, player_hand_states, player_game_states):
    go = 0

    if player_hand_states != player_game_states:
        text_surface = my_font.render('Get in your position!', False, (255, 255, 255))
    else:
        text_surface = my_font.render('', False, (255, 0, 0)) 
        go = 1

    text_rect = text_surface.get_rect(center=(FRAME_WIDTH/2, 400))
    screen.blit(text_surface, text_rect)
    
    return go

def doTurnProcessing(cap, hd, bot_game_states, player_game_states, turnCounter, my_font, screen, bot_images):
    receivingHand = 0
    # the bot attacks
    if turnCounter % 2 == 0:
        # decide a move (greedy for now)
        if bot_game_states[0] > bot_game_states[1]:
            attackingHand = 0
        else:
            attackingHand = 1
        if player_game_states[0] > player_game_states[1]:
            receivingHand = 0
        else:
            receivingHand = 1

        # update game states
        player_game_states[receivingHand] += bot_game_states[attackingHand]
        if player_game_states[receivingHand] >= 5:
            player_game_states[receivingHand] = player_game_states[receivingHand] % 5

    # the player attacks
    else:
        text_surface = my_font.render('Drop hand NOT attacking with', False, (255, 0, 0)) 

        text_rect = text_surface.get_rect(center=(FRAME_WIDTH/2, 400))
        screen.blit(text_surface, text_rect)

        player_hand_states = [0, 0]
        # decide attacking hand
        while(True):
            exit = 0
            left_count, right_count, frame = getWebcamImage(cap, hd, screen, bot_images)

            player_hand_states[0] = left_count
            player_hand_states[1] = right_count

            for i in range(2):
                if player_hand_states[i] == 0:
                    attackingHand = 1 - i
                    exit = 1
            
            cam = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
            cam = pygame.transform.scale_by(cam, 0.4)
            screen.blit(cam, (384, 432))

            pygame.display.flip()

            if exit == 1:
                break
            
        
        text_surface = my_font.render('Drop hand NOT attacking with', False, (0, 0, 0)) 

        text_rect = text_surface.get_rect(center=(FRAME_WIDTH/2, 400))
        screen.blit(text_surface, text_rect)

        text_surface = my_font.render('Put up ONE hand on the side youre attacking', False, (255, 0, 0)) 

        text_rect = text_surface.get_rect(center=(FRAME_WIDTH/2, 400))
        screen.blit(text_surface, text_rect)
        start_time = time.time()
        time_passed = 0
        # decide target hand
        while(time_passed <= 5):
            left_count, right_count, frame = getWebcamImage(cap, hd, screen, bot_images)

            time_passed = time.time() - start_time

            cam = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
            cam = pygame.transform.scale_by(cam, 0.4)
            screen.blit(cam, (384, 432))

            pygame.display.flip()
        
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        hands, _ = hd.findHands(frame)

        if len(hands) > 0:
            receiving = hands[0]["type"]
        if receiving == "Left":
            receivingHand = 1
        else:
            receivingHand = 0

        # update game states
        bot_game_states[receivingHand] += player_game_states[attackingHand]
        if bot_game_states[receivingHand] >= 5:
            bot_game_states[receivingHand] = bot_game_states[receivingHand] % 5

    return attackingHand, receivingHand

def doHandAnimation(cap, hd, attack, receive, screen, hand_images, player_game_states, bot_game_states, bot_images, turnCount):
    botRH_img = hand_images[bot_game_states[1]]
    botLH_img = hand_images[bot_game_states[0]]
    botLH_img = pygame.transform.flip(botLH_img, False, True)
    botRH_img = pygame.transform.flip(botRH_img, True, True)
    botLH_rect = botLH_img.get_rect(topleft=(145, 175))
    botRH_rect = botRH_img.get_rect(topleft=(920, 175))
    playerLH_img = hand_images[player_game_states[0]]
    playerRH_img = hand_images[player_game_states[1]]
    playerRH_img = pygame.transform.flip(playerRH_img, True, False)
    playerLH_rect = playerLH_img.get_rect(topleft=(145, 375))
    playerRH_rect = playerRH_img.get_rect(topleft=(920, 375))
    speed = 1
    first_half = True

    if attack == 0 and turnCount % 2 == 0:
        hand_rect = botLH_rect
    elif attack == 0 and turnCount % 2 == 1:
        hand_rect = playerLH_rect
    elif attack == 1 and turnCount % 2 == 1:
        hand_rect = playerRH_rect
    else:
        hand_rect = botRH_rect

    # horizontal poke
    if attack == receive and turnCount % 2 == 0:
        seed = random.randint(0, 50)
        while True:
            screen.fill((0, 0, 0))
            doBotExpressions(seed, screen, bot_images, True, False, False, False)

            left_count, right_count, frame = getWebcamImage(cap, hd, screen, bot_images)

            screen.blit(playerLH_img, (145, 375))
            screen.blit(playerRH_img, (920, 375))

            if attack == 0:
                screen.blit(botLH_img, hand_rect)
                screen.blit(botRH_img, (920, 175))
            else:
                screen.blit(botLH_img, (145, 175))
                screen.blit(botRH_img, hand_rect)

            cam = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
            cam = pygame.transform.scale_by(cam, 0.4)
            screen.blit(cam, (384, 432))

            pygame.display.flip()

            if first_half:
                hand_rect.y += speed
                speed *= 1.1
                if hand_rect.y > 190:
                    first_half = False
                    speed = -1
            else:
                hand_rect.y += speed
                speed *= 1.1
                if hand_rect.y <= 145:
                    break

        return 0
    elif attack == receive and turnCount % 2 == 1:
        seed = random.randint(0, 50)
        while True:
            screen.fill((0, 0, 0))
            doBotExpressions(seed, screen, bot_images, False, True, False, False)

            left_count, right_count, frame = getWebcamImage(cap, hd, screen, bot_images)

            screen.blit(botLH_img, (145, 175))
            screen.blit(botRH_img, (920, 175))

            if attack == 0:
                screen.blit(playerLH_img, hand_rect)
                screen.blit(playerRH_img, (920, 375))
            else:
                screen.blit(playerLH_img, (145, 375))
                screen.blit(playerRH_img, hand_rect)

            cam = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
            cam = pygame.transform.scale_by(cam, 0.4)
            screen.blit(cam, (384, 432))

            pygame.display.flip()

            if first_half:
                hand_rect.y -= speed
                speed *= 1.1
                if hand_rect.y < 360:
                    first_half = False
                    speed = -1
            else:
                hand_rect.y -= speed
                speed *= 1.1
                if hand_rect.y >= 405:
                    break

        return 0
    # diagonal poke
    elif attack != receive and turnCount % 2 == 0:
        seed = random.randint(0, 50)
        while True:
            screen.fill((0, 0, 0))
            doBotExpressions(seed, screen, bot_images, True, False, False, False)

            left_count, right_count, frame = getWebcamImage(cap, hd, screen, bot_images)

            screen.blit(playerLH_img, (145, 375))
            screen.blit(playerRH_img, (920, 375))

            if attack == 0:
                screen.blit(pygame.transform.rotate(botLH_img, 45), hand_rect)
                screen.blit(botRH_img, (920, 175))
            else:
                screen.blit(botLH_img, (145, 175))
                screen.blit(pygame.transform.rotate(botRH_img, 315), hand_rect)

            cam = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
            cam = pygame.transform.scale_by(cam, 0.4)
            screen.blit(cam, (384, 432))

            pygame.display.flip()


            if first_half:
                hand_rect.y += speed
                if attack == 1:
                    hand_rect.x -= speed * 29.5
                else:
                    hand_rect.x += speed * 29.5
                speed *= 1.1
                if hand_rect.y > 190:
                    first_half = False
                    speed = -1
            else:
                hand_rect.y += speed
                if attack == 1:
                    hand_rect.x -= speed * 3.5
                else:
                    hand_rect.x += speed * 3.5
                speed *= 1.1
                if hand_rect.y <= 145:
                    break

        return 0
    elif attack != receive and turnCount % 2 == 1:
        seed = random.randint(0, 50)
        while True:
            screen.fill((0, 0, 0))
            doBotExpressions(seed, screen, bot_images, False, True, False, False)

            left_count, right_count, frame = getWebcamImage(cap, hd, screen, bot_images)

            screen.blit(botLH_img, (145, 175))
            screen.blit(botRH_img, (920, 175))

            if attack == 0:
                screen.blit(pygame.transform.rotate(playerLH_img, 315), hand_rect)
                screen.blit(playerRH_img, (920, 375))
            else:
                screen.blit(playerLH_img, (145, 375))
                screen.blit(pygame.transform.rotate(playerRH_img, 45), hand_rect)

            cam = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
            cam = pygame.transform.scale_by(cam, 0.4)
            screen.blit(cam, (384, 432))

            pygame.display.flip()


            if first_half:
                hand_rect.y -= speed
                if attack == 1:
                    hand_rect.x -= speed * 29.5
                else:
                    hand_rect.x += speed * 29.5
                speed *= 1.1
                if hand_rect.y < 360:
                    first_half = False
                    speed = -1
            else:
                hand_rect.y -= speed
                if attack == 1:
                    hand_rect.x -= speed * 3.5
                else:
                    hand_rect.x += speed * 3.5
                speed *= 1.1
                if hand_rect.y >= 405:
                    break

        return 0
    
def doBotExpressions(seed, screen, bot_images, attack=False, defend=False, idle=True, death=False):
    random.seed(seed)
    if idle:
        expression = bot_images[10]
    elif death:
        expression = bot_images[9]
    elif attack:
        expression = bot_images[random.randint(0, 8)]
    elif defend:
        expression = bot_images[random.randint(11, len(bot_images) - 1)]
    
    img_rect = expression.get_rect(center=((FRAME_WIDTH // 2, 250)))
    screen.blit(expression, img_rect)

def main():
    # initialise everything
    if True:
        pygame.init() 
        pygame.font.init()
        pygame.time.Clock().tick(60)
        my_font = pygame.font.SysFont('determinationmonowebregular', 30)
        
        screen = pygame.display.set_mode((FRAME_WIDTH, FRAME_HEIGHT)) 

        hand_images = load_images('assets/img')
        bot_images = load_images('assets/faces', 0.5)

        cap = cv2.VideoCapture(0)
        cap.set(10, 200)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        hd = HandDetector(detectionCon=0.6)

        turnCounter = 1
        winner = ""

        bot_game_states = [1, 1]
        player_game_states = [1, 1]
        player_hand_states = [0, 0]

        running = True

    while running:
        screen.fill((0, 0, 0))
        doBotExpressions(random.randint(0, 50), screen, bot_images)

        left_count, right_count, frame = getWebcamImage(cap, hd, screen, bot_images)

        if winner == "":
            player_hand_states[0] = left_count % 6
            player_hand_states[1] = right_count % 6

            score1 = my_font.render(f'{player_game_states[0]}', False, (255, 0, 0))        
            screen.blit(score1, (FRAME_WIDTH // 4, (FRAME_HEIGHT // 8) * 7))

            score2 = my_font.render(f'{player_game_states[1]}', False, (255, 0, 0))
            screen.blit(score2, ((FRAME_WIDTH // 4) * 3, (FRAME_HEIGHT // 8) * 7))

            valid = processGameState(my_font, screen, player_hand_states, player_game_states)

            botRH_img = hand_images[bot_game_states[1]]
            botLH_img = hand_images[bot_game_states[0]]
            botLH_img = pygame.transform.flip(botLH_img, False, True)
            botRH_img = pygame.transform.flip(botRH_img, True, True)
            playerLH_img = hand_images[player_hand_states[0]]
            playerRH_img = hand_images[player_hand_states[1]]
            playerRH_img = pygame.transform.flip(playerRH_img, True, False)

            screen.blit(playerLH_img, (145, 375))
            screen.blit(playerRH_img, (920, 375))
            screen.blit(botLH_img, (145, 175))
            screen.blit(botRH_img, (920, 175))

            if valid == 1:
                attack, receive = doTurnProcessing(cap, hd, bot_game_states, player_game_states, turnCounter, my_font, screen, bot_images)
                
                doHandAnimation(cap, hd, attack, receive, screen, hand_images, player_game_states, bot_game_states, bot_images, turnCounter)

                if bot_game_states[0] == 0 and bot_game_states[1] == 0:
                    winner = "PLAYER"
                elif player_hand_states[0] == 0 and player_game_states[1] == 0:
                    winner = "BOT"

                turnCounter += 1

            cam = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
            cam = pygame.transform.scale_by(cam, 0.4)
            screen.blit(cam, (384, 432))

            pygame.display.flip()

        if winner != "":
            screen.fill((0, 0, 0))
            if winner == "PLAYER":
                doBotExpressions(random.randint(0, 50), screen, bot_images, False, False, False, True)
                text_surface = my_font.render('YOUVE WON!', False, (255, 255, 0)) 
            elif winner == "BOT":
                text_surface = my_font.render('YOUVE LOST!', False, (255, 0, 0)) 
                doBotExpressions(random.randint(0, 50), screen, bot_images, False, False, True, False)
            

            text_rect = text_surface.get_rect(center=(FRAME_WIDTH/2, 400))
            screen.blit(text_surface, text_rect)
            cam = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
            cam = pygame.transform.scale_by(cam, 0.4)
            screen.blit(cam, (384, 432))

            pygame.display.flip()

        # press esc to close
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key== pygame.K_ESCAPE:
                    running = False

    print("WINNER: " + winner)

    pygame.quit()
    cap.release()

main()