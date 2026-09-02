"""Sinalização física da catraca: LEDs e buzzer via gpiozero (não-bloqueante)."""
from gpiozero import LED, Buzzer


class GateSignals:
    def __init__(self, green_pin: int = 17, red_pin: int = 27, buzzer_pin: int = 22,
                 hold_s: float = 3.0):
        self.green = LED(green_pin)
        self.red = LED(red_pin)
        self.buzzer = Buzzer(buzzer_pin)
        self._hold = hold_s

    def authorized(self) -> None:
        self.red.off()
        self.green.blink(on_time=self._hold, off_time=0.1, n=1, background=True)
        self.buzzer.beep(on_time=0.1, off_time=0.1, n=2, background=True)

    def denied(self) -> None:
        self.green.off()
        self.red.blink(on_time=self._hold, off_time=0.1, n=1, background=True)
        self.buzzer.beep(on_time=0.6, off_time=0.1, n=1, background=True)

    def close(self) -> None:
        for dev in (self.green, self.red, self.buzzer):
            dev.close()
