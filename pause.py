#!/usr/bin/env python3
"""
Script de pausas obrigatórias para descanso visual
Requer: tkinter, screeninfo, dbus-python
Instalar: 
    sudo apt install python3-tk python3-pip python3-dbus
    pip3 install screeninfo

Uso:
    python3 pausa_visual.py              # Modo normal (10 min trabalho, 30s pausa)
    python3 pausa_visual.py --20-20-20   # Regra 20-20-20 (20 min trabalho, 20s pausa)
    python3 pausa_visual.py --test       # Modo teste (5s trabalho, 5s pausa)
"""

import tkinter as tk
from tkinter import font
import time
import sys
import subprocess
import threading
from datetime import datetime
try:
    from screeninfo import get_monitors
except ImportError:
    print("ERRO: Instale o screeninfo com: pip3 install screeninfo")
    exit(1)

class EyeBreakTimer:
    def __init__(self, mode='normal'):
        if mode == 'test':
            self.work_duration = 5  # 5 segundos para teste
            self.break_duration = 5  # 5 segundos para teste
            print("\n🧪 MODO TESTE ATIVADO")
        elif mode == '20-20-20':
            self.work_duration = 20 * 60  # 20 minutos
            self.break_duration = 20  # 20 segundos
            print("\n👁️ REGRA 20-20-20 ATIVADA")
        else:
            self.work_duration = 10 * 60  # 10 minutos em segundos
            self.break_duration = 30  # 30 segundos
        self.running = True
        self.timer_reset = False
        self.last_unlock_time = time.time()
        
    def is_screen_locked(self):
        """Verifica se a tela está bloqueada (GNOME/Ubuntu)"""
        try:
            result = subprocess.run(
                ['gnome-screensaver-command', '-q'],
                capture_output=True,
                text=True,
                timeout=1
            )
            return 'inactive' not in result.stdout.lower()
        except:
            # Alternativa para sistemas mais novos
            try:
                result = subprocess.run(
                    ['loginctl', 'show-session', '$(loginctl show-user $(whoami) -p Display --value)', '-p', 'LockedHint'],
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=1
                )
                return 'yes' in result.stdout.lower()
            except:
                return False
    
    def monitor_screen_lock(self):
        """Monitora o estado de bloqueio da tela em background"""
        was_locked = False
        while self.running:
            is_locked = self.is_screen_locked()
            
            # Detecta quando a tela foi desbloqueada
            if was_locked and not is_locked:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔓 Tela desbloqueada - Timer resetado!")
                self.last_unlock_time = time.time()
                self.timer_reset = True
            
            was_locked = is_locked
            time.sleep(2)  # Verifica a cada 2 segundos
        
    def show_break_window(self):
        """Mostra janela de pausa discreta em todos os monitores"""
        windows = []
        
        # Cria uma janela para cada monitor
        monitors = get_monitors()
        
        for i, monitor in enumerate(monitors):
            root = tk.Tk()
            
            # Posiciona a janela no monitor específico
            root.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
            root.attributes('-topmost', True)
            root.overrideredirect(True)  # Remove bordas e botões
            
            # Fundo discreto (cinza escuro semi-transparente)
            root.configure(bg='#1a1a1a')
            root.attributes('-alpha', 0.92)  # Leve transparência
            
            # Desabilita fechamento
            root.protocol("WM_DELETE_WINDOW", lambda: None)
            
            # Frame central apenas no monitor principal (primeiro)
            if i == 0:
                frame = tk.Frame(root, bg='#1a1a1a')
                frame.place(relx=0.5, rely=0.5, anchor='center')
                
                # Ícone e texto discreto
                title_font = font.Font(family='Helvetica', size=18)
                title = tk.Label(
                    frame, 
                    text="Pausa para descanso visual", 
                    font=title_font,
                    bg='#1a1a1a',
                    fg='#cccccc'
                )
                title.pack(pady=15)
                
                # Timer pequeno e discreto
                timer_font = font.Font(family='Helvetica', size=32)
                timer_label = tk.Label(
                    frame,
                    text=str(self.break_duration),
                    font=timer_font,
                    bg='#1a1a1a',
                    fg='#888888'
                )
                timer_label.pack(pady=10)
                
                # Armazena referência do timer para atualizar
                self.timer_label = timer_label
            
            windows.append(root)
        
        # Atualiza o contador apenas na janela principal
        remaining = self.break_duration
        
        def update_timer():
            nonlocal remaining
            if remaining > 0:
                self.timer_label.config(text=str(remaining))
                remaining -= 1
                windows[0].after(1000, update_timer)
            else:
                for w in windows:
                    w.destroy()
        
        update_timer()
        windows[0].mainloop()
    
    def run(self):
        """Loop principal do programa"""
        print("=" * 60)
        print("Script de Pausas para Descanso Visual iniciado!")
        print(f"Trabalho: {self.work_duration // 60} minutos")
        print(f"Pausa: {self.break_duration} segundos")
        
        # Mostra quantos monitores foram detectados
        try:
            monitors = get_monitors()
            print(f"Monitores detectados: {len(monitors)}")
            for i, m in enumerate(monitors, 1):
                print(f"  Monitor {i}: {m.width}x{m.height} @ ({m.x}, {m.y})")
        except:
            pass
        
        print("=" * 60)
        print("⚠️  Timer será resetado automaticamente ao desbloquear a tela")
        print("\nPressione Ctrl+C para encerrar\n")
        
        # Inicia thread de monitoramento de bloqueio de tela
        monitor_thread = threading.Thread(target=self.monitor_screen_lock, daemon=True)
        monitor_thread.start()
        
        try:
            cycle = 1
            while self.running:
                # Período de trabalho com verificação de reset
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Ciclo {cycle}: Trabalhando...")
                
                elapsed = 0
                while elapsed < self.work_duration:
                    time.sleep(1)
                    elapsed += 1
                    
                    # Verifica se o timer deve ser resetado
                    if self.timer_reset:
                        self.timer_reset = False
                        elapsed = 0
                        cycle = 1
                
                # Pausa obrigatória
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏸️  PAUSA OBRIGATÓRIA!")
                self.show_break_window()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Pausa concluída\n")
                
                cycle += 1
                
        except KeyboardInterrupt:
            print("\n\nScript encerrado pelo usuário.")
            print("Cuide bem dos seus olhos! 👁️")

if __name__ == "__main__":
    # Determina o modo de operação
    mode = 'normal'
    if "--test" in sys.argv or "-t" in sys.argv:
        mode = 'test'
        print("\n" + "="*60)
        print("🧪 MODO TESTE - Teste rápido do bloqueio de tela")
        print("="*60)
    elif "--20-20-20" in sys.argv:
        mode = '20-20-20'
    
    timer = EyeBreakTimer(mode=mode)
    timer.run()
