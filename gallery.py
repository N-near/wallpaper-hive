

#!/usr/bin/env python3

import os
import math
import random
import subprocess

import gi
import cairo

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf


# ---------------- CONFIGURACIÓN ----------------

WALLPAPER_DIR = os.path.expanduser("~/Pictures/Wallpapers")

THUMB_WIDTH = 160
THUMB_HEIGHT = round(THUMB_WIDTH * math.sqrt(3) / 2)

GAP = 4
PURPLE = (0.77, 0.65, 0.91)
MARGIN = 24

# Distancia entre hexágonos vecinos.
CELL_X = THUMB_WIDTH * 0.75 + GAP
CELL_Y = THUMB_HEIGHT + GAP


# ---------------- CARGA DE IMÁGENES ----------------

def load_wallpapers():
    """Busca imágenes compatibles en la carpeta de fondos."""

    extensions = (".jpg", ".jpeg", ".png", ".webp")

    if not os.path.isdir(WALLPAPER_DIR):
        return []

    return sorted(
        os.path.join(WALLPAPER_DIR, filename)
        for filename in os.listdir(WALLPAPER_DIR)
        if filename.lower().endswith(extensions)
        and os.path.isfile(os.path.join(WALLPAPER_DIR, filename))
    )


def load_thumbnail(path):
    """Carga una miniatura conservando su proporción."""

    try:
        _, width, height = GdkPixbuf.Pixbuf.get_file_info(path)

        if not width or not height:
            raise ValueError("No se pudo obtener el tamaño")

        ratio = THUMB_WIDTH / THUMB_HEIGHT
        image_ratio = width / height

        if image_ratio > ratio:
            scaled_width = math.ceil(THUMB_HEIGHT * image_ratio)
            scaled_height = THUMB_HEIGHT
        else:
            scaled_width = THUMB_WIDTH
            scaled_height = math.ceil(THUMB_WIDTH / image_ratio)

        return GdkPixbuf.Pixbuf.new_from_file_at_scale(
            path,
            scaled_width,
            scaled_height,
            True
        )

    except Exception as error:
        print(f"No se pudo cargar {path}: {error}")
        return None


# ---------------- DISTRIBUCIÓN DEL PANAL ----------------

def generate_positions(count):
    """Genera grupos irregulares de hexágonos conectados."""

    rng = random.Random(42)

    if count == 0:
        return [], 300

    cells = {(0, 1), (0, 2)}

    directions = [
        (0, 1),
        (0, -1),
        (1, 0),
        (1, -1),
        (-1, 0),
        (-1, 1)
    ]

    # Generamos algunas posiciones adicionales
    # para poder dejar pequeños espacios naturales.
    target = count + max(2, count // 5)

    frontier = set()

    def add_neighbors(cell):
        q, r = cell

        for dq, dr in directions:
            neighbor = (q + dq, r + dr)

            if (
                neighbor not in cells
                and 0 <= neighbor[1] <= 3
                and neighbor[0] >= 0
            ):
                frontier.add(neighbor)

    for cell in cells:
        add_neighbors(cell)

    while len(cells) < target and frontier:

        cell = rng.choice(tuple(frontier))
        frontier.remove(cell)

        cells.add(cell)
        add_neighbors(cell)

    # Dejamos algunos huecos para una silueta irregular.
    cells = list(cells)
    rng.shuffle(cells)
    cells = cells[:count]

    # Convertimos las coordenadas hexagonales a píxeles.
    positions = []

    for q, r in cells:

        x = q * CELL_X

        y = (
            r + (q % 2) * 0.5
        ) * CELL_Y

        positions.append((x, y))

    # Normalizamos la posición vertical.
    min_y = min(y for x, y in positions)

    positions = [
        (x + MARGIN, y - min_y + MARGIN)
        for x, y in positions
    ]

    # Ordenamos de izquierda a derecha.
    positions.sort(key=lambda point: (point[0], point[1]))

    canvas_width = (
        max(x for x, y in positions)
        + THUMB_WIDTH
        + MARGIN
    )

    canvas_height = (
        max(y for x, y in positions)
        + THUMB_HEIGHT
        + MARGIN
    )

    return positions, canvas_height


# ---------------- VENTANA PRINCIPAL ----------------

class WallpaperGallery(Gtk.Window):

    def __init__(self):
        super().__init__(title="Wallpapers")

        self.set_default_size(900, 650)
        self.set_border_width(16)
        self.set_decorated(False)

        self.wallpapers = []
        self.selected_wallpaper = None

        self.prepare_transparency()
        self.apply_styles()

        self.connect("draw", self.on_draw_background)

        self.create_interface()
        self.populate_gallery()

    # ---------------- TRANSPARENCIA ----------------

    def prepare_transparency(self):
        """Solicita una superficie con canal alfa."""

        screen = Gdk.Screen.get_default()
        visual = screen.get_rgba_visual()

        if visual is not None:
            self.set_visual(visual)

        self.set_app_paintable(True)

    def on_draw_background(self, widget, cr):
        """Limpia el fondo de la ventana."""

        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()

        cr.set_operator(cairo.OPERATOR_OVER)

        return False

    def apply_styles(self):
        """Mantiene transparentes los contenedores GTK."""

        css = Gtk.CssProvider()

        css.load_from_data("""
            window,
            box,
            scrolledwindow,
            viewport,
            drawingarea {
                background-color: transparent;
                background-image: none;
                border: none;
                box-shadow: none;
            }
        """.encode())

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # ---------------- INTERFAZ ----------------

    def create_interface(self):
        """Crea el lienzo con desplazamiento horizontal."""

        main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL
        )

        self.add(main_box)

        screen = Gdk.Screen.get_default()

        self.canvas_width = max(
            600,
            screen.get_width() - 32
        )

        self.canvas = Gtk.DrawingArea()

        self.canvas.set_size_request(
            self.canvas_width,
            screen.get_height() - 32
        )

        self.canvas.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
        )

        self.canvas.connect(
            "draw",
            self.on_draw_gallery
        )

        self.canvas.connect(
            "button-press-event",
            self.on_click
        )

        self.scroll = Gtk.ScrolledWindow()

        # Desplazamiento horizontal, sin barra vertical.
        self.scroll.set_policy(
            Gtk.PolicyType.AUTOMATIC,
            Gtk.PolicyType.NEVER
        )

        self.scroll.set_shadow_type(Gtk.ShadowType.NONE)
        self.scroll.add(self.canvas)

        main_box.pack_start(
            self.scroll,
            True,
            True,
            0
        )

    # ---------------- MINIATURAS ----------------

    def populate_gallery(self):
        """Carga los fondos y calcula sus posiciones."""

        for path in load_wallpapers():

            pixbuf = load_thumbnail(path)

            if pixbuf is not None:
                self.wallpapers.append({
                    "path": path,
                    "pixbuf": pixbuf,
                    "x": 0,
                    "y": 0
                })

        positions, canvas_height = generate_positions(
            len(self.wallpapers)
        )

        for wallpaper, position in zip(
            self.wallpapers,
            positions
        ):

            wallpaper["x"] = position[0]
            wallpaper["y"] = position[1]

        canvas_width = max(
            self.canvas_width,
            max(
                (wallpaper["x"] + THUMB_WIDTH + MARGIN
                 for wallpaper in self.wallpapers),
                default=self.canvas_width
            )
        )

        self.canvas.set_size_request(
            canvas_width,
            max(canvas_height, 300)
        )

        self.canvas.queue_draw()

    # ---------------- DIBUJO ----------------

    def draw_hexagon(self, cr, x, y):
        """Dibuja un hexágono regular horizontal."""

        offset = THUMB_WIDTH / 4

        cr.move_to(x + offset, y)
        cr.line_to(x + THUMB_WIDTH - offset, y)
        cr.line_to(x + THUMB_WIDTH, y + THUMB_HEIGHT / 2)
        cr.line_to(x + THUMB_WIDTH - offset, y + THUMB_HEIGHT)
        cr.line_to(x + offset, y + THUMB_HEIGHT)
        cr.line_to(x, y + THUMB_HEIGHT / 2)

        cr.close_path()

    def on_draw_gallery(self, widget, cr):
        """Dibuja todos los fondos."""

        for wallpaper in self.wallpapers:

            x = wallpaper["x"]
            y = wallpaper["y"]
            pixbuf = wallpaper["pixbuf"]

            image_x = x + (
                THUMB_WIDTH - pixbuf.get_width()
            ) / 2

            image_y = y + (
                THUMB_HEIGHT - pixbuf.get_height()
            ) / 2

            cr.save()

            self.draw_hexagon(cr, x, y)
            cr.clip()

            Gdk.cairo_set_source_pixbuf(
                cr,
                pixbuf,
                image_x,
                image_y
            )

            cr.paint()
            cr.restore()

            if wallpaper["path"] == self.selected_wallpaper:

                self.draw_hexagon(cr, x, y)

                cr.set_source_rgba(*PURPLE, 1.0)
                cr.set_line_width(3)
                cr.stroke()

        return False

    # ---------------- DETECCIÓN DE CLICS ----------------

    def point_inside_hexagon(self, px, py, x, y):
        """Comprueba si el clic está dentro de un hexágono."""

        points = [
            (x + THUMB_WIDTH / 4, y),
            (x + THUMB_WIDTH * 3 / 4, y),
            (x + THUMB_WIDTH, y + THUMB_HEIGHT / 2),
            (x + THUMB_WIDTH * 3 / 4, y + THUMB_HEIGHT),
            (x + THUMB_WIDTH / 4, y + THUMB_HEIGHT),
            (x, y + THUMB_HEIGHT / 2)
        ]

        inside = False
        j = len(points) - 1

        for i in range(len(points)):

            xi, yi = points[i]
            xj, yj = points[j]

            if (yi > py) != (yj > py):

                intersection = (
                    (xj - xi) * (py - yi) / (yj - yi) + xi
                )

                if px < intersection:
                    inside = not inside

            j = i

        return inside

    def on_click(self, widget, event):
        """Identifica el hexágono seleccionado."""

        for wallpaper in self.wallpapers:

            if self.point_inside_hexagon(
                event.x,
                event.y,
                wallpaper["x"],
                wallpaper["y"]
            ):

                self.select_wallpaper(wallpaper["path"])
                return True

        return False

    # ---------------- APLICAR FONDO ----------------

    def select_wallpaper(self, path):
        """Aplica el wallpaper seleccionado."""

        try:
            subprocess.run(
                ["pkill", "-x", "swaybg"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            subprocess.Popen([
                "swaybg",
                "-i", path,
                "-m", "fill"
            ])

            self.selected_wallpaper = path
            self.destroy()

        except OSError as error:
            print(f"No se pudo aplicar el fondo: {error}")


# ---------------- INICIO ----------------

def main():
    window = WallpaperGallery()

    window.connect("destroy", Gtk.main_quit)
    window.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
