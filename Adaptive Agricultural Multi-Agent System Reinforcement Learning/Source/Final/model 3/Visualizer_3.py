import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np


class SimulationVisualizer:

    def __init__(self, states):

        self.states = states

        # --------------------------------------------------------
        # CONFIGURACIÓN DE LA FIGURA
        # --------------------------------------------------------

        plt.ion()

        self.fig = plt.figure(figsize=(15, 9))

        # Mapa
        self.ax = self.fig.add_axes(
            [0.04, 0.30, 0.66, 0.63]
        )

        # Gráfica de rewards
        self.reward_ax = self.fig.add_axes(
            [0.04, 0.06, 0.66, 0.18]
        )

        # Panel de información
        self.info_ax = self.fig.add_axes(
            [0.73, 0.05, 0.25, 0.88]
        )

        self.info_ax.axis("off")

        self.info_text = self.info_ax.text(
            0,
            1,
            "",
            verticalalignment="top",
            fontsize=9,
            family="monospace"
        )

        # --------------------------------------------------------
        # COLORES DE COLONIAS
        # --------------------------------------------------------

        self.colony_colors = {}

        self.color_palette = [
            "red",
            "blue",
            "green",
            "purple",
            "orange",
            "cyan",
            "magenta",
            "yellow",
            "brown",
            "pink",
            "lime",
            "navy",
            "gold",
            "teal",
            "coral",
            "indigo",
            "olive",
            "maroon",
            "turquoise",
            "violet"
        ]

    # ============================================================
    # COLOR DE COLONIA
    # ============================================================

    def get_colony_color(self, colony_id):

        if colony_id not in self.colony_colors:

            index = len(self.colony_colors)

            self.colony_colors[colony_id] = (
                self.color_palette[
                    index % len(self.color_palette)
                ]
            )

        return self.colony_colors[colony_id]

    # ============================================================
    # DRAW
    # ============================================================

    def draw(
        self,
        civilization,
        turn,
        visits=None,
        rewards=None,
        current_actions=None,
        colonies=None
    ):

        # --------------------------------------------------------
        # 1. LIMPIAR MAPA
        # --------------------------------------------------------

        self.ax.clear()

        # --------------------------------------------------------
        # 2. OBTENER LÍMITES
        # --------------------------------------------------------

        xs = [x for x, y in self.states.keys()]
        ys = [y for x, y in self.states.keys()]

        min_x = min(xs)
        max_x = max(xs)

        min_y = min(ys)
        max_y = max(ys)

        width = max_x - min_x + 1
        height = max_y - min_y + 1

        # --------------------------------------------------------
        # 3. TERRENO
        # --------------------------------------------------------

        terrain = np.full(
            (height, width),
            np.nan
        )

        for (x, y), cell in self.states.items():

            row = y - min_y
            col = x - min_x

            terrain[row, col] = cell["height"]

        self.ax.imshow(
            terrain,
            cmap="terrain",
            origin="upper",
            interpolation="nearest",
            zorder=0
        )

        # --------------------------------------------------------
        # 4. MAPA DE VISITAS
        # --------------------------------------------------------

        if visits is not None:

            visit_map = np.zeros(
                (height, width)
            )

            for (x, y), count in visits.items():

                if (x, y) not in self.states:
                    continue

                row = y - min_y
                col = x - min_x

                visit_map[row, col] = count

            self.ax.imshow(
                visit_map,
                cmap="Blues",
                alpha=0.18,
                origin="upper",
                interpolation="nearest",
                zorder=1
            )

        # --------------------------------------------------------
        # 5. TERRITORIOS DE COLONIAS
        # --------------------------------------------------------

        if colonies is not None:

            for colony in colonies:

                colony_id = colony.id

                base_color = self.get_colony_color(
                    colony_id
                )

                # ------------------------------------------------
                # TERRITORIO
                # ------------------------------------------------

                territory_map = np.full(
                    (height, width),
                    np.nan
                )

                for position in colony.states:

                    if position not in self.states:
                        continue

                    x, y = position

                    row = y - min_y
                    col = x - min_x

                    territory_map[row, col] = 1

                self.ax.imshow(
                    territory_map,
                    cmap=mcolors.ListedColormap(
                        [base_color]
                    ),
                    alpha=0.22,
                    origin="upper",
                    interpolation="nearest",
                    zorder=2
                )

                # ------------------------------------------------
                # FRONTERA DE LA COLONIA
                # ------------------------------------------------

                boundary_x = []
                boundary_y = []

                colony_states = set(
                    colony.states.keys()
                )

                for position in colony_states:

                    x, y = position

                    neighbours = [
                        (x + 1, y),
                        (x - 1, y),
                        (x, y + 1),
                        (x, y - 1)
                    ]

                    # Si toca una celda fuera del territorio,
                    # forma parte de la frontera.
                    if any(
                        neighbour not in colony_states
                        for neighbour in neighbours
                    ):

                        col = x - min_x
                        row = y - min_y

                        boundary_x.append(col)
                        boundary_y.append(row)

                if boundary_x:

                    self.ax.scatter(
                        boundary_x,
                        boundary_y,
                        s=10,
                        facecolors="none",
                        edgecolors=base_color,
                        linewidths=0.8,
                        alpha=0.8,
                        zorder=4
                    )

                # ------------------------------------------------
                # CENTRO DE COLONIA
                # ------------------------------------------------

                cx, cy = colony.central_point

                center_col = cx - min_x
                center_row = cy - min_y

                self.ax.scatter(
                    center_col,
                    center_row,
                    s=150,
                    marker="*",
                    facecolors=base_color,
                    edgecolors="black",
                    linewidths=1.5,
                    zorder=8
                )

                self.ax.text(
                    center_col,
                    center_row - 0.7,
                    f"C{colony_id}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                    color="black",
                    zorder=9
                )

        # --------------------------------------------------------
        # 6. COMUNIDADES
        # --------------------------------------------------------

        # Primero mostramos comunidades normales.
        # Los miembros de colonias reciben el color de su colonia.

        colony_members = {}

        if colonies is not None:

            for colony in colonies:

                colony_members[id(colony.haman)] = colony
                colony_members[id(colony.hurin)] = colony

        for com in civilization.communities:

            if com.position not in self.states:
                continue

            x, y = com.position

            row = y - min_y
            col = x - min_x

            size = 40 + min(
                com.population,
                500
            ) * 0.4

            # Comunidad normal
            face_color = "white"

            # Si pertenece a una colonia,
            # utiliza el color de la colonia.
            colony = colony_members.get(id(com))

            if colony is not None:

                face_color = self.get_colony_color(
                    colony.id
                )

            self.ax.scatter(
                col,
                row,
                s=size,
                facecolors=face_color,
                edgecolors="black",
                linewidths=1.5,
                zorder=10
            )

            self.ax.text(
                col,
                row,
                str(com.id),
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
                color="black",
                zorder=11
            )

        # --------------------------------------------------------
        # 7. DIBUJAR HANAN Y HURIN
        # --------------------------------------------------------

        if colonies is not None:

            for colony in colonies:

                base_color = self.get_colony_color(
                    colony.id
                )

                # Hanan
                haman = colony.haman

                if haman.position in self.states:

                    x, y = haman.position

                    row = y - min_y
                    col = x - min_x

                    size = 80 + min(
                        haman.population,
                        500
                    ) * 0.35

                    self.ax.scatter(
                        col,
                        row,
                        s=size,
                        marker="^",
                        facecolors=base_color,
                        edgecolors="black",
                        linewidths=2,
                        zorder=12
                    )

                    self.ax.text(
                        col,
                        row,
                        "H",
                        ha="center",
                        va="center",
                        fontsize=8,
                        fontweight="bold",
                        zorder=13
                    )

                # Hurin
                hurin = colony.hurin

                if hurin.position in self.states:

                    x, y = hurin.position

                    row = y - min_y
                    col = x - min_x

                    size = 80 + min(
                        hurin.population,
                        500
                    ) * 0.35

                    self.ax.scatter(
                        col,
                        row,
                        s=size,
                        marker="o",
                        facecolors=base_color,
                        edgecolors="black",
                        linewidths=2,
                        zorder=12
                    )

                    self.ax.text(
                        col,
                        row,
                        "R",
                        ha="center",
                        va="center",
                        fontsize=8,
                        fontweight="bold",
                        zorder=13
                    )

        # --------------------------------------------------------
        # 8. CONFIGURACIÓN DEL MAPA
        # --------------------------------------------------------

        self.ax.set_title(
            f"Andean Agricultural Simulation — "
            f"Model 3 — Turn {turn}"
        )

        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")

        self.ax.set_xlim(
            -0.5,
            width - 0.5
        )

        self.ax.set_ylim(
            height - 0.5,
            -0.5
        )

        self.ax.set_aspect("equal")

        # --------------------------------------------------------
        # 9. PANEL DE INFORMACIÓN
        # --------------------------------------------------------

        info = ""

        info += f"MODEL 3 — TURN {turn}\n"
        info += "=" * 32
        info += "\n\n"

        # --------------------------------------------------------
        # COMUNIDADES NORMALES
        # --------------------------------------------------------

        normal_count = 0

        if civilization.communities:

            for com in civilization.communities:

                if id(com) in colony_members:
                    continue

                normal_count += 1

        info += (
            f"COMMUNITIES : {normal_count}\n"
        )

        info += (
            f"COLONIES    : "
            f"{len(colonies) if colonies is not None else 0}\n"
        )

        info += "\n"

        # --------------------------------------------------------
        # INFORMACIÓN DE COLONIAS
        # --------------------------------------------------------

        if colonies is not None:

            for colony in colonies:

                color = self.get_colony_color(
                    colony.id
                )

                info += (
                    f"COLONY {colony.id}\n"
                )

                info += "-" * 28
                info += "\n"

                info += (
                    f"Center    : "
                    f"{colony.central_point}\n"
                )

                info += (
                    f"Territory : "
                    f"{len(colony.states)} cells\n"
                )

                info += (
                    f"Radius    : "
                    f"{getattr(colony, 'radius', '?')}\n"
                )

                info += (
                    f"Hanan     : "
                    f"{colony.haman.position}\n"
                )

                info += (
                    f"Hurin     : "
                    f"{colony.hurin.position}\n"
                )

                info += (
                    f"H population: "
                    f"{colony.haman.population}\n"
                )

                info += (
                    f"R population: "
                    f"{colony.hurin.population}\n"
                )

                info += "\n"

        # --------------------------------------------------------
        # COMUNIDADES NORMALES DETALLADAS
        # --------------------------------------------------------

        for com in civilization.communities:

            if id(com) in colony_members:
                continue

            info += (
                f"COMMUNITY {com.id}\n"
            )

            info += "-" * 28
            info += "\n"

            info += (
                f"Position  : "
                f"{com.position}\n"
            )

            info += (
                f"Population: "
                f"{com.population}\n"
            )

            info += (
                f"Calories  : "
                f"{com.calories:.0f}\n"
            )

            info += (
                f"Tension   : "
                f"{com.tension:.2f}\n"
            )

            info += (
                f"Seeds     : "
                f"{len(com.seeds)}\n"
            )

            info += (
                f"Food      : "
                f"{len(com.food)}\n"
            )

            if (
                current_actions is not None
                and com.id in current_actions
            ):

                data = current_actions[com.id]

                info += (
                    f"Action    : "
                    f"{data['action']}\n"
                )

                info += (
                    f"Reward    : "
                    f"{data['reward']:.2f}\n"
                )

            info += "\n"

        self.info_text.set_text(info)

        # --------------------------------------------------------
        # 10. REWARDS
        # --------------------------------------------------------

        self.reward_ax.clear()

        if rewards is not None and len(rewards) > 0:

            self.reward_ax.plot(
                rewards,
                alpha=0.25,
                linewidth=0.8
            )

            window = 50

            if len(rewards) >= window:

                moving_average = np.convolve(
                    rewards,
                    np.ones(window) / window,
                    mode="valid"
                )

                self.reward_ax.plot(
                    range(
                        window - 1,
                        len(rewards)
                    ),
                    moving_average,
                    linewidth=2
                )

        self.reward_ax.set_title(
            "Reward over time"
        )

        self.reward_ax.set_xlabel(
            "Action / Step"
        )

        self.reward_ax.set_ylabel(
            "Reward"
        )

        self.reward_ax.grid(
            alpha=0.2
        )

        # --------------------------------------------------------
        # 11. ACTUALIZAR
        # --------------------------------------------------------

        self.fig.canvas.draw()

        self.fig.canvas.flush_events()

        plt.pause(0.001)