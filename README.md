# Bandurria Hero

Bandurria Hero es un juego serio interactivo basado en visión por computador y seguimiento de manos en tiempo real mediante MediaPipe, OpenCV y Pygame. Permite interpretar canciones tradicionales españolas sobre un diapasón virtual de bandurria sin necesidad de hardware externo, empleando únicamente una cámara web estándar.

---

## Enfoque Clínico y Rehabilitación Motora

El diseño de Bandurria Hero está orientado a la rehabilitación y a la mejora de la coordinación de las manos y los dedos, aportando los siguientes beneficios terapéuticos:

- **Motricidad fina y disociación digital:** Exige posicionar con precisión las yemas de los dedos sobre trastes y cuerdas específicos, además de controlar la apertura de la mano en las notas al aire
- **Coordinación ojo-mano y tiempo de reacción:** El indicador visual de progreso que se contrae al ritmo de cada figura musical entrena la sincronización visomotora.
- **Adaptabilidad y accesibilidad:** El diapasón puede escalarse (de 60 a 120% del tamaño original) y desplazarse libremente en la pantalla antes y durante la partida para adaptarse a cada usuario
- **Progresión gradual:** El selector de velocidad ralentiza la ejecución manteniendo el tono original, facilitando el aprendizaje progresivo
- **Adherencia al tratamiento:** El sistema de récords y rankings según la velocidad ayuda a motivar a los pacientes independientemente de la dificultad que sea cómoda para ellos

---

## Instalación y Requisitos

1. **Prerrequisito:** Tener instalado Conda ([descargar Miniconda aquí](https://www.anaconda.com/docs/getting-started/miniconda/install)).
2. Clonar o descomprimir el repositorio y situarse en la carpeta del proyecto.
3. Crear y activar un entorno virtual:
   ```bash
   conda create -n bandurria_hero python=3.12 -y
   conda activate bandurria_hero
   ```
4. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
5. Descargar el modelo de detección de manos (si no está presente en `models/`):
   ```bash
   python download_models.py
   ```
6. Ejecutar la aplicación:
   ```bash
   python app.py
   ```

---

## Controles

| Tecla | Acción |
| :--- | :--- |
| `1, 2, 3` | Seleccionar canción y comenzar partida |
| `Z / X` | Disminuir / aumentar velocidad de reproducción (0.25x – 1.0x) |
| `+ / -` | Aumentar / reducir el tamaño del diapasón (60% – 120%) |
| `W A S D` | Mover la posición del diapasón en pantalla |
| `R` | Restablecer tamaño (100%) y posición original del diapasón |
| `ESC` | Salir de la aplicación |

### Durante la partida y pantalla final

- **Ajuste en tiempo real:** Las teclas `+/-` `W A S D` y `R` siguen activas durante la canción.
- **Cuerda al aire:** Cuando aparece el indicador amarillo con un 0 mantén la mano visible sin apoyar los dedos sobre esa cuerda en el diapasón.
- **Silencios:** Se indican en pantalla para pausar la pulsación sin penalizar la precisión.
- **Ranking Arcade:** Al terminar la canción introduce tus 3 iniciales y pulsa enter para guardar tu marca en el top 3 de esa canción y velocidad, y vuelve a pulsar enter para regresar al menú

---

## Estructura del Proyecto

- `app.py`: Bucle principal, gestión de cámara, menú, partida, fin de juego etc e inputs de teclado.
- `hand_tracker.py`: Detección de landmarks de la mano con MediaPipe y lógica de acierto en traste o cuerda al aire.
- `song.py`: Carga de partituras CSV, sincronización temporal con el audio y estiramiento de tempo.
- `ui.py`: Renderizado del menú, diapasón escalable, figuras musicales vectoriales, landmarks y tabla de puntuaciones.
- `ranking.py`: Lectura y persistencia del Top 3 por canción y velocidad en `ranking.json`.
- `config.py`: Rutas, parámetros de detección, dimensiones base y paleta de colores.
- `download_models.py`: Script de descarga automática del modelo `hand_landmarker.task`.