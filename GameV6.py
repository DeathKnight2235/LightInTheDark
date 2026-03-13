import tkinter as tk
import random

# window creation
root = tk.Tk()
# get screen data
width, height = root.winfo_screenwidth(), root.winfo_screenheight()
# set size
root.geometry(f'{width}x{height}')
# config
root.attributes("-fullscreen", True)
root.bind("<Escape>", lambda e: root.destroy())
root.title("Game")

# draw canvas - game window
canvas = tk.Canvas(root, width=width, height=height, bg="white")
canvas.pack()

# player variables
pX = width//2.15
pY = height//2
pWidth = width//16
pHeight = width//16
cornerRad = width//64
speed = width//128
jumpPower = height//32
gravity = 2
velocityY = 0
isGrounded = False
ground = height * 0.95
ceiling = height * 0.05
jumpBuffer = 0
jumpBufferMax = 10
gravityFlipped = False
shakeFrames = 0
shakeIntensity = 8
lasers = []
laserSpawnTimer = 0
laserSpawnInterval = 70
gameOver = False

def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

# draw floor, roof and player
floor = canvas.create_rectangle(0, ground, width, height, fill="black")
roof = canvas.create_rectangle(0, 0, width, ceiling, fill="black")
player = create_rounded_rectangle(canvas, pX, pY, pX + pWidth, pY + pHeight, cornerRad, fill="black", state="hidden")

# track which keys are currently held down
keys_held = set()

def key_press(event):
    global jumpBuffer, gravityFlipped, shakeFrames, velocityY
    keys_held.add(event.keysym)
    if event.keysym == "Up":
        jumpBuffer = jumpBufferMax
    if event.keysym == "space":
        gravityFlipped = not gravityFlipped
        velocityY = 0
        shakeFrames = 15
        if gravityFlipped:
            canvas.config(bg="black")
            canvas.itemconfig(player, fill="white")
            canvas.itemconfig(floor, fill="white")
            canvas.itemconfig(roof, fill="white")
            for laser in lasers:
                canvas.itemconfig(laser["warning"], fill="white")
                canvas.itemconfig(laser["beam"], fill="white")
        else:
            canvas.config(bg="white")
            canvas.itemconfig(player, fill="black")
            canvas.itemconfig(floor, fill="black")
            canvas.itemconfig(roof, fill="black")
            for laser in lasers:
                canvas.itemconfig(laser["warning"], fill="black")
                canvas.itemconfig(laser["beam"], fill="black")

def key_release(event):
    keys_held.discard(event.keysym)

def spawn_laser():
    y = random.uniform(ceiling + pHeight * 2, ground - pHeight * 2)
    color = "white" if gravityFlipped else "black"
    warning = canvas.create_rectangle(0, y - 2, width, y + 2, fill=color, stipple="gray50")
    beam = canvas.create_rectangle(0, y - height//8, width, y + height//8, fill=color, state="hidden")
    lasers.append({"warning": warning, "beam": beam, "y": y, "timer": 0})

def update_lasers():
    global shakeFrames
    for laser in lasers[:]:
        laser["timer"] += 1
        if laser["timer"] == 60:  # warning phase ends, fire!
            canvas.itemconfig(laser["warning"], state="hidden")
            canvas.itemconfig(laser["beam"], state="normal")
            shakeFrames = 8  # small shake when laser fires
        if laser["timer"] > 60:  # check collision while firing
            if laser["y"] - 8 < pY + pHeight and laser["y"] + 8 > pY:
                return True  # player hit
        if laser["timer"] == 90:  # laser disappears
            canvas.delete(laser["warning"])
            canvas.delete(laser["beam"])
            lasers.remove(laser)
    return False

def show_game_over():
    canvas.itemconfig(player, state="hidden")
    color = "white" if gravityFlipped else "black"
    bg = "black" if gravityFlipped else "white"
    title = canvas.create_text(width//2, height//3, text="GAME OVER", font=("Arial", width//15, "bold"), fill=color)
    restart_button = tk.Button(root, text="RESTART", font=("Arial", width//40, "bold"), bg=color, fg=bg, cursor="hand2",
        command=lambda: restart_game([title, restart_button_window]))
    restart_button_window = canvas.create_window(width//2, height//2, window=restart_button)

def restart_game(elements):
    global pX, pY, velocityY, isGrounded, gravityFlipped, lasers, laserSpawnTimer, gameOver
    for element in elements:
        canvas.delete(element)
    # clear any remaining lasers
    for laser in lasers:
        canvas.delete(laser["warning"])
        canvas.delete(laser["beam"])
    lasers = []
    laserSpawnTimer = 0
    gameOver = False
    # reset gravity
    gravityFlipped = False
    canvas.config(bg="white")
    canvas.itemconfig(player, fill="black")
    canvas.itemconfig(floor, fill="black")
    canvas.itemconfig(roof, fill="black")
    # reset player position
    startX = width//2
    startY = ground - pHeight
    canvas.move(player, startX - pX, startY - pY)
    pX = startX
    pY = startY
    canvas.itemconfig(player, state="normal")
    root.after(16, game_loop)

def game_loop():
    global pY, pX, velocityY, isGrounded, jumpBuffer, shakeFrames, laserSpawnTimer, gameOver

    dx, dy = 0, 0

    if "Left" in keys_held:
        dx -= speed
    if "Right" in keys_held:
        dx += speed

    if jumpBuffer > 0:
        jumpBuffer -= 1

    if jumpBuffer > 0 and isGrounded:
        velocityY = jumpPower if gravityFlipped else -jumpPower
        jumpBuffer = 0

    if gravityFlipped:
        velocityY -= gravity
        dy += velocityY
        if pY + dy <= ceiling:
            dy = ceiling - pY
            velocityY = 0
            isGrounded = True
        else:
            isGrounded = False
    else:
        velocityY += gravity
        dy += velocityY
        if pY + pHeight + dy >= ground:
            dy = ground - (pY + pHeight)
            velocityY = 0
            isGrounded = True
        else:
            isGrounded = False

    pX += dx
    pY += dy
    canvas.move(player, dx, dy)

    if pX + pWidth < 0:
        pX = width
        canvas.move(player, width + pWidth, 0)
    elif pX > width:
        pX = -pWidth
        canvas.move(player, -(width + pWidth), 0)

    if shakeFrames > 0:
        shakeX = random.randint(-shakeIntensity, shakeIntensity)
        shakeY = random.randint(-shakeIntensity, shakeIntensity)
        canvas.place(x=shakeX, y=shakeY)
        shakeFrames -= 1
    else:
        canvas.place(x=0, y=0)

    # spawn and update lasers
    laserSpawnTimer += 1
    if laserSpawnTimer >= laserSpawnInterval:
        spawn_laser()
        laserSpawnTimer = 0

    if update_lasers():
        show_game_over()
        return  # stop the game loop

    root.after(16, game_loop)

def start_game(menu_elements):
    global pX, pY
    for element in menu_elements:
        canvas.delete(element)
    root.unbind("<KeyPress>")
    root.bind("<KeyPress>", key_press)
    root.bind("<KeyRelease>", key_release)
    startX = width//2
    startY = ground - pHeight
    canvas.move(player, startX - pX, startY - pY)
    pX = startX
    pY = startY
    canvas.itemconfig(player, state="normal")
    root.after(16, game_loop)

def show_lore(menu_elements):
    for element in menu_elements:
        canvas.delete(element)
    title = canvas.create_text(width//2, height//5, text="LORE", font=("Arial", width//20, "bold"), fill="black")
    line1 = canvas.create_text(width//2, height//2 - height//8, text="Use LEFT and RIGHT arrow keys to move", font=("Arial", width//50), fill="black")
    line2 = canvas.create_text(width//2, height//2 - height//16, text="Press UP to jump", font=("Arial", width//50), fill="black")
    line3 = canvas.create_text(width//2, height//2, text="Press SPACE to flip gravity and invert colors", font=("Arial", width//50), fill="black")
    lore_elements = [title, line1, line2, line3]
    back_button = tk.Button(root, text="Back", font=("Arial", width//40, "bold"), bg="black", fg="white", cursor="hand2",
        command=lambda: [back_button.destroy(), [canvas.delete(e) for e in lore_elements], show_menu()])
    canvas.create_window(width//10, height//1.2, window=back_button)

def show_controls(menu_elements):
    for element in menu_elements:
        canvas.delete(element)
    title1 = canvas.create_text(width//2, height//5, text="CONTROLS", font=("Arial", width//20, "bold"), fill="black")
    line11 = canvas.create_text(width//2, height//2 - height//8, text="Use LEFT and RIGHT arrow keys to move", font=("Arial", width//50), fill="black")
    line22 = canvas.create_text(width//2, height//2 - height//16, text="Press UP to jump", font=("Arial", width//50), fill="black")
    line33 = canvas.create_text(width//2, height//2, text="Press SPACE to flip gravity | This can be done midair", font=("Arial", width//50), fill="black")
    controls_elements = [title1, line11, line22, line33]
    back_button = tk.Button(root, text="Back", font=("Arial", width//40, "bold"), bg="black", fg="white", cursor="hand2",
        command=lambda: [back_button.destroy(), [canvas.delete(e) for e in controls_elements], show_menu()])
    canvas.create_window(width*0.87, height//1.2, window=back_button)

def show_menu():
    title = canvas.create_text(width//2, height//3, text="GameV6", font=("Arial", width//20, "bold"), fill="black")
    play_button = tk.Button(root, text="PLAY", font=("Arial", width//40, "bold"), bg="black", fg="white", cursor="hand2",
        command=lambda: [play_button.destroy(), lore_button.destroy(), controls_button.destroy(), start_game([title])])
    lore_button = tk.Button(root, text="Lore", font=("Arial", width//40, "bold"), bg="black", fg="white", cursor="hand2",
        command=lambda: [play_button.destroy(), lore_button.destroy(), controls_button.destroy(), show_lore([title])])
    controls_button = tk.Button(root, text="Controls", font=("Arial", width//40, "bold"), bg="black", fg="white", cursor="hand2",
        command=lambda: [play_button.destroy(), lore_button.destroy(), controls_button.destroy(), show_controls([title])])
    canvas.create_window(width//2, height//1.2, window=play_button)
    canvas.create_window(width//10, height//1.2, window=lore_button)
    canvas.create_window(width*0.87, height//1.2, window=controls_button)

show_menu()
root.mainloop()