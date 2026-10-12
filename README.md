# Sistema Web de Votaciones – Festival de la Leyenda Vallenata 2027

Proyecto académico de la asignatura **Desarrollo Web** (Fundación Universitaria del Área Andina, Ingeniería de Sistemas).
Propuesta de una plataforma web configurable para gestionar las votaciones del público del Festival de la Leyenda Vallenata.

> Prototipo académico con datos de ejemplo. No es un sitio oficial del Festival ni de la Fundación.

**Prototipo publicado:** https://jang3l-98.github.io/votaciones-festival-2027/ · **Mapa de pantallas:** https://jang3l-98.github.io/votaciones-festival-2027/mapa.html

## Equipo

| Integrante | Rol en la Entrega 1 |
| --- | --- |
| Liana Victoria Gaitán Higuera | Contexto, benchmarking, problema, objetivos y alcance |
| Harold de Jesús Marimón Herrera | Actores, requerimientos, reglas de negocio y preguntas al cliente |
| John Edisson Gómez Cortés | Casos de uso, modelo conceptual y riesgos |
| Juan Angel Velásquez Gómez | Arquitectura, flujo principal y prototipo UX/UI |

## Estructura del repositorio

```
votaciones-festival-2027/
├── docs/                    ← Prototipo navegable (lo publica GitHub Pages)
│   ├── index.html           UI-01 Inicio
│   ├── registro.html        UI-02 Registro
│   ├── login.html           UI-03 Inicio de sesión
│   ├── categorias.html      UI-04 Categorías
│   ├── votaciones.html      UI-05 Votaciones disponibles
│   ├── votacion.html        UI-06 Detalle de la votación
│   ├── opciones.html        UI-07 Opciones disponibles
│   ├── confirmar.html       UI-08 Confirmación del voto
│   ├── voto-registrado.html UI-09 Voto registrado
│   ├── mapa.html            Índice de las 14 pantallas
│   ├── admin/               UI-10 a UI-14 (administración)
│   └── assets/
│       ├── css/estilos.css  Estilos propios: colores, tipografía, componentes
│       ├── css/bootstrap.min.css
│       ├── js/prototipo.js  Simula el flujo de voto y la cuenta regresiva
│       ├── js/bootstrap.bundle.min.js
│       └── fonts/           Tipografías Poppins y Raleway (licencia OFL), las mismas del sitio oficial
├── .vscode/                 Extensiones y ajustes compartidos del editor
├── CONTRIBUTING.md          Cómo trabajar en equipo con Git y GitHub
├── README.md
└── .gitignore               Archivos que Git no debe subir
```

El documento de la entrega (con diagramas y capturas) se entrega aparte; el repositorio guarda solo el código.

En las próximas entregas se agregará la aplicación Django (Python + MySQL) en su propia carpeta, sin mover el prototipo.

## Ver el prototipo en tu computador

1. Abre la carpeta del repositorio en Visual Studio Code.
2. Instala la extensión **Live Server** (VS Code la sugiere al abrir el proyecto).
3. Haz clic en **Go Live**, en la barra inferior. Se abre `http://127.0.0.1:5500` con el prototipo y se recarga solo cada vez que guardas.

## Convenciones del proyecto

- Cada pantalla muestra en la última línea del pie su código (**UI-01** a **UI-14**), su caso de uso (**CU-01** a **CU-09**) y el enlace al mapa del prototipo, para mantener la trazabilidad con el documento.
- El aviso negro de la parte superior indica en todas las pantallas que es un prototipo académico con datos de ejemplo.
- Las ilustraciones (instrumentos, Sierra Nevada, pollera, tarima) son dibujos propios en SVG. No se usan fotos, logos ni marcas del Festival.
- Los formularios del prototipo no guardan datos y tienen el autocompletado del navegador desactivado.
- Las reglas que la Fundación no ha confirmado llevan la etiqueta **Pendiente de validación**.
- Los colores y tipografías están centralizados en `docs/assets/css/estilos.css`, en el bloque `:root`.

## Tecnologías

HTML5 · CSS3 · Bootstrap 5.3 · JavaScript · (próximas entregas: Python, Django y MySQL)
