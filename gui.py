import customtkinter as ctk
from tkinter import filedialog
import xml.etree.ElementTree as ET
import time
import os
import re
import serial.tools.list_ports # Kept for port scanning display
from datetime import datetime

class STM32Uploader(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title("Boolean Boys -> BreAId-Board")
        self.geometry("1000x1000")
        self.resizable(True, True)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Internal Variables ---
        self.raw_payload = "" 
        self.selected_port = ctk.StringVar(value="Select COM Port")

        # --- UI Layout ---
        self.label = ctk.CTkLabel(self, text="BreAId-Board Parser", font=("Helvetica", 28, "bold"))
        self.label.pack(pady=(20, 10))

        # 1. Port Selection Section (Still scans for show, but won't be used)
        self.port_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.port_frame.pack(pady=5)
        
        self.port_menu = ctk.CTkOptionMenu(self.port_frame, variable=self.selected_port, values=["Scanning..."])
        self.port_menu.pack(side="left", padx=5)
        
        self.refresh_btn = ctk.CTkButton(self.port_frame, text="🔄 Refresh Ports", width=120, command=self.update_ports, fg_color="#34495e")
        self.refresh_btn.pack(side="left", padx=5)

        # 2. File Selection
        self.select_btn = ctk.CTkButton(self, text="📂 Generate 190-bit Matrix", command=self.select_file, 
                                        fg_color="#6c5ce7", font=("Helvetica", 14, "bold"), height=40)
        self.select_btn.pack(pady=10)

        # 3. Visual Grid Preview (Pure 20x20 Data)
        self.preview_label = ctk.CTkLabel(self, text="Live Matrix Preview (0-9: Side A | 10-19: Side B)", font=("Helvetica", 12, "italic"))
        self.preview_label.pack(pady=(5, 0))
        self.preview_box = ctk.CTkTextbox(self, width=650, height=450, font=("Courier New", 16), wrap="none")
        self.preview_box.pack(pady=5, padx=20)

        # 4. Action Buttons
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=10)

        self.save_btn = ctk.CTkButton(self.button_frame, text="💾 Export XML", command=self.save_to_file, state="disabled", fg_color="#9923a6")
        self.save_btn.pack(side="left", padx=10)

        self.upload_btn = ctk.CTkButton(self.button_frame, text="🚀 Sync & Upload", command=self.upload_to_hardware, state="disabled", fg_color="#e67e22")
        self.upload_btn.pack(side="left", padx=10)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(pady=10, padx=20, fill="x")

        # 5. System Console
        self.console = ctk.CTkTextbox(self, width=850, height=180, font=("Courier New", 12), fg_color="#1a1a1a", text_color="#00ff00")
        self.console.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Initial scan
        self.update_ports()
        self.log("System Initialized")

    def log(self, message):
        """Adds a message to the internal GUI console."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.insert("end", f"[{timestamp}] {message}\n")
        self.console.see("end")

    def update_ports(self):
        """Scans for ports and logs the list for visual parity."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if not ports:
            self.port_menu.configure(values=["No Ports Found"])
            self.selected_port.set("No Ports Found")
            self.log("SCAN: No physical COM ports detected.")
        else:
            self.port_menu.configure(values=ports)
            if self.selected_port.get() not in ports:
                self.selected_port.set(ports[0])
            self.log(f"SCAN: Found {len(ports)} active ports: {', '.join(ports)}")

    def parse_to_grid(self, path):
        """Builds a 20x20 matrix for GUI (0 diagonals)."""
        try:
            self.log(f"Parsing: {os.path.basename(path)}")
            input_tree = ET.parse(path)
            input_root = input_tree.getroot()
            
            matrix = [[0 for _ in range(20)] for _ in range(20)]

            for net in input_root.findall(".//net"):
                active_indices = set()
                for connector in net.findall("connector"):
                    conn_id = connector.get("id") or ""
                    # Mapping A-E (0-9) and F-J (10-19) for Rows 1-10
                    match = re.match(r'^([A-J])(\d+)$', conn_id, re.IGNORECASE)
                    if match:
                        col, row = match.group(1).upper(), int(match.group(2))
                        if 1 <= row <= 10:
                            idx = (row - 1) if col in "ABCDE" else (row + 9)
                            active_indices.add(idx)

                for i in active_indices:
                    for j in active_indices:
                        if i != j: matrix[i][j] = 1

            # Prepare the 190-bit Triangle Payload
            triangle_bits = [str(matrix[i][j]) for i in range(20) for j in range(i+1, 20)]
            self.raw_payload = f"#{''.join(triangle_bits)}!"

            # Format the GUI 2D Display
            visual_grid = ""
            for r in range(20):
                visual_grid += " ".join([str(matrix[r][c]) for c in range(20)]) + "\n"

            self.log("Matrix parsed. Ready for sync.")
            return visual_grid

        except Exception as e:
            self.log(f"PARSE ERROR: {e}")
            return ""

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("XML Netlist", "*.xml")])
        if file_path:
            grid_display = self.parse_to_grid(file_path)
            self.preview_box.delete("0.0", "end")
            self.preview_box.insert("0.0", grid_display)
            self.save_btn.configure(state="normal")
            self.upload_btn.configure(state="normal")

    def upload_to_hardware(self):
        """Simulates the STM32 handshake and transfer process."""
        self.upload_btn.configure(state="disabled") # Prevent double-click
        
        # 1. Simulate Connection
        self.log(f"Attempting connection to {self.selected_port.get()}...")
        self.update_idletasks()
        time.sleep(1) # Simulated delay
        
        # 2. Simulate Handshake
        self.log("Waiting for STM32 'Ready' signal...")
        self.update_idletasks()
        time.sleep(1.5) # Simulated wait for 'Ready'
        
        # 3. Simulate Data Burst
        self.log("Sync confirmed. Transmitting 190-bit triangle...")
        self.update_idletasks()
        time.sleep(0.5)
        
        # 4. Simulated Verification Window (User's requested 4s delay)
        self.log("Data transmitted. Verifying on STM32...")
        self.update_idletasks()
        
        time.sleep(2) # The big 4-second wait
        
        # 5. Success Message
        self.log(".xml file transfer is successful")
        
        # Reset and Animation
        self.progress_animation("Task Finished!")
        self.upload_btn.configure(state="normal")

    def save_to_file(self):
        try:
            output_path = os.path.join(os.path.dirname(__file__), "mapped_nodes.xml")
            with open(output_path, "w", encoding='utf-8') as f:
                f.write(self.raw_payload)
            self.log(f"Parity File Exported: {output_path}")
            self.progress_animation("XML Saved! ")
        except Exception as e:
            self.log(f"SAVE ERROR: {e}")

    def progress_animation(self, msg):
        self.progress.set(0)
        for i in range(1, 11):
            time.sleep(0.04)
            self.progress.set(i / 10)
            self.update_idletasks()
        self.log(msg)

if __name__ == "__main__":
    app = STM32Uploader()
    app.mainloop()