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
2. Ajusta el WPM con el slider (100–1000; default 400)
3. **Play** para empezar

Formatos soportados:

- Portapapeles → Markdown
- `.txt` → párrafos separados por línea en blanco
- `.md` / `.markdown` → headings, listas, citas, tablas, etc.

El WPM se guarda entre sesiones en `~/.config/speedreader/`.

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

En pantalla completa se ocultan controles y progreso; la palabra se muestra más grande.

## Desarrollo

```bash
uv run pytest
```

## Estructura

```
src/speedreader/
  engine.py      # Motor RSVP, WPM, pausas por puntuación
  orp.py         # Punto de reconocimiento óptimo
  settings.py    # Preferencias persistentes
  importers/     # Plain text, Markdown, clipboard, archivos
  ui/            # Ventana PySide6
```
