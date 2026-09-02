"""Loop principal: câmera → movimento → ALPR → decisão → GPIO → fila de eventos."""
import logging
import time

import cv2
import numpy as np

from catraca import plates
from catraca.alpr_engine import AlprEngine
from catraca.config import Config
from catraca.decision import DecisionEngine
from catraca.events import EventStore
from catraca.motion import MotionGate
from catraca.signals import GateSignals
from catraca.sync import CloudClient, SyncWorker
from catraca.whitelist import Whitelist

log = logging.getLogger(__name__)


def _jpeg(frame: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return buf.tobytes() if ok else b""


def _open_camera(cfg: Config) -> cv2.VideoCapture | None:
    cap = cv2.VideoCapture(cfg.camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.frame_height)
    if cap.isOpened():
        return cap
    cap.release()
    return None


def process_frame(frame, *, motion, alpr, engine, signals, store, cfg,
                  fallback=None, button=None, preview=None) -> str:
    if not motion.triggered(frame):
        return "no_motion"

    reading = alpr.read(frame)
    if reading is None:
        return "no_plate"

    plate = reading.plate
    used_fallback = False
    if not plates.is_valid(plate):
        fixed = plates.fix_confusions(plate)
        if fixed is not None:
            plate = fixed
        elif fallback is not None and reading.ocr_confidence < cfg.ocr_conf_threshold:
            alt = fallback.read_plate(_jpeg(reading.crop))
            if alt is not None and plates.is_valid(alt):
                plate = alt
                used_fallback = True
    if not plates.is_valid(plate):
        return "invalid"
    if not used_fallback and reading.ocr_confidence < cfg.min_decision_conf:
        return "low_conf"  # leitura duvidosa: espera um frame melhor

    decision = engine.decide(plate)
    if decision is None:
        return "cooldown"

    if decision.authorized:
        signals.authorized()
    else:
        signals.denied()
        if button is not None:
            button.register_denied(plate)
    store.record(plate, decision.authorized, reading.ocr_confidence,
                 used_fallback, _jpeg(frame))
    if preview is not None:
        preview.set_status(
            f"{plate} {'AUTORIZADA' if decision.authorized else 'NEGADA'} "
            f"(conf={reading.ocr_confidence:.2f})"
        )
    log.info("placa=%s %s (conf=%.2f fallback=%s)", plate,
             "AUTORIZADA" if decision.authorized else "NEGADA",
             reading.ocr_confidence, used_fallback)
    return "authorized" if decision.authorized else "denied"


def run() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = Config.from_env()

    whitelist = Whitelist(cfg.db_path)
    store = EventStore(cfg.db_path)
    deps = dict(
        motion=MotionGate(threshold=cfg.motion_threshold),
        alpr=AlprEngine(),
        engine=DecisionEngine(whitelist, cooldown_s=cfg.cooldown_s),
        signals=GateSignals(),
        store=store,
        cfg=cfg,
        fallback=None,
    )
    if cfg.fallback_enabled:
        from catraca.fallback import ClaudeOcrFallback

        deps["fallback"] = ClaudeOcrFallback()
        log.info("fallback LLM habilitado")

    if cfg.cloud_url:
        client = CloudClient(cfg.cloud_url, cfg.cloud_api_key)
        worker = SyncWorker(store, whitelist, client, interval_s=cfg.sync_interval_s)
        worker.start()
        log.info("sync com %s a cada %.0fs", cfg.cloud_url, cfg.sync_interval_s)
        if cfg.button_enabled:
            from catraca.button import AuthorizeButton

            def _on_authorized(plate: str) -> None:
                worker.run_once()  # puxa a whitelist atualizada sem esperar o ciclo
                deps["signals"].authorized()

            deps["button"] = AuthorizeButton(
                client, pin=cfg.button_pin, window_s=cfg.button_window_s,
                on_authorized=_on_authorized,
            )
            log.info("botão de autorização no GPIO%d", cfg.button_pin)
    else:
        log.warning("CATRACA_CLOUD_URL vazio: rodando 100%% offline")

    preview = None
    if cfg.preview_port:
        from catraca.preview import Preview, start_server

        preview = Preview()
        start_server(preview, cfg.preview_port)
        deps["preview"] = preview
        log.info("preview da camera em http://<ip-do-pi>:%d", cfg.preview_port)

    cap = _open_camera(cfg)
    if cap is None:
        raise SystemExit(f"webcam {cfg.camera_index} nao abriu")
    log.info("catraca no ar (camera %d @ %dx%d)", cfg.camera_index,
             cfg.frame_width, cfg.frame_height)

    try:
        last_preview = 0.0
        frames_perdidos = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                frames_perdidos += 1
                if frames_perdidos == 1:
                    log.warning("frame perdido; aguardando camera")
                if frames_perdidos >= 20:  # ~10s sem frame: USB caiu, reabre
                    log.warning("camera sumiu; tentando reabrir")
                    if preview is not None:
                        preview.set_status("camera desconectada — reconectando…")
                    cap.release()
                    time.sleep(2)
                    nova = _open_camera(cfg)
                    if nova is not None:
                        cap = nova
                        log.info("camera reaberta")
                        if preview is not None:
                            preview.set_status("camera reconectada")
                    frames_perdidos = 0
                else:
                    time.sleep(0.5)
                continue
            frames_perdidos = 0
            if preview is not None and time.monotonic() - last_preview >= 0.5:
                preview.update_frame(_jpeg(frame))
                last_preview = time.monotonic()
            process_frame(frame, **deps)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        deps["signals"].close()
        if deps.get("button") is not None:
            deps["button"].close()


if __name__ == "__main__":
    run()
