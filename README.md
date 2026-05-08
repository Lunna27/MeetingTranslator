🎙️ Meeting Translator RTX
Meeting Translator RTX es una herramienta de transcripción y traducción bidireccional en tiempo real de alto rendimiento. Utiliza modelos de IA avanzados ejecutados localmente para garantizar total privacidad y una latencia mínima.

Desarrollado con una arquitectura de microservicios locales: un motor de procesamiento en Python (Cerebro) y una interfaz gráfica flotante en C# WPF (Rostro), comunicados mediante WebSockets.

🚀 Características Principales
Aceleración por Hardware: Optimizado para correr sobre núcleos Tensor Cores de NVIDIA (probado en RTX 5060 Ti).

Traducción Bidireccional Automática: Detecta si hablas en Inglés o Español y traduce al idioma opuesto al instante.

Filtro VAD (Voice Activity Detection): Inteligencia que ignora música, ruidos de fondo y silencios para evitar alucinaciones en la traducción.

Cero Puntos Ciegos: Sistema de grabación continua con hilos paralelos y traslape de audio para no perder ni una sola palabra.

Interfaz Flotante con Historial: Ventana minimalista "Always on Top" con scroll automático para consultar frases anteriores.

Privacidad Total: El audio nunca sale de tu computadora; todo el procesamiento es local.

🛠️ Requisitos del Sistema
GPU: NVIDIA RTX (Serie 30 o superior recomendada para float16).

CPU: Ryzen 7 5700X o equivalente.

RAM: 16GB mínimo (32GB recomendado).

SO: Windows 10/11.

Software: Python 3.11 y .NET 8.0 SDK.

📦 Instalación y Configuración
1. Motor de Inteligencia Artificial (Python)
Dentro de la carpeta raíz, configura tu entorno virtual:

Bash
python -m venv interprete_env
.\interprete_env\Scripts\activate
pip install -r requirements.txt
Nota Crítica: Para habilitar el soporte CUDA en Windows, debes copiar las librerías cublas64_12.dll y cudnn_ops64_9.dll (y asociadas) de tu carpeta de paquetes de Nvidia a la raíz del proyecto.

2. Interfaz de Usuario (C# WPF)
Abre la carpeta MeetingTranslator/ en Visual Studio 2022.

Restaura los paquetes NuGet.

Compila el proyecto en modo Release.

🎮 Cómo usarlo
Ejecuta el motor de Python: python interprete.py.

Lanza la aplicación C# desde Visual Studio o el ejecutable generado.

Reproduce cualquier audio (Teams, Zoom, YouTube) y los subtítulos aparecerán automáticamente en la ventana flotante.

🏗️ Estructura del Proyecto
/interprete.py: Lógica de captura de audio, VAD, Whisper y servidor WebSocket.

/MeetingTranslator/: Código fuente de la interfaz gráfica en .NET WPF.

/requirements.txt: Dependencias de Python necesarias.

✒️ Autor
Este proyecto fue conceptualizado, diseñado y programado por:

Emmanuel Luna - Software Developer 

📝 Licencia
Este proyecto es de uso personal y educativo.
