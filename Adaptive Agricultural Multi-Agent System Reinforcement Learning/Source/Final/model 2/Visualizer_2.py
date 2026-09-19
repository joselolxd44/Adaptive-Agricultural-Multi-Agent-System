import matplotlib.pyplot as plt
import numpy as np


class SimulationVisualizer:

    def __init__(self, states):

        self.states = states

        # --------------------------------------------------------
        # CONFIGURACIÓN DE LA FIGURA
        # --------------------------------------------------------

        plt.ion()

        self.fig = plt.figure(figsize=(14, 9))

        # Mapa
        self.ax = self.fig.add_axes(
            [0.05, 0.30, 0.65, 0.63]
        )

        # Gráfica de rewards
        self.reward_ax = self.fig.add_axes(
            [0.05, 0.06, 0.65, 0.18]
        )

        # Panel de información
        self.info_ax = self.fig.add_axes(
            [0.73, 0.08, 0.25, 0.85]
        )

        self.info_ax.axis("off")

        self.info_text = self.info_ax.text(
            0,
            1,
            "",
            verticalalignment="top",
            fontsize=10,
            family="monospace"
        )

    # ============================================================
    # DRAW
    # ============================================================

    def draw(
        self,
        civilization,
        turn,
        visits=None,
        rewards=None,
        current_actions=None
    ):

        # --------------------------------------------------------
        # 1. LIMPIAR MAPA
        # --------------------------------------------------------

        self.ax.clear()

        # Obtener límites reales de la grid
        xs = [x for x, y in self.states.keys()]
        ys = [y for x, y in self.states.keys()]

        min_x = min(xs)
        max_x = max(xs)

        min_y = min(ys)
        max_y = max(ys)

        width = max_x - min_x + 1
        height = max_y - min_y + 1

        # --------------------------------------------------------
        # 2. CREAR MAPA DEL TERRENO
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
            interpolation="nearest"
        )

        # --------------------------------------------------------
        # 3. MAPA DE VISITAS
        # --------------------------------------------------------

        if visits is not None:

            visit_map = np.zeros(
                (height, width)
            )

            for (x, y), count in visits.items():

                # Ignorar posiciones que no existen
                # en la grid
                if (x, y) not in self.states:
                    continue

                row = y - min_y
                col = x - min_x

                visit_map[row, col] = count

            self.ax.imshow(
                visit_map,
                cmap="Blues",
                alpha=0.30,
                origin="upper",
                interpolation="nearest"
            )

        # --------------------------------------------------------
        # 4. DIBUJAR COMUNIDADES
        # --------------------------------------------------------

        for com in civilization.communities:

            # La comunidad puede estar en una posición
            # que ya no sea válida
            if com.position not in self.states:
                continue

            x, y = com.position

            row = y - min_y
            col = x - min_x

            # Tamaño según población
            size = 40 + min(
                com.population,
                500
            ) * 0.4

            self.ax.scatter(
                col,
                row,
                s=size,
                edgecolors="black",
                linewidths=1.5,
                zorder=10
            )

            # ID de la comunidad
            self.ax.text(
                col,
                row,
                str(com.id),
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
                zorder=11
            )

        # --------------------------------------------------------
        # 5. CONFIGURACIÓN DEL MAPA
        # --------------------------------------------------------

        self.ax.set_title(
            f"Andean Agricultural Simulation — Turn {turn}"
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
        # 6. INFORMACIÓN DE LAS COMUNIDADES
        # --------------------------------------------------------

        info = ""

        info += f"TURN {turn}\n"
        info += "=" * 30
        info += "\n\n"

        for com in civilization.communities:

            info += f"COMMUNITY {com.id}\n"
            info += "-" * 25
            info += "\n"

            info += (
                f"Position  : {com.position}\n"
            )

            info += (
                f"Population: {com.population}\n"
            )

            info += (
                f"Calories  : {com.calories:.0f}\n"
            )

            info += (
                f"Tension   : {com.tension:.2f}\n"
            )

            info += (
                f"Seeds     : {len(com.seeds)}\n"
            )

            info += (
                f"Food      : {len(com.food)}\n"
            )

            # Información de la acción actual
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
        # 7. GRÁFICA DE REWARDS
        # --------------------------------------------------------

        self.reward_ax.clear()

        if rewards is not None and len(rewards) > 0:

            # Reward individual
            self.reward_ax.plot(
                rewards,
                alpha=0.25,
                linewidth=0.8
            )

            # ----------------------------------------------------
            # PROMEDIO MÓVIL
            # ----------------------------------------------------

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
        # 8. ACTUALIZAR FIGURA
        # --------------------------------------------------------

        self.fig.canvas.draw()

        self.fig.canvas.flush_events()

        plt.pause(0.001)