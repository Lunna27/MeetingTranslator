import os
import asyncio
import websockets
import json
import pyaudiowpatch as pyaudio
import wave
import threading
import queue
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator

# --- CONFIGURACIÓN ---
MODELO_WHISPER = "medium" 
TIEMPO_GRABACION = 4   # Tamaño del bloque a procesar (4 segundos)
TIEMPO_TRASLAPE = 1    # Retenemos 1 segundo para evitar cortar palabras a la mitad
ARCHIVO_TEMP = "temp_audio.wav"

print("Cargando modelo de IA en la RTX 5060 Ti...")
modelo = WhisperModel(MODELO_WHISPER, device="cuda", compute_type="float16")
traductor_en_es = GoogleTranslator(source='en', target='es')
traductor_es_en = GoogleTranslator(source='es', target='en')
print("¡Modelo y traductores cargados exitosamente!")

# Esta cola comunicará nuestro micrófono (hilo 2) con nuestro traductor (hilo 1)
cola_audio = queue.Queue()

def hilo_grabador():
    """Este hilo corre en paralelo. Nunca se detiene, nunca deja de escuchar."""
    p = pyaudio.PyAudio()
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        
        if not default_speakers["isLoopbackDevice"]:
            for loopback in p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
                    
        CHUNK = 4096
        FORMAT = pyaudio.paInt16
        CHANNELS = default_speakers["maxInputChannels"]
        RATE = int(default_speakers["defaultSampleRate"])
        
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                        frames_per_buffer=CHUNK, input_device_index=default_speakers["index"])
        
        frames = []
        chunks_totales = int(RATE / CHUNK * TIEMPO_GRABACION)
        chunks_traslape = int(RATE / CHUNK * TIEMPO_TRASLAPE)
        
        print("🎙️ Grabación continua activada (Cero puntos ciegos)...")
        while True:
            data = stream.read(CHUNK)
            frames.append(data)
            
            # Cuando juntamos 4 segundos de audio...
            if len(frames) >= chunks_totales:
                # Enviamos una copia a traducir
                cola_audio.put((frames.copy(), CHANNELS, p.get_sample_size(FORMAT), RATE))
                
                # TRUCO MÁGICO: No vaciamos la memoria. Nos quedamos con el último segundo.
                # Esto asegura que ninguna palabra se corte entre dos bloques.
                frames = frames[-chunks_traslape:]
                
    except Exception as e:
        print(f"Error crítico en el micrófono: {e}")

async def procesar_y_enviar(websocket):
    print("¡Cliente C# conectado! Iniciando el motor de traducción...")
    
    # Encendemos el micrófono en un núcleo separado de tu procesador
    threading.Thread(target=hilo_grabador, daemon=True).start()
    
    texto_anterior = "" # Memoria a corto plazo para la IA
    
    while True:
        try:
            # Esperamos a que el micrófono nos pase un bloque de audio listo
            if cola_audio.empty():
                await asyncio.sleep(0.05)
                continue
                
            # Extraemos el audio de la cola
            frames, channels, sample_width, rate = cola_audio.get()
            
            # Guardamos el archivo para que Whisper lo lea
            wf = wave.open(ARCHIVO_TEMP, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            # Pasamos el audio + el filtro de silencios + el contexto anterior
            segments, info = modelo.transcribe(
                ARCHIVO_TEMP, 
                beam_size=5, 
                vad_filter=True, 
                vad_parameters=dict(min_silence_duration_ms=500),
                initial_prompt=texto_anterior # La IA recuerda la frase pasada
            )
            
            texto_original = "".join([segment.text for segment in segments]).strip()
            
            if texto_original:
                idioma_detectado = info.language 
                
                if idioma_detectado == "es":
                    print(f"🗣️ [ES]: {texto_original}")
                    texto_traducido = traductor_es_en.translate(texto_original)
                    mensaje = {"original": texto_traducido, "traduccion": texto_original}
                else:
                    print(f"🗣️ [EN]: {texto_original}")
                    texto_traducido = traductor_en_es.translate(texto_original)
                    mensaje = {"original": texto_original, "traduccion": texto_traducido}
                
                await websocket.send(json.dumps(mensaje))
                
                # Guardamos lo que acaba de decir para dárselo de contexto en el siguiente bloque
                texto_anterior = texto_original 
                
                await asyncio.sleep(0.1) # Respiro para el websocket
                
        except websockets.exceptions.ConnectionClosed:
            print("Cliente C# desconectado.")
            break
        except Exception as e:
            print(f"Error procesando: {e}")
            await asyncio.sleep(1)

async def main():
    async with websockets.serve(procesar_y_enviar, "127.0.0.1", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())