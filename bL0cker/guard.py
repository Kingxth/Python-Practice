import time
import random
import threading
import os
import subprocess
import platform
import tkinter as tk
from tkinter import messagebox, simpledialog
from calculos import generar_operacion

CONFIG_FILE = "config_objetivo.txt"

COLOR_BG = "#1e1e2e"
COLOR_CARD = "#252538"
COLOR_TEXTO = "#cdd6f4"
COLOR_ACENTO = "#89b4fa"
COLOR_ROJO = "#f38ba8"
COLOR_VERDE = "#a6e3a1"
COLOR_MUTED = "#6c7086"

class MathGuardianApp:
    def __init__(self, root, target_process):
        self.root = root
        self.root.title("Guardián Académico - Sistema de Bloqueo")
        self.root.geometry("520x460+400+300")
        self.root.config(bg=COLOR_BG)
        self.root.protocol("WM_DELETE_WINDOW", self.prevenir_cierre)
        
        self.target_process_name = target_process.lower().strip()
        self.max_lives = 3
        self.current_lives = self.max_lives
        self.total_exercises_target = 10 # cantidad de ejercicios
        self.exercises_completed = 0
        

        # tiempos :D 
        self.exam_time_limit_seconds = 1800  # 30 minutos de limite
        self.penalty_duration_seconds = 7200 # 2 horas de castigo
        self.exam_start_timestamp = 0
        self.block_expiration_timestamp = 0
        
        self.current_correct_answer = None
        self.is_exam_active = False
        self.is_system_blocked = False

        # Inicia interfaz
        self.crear_interfaz()
        
        # Iniciar hilo de vigilancia 
        self.monitoring_thread = threading.Thread(target=self.loop_vigilancia_sistema, daemon=True)
        self.monitoring_thread.start()

    def crear_interfaz(self):
        # Marco superior
        self.frame_estado = tk.Frame(self.root, bg=COLOR_BG, padx=20, pady=15)
        self.frame_estado.pack(fill=tk.X)
        
        self.label_vidas = tk.Label(self.frame_estado, text=f"Vidas: {self.current_lives} / {self.max_lives}", font=("Segoe UI", 11, "bold"), fg=COLOR_ROJO, bg=COLOR_BG)
        self.label_vidas.pack(side=tk.LEFT)
        
        self.label_tiempo_examen = tk.Label(self.frame_estado, text="Tiempo: 30:00", font=("Segoe UI", 11), fg=COLOR_ACENTO, bg=COLOR_BG)
        self.label_tiempo_examen.pack(side=tk.RIGHT)

        # Marco Central
        self.frame_card = tk.Frame(self.root, bg=COLOR_CARD, padx=20, pady=20)
        self.frame_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        self.label_instruccion = tk.Label(self.frame_card, text=f"Monitoreando: {self.target_process_name}", font=("Segoe UI", 11, "bold"), fg=COLOR_ACENTO, bg=COLOR_CARD)
        self.label_instruccion.pack(pady=5)

        self.label_operacion = tk.Label(self.frame_card, text="Sistema en espera...", font=("Segoe UI", 22, "bold"), fg=COLOR_TEXTO, bg=COLOR_CARD)
        self.label_operacion.pack(pady=20)

        self.entry_respuesta = tk.Entry(self.frame_card, font=("Segoe UI", 16), justify="center", bg="#313244", fg=COLOR_TEXTO, insertbackground="white", relief=tk.FLAT)
        self.entry_respuesta.pack(pady=10, ipady=5, fill=tk.X)
        self.entry_respuesta.bind("<Return>", self.verificar_respuesta_usuario)
        self.entry_respuesta.config(state=tk.DISABLED)

        self.btn_enviar = tk.Button(self.frame_card, text="Enviar Respuesta", font=("Segoe UI", 11, "bold"), bg=COLOR_ACENTO, fg="#11111b", activebackground="#b4befe", relief=tk.FLAT, cursor="hand2", command=self.verificar_respuesta_usuario)
        self.btn_enviar.pack(pady=10, fill=tk.X, ipady=3)
        self.btn_enviar.config(state=tk.DISABLED)

        # Boton de pruebas manuales sutil
        self.btn_prueba_manual = tk.Button(self.root, text="[Modo Prueba Manual]", font=("Segoe UI", 9), bg=COLOR_BG, fg=COLOR_MUTED, activebackground=COLOR_BG, activeforeground=COLOR_TEXTO, relief=tk.FLAT, command=self.iniciar_examen)
        self.btn_prueba_manual.pack(pady=2)

        # Marco inferior: Feedback
        self.label_feedback = tk.Label(self.root, text="", font=("Segoe UI", 10), fg=COLOR_MUTED, bg=COLOR_BG, pady=10)
        self.label_feedback.pack(fill=tk.X)

    def iniciar_examen(self):
        if self.is_exam_active:
            return
        
        print("> ¡Examen activado por deteccion de app")
        self.is_exam_active = True
        self.current_lives = self.max_lives
        self.exercises_completed = 0
        self.exam_start_timestamp = time.time()
        
        self.entry_respuesta.config(state=tk.NORMAL)
        self.btn_enviar.config(state=tk.NORMAL)
        self.actualizar_interfaz_vidas()
        self.siguiente_ejercicio()
        self.actualizar_cronometro_examen()
        
        # Forzar ventana al frente
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)

    def siguiente_ejercicio(self):
        if self.exercises_completed >= self.total_exercises_target:
            self.aprobar_examen()
            return

        tipos_disponibles = ['suma', 'resta', 'multiplicacion', 'division', 'potencias', 'raices']
        dificultades_disponibles = ['facil', 'medio', 'dificil']
        
        tipo_seleccionado = random.choice(tipos_disponibles)
        dificultad_seleccionada = random.choice(dificultades_disponibles)
        
        pregunta, self.current_correct_answer = generar_operacion(tipo_seleccionado, dificultad_seleccionada)
        
        progreso_actual = self.exercises_completed + 1
        self.label_instruccion.config(text=f"Ejercicio {progreso_actual} de {self.total_exercises_target}")
        self.label_operacion.config(text=pregunta)
        self.entry_respuesta.delete(0, tk.END)
        self.entry_respuesta.focus()

    def verificar_respuesta_usuario(self, event=None):
        if not self.is_exam_active:
            return

        respuesta_texto = self.entry_respuesta.get().strip()
        try:
            respuesta_usuario = float(respuesta_texto)
            if abs(respuesta_usuario - float(self.current_correct_answer)) < 1e-5:
                self.exercises_completed += 1
                self.label_feedback.config(text="¡Respuesta correcta!", fg=COLOR_VERDE)
                self.siguiente_ejercicio()
            else:
                raise ValueError
        except ValueError:
            self.current_lives -= 1
            self.actualizar_interfaz_vidas()
            self.label_feedback.config(text=f"Incorrecto. Era: {self.current_correct_answer}", fg=COLOR_ROJO)
            
            if self.current_lives <= 0:
                self.fallar_examen()
            else:
                self.siguiente_ejercicio()

    def actualizar_interfaz_vidas(self):
        self.label_vidas.config(text=f"Vidas: {self.current_lives} / {self.max_lives}")

    def actualizar_cronometro_examen(self):
        if not self.is_exam_active:
            return

        tiempo_transcurrido = time.time() - self.exam_start_timestamp
        tiempo_restante = int(self.exam_time_limit_seconds - tiempo_transcurrido)

        if tiempo_restante <= 0:
            self.fallar_examen()
            return

        minutos = tiempo_restante // 60
        segundos = tiempo_restante % 60
        self.label_tiempo_examen.config(text=f"Tiempo: {minutos:02d}:{segundos:02d}")
        
        self.root.after(1000, self.actualizar_cronometro_examen)

    def aprobar_examen(self):
        self.is_exam_active = False
        self.entry_respuesta.config(state=tk.DISABLED)
        self.btn_enviar.config(state=tk.DISABLED)
        self.label_instruccion.config(text="PRACTICA HECHA")
        self.label_operacion.config(text="¡Acceso concedido!")
        self.label_feedback.config(text="Well done, u can continue", fg=COLOR_VERDE)
        messagebox.showinfo("Aprobado", "Has completado los ejercicios con exitozamenth3.")

    def fallar_examen(self):
        self.is_exam_active = False
        self.is_system_blocked = True
        self.block_expiration_timestamp = time.time() + self.penalty_duration_seconds
        
        self.entry_respuesta.config(state=tk.DISABLED)
        self.btn_enviar.config(state=tk.DISABLED)
        
        self.matar_proceso_objetivo()
        self.ejecutar_pantalla_bloqueo()

    def ejecutar_pantalla_bloqueo(self):
        tiempo_actual = time.time()
        if tiempo_actual < self.block_expiration_timestamp:
            tiempo_bloqueo_restante = int(self.block_expiration_timestamp - tiempo_actual)
            horas = tiempo_bloqueo_restante // 3600
            minutos = (tiempo_bloqueo_restante % 3600) // 60
            segundos = tiempo_bloqueo_restante % 60
            
            self.label_instruccion.config(text="ACCESO BLOQUEADO")
            self.label_operacion.config(text=f"Castigo Activo")
            self.label_tiempo_examen.config(text=f"Bloqueo: {horas:02d}:{minutos:02d}:{segundos:02d}")
            self.label_feedback.config(text="No puedes abrir la app hasta que termine el tiempo.", fg=COLOR_ROJO)
            
            self.root.after(1000, self.ejecutar_pantalla_bloqueo)
        else:
            self.is_system_blocked = False
            self.label_instruccion.config(text=f"Monitoreando: {self.target_process_name}")
            self.label_operacion.config(text="Sistema listo.")
            self.label_tiempo_examen.config(text="Tiempo: --:--")
            self.label_feedback.config(text="El bloqueo ha finalizado.", fg=COLOR_ACENTO)

    def loop_vigilancia_sistema(self):
        while True:
            if self.verificar_si_proceso_esta_activo():
                self.matar_proceso_objetivo()
                
                if not self.is_system_blocked and not self.is_exam_active:
                    self.root.after(0, self.iniciar_examen)
            time.sleep(1)

    def verificar_si_proceso_esta_activo(self):
        sistema = platform.system()
        try:
            if sistema == "Linux" or sistema == "Darwin":
                resultado = subprocess.run(['pgrep', '-f', self.target_process_name], capture_output=True, text=True)
                pids = resultado.stdout.strip().split('\n')
                for pid in pids:
                    if pid.isdigit():
                        if int(pid) == os.getpid():
                            continue
                        return True
            elif sistema == "Windows":
                resultado = subprocess.run(['tasklist', '/fi', f'imagename eq *{self.target_process_name}*'], capture_output=True, text=True)
                if self.target_process_name.lower() in resultado.stdout.lower():
                    if "python" not in resultado.stdout.lower():
                        return True
        except Exception:
            pass
        return False

    def matar_proceso_objetivo(self):
        sistema = platform.system()
        try:
            if sistema == "Linux" or sistema == "Darwin":
                mi_pid = os.getpid()
                resultado = subprocess.run(['pgrep', '-f', self.target_process_name], capture_output=True, text=True)
                for pid in resultado.stdout.strip().split('\n'):
                    if pid.isdigit() and int(pid) != mi_pid:
                        os.kill(int(pid), 9)
            elif sistema == "Windows":
                subprocess.run(['taskkill', '/f', '/im', f'*{self.target_process_name}*'], capture_output=True)
        except Exception:
            pass

    def prevenir_cierre(self):
        if self.is_exam_active:
            messagebox.showwarning("WARRRRRNING", " YOU CANT CLOSE BL0CKER CUZ U ARE IN MIDDLE OF SOMETHING")
        else:
            self.root.destroy()

def obtener_proceso_a_bloquear():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            proceso_guardado = f.read().strip()
            if proceso_guardado:
                return proceso_guardado

    root_temp = tk.Tk()
    root_temp.withdraw()
    proceso_ingresado = simpledialog.askstring(
        "Config de BL0CKER", 
        "Ingresa el nombre del proceso a bloquear\n(ejemplo: steam, minecraft, firefox, discord):"
    )
    root_temp.destroy()

    if not proceso_ingresado:
        proceso_ingresado = "steam"

    with open(CONFIG_FILE, "w") as f:
        f.write(proceso_ingresado.strip())

    return proceso_ingresado.strip()

if __name__ == "__main__":
    proceso_elegido = obtener_proceso_a_bloquear()
    print(f"Revisando app seleccionada: {proceso_elegido}")
    
    root = tk.Tk()
    app = MathGuardianApp(root, proceso_elegido)
    root.mainloop()