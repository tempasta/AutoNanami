version = "v2.0.0"

import time
import threading
import random
import platform
import ctypes
import os
import sys
import pyautogui
from colorama import init, Fore, Style, Back

init(autoreset=True)
import dearpygui.dearpygui as dpg
from robloxmemoryapi import RobloxGameClient

# Change these if you want to
CLICK_THRESHOLD_MIN = 0.70
CLICK_THRESHOLD_MAX = 0.745
RESET_THRESHOLD     = 0.76
AUTOCLICK_DELAY     = 0.1
IDLE_SLEEP          = 0.001
pyautogui.PAUSE = 0

def run_loader():
    os.system("cls" if os.name == "nt" else "clear")

    C  = Fore.CYAN
    W  = Fore.WHITE + Style.BRIGHT
    DW = Fore.WHITE + Style.DIM
    G  = Fore.GREEN + Style.BRIGHT
    R  = Fore.RED   + Style.BRIGHT
    Y  = Fore.YELLOW
    RS = Style.RESET_ALL

    border = C + "  ║" + RS
    TOP    = C + "  ╔══════════════════════════════════════════╗" + RS
    MID    = C + "  ╠══════════════════════════════════════════╣" + RS
    BOT    = C + "  ╚══════════════════════════════════════════╝" + RS
    BLANK  = border + " " * 42 + C + "║" + RS

    print(TOP)
    print(BLANK)
    title_raw  = "  AutoNanami  "
    title_pad  = (42 - len(title_raw)) // 2
    print(border + " " * title_pad + W + title_raw + RS + " " * (42 - title_pad - len(title_raw)) + C + "║" + RS)
    sub_raw = f"[{version}]"
    sub_pad = (42 - len(sub_raw)) // 2
    print(border + " " * sub_pad + DW + sub_raw + RS + " " * (42 - sub_pad - len(sub_raw)) + C + "║" + RS)
    print(BLANK)
    print(MID)
    print(BLANK)

    def step(label):
        txt = f"  >  {label}..."
        sys.stdout.write(border + Y + txt + RS + " " * (42 - len(txt)) + C + "║" + RS + "\r")
        sys.stdout.flush()

    def done(label, ok=True):
        badge   = (G + " OK " + RS) if ok else (R + " ERR " + RS)
        visible = f"  [ OK ]  {label}" if ok else f"  [ ERR ]  {label}"
        pad     = 42 - len(visible)
        print(border + f"  [" + badge + f"]  {label}" + " " * max(0, pad) + C + "║" + RS)

    step("Locating Roblox process")
    time.sleep(0.15)
    try:
        RobloxGameClient(allow_write=False).close()
        done("Roblox process detected")
    except Exception:
        done("Roblox is not running", ok=False)
        print(BLANK)
        print(BOT)
        time.sleep(2)
        sys.exit()

    step("Attaching memory hooks")
    time.sleep(0.25)
    done("Memory interface ready")

    step("Loading UI renderer")
    time.sleep(0.15)
    done("UI context initialized")

    print(BLANK)
    print(BOT)
    print()

    launch_msg = "  Launching"
    for ch in launch_msg:
        sys.stdout.write(C + ch + RS)
        sys.stdout.flush()
        time.sleep(0.01)
    for _ in range(3):
        sys.stdout.write(C + "." + RS)
        sys.stdout.flush()
        time.sleep(0.01)
    print()

    time.sleep(0.05)
    os.system("cls" if os.name == "nt" else "clear")

def hide_console():
    if platform.system() == "Windows":
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)


class NanamiBot:
    def __init__(self):
        if platform.system() != "Windows":
            raise RuntimeError("Windows support required")

        self.client = RobloxGameClient(allow_write=False)
        if self.client.failed:
            raise RuntimeError("API Hook failure")

        self.game      = self.client.DataModel
        self.character = None
        self.live_folder   = None
        self.target_cutter = None
        self.target_name   = "None"
        self.current_scale = 0.0

        self.nanamiaim   = False
        self.ratio_counter = 0
        self.zone_buff   = False

        self.phase   = "Init"
        self.status  = "Idle"

        self.enabled         = True
        self.hit_probability = 100

        self.game.bind_to_refresh(self.on_refresh, invoke_if_ready=True)

    def clear_target(self):
        self.target_cutter = None
        self.target_name   = "None"
        self.current_scale = 0.0

    def full_reset(self):
        self.clear_target()
        self.nanamiaim    = False
        self.ratio_counter = 0
        self.zone_buff    = False

    def on_refresh(self, datamodel):
        if self.game.is_lua_app():
            self.phase = "Home Screen"
            self.full_reset()
        else:
            self.phase = "In-Game"

    def update_cache_loop(self):
        while True:
            if self.game.is_lua_app():
                time.sleep(1.0)
                continue

            local_player = self.game.Players.LocalPlayer
            if not local_player:
                time.sleep(0.2)
                continue

            self.character   = local_player.Character
            self.live_folder = self.game.Workspace.FindFirstChild("Live")

            if self.character:
                a = self.character.GetAttribute("NANAMIAIM")
                r = self.character.GetAttribute("RatioCounter")
                z = self.character.GetAttribute("NanamiZoneBuff")

                self.nanamiaim    = a.value if a else False
                self.ratio_counter = r.value if r else 0
                self.zone_buff    = z.value if z else False
                self.phase = "Ready"
            else:
                self.phase = "Locating Character"

            time.sleep(0.2)

    def find_cutter(self):
        if not self.live_folder:
            return None

        for entity in self.live_folder.GetChildren():
            if self.character and entity.Name == self.character.Name:
                continue
            hrp    = entity.FindFirstChild("HumanoidRootPart")
            if not hrp:    continue
            gui    = hrp.FindFirstChild("NanamiCutGUI")
            if not gui:    continue
            bar    = gui.FindFirstChild("MainBar")
            if not bar:    continue
            cutter = bar.FindFirstChild("Cutter")
            if cutter:
                self.target_name = entity.Name
                return cutter
        return None

    def logic_loop(self):
        while True:
            if not self.enabled:
                self.status = "Disabled"
                self.clear_target()
                time.sleep(0.1)
                continue

            if not self.nanamiaim or not self.character:
                self.status = "Waiting"
                self.clear_target()
                time.sleep(IDLE_SLEEP)
                continue

            if not self.target_cutter:
                self.status = "Scanning"
                self.target_cutter = self.find_cutter()
                if not self.target_cutter:
                    self.clear_target()
                time.sleep(IDLE_SLEEP)
                continue

            try:
                scale = self.target_cutter.Position.X.Scale
                self.current_scale = scale

                if scale >= RESET_THRESHOLD:
                    self.status = "Reset"
                    self.clear_target()
                    continue

                if CLICK_THRESHOLD_MIN <= scale <= CLICK_THRESHOLD_MAX:
                    if random.uniform(0.0, 100.0) <= self.hit_probability:
                        self.status = "HIT"
                        pyautogui.click()
                    else:
                        self.status = "MISSED"
                    time.sleep(AUTOCLICK_DELAY)
                    self.clear_target()
                else:
                    self.status = "Tracking"

            except Exception:
                self.status = "Lost Target"
                self.clear_target()

            time.sleep(IDLE_SLEEP)

run_loader()
bot = NanamiBot()
threading.Thread(target=bot.update_cache_loop, daemon=True).start()
threading.Thread(target=bot.logic_loop, daemon=True).start()

dpg.create_context()

def get_font_paths():
    primary = [
        "C:/Windows/Fonts/JetBrainsMonoNerdFont-Regular.ttf",
        "C:/Windows/Fonts/JetBrainsMonoNF-Regular.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    bold = [
        "C:/Windows/Fonts/JetBrainsMonoNerdFont-Bold.ttf",
        "C:/Windows/Fonts/JetBrainsMonoNF-Bold.ttf",
        "C:/Windows/Fonts/consolab.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
    ]
    font_reg = next((f for f in primary if os.path.exists(f)), "C:/Windows/Fonts/segoeui.ttf")
    font_bld = next((f for f in bold   if os.path.exists(f)), "C:/Windows/Fonts/segoeuib.ttf")
    return font_reg, font_bld


reg_font_path, bold_font_path = get_font_paths()

with dpg.font_registry():
    main_font  = dpg.add_font(reg_font_path,  13)
    title_font = dpg.add_font(bold_font_path, 13)
    small_font = dpg.add_font(reg_font_path,  11)

dpg.bind_font(main_font)

with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg,          (14, 14, 18, 255))
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg,           (35, 35, 48, 255))
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg,           (20, 20, 26, 255))
        dpg.add_theme_color(dpg.mvThemeCol_Separator,         (45, 45, 60, 255))
        dpg.add_theme_color(dpg.mvThemeCol_Button,            (35, 35, 48, 255))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,     (55, 55, 75, 255))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,      (80, 80, 110, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab,        (80, 140, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive,  (110, 170, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg,           (30, 30, 42, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered,    (40, 40, 56, 255))
        dpg.add_theme_color(dpg.mvThemeCol_CheckMark,         (80, 140, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_Header,            (40, 40, 60, 255))
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered,     (55, 55, 80, 255))
        dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg,       (14, 14, 18, 255))
        dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab,     (50, 50, 70, 255))
        dpg.add_theme_color(dpg.mvThemeCol_Text,              (210, 210, 220, 255))
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding,     10, 10)
        dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing,        8,  5)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding,       6,  4)
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding,     0)
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding,      0)
        dpg.add_theme_style(dpg.mvStyleVar_GrabRounding,       0)
        dpg.add_theme_style(dpg.mvStyleVar_ChildRounding,      0)
        dpg.add_theme_style(dpg.mvStyleVar_PopupRounding,      0)
        dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding,  0)
        dpg.add_theme_color(dpg.mvThemeCol_Border,             (0, 0, 0, 0))
        dpg.add_theme_color(dpg.mvThemeCol_BorderShadow,       (0, 0, 0, 0))

dpg.bind_theme(global_theme)

VPORT_W   = 250
VPORT_H   = 385
TITLEBAR_H = 30

dpg.create_viewport(
    title="AutoNanami",
    width=VPORT_W,
    height=VPORT_H,
    always_on_top=True,
    decorated=False,
)

def app_close():
    bot.client.close()
    dpg.destroy_context()
    sys.exit()

def app_minimize():
    dpg.minimize_viewport()

def on_toggle_enable(sender, app_data):
    bot.enabled = app_data

def on_probability_change(sender, app_data):
    bot.hit_probability = app_data

def rescan():
    bot.target_cutter = None
    bot.character     = None
    bot.phase         = "Rescanning..."

with dpg.theme() as close_btn_theme:
    with dpg.theme_component(dpg.mvButton):
        dpg.add_theme_color(dpg.mvThemeCol_Button,        (70, 30, 30, 255))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (150, 40, 40, 255))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  (200, 50, 50, 255))

INNER_W = VPORT_W - 20

with dpg.window(
    tag="Primary",
    width=VPORT_W,
    height=VPORT_H,
    pos=(0, 0),
    no_title_bar=True,
    no_move=True,
    no_resize=True,
    no_scroll_with_mouse=True,
    no_scrollbar=True,
):
    with dpg.child_window(tag="titlebar", height=TITLEBAR_H, border=False, no_scrollbar=True):
        with dpg.theme() as title_bar_theme:
            with dpg.theme_component(dpg.mvChildWindow):
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing,   0, 0)
        dpg.bind_item_theme(dpg.last_item(), title_bar_theme)

        lbl = dpg.add_text("AutoNanami", pos=(8, 6), color=[200, 200, 215])
        dpg.bind_item_font(lbl, title_font)

        btn_min = dpg.add_button(label="_", width=20, height=20, callback=app_minimize, pos=(184, 5))
        dpg.bind_item_font(btn_min, small_font)

        btn_cls = dpg.add_button(label="X", width=20, height=20, callback=app_close, pos=(206, 5))
        dpg.bind_item_theme(btn_cls, close_btn_theme)
        # dpg.bind_item_font(btn_cls, small_font)

    dpg.add_spacer(height=2)
    dpg.add_separator()
    dpg.add_spacer(height=2)

    dpg.add_checkbox(label="Enable Automation", default_value=True, callback=on_toggle_enable)
    dpg.add_spacer(height=2)
    dpg.add_text("HIT CHANCE", color=[160, 160, 180])
    dpg.bind_item_font(dpg.last_item(), small_font)
    dpg.add_slider_int(
        label="##hc",
        default_value=100,
        min_value=0,
        max_value=100,
        clamped=True,
        format="%d%%",
        callback=on_probability_change,
        width=INNER_W,
    )

    dpg.add_spacer(height=2)
    dpg.add_separator()
    dpg.add_spacer(height=1)

    with dpg.table(
        header_row=False,
        borders_innerH=False, borders_outerH=False,
        borders_innerV=False, borders_outerV=False,
        resizable=False, no_pad_outerX=True,
    ):
        dpg.add_table_column(width_fixed=True, init_width_or_weight=82)
        dpg.add_table_column()

        def stat_row(label, tag, default="—", default_color=None):
            with dpg.table_row():
                lbl_item = dpg.add_text(label.upper(), color=[140, 140, 170])
                dpg.bind_item_font(lbl_item, small_font)
                kw = {"color": default_color} if default_color else {}
                dpg.add_text(default, tag=tag, **kw)

        stat_row("Phase",  "ui_phase",  "Init",   [160, 160, 180])
        stat_row("Status", "ui_status", "Idle",   [160, 160, 180])
        stat_row("Target", "ui_target", "None",   [160, 160, 180])
        stat_row("Scale",  "ui_scale",  "0.0000", [160, 160, 180])

    dpg.add_separator()
    dpg.add_spacer(height=1)

    with dpg.table(
        header_row=False,
        borders_innerH=False, borders_outerH=False,
        borders_innerV=False, borders_outerV=False,
        resizable=False, no_pad_outerX=True,
    ):
        dpg.add_table_column(width_fixed=True, init_width_or_weight=82)
        dpg.add_table_column()

        with dpg.table_row():
            rc_lbl = dpg.add_text("RATIOS", color=[140, 140, 170])
            dpg.bind_item_font(rc_lbl, small_font)
            dpg.add_text("0", tag="ui_ratio", color=[210, 210, 220])

        with dpg.table_row():
            bf_lbl = dpg.add_text("BLACK FLASH", color=[140, 140, 170])
            dpg.bind_item_font(bf_lbl, small_font)
            dpg.add_text("Inactive", tag="ui_zone", color=[200, 60, 60])

    dpg.add_separator()
    dpg.add_spacer(height=2)

    dpg.add_button(label="Rescan", width=INNER_W, height=26, callback=rescan)

drag_allowed = False
drag_pressed = False
 
def mouse_down_handler(sender, data):
    global drag_allowed, drag_pressed
    if not drag_pressed:
        drag_allowed = dpg.is_item_hovered("titlebar")
        drag_pressed = True
 
def mouse_release_handler(sender, data):
    global drag_allowed, drag_pressed
    drag_allowed = False
    drag_pressed = False
 
def drag_handler(sender, data):
    if not drag_allowed:
        return
    vx, vy = dpg.get_viewport_pos()
    dpg.set_viewport_pos([vx + data[1], vy + data[2]])
 
with dpg.handler_registry():
    dpg.add_mouse_down_handler(button=0,    callback=mouse_down_handler)
    dpg.add_mouse_release_handler(button=0, callback=mouse_release_handler)
    dpg.add_mouse_drag_handler(button=0,    callback=drag_handler)

dpg.setup_dearpygui()
dpg.show_viewport()
hide_console()

STATUS_COLORS = {
    "Disabled":    [100, 100, 100],
    "Waiting":     [200, 160,  40],
    "Scanning":    [200, 200,  40],
    "Tracking":    [ 60, 160, 255],
    "HIT":         [ 60, 220,  90],
    "MISSED":      [220,  70,  70],
    "Lost Target": [220,  70,  70],
    "Reset":       [160, 160, 160],
}

PHASE_COLORS = {
    "Ready":             [ 60, 210,  90],
    "Locating Character":[200, 160,  40],
    "Home Screen":       [120, 120, 120],
    "Rescanning...":     [200, 200,  40],
    "In-Game":           [ 60, 160, 255],
    "Init":              [120, 120, 120],
}

while dpg.is_dearpygui_running():
    dpg.set_value("ui_target", bot.target_name)
    dpg.set_value("ui_scale",  f"{bot.current_scale:.4f}")
    dpg.set_value("ui_ratio",  str(int(bot.ratio_counter)))
    dpg.set_value("ui_phase",  bot.phase)

    st = bot.status
    dpg.set_value("ui_status", st)
    dpg.configure_item("ui_status", color=STATUS_COLORS.get(st, [200, 200, 210]))
    dpg.configure_item("ui_phase",  color=PHASE_COLORS.get(bot.phase, [200, 200, 210]))

    if bot.zone_buff:
        dpg.set_value("ui_zone", "Active")
        dpg.configure_item("ui_zone", color=[60, 210, 90])
    else:
        needed = max(0, 7 - int(bot.ratio_counter))
        dpg.set_value("ui_zone", f"Inactive  ({needed} left)")
        dpg.configure_item("ui_zone", color=[200, 60, 60])

    dpg.render_dearpygui_frame()

bot.client.close()
dpg.destroy_context()