from __future__ import annotations

from datetime import datetime
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from gp_gui.client import (
    GlobalProtectClient,
    GlobalProtectError,
    CommandResult,
    ConnectionStatus,
    parse_status_output,
)
from gp_gui.config import AppConfig, load_config, save_config


class GlobalProtectApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GlobalProtect GUI (Linux)")
        self.root.geometry("860x560")
        self.root.minsize(780, 500)

        self.client = GlobalProtectClient()
        self.config = load_config()

        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._is_busy = False

        self._build_ui()
        self._set_form_from_config()

        self.root.after(150, self._poll_queue)
        self.root.after(300, self.refresh_status)

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        top = ttk.LabelFrame(main, text="Connection", padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Portal").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.portal_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.portal_var, width=50).grid(
            row=0, column=1, sticky=tk.EW, padx=6
        )

        ttk.Label(top, text="Username").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.username_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.username_var, width=50).grid(
            row=1, column=1, sticky=tk.EW, padx=6
        )

        top.columnconfigure(1, weight=1)

        button_row = ttk.Frame(top)
        button_row.grid(row=0, column=2, rowspan=2, padx=(6, 0))
        self.connect_btn = ttk.Button(button_row, text="Connect", command=self.connect)
        self.connect_btn.pack(fill=tk.X, pady=2)
        self.disconnect_btn = ttk.Button(button_row, text="Disconnect", command=self.disconnect)
        self.disconnect_btn.pack(fill=tk.X, pady=2)
        self.refresh_btn = ttk.Button(button_row, text="Refresh", command=self.refresh_status)
        self.refresh_btn.pack(fill=tk.X, pady=2)
        self.details_btn = ttk.Button(button_row, text="Details", command=self.show_details)
        self.details_btn.pack(fill=tk.X, pady=2)

        status_frame = ttk.LabelFrame(main, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_var = tk.StringVar(value="Unknown")
        self.user_var = tk.StringVar(value="-")
        self.gateway_var = tk.StringVar(value="-")
        self.ip_var = tk.StringVar(value="-")

        self._status_row(status_frame, 0, "State", self.status_var)
        self._status_row(status_frame, 1, "User", self.user_var)
        self._status_row(status_frame, 2, "Gateway", self.gateway_var)
        self._status_row(status_frame, 3, "IP", self.ip_var)

        log_frame = ttk.LabelFrame(main, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=12, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scroll.set)

        footer = ttk.Frame(main)
        footer.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(footer, text="Auto-refresh (s)").pack(side=tk.LEFT)
        self.refresh_var = tk.IntVar(value=max(2, self.config.auto_refresh_seconds))
        spin = ttk.Spinbox(footer, from_=2, to=60, textvariable=self.refresh_var, width=5)
        spin.pack(side=tk.LEFT, padx=(6, 12))
        ttk.Button(footer, text="Save Settings", command=self.save_settings).pack(side=tk.LEFT)

    @staticmethod
    def _status_row(frame: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(frame, text=f"{label}:", width=12).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Label(frame, textvariable=var).grid(row=row, column=1, sticky=tk.W, pady=2)

    def _set_form_from_config(self) -> None:
        self.portal_var.set(self.config.portal)
        self.username_var.set(self.config.username)

    def _log(self, message: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {message}\n"
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _set_busy(self, busy: bool) -> None:
        self._is_busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.connect_btn.configure(state=state)
        self.disconnect_btn.configure(state=state)
        self.refresh_btn.configure(state=state)
        self.details_btn.configure(state=state)

    def _run_async(self, action: str, fn, *args) -> None:
        if self._is_busy:
            self._log("Busy: wait for the current operation to complete.")
            return
        self._set_busy(True)

        def worker() -> None:
            try:
                result = fn(*args)
                self._queue.put((action, result))
            except Exception as exc:
                self._queue.put(("error", exc))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self) -> None:
        try:
            while True:
                action, payload = self._queue.get_nowait()
                self._handle_result(action, payload)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _update_status_fields(self, parsed: ConnectionStatus) -> None:
        self.status_var.set(parsed.state.capitalize())
        self.user_var.set(parsed.user or "-")
        self.gateway_var.set(parsed.gateway or "-")
        self.ip_var.set(parsed.ip or "-")

    def _handle_result(self, action: str, payload: object) -> None:
        self._set_busy(False)

        if action == "error":
            self._log(f"Error: {payload}")
            messagebox.showerror("GlobalProtect GUI", str(payload))
            return

        if isinstance(payload, CommandResult):
            result = payload
            if result.stdout:
                self._log(result.stdout)
            if result.stderr:
                self._log(f"stderr: {result.stderr}")
            if result.returncode != 0:
                self._log(f"Command failed with exit code {result.returncode}")

            if action in {"status", "details", "connect", "disconnect"}:
                parsed = parse_status_output(result.stdout if result.stdout else result.stderr)
                self._update_status_fields(parsed)

            if action == "connect":
                self._log("If your company uses Okta/SAML, complete login in the browser/MFA prompt.")
                self._run_async("post_connect", self.client.wait_for_connected)
                return

        if action == "post_connect" and isinstance(payload, ConnectionStatus):
            self._update_status_fields(payload)
            if payload.state == "connected":
                self._log("Connected successfully.")
            else:
                self._log("Connect command finished but tunnel is not connected yet.")

        self._schedule_auto_refresh()

    def _schedule_auto_refresh(self) -> None:
        interval_ms = max(2000, self.refresh_var.get() * 1000)
        self.root.after(interval_ms, self.refresh_status)

    def connect(self) -> None:
        portal = self.portal_var.get().strip()
        username = self.username_var.get().strip()
        if not portal:
            messagebox.showwarning("GlobalProtect GUI", "Please enter a portal first.")
            return
        self._log(f"Connecting to portal: {portal}")
        self._run_async("connect", self.client.connect, portal, username)

    def disconnect(self) -> None:
        self._log("Disconnecting...")
        self._run_async("disconnect", self.client.disconnect)

    def refresh_status(self) -> None:
        if self._is_busy:
            return
        self._run_async("status", self.client.show_status)

    def show_details(self) -> None:
        self._run_async("details", self.client.show_details)

    def save_settings(self) -> None:
        self.config = AppConfig(
            portal=self.portal_var.get().strip(),
            username=self.username_var.get().strip(),
            auto_refresh_seconds=max(2, int(self.refresh_var.get())),
        )
        save_config(self.config)
        self._log("Settings saved.")


def main() -> None:
    root = tk.Tk()
    app = GlobalProtectApp(root)
    app._log("GlobalProtect GUI started.")

    try:
        app.client.ensure_available()
    except GlobalProtectError as exc:
        app._log(str(exc))
        messagebox.showwarning("GlobalProtect GUI", str(exc))

    root.mainloop()


if __name__ == "__main__":
    main()
