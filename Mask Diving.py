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

# color schemes - one per checkpoint
colorSchemes = [
    {"bg": "white",       "fg": "black",      "progressBg": "gray",      "invertBg": "black",      "invertFg": "white",      "invertProgressBg": "gray25"},
    {"bg": "black",       "fg": "white",      "progressBg": "gray25",    "invertBg": "white",      "invertFg": "black",      "invertProgressBg": "gray"},
    {"bg": "navy",        "fg": "cyan",       "progressBg": "blue",      "invertBg": "cyan",       "invertFg": "navy",       "invertProgressBg": "teal"},
    {"bg": "red",         "fg": "white",      "progressBg": "darkred",   "invertBg": "white",      "invertFg": "red",        "invertProgressBg": "pink"},
    {"bg": "#1a0033",     "fg": "#cc99ff",    "progressBg": "#6600cc",   "invertBg": "#cc99ff",    "invertFg": "#1a0033",    "invertProgressBg": "#9933ff"},
    {"bg": "#003300",     "fg": "#00ff66",    "progressBg": "#005500",   "invertBg": "#00ff66",    "invertFg": "#003300",    "invertProgressBg": "#007722"},
]

# difficulty settings - one per checkpoint
difficultySettings = [
    {"spawnInterval": 70,  "warningDuration": 60, "maxLasers": 1},
    {"spawnInterval": 60,  "warningDuration": 50, "maxLasers": 1},
    {"spawnInterval": 50,  "warningDuration": 40, "maxLasers": 2},
    {"spawnInterval": 40,  "warningDuration": 30, "maxLasers": 3},
    {"spawnInterval": 30,  "warningDuration": 22, "maxLasers": 4},
    {"spawnInterval": 20,  "warningDuration": 15, "maxLasers": 5},
]

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

# dash variables
dashing = False
dashFrames = 0
dashFramesMax = 10
dashSpeed = width//32
dashCooldown = 0
dashCooldownMax = 10
# slam variables
slamming = False
slamGravity = 100

# laser variables
lasers = []
laserSpawnTimer = 0
laserSpawnInterval = difficultySettings[0]["spawnInterval"]
laserWarningDuration = difficultySettings[0]["warningDuration"]
laserBeamSize = 8
maxSimultaneousLasers = difficultySettings[0]["maxLasers"]
gameOver = False

# progress / difficulty variables
progress = 0
progressMax = 300
checkpoint = 0
maxCheckpoints = 5

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

# draw floor, roof, progress bar and player
floor = canvas.create_rectangle(0, ground, width, height, fill="black")
roof = canvas.create_rectangle(0, 0, width, ceiling, fill="black")
progressBarBg = canvas.create_rectangle(0, 0, width, height * 0.01, fill="gray")
progressBar = canvas.create_rectangle(0, 0, 0, height * 0.01, fill="black")
player = create_rounded_rectangle(canvas, pX, pY, pX + pWidth, pY + pHeight, cornerRad, fill="black", state="hidden")

# track which keys are currently held down
keys_held = set()

def get_scheme():
    return colorSchemes[min(checkpoint, len(colorSchemes) - 1)]

def apply_color_scheme(scheme, flipped=False):
    bg = scheme["invertBg"] if flipped else scheme["bg"]
    fg = scheme["invertFg"] if flipped else scheme["fg"]
    pbg = scheme["invertProgressBg"] if flipped else scheme["progressBg"]
    canvas.config(bg=bg)
    canvas.itemconfig(player, fill=fg)
    canvas.itemconfig(floor, fill=fg)
    canvas.itemconfig(roof, fill=fg)
    canvas.itemconfig(progressBar, fill=fg)
    canvas.itemconfig(progressBarBg, fill=pbg)
    for laser in lasers:
        canvas.itemconfig(laser["warning"], fill=fg)
        canvas.itemconfig(laser["beam"], fill=fg)

def key_press(event):
    global jumpBuffer, gravityFlipped, shakeFrames, velocityY, dashing, dashFrames, dashCooldown, slamming
    keys_held.add(event.keysym)
    if event.keysym == "w":
        jumpBuffer = jumpBufferMax
    if event.keysym == "Shift_L" and dashCooldown == 0 and not dashing:
        dashing = True
        dashFrames = dashFramesMax
    if event.keysym == "s" and not isGrounded and not slamming:
        slamming = True
        velocityY = 0
    if event.keysym == "space":
        gravityFlipped = not gravityFlipped
        velocityY = 0
        shakeFrames = 15
        apply_color_scheme(get_scheme(), flipped=gravityFlipped)

def key_release(event):
    keys_held.discard(event.keysym)

def spawn_laser():
    fg = get_scheme()["invertFg"] if gravityFlipped else get_scheme()["fg"]
    safeTop = height * 0.35
    safeBottom = height * 0.65
    if checkpoint >= 1 and random.random() < 0.4:
        x = random.uniform(pWidth * 2, width - pWidth * 2)
        warning = canvas.create_rectangle(x - 2, ceiling, x + 2, ground, fill=fg, stipple="gray50")
        beam = canvas.create_rectangle(x - laserBeamSize, ceiling, x + laserBeamSize, ground, fill=fg, state="hidden")
        lasers.append({"warning": warning, "beam": beam, "x": x, "type": "vertical", "timer": 0})
    else:
        if random.random() < 0.5:
            y = random.uniform(ceiling + pHeight * 3, safeTop)
        else:
            y = random.uniform(safeBottom, ground - pHeight * 3)
        warning = canvas.create_rectangle(0, y - 2, width, y + 2, fill=fg, stipple="gray50")
        beam = canvas.create_rectangle(0, y - laserBeamSize, width, y + laserBeamSize, fill=fg, state="hidden")
        lasers.append({"warning": warning, "beam": beam, "y": y, "type": "horizontal", "timer": 0})

def update_lasers():
    global shakeFrames
    for laser in lasers[:]:
        laser["timer"] += 1
        if laser["timer"] == laserWarningDuration:
            canvas.itemconfig(laser["warning"], state="hidden")
            canvas.itemconfig(laser["beam"], state="normal")
            shakeFrames = 8
        if laser["timer"] > laserWarningDuration:
            if laser["type"] == "horizontal":
                if laser["y"] - laserBeamSize < pY + pHeight and laser["y"] + laserBeamSize > pY:
                    return True
            elif laser["type"] == "vertical":
                if laser["x"] - laserBeamSize < pX + pWidth and laser["x"] + laserBeamSize > pX:
                    return True
        if laser["timer"] == laserWarningDuration + 30:
            canvas.delete(laser["warning"])
            canvas.delete(laser["beam"])
            lasers.remove(laser)
    return False

def update_progress():
    global progress, checkpoint, laserSpawnInterval, laserWarningDuration, maxSimultaneousLasers, shakeFrames, progressMax
    if checkpoint >= maxCheckpoints:
        return
    progress += 1
    if progress >= progressMax:
        progress = 0
        checkpoint += 1
        progressMax = int(progressMax * 1.5)
        shakeFrames = 20
        settings = difficultySettings[min(checkpoint, len(difficultySettings) - 1)]
        laserSpawnInterval = settings["spawnInterval"]
        laserWarningDuration = settings["warningDuration"]
        maxSimultaneousLasers = settings["maxLasers"]
        apply_color_scheme(get_scheme(), flipped=gravityFlipped)
    barWidth = (progress / progressMax) * width
    canvas.coords(progressBar, 0, 0, barWidth, height * 0.01)

def show_game_over():
    canvas.itemconfig(player, state="hidden")
    for laser in lasers:
        canvas.itemconfig(laser["warning"], state="hidden")
        canvas.itemconfig(laser["beam"], state="hidden")
    scheme = get_scheme()
    color = scheme["invertFg"] if gravityFlipped else scheme["fg"]
    bg = scheme["invertBg"] if gravityFlipped else scheme["bg"]
    title = canvas.create_text(width//2, height//3, text="Skill: Lacking", font=("Arial", width//15, "bold"), fill=color)
    restart_button = tk.Button(root, text="RESTART", font=("Arial", width//40, "bold"), bg=color, fg=bg, cursor="hand2",
        command=lambda: restart_game([title, restart_button_window]))
    restart_button_window = canvas.create_window(width//2, height//1.2, window=restart_button)

def restart_game(elements):
    global pX, pY, velocityY, isGrounded, gravityFlipped, lasers, laserSpawnTimer, gameOver
    global progress, checkpoint, laserSpawnInterval, laserWarningDuration, maxSimultaneousLasers
    global dashing, dashFrames, dashCooldown, slamming, progressMax
    for element in elements:
        canvas.delete(element)
    for laser in lasers:
        canvas.delete(laser["warning"])
        canvas.delete(laser["beam"])
    lasers = []
    laserSpawnTimer = 0
    gameOver = False
    progress = 0
    progressMax = 300
    checkpoint = 0
    laserSpawnInterval = difficultySettings[0]["spawnInterval"]
    laserWarningDuration = difficultySettings[0]["warningDuration"]
    maxSimultaneousLasers = difficultySettings[0]["maxLasers"]
    dashing = False
    dashFrames = 0
    dashCooldown = 0
    slamming = False
    gravityFlipped = False
    apply_color_scheme(colorSchemes[0])
    canvas.coords(progressBar, 0, 0, 0, height * 0.01)
    startX = width//2
    startY = ground - pHeight
    canvas.move(player, startX - pX, startY - pY)
    pX = startX
    pY = startY
    canvas.itemconfig(player, state="normal")
    root.after(16, game_loop)

def game_loop():
    global pY, pX, velocityY, isGrounded, jumpBuffer, shakeFrames, laserSpawnTimer, gameOver, dashing, dashFrames, dashCooldown, slamming

    dx, dy = 0, 0

    if "a" in keys_held:
        dx -= speed
    if "d" in keys_held:
        dx += speed

    if dashing:
        if "a" in keys_held:
            dx -= dashSpeed
        elif "d" in keys_held:
            dx += dashSpeed
        else:
            dx += dashSpeed
        dashFrames -= 1
        if dashFrames <= 0:
            dashing = False
            dashCooldown = dashCooldownMax

    if dashCooldown > 0:
        dashCooldown -= 1

    if jumpBuffer > 0:
        jumpBuffer -= 1

    if jumpBuffer > 0 and isGrounded:
        velocityY = jumpPower if gravityFlipped else -jumpPower
        jumpBuffer = 0

    if gravityFlipped:
        velocityY -= slamGravity if slamming else gravity
        dy += velocityY
        if pY + dy <= ceiling:
            dy = ceiling - pY
            velocityY = 0
            isGrounded = True
            slamming = False
        else:
            isGrounded = False
    else:
        velocityY += slamGravity if slamming else gravity
        dy += velocityY
        if pY + pHeight + dy >= ground:
            dy = ground - (pY + pHeight)
            velocityY = 0
            isGrounded = True
            slamming = False
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

    laserSpawnTimer += 1
    if laserSpawnTimer >= laserSpawnInterval:
        for _ in range(random.randint(1, maxSimultaneousLasers)):
            spawn_laser()
        laserSpawnTimer = 0

    if update_lasers():
        show_game_over()
        return

    update_progress()

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
    line1 = canvas.create_text(width//2, height//2 - height//8, text="Use A and D to move", font=("Arial", width//50), fill="black")
    line2 = canvas.create_text(width//2, height//2 - height//16, text="Press W to jump", font=("Arial", width//50), fill="black")
    line3 = canvas.create_text(width//2, height//2, text="Press SPACE to flip gravity and invert colors", font=("Arial", width//50), fill="black")
    line4 = canvas.create_text(width//2, height//2 + height//16, text="Press E to dash", font=("Arial", width//50), fill="black")
    line5 = canvas.create_text(width//2, height//2 + height//8, text="Press S in the air to slam down", font=("Arial", width//50), fill="black")
    lore_elements = [title, line1, line2, line3, line4, line5]
    back_button = tk.Button(root, text="Back", font=("Arial", width//40, "bold"), bg="black", fg="white", cursor="hand2",
        command=lambda: [back_button.destroy(), [canvas.delete(e) for e in lore_elements], show_menu()])
    canvas.create_window(width//10, height//1.2, window=back_button)

def show_controls(menu_elements):
    for element in menu_elements:
        canvas.delete(element)
    title1 = canvas.create_text(width//2, height//5, text="CONTROLS", font=("Arial", width//20, "bold"), fill="black")
    line11 = canvas.create_text(width//2, height//2 - height//8, text="Use A and D to move", font=("Arial", width//50), fill="black")
    line22 = canvas.create_text(width//2, height//2 - height//16, text="Press W to jump", font=("Arial", width//50), fill="black")
    line33 = canvas.create_text(width//2, height//2, text="Press SPACE to flip gravity | This can be done midair", font=("Arial", width//50), fill="black")
    line44 = canvas.create_text(width//2, height//2 + height//16, text="Press E to dash", font=("Arial", width//50), fill="black")
    line55 = canvas.create_text(width//2, height//2 + height//8, text="Press S in the air to slam down", font=("Arial", width//50), fill="black")
    controls_elements = [title1, line11, line22, line33, line44, line55]
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