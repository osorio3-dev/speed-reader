# Speedreader

Estación personal de lectura rápida (RSVP) para texto plano y Markdown.

Muestra una palabra a la vez, con punto de reconocimiento óptimo (ORP) resaltado y pausas automáticas en la puntuación.

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recomendado) o `pip`
- Dependencias gráficas de Qt en Linux (X11):

```bash
sudo apt install libxcb-cursor0
```

Si la ventana no abre y ves un error de `xcb`, instala también:

```bash
sudo apt install \
  libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
  libxkbcommon-x11-0
```

## Instalación

```bash
cd /ruta/a/reader
uv sync
```

Con dependencias de desarrollo (tests):

```bash
uv sync --extra dev
```

## Uso

```bash
uv run -m speedreader
```

También:

```bash
uv run speedreader
```

### Flujo básico

1. **Open** (`Ctrl+O`) o **Paste** (`Ctrl+V`) para cargar texto
2. Ajusta el WPM con el slider (100–1500, saltos de 25; default 400)
3. **Play** para empezar

Formatos soportados:

- Portapapeles → Markdown
- `.txt` → párrafos separados por línea en blanco
- `.md` / `.markdown` → headings, listas, citas, tablas, etc.

El WPM y el tamaño de fuente se guardan entre sesiones en `~/.config/speedreader/`.

Al cerrar con un archivo abierto, la app guarda la ruta y la posición actual. La próxima vez que la abras, retoma donde lo dejaste. Si terminaste el texto, vuelve al inicio. El contenido pegado del portapapeles no se restaura.

La barra de progreso permite saltar a cualquier palabra (arrastrar o clic). Los headings, listas, citas y bloques de código se muestran más despacio que el texto normal.

## Acceso directo en el menú de aplicaciones

Desde la raíz del proyecto:

```bash
./scripts/install-desktop.sh
```

Esto instala `~/.local/share/applications/speedreader.desktop` y el icono en `~/.local/share/icons/`.

Para desinstalar:

```bash
rm ~/.local/share/applications/speedreader.desktop
rm ~/.local/share/icons/hicolor/256x256/apps/speedreader.png
```

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `Espacio` | Play / Pause |
| `Ctrl+O` | Abrir archivo |
| `Ctrl+V` | Pegar |
| `←` / `→` | Palabra anterior / siguiente |
| `R` | Reiniciar lectura |
| `F11` | Pantalla completa (modo foco) |
| `Esc` | Salir de pantalla completa |
| `?` | Mostrar atajos de teclado |

Con **TTS + Piper**: lectura por frases, RSVP sincronizado palabra a palabra, y `←`/`→` saltan frases.

Arrastra un archivo `.txt` o `.md` a la ventana para abrirlo.

En pantalla completa se ocultan controles y progreso; la palabra se muestra más grande.

## TTS offline (opcional)

Instala el extra de voz neural:

```bash
uv sync --extra tts
./scripts/download-voice.sh
```

Por defecto descarga `es_MX-ald-x_low` (~20 MB, voz latina ligera). Otras opciones:

```bash
./scripts/download-voice.sh es_MX-claude-high
./scripts/download-voice.sh --list
```

En la app, el desplegable junto a **TTS** permite elegir entre voces Piper instaladas o **Qt / eSpeak**.

Sin Piper, el botón **TTS** usa `QTextToSpeech` (eSpeak) en español si el sistema lo ofrece:

```bash
sudo apt install speech-dispatcher espeak-ng
```

Con **TTS** activo, la voz marca el ritmo. **RSVP** y **TTS** tienen sliders WPM independientes (100–1500, saltos de 25). Con **Piper** se lee frase a frase con RSVP sincronizado; con Qt/eSpeak, palabra a palabra.

Cada voz tiene dos sliders cuando TTS está activo:

- **TTS WPM**: 100–1500, default 400. Acelera el ritmo (todos los backends).
- **Pitch**: -50% a +50%, default 0%. Sube/baja el tono sin acelerar. Lo soportan Qt, Edge y Azure. Piper no soporta pitch — el slider se desactiva automáticamente.

Piper y Edge no soportan exactamente el mismo rango de pitch: Edge usa Hz (±50%), Azure usa % (±50%), Qt usa un factor [-1, 1]. El slider los normaliza visualmente.

Los bloques de código se omiten en TTS. El WPM controla la velocidad base.

## Voces TTS

Tres modos, en orden de calidad:

| Modo | Comando | Setup | Calidad ES | Coste |
|---|---|---|---|---|
| Piper (offline, default si instalaste `--extra piper`) | `uv sync --extra piper` | descargar voz con `./scripts/download-voice.sh es_MX-ald-x_low` | buena | $0 |
| Edge (online, sin key) | `uv sync --extra edge` | ninguno | excelente | $0 |
| Azure (online, con key) | `uv sync --extra azure` | clic "Voces TTS" → key | excelente + SSML | $0 hasta 500k chars/mes |

Para instalar todos los TTS a la vez (compatibilidad con instrucciones viejas):

```bash
uv sync --extra tts
```

Fallback automático: si un backend online falla, app vuelve a Piper o Qt sin ruido.

## Desarrollo

```bash
uv run pytest
```

## Estructura

```
src/speedreader/
  engine.py      # Motor RSVP, WPM, pausas por puntuación
  profiles.py    # Perfiles de ritmo visual y TTS
  orp.py         # Punto de reconocimiento óptimo
  settings.py    # Preferencias persistentes
  speech/        # TTS offline (Piper + Qt)
  importers/     # Plain text, Markdown, clipboard, archivos
  ui/            # Ventana PySide6
```
