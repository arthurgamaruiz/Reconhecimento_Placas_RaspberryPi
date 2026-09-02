"""Smoke de hardware: valida a fiação ANTES de subir o serviço.

Rodar NO PI:  ~/catraca/venv/bin/python ~/catraca/hw_smoke.py
Esperado: LED verde 2s, LED vermelho 2s, 2 beeps. Se algo não acontecer,
revisar a fiação (verde=GPIO17/pino 11, vermelho=GPIO27/pino 13, buzzer=GPIO22/pino 15).
"""
import time

from gpiozero import LED, Buzzer

green, red, buzzer = LED(17), LED(27), Buzzer(22)

print("LED verde...")
green.on(); time.sleep(2); green.off()
print("LED vermelho...")
red.on(); time.sleep(2); red.off()
print("buzzer (2 beeps)...")
buzzer.beep(on_time=0.15, off_time=0.15, n=2, background=False)
print("ok — se você viu verde, vermelho e ouviu 2 beeps, a fiação está certa")
