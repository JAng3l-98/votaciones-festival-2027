# Cómo trabajar en este repositorio

Guía para que cualquier integrante del equipo pueda aportar sin dañar el trabajo de los demás.

## 1. Preparar tu computador (una sola vez)

1. Crea una cuenta en https://github.com y envíale tu usuario a Juan Angel para que te invite como colaborador.
2. Acepta la invitación que llega a tu correo.
3. Instala **Git**:
   - **macOS:** abre Terminal y escribe `git --version`. Si no está instalado, el sistema ofrece instalar las herramientas de línea de comandos: acepta.
   - **Windows:** descarga el instalador desde https://git-scm.com y deja las opciones por defecto.
4. Instala **Visual Studio Code** desde https://code.visualstudio.com.
5. Configura tu nombre y correo en Git (en Terminal o en Git Bash):

   ```bash
   git config --global user.name "Tu Nombre Completo"
   git config --global user.email "el-correo-de-tu-cuenta-de-github"
   git config --global init.defaultBranch main
   ```

## 2. Descargar el proyecto (clonar)

1. En VS Code abre la paleta de comandos (`Cmd + Shift + P` en Mac, `Ctrl + Shift + P` en Windows).
2. Escribe **Git: Clone** y pega la dirección del repositorio:
   `https://github.com/JAng3l-98/votaciones-festival-2027.git`
3. Elige una carpeta (por ejemplo `Documentos/Proyectos`) y abre el proyecto cuando VS Code lo pregunte.
4. Instala las extensiones que VS Code recomienda en la esquina inferior derecha.

## 3. Trabajar en una tarea

Nunca trabajes directamente sobre `main`. Cada tarea va en su propia rama.

1. Antes de empezar, trae los últimos cambios: en la barra inferior de VS Code haz clic en el ícono de sincronizar, o en la terminal:

   ```bash
   git checkout main
   git pull
   ```

2. Crea una rama con tu nombre y la tarea:

   ```bash
   git checkout -b liana/capturas-benchmarking
   ```

3. Haz tus cambios y guarda.
4. En VS Code, abre **Control de código fuente** (`Ctrl + Shift + G`), escribe un mensaje claro y pulsa **Confirmar** (Commit). Ejemplos de mensajes:
   - `Agrega capturas del benchmarking`
   - `Corrige el formulario de registro (UI-02)`
5. Pulsa **Publicar rama** (Publish Branch) para subirla a GitHub.

## 4. Pedir que se integre tu trabajo (Pull Request)

1. En GitHub, en la página del repositorio, aparece el aviso **Compare & pull request**: haz clic.
2. Explica en pocas líneas qué cambiaste y qué pantallas o secciones toca.
3. Juan Angel revisa y, si todo está bien, lo une a `main` (**Merge**).
4. GitHub Pages actualiza el prototipo publicado en uno o dos minutos.

## 5. Reglas del equipo

- Una rama por tarea; ramas cortas y con nombre claro.
- Mensajes de commit en español, en presente: "Agrega…", "Corrige…", "Actualiza…".
- Respeta los códigos UI-xx, CU-xx, RF-xx y RN-xx del documento.
- Los colores y fuentes solo se cambian en `docs/assets/css/estilos.css` (bloque `:root`).
- Si algo se rompe, avisa en el grupo antes de intentar arreglarlo sobre `main`.
