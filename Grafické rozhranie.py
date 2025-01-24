import sys
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from scipy.interpolate import Rbf
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QComboBox, QHBoxLayout
from PyQt5.QtCore import Qt


class SensorVisualizer:
    def __init__(self):
        self.room_width = 3.5  # X
        self.room_length = 3.5  # Y
        self.room_height = 3.0  # Z
        self.generate_sensor_coordinates()

    def read_data_batch(self, filename, batch_number, batch_size):
        try:
            data = pd.read_csv(filename)

            start_index = (batch_number - 1) * batch_size
            end_index = batch_number * batch_size

            data_batch = data.iloc[start_index:end_index]

            if data_batch.empty:
                return None, None

            first_timestamp = data_batch.iloc[0]['timestamp']

            return data_batch, first_timestamp
        except Exception as e:
            return None, None

    def list_branches(self, filename, batch_size):

        try:

            data = pd.read_csv(filename)


            total_rows = len(data)
            num_batches = (total_rows + batch_size - 1) // batch_size

            for batch_number in range(1, num_batches + 1):
                start_index = (batch_number - 1) * batch_size
                end_index = min(batch_number * batch_size, total_rows)

                first_timestamp = data.iloc[start_index]['timestamp']
        except Exception as e:
            return None, None


    def generate_sensor_coordinates(self):

        offset = 0

        wall_sensors = [

            (0.0, self.room_length / 4, self.room_height / 4),
            (0.0, 3 * self.room_length / 4, self.room_height / 4),
            (0.0, self.room_length / 2, 3 * self.room_height / 4),


            (self.room_width, self.room_length / 4, self.room_height / 4),
            (self.room_width, 3 * self.room_length / 4, self.room_height / 4),
            (self.room_width, self.room_length / 2, 3 * self.room_height / 4),


            (self.room_width / 4, 0.0, self.room_height / 4),
            (3 * self.room_width / 4, 0.0, self.room_height / 4),
            (self.room_width / 2, 0.0, 3 * self.room_height / 4),


            (self.room_width / 4, self.room_length, self.room_height / 4),
            (3 * self.room_width / 4, self.room_length, self.room_height / 4),
            (self.room_width / 2, self.room_length, 3 * self.room_height / 4)
        ]

        floor_sensors = [
            (self.room_width / 4, self.room_length / 4, 0.0),
            (3 * self.room_width / 4, self.room_length / 4, 0.0),
            (self.room_width / 4, 3 * self.room_length / 4, 0.0),
            (3 * self.room_width / 4, 3 * self.room_length / 4, 0.0)
        ]

        ceiling_sensors = [
            (self.room_width / 4, self.room_length / 4, self.room_height),
            (3 * self.room_width / 4, self.room_length / 4, self.room_height),
            (self.room_width / 4, 3 * self.room_length / 4, self.room_height),
            (3 * self.room_width / 4, 3 * self.room_length / 4, self.room_height)
        ]


        all_sensors = wall_sensors + floor_sensors + ceiling_sensors


        self.x_coords = np.array([x for x, y, z in all_sensors])
        self.y_coords = np.array([y for x, y, z in all_sensors])
        self.z_coords = np.array([z for x, y, z in all_sensors])


    def generate_virtual_points(self, points, values):
        virtual_points = []
        virtual_values = []
        extension = 0.3
        edges = [

            (0, 0, self.room_height / 2),
            (0, self.room_length, self.room_height / 2),
            (self.room_width, 0, self.room_height / 2),
            (self.room_width, self.room_length, self.room_height / 2),

            (self.room_width / 2, 0, 0),
            (self.room_width / 2, self.room_length, 0),
            (0, self.room_length / 2, 0),
            (self.room_width, self.room_length / 2, 0),

            (self.room_width / 2, 0, self.room_height),
            (self.room_width / 2, self.room_length, self.room_height),
            (0, self.room_length / 2, self.room_height),
            (self.room_width, self.room_length / 2, self.room_height)
        ]

        for edge in edges:
            virtual_points.append(edge)
            distances = np.sqrt(
                (points[:, 0] - edge[0]) ** 2 +
                (points[:, 1] - edge[1]) ** 2 +
                (points[:, 2] - edge[2]) ** 2
            )
            nearest_indices = np.argsort(distances)[:2]
            virtual_values.append(np.mean(values[nearest_indices]))

        for i, (x, y, z) in enumerate(points):
            if x <= 0.1:
                virtual_points.append([-extension, y, z])
                virtual_values.append(values[i])
            elif x >= self.room_width - 0.1:
                virtual_points.append([self.room_width + extension, y, z])
                virtual_values.append(values[i])

            if y <= 0.1:
                virtual_points.append([x, -extension, z])
                virtual_values.append(values[i])
            elif y >= self.room_length - 0.1:
                virtual_points.append([x, self.room_length + extension, z])
                virtual_values.append(values[i])

            if z <= 0.1:  # Пол
                virtual_points.append([x, y, -extension])
                virtual_values.append(values[i])
            elif z >= self.room_height - 0.1:
                virtual_points.append([x, y, self.room_height + extension])
                virtual_values.append(values[i])

        corners_ext = [
            (-extension, -extension, -extension),
            (-extension, -extension, self.room_height + extension),
            (-extension, self.room_length + extension, -extension),
            (-extension, self.room_length + extension, self.room_height + extension),
            (self.room_width + extension, -extension, -extension),
            (self.room_width + extension, -extension, self.room_height + extension),
            (self.room_width + extension, self.room_length + extension, -extension),
            (self.room_width + extension, self.room_length + extension, self.room_height + extension)
        ]

        for corner in corners_ext:
            virtual_points.append(corner)
            distances = np.sqrt(
                (points[:, 0] - corner[0]) ** 2 +
                (points[:, 1] - corner[1]) ** 2 +
                (points[:, 2] - corner[2]) ** 2
            )
            nearest_idx = np.argmin(distances)
            virtual_values.append(values[nearest_idx])

        return (np.vstack([points, virtual_points]),
                np.hstack([values, virtual_values]))

    def smooth_interpolation(self, points, values, grid_x, grid_y, grid_z):
        rbf = Rbf(points[:, 0], points[:, 1], points[:, 2], values,
                  function='quintic',
                  epsilon=0.8,
                  smooth=0.05)

        return rbf(grid_x.flatten(),
                   grid_y.flatten(),
                   grid_z.flatten()).reshape(grid_x.shape)

    def plot_3d(self, data, mode='temperature'):
        if data is None:
            return

        plot_config = {
            'temperature': {
                'column': 'temperature',
                'title': '3D Temperature Distribution',
                'colorscale': 'jet',
                'vmin': -40,
                'vmax': 150
            },
            'humidity': {
                'column': 'humidity',
                'title': '3D Humidity Distribution',
                'colorscale': 'Blues',
                'vmin': 0,
                'vmax': 100
            }
        }

        config = plot_config.get(mode)
        if not config or config['column'] not in data.columns:
            return

        values = data[config['column']].values

        grid_points = 60
        xi = np.linspace(-0.3, self.room_width + 0.3, grid_points)
        yi = np.linspace(-0.3, self.room_length + 0.3, grid_points)
        zi = np.linspace(-0.3, self.room_height + 0.3, grid_points)
        grid_x, grid_y, grid_z = np.meshgrid(xi, yi, zi, indexing='ij')

        points = np.column_stack((self.x_coords, self.y_coords, self.z_coords))
        ext_points, ext_values = self.generate_virtual_points(points, values)

        grid_values = self.smooth_interpolation(ext_points, ext_values,
                                                grid_x, grid_y, grid_z)

        mask = ((grid_x >= -0.01) & (grid_x <= self.room_width + 0.01) &
                (grid_y >= -0.01) & (grid_y <= self.room_length + 0.01) &
                (grid_z >= -0.01) & (grid_z <= self.room_height + 0.01))
        grid_values[~mask] = np.nan

        fig = go.Figure()

        fig.add_trace(go.Volume(
            x=grid_x.flatten(),
            y=grid_y.flatten(),
            z=grid_z.flatten(),
            value=grid_values.flatten(),
            isomin=config['vmin'],
            isomax=config['vmax'],
            opacity=0.15,
            surface_count=35,
            colorscale=config['colorscale'],
            caps=dict(x_show=False, y_show=False, z_show=False),
            reversescale=(mode == 'humidity'),
            colorbar=dict(
                title=f"{mode.capitalize()} Scale",
                titleside="right",
                x=1.15
            )
        ))

        hover_text = [
            f"Sensor {i + 1}<br>" +
            f"Position: ({x:.1f}, {y:.1f}, {z:.1f})<br>" +
            f"Temperature: {data['temperature'].iloc[i]:.1f}°C<br>" +
            f"Humidity: {data['humidity'].iloc[i]:.1f}%"
            for i, (x, y, z) in enumerate(zip(self.x_coords, self.y_coords, self.z_coords))
        ]

        fig.add_trace(go.Scatter3d(
            x=self.x_coords,
            y=self.y_coords,
            z=self.z_coords,
            mode='markers+text',
            marker=dict(
                size=5,
                color='black',
                symbol='circle',
                line=dict(color='white', width=1)
            ),
            text=[f"{i + 1}" for i in range(len(self.x_coords))],
            textposition="top center",
            textfont=dict(size=8),
            hovertext=hover_text,
            hoverinfo='text',
            name='Sensors'
        ))

        walls = [

            dict(x=[0, 0, 0, 0], y=[0, 3.5, 3.5, 0], z=[0, 0, 3, 3]),
            dict(x=[3.5, 3.5, 3.5, 3.5], y=[0, 3.5, 3.5, 0], z=[0, 0, 3, 3]),
            dict(x=[0, 3.5, 3.5, 0], y=[0, 0, 0, 0], z=[0, 0, 3, 3]),
            dict(x=[0, 3.5, 3.5, 0], y=[3.5, 3.5, 3.5, 3.5], z=[0, 0, 3, 3])
        ]

        for wall in walls:
            fig.add_trace(go.Mesh3d(
                x=wall['x'],
                y=wall['y'],
                z=wall['z'],
                opacity=0.1,
                color='lightgray',
                hoverinfo='skip',
                showscale=False
            ))

        fig.update_layout(
            title=dict(
                text=config['title'],
                x=0.5,
                y=0.95,
                xanchor='center',
                yanchor='top'
            ),
            scene=dict(
                xaxis_title='Width (m)',
                yaxis_title='Length (m)',
                zaxis_title='Height (m)',
                camera=dict(
                    eye=dict(x=1.8, y=1.8, z=1.5)
                ),
                aspectmode='data'
            ),
            showlegend=False
        )

        fig.show()


class SensorVisualizerApp(QMainWindow):
    def __init__(self, visualizer):
        super().__init__()
        self.visualizer = visualizer
        self.filename = None

        self.setWindowTitle("Sensor Visualizer")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        header_label = QLabel("Vizualizácia údajov zo senzorov")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        self.file_label = QLabel("Súbor nie je vybraný.")
        layout.addWidget(self.file_label)

        buttons_layout = QHBoxLayout()

        file_button = QPushButton("Výber súboru")
        file_button.setMinimumWidth(150)
        file_button.clicked.connect(self.select_file)
        buttons_layout.addWidget(file_button)

        visualize_button = QPushButton("Spustenie vizualizácie")
        visualize_button.setMinimumWidth(150)
        visualize_button.clicked.connect(self.visualize_data)
        buttons_layout.addWidget(visualize_button)

        layout.addLayout(buttons_layout)

        self.batch_combobox = QComboBox()
        layout.addWidget(self.batch_combobox)

        self.mode_combobox = QComboBox()
        self.mode_combobox.addItems(["temperature", "humidity"])
        layout.addWidget(self.mode_combobox)

        central_widget.setLayout(layout)

    def select_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("CSV Files (*.csv)")

        if file_dialog.exec_():
            self.filename = file_dialog.selectedFiles()[0]
            self.file_label.setText(f"Vybraný súbor: {self.filename}")
            self.update_batch_options()

    def update_batch_options(self):
        if not self.filename:
            return

        try:
            self.visualizer.list_branches(self.filename, 20)
            num_batches = len(pd.read_csv(self.filename)) // 20

            self.batch_combobox.clear()

            for batch_number in range(1, num_batches + 1):
                _, first_timestamp = self.visualizer.read_data_batch(self.filename, batch_number, 20)
                self.batch_combobox.addItem(f"Blok {batch_number}: {first_timestamp}")

        except Exception as e:
            print(f"Chyba pri aktualizácii blokov: {e}")

    def visualize_data(self):
        selected_item = self.batch_combobox.currentText()
        batch_number = int(selected_item.split(':')[0].split()[-1])
        timestamp = selected_item.split(': ')[-1]

        data, first_timestamp = self.visualizer.read_data_batch(self.filename, batch_number, 20)
        if data is None:
            print("Chyba pri načítaní údajov.")
            return

        mode = self.mode_combobox.currentText()
        self.visualizer.plot_3d(data, mode)


def main():
    visualizer = SensorVisualizer()

    app = QApplication(sys.argv)
    main_window = SensorVisualizerApp(visualizer)
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
