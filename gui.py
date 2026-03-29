import customtkinter as ctk
from tkinter import filedialog
import xml.etree.ElementTree as ET
import time
import os
import re
import serial  # pip install pyserial
import serial.tools.list_ports
from datetime import datetime

class STM32Uploader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Boolean Boys -> BreAId-Board Pro")
        self.geometry("900x950")
        self.resizable(True, True)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Variables ---
        self.processed_matrix = ""
        self.selected_port = ctk.StringVar(value="Select COM Port")

        # --- UI Elements ---
        self.label = ctk.CTkLabel(self, text="BreAId-Board Pro Parser", font=("Helvetica", 28, "bold"))
        self.label.pack(pady=(20, 10))

        # Port Selection Frame
        self.port_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.port_frame.pack(pady=5)
        
        self.port_menu = ctk.CTkOptionMenu(self.port_frame, variable=self.selected_port, values=["Scanning..."])
        self.port_menu.pack(side="left", padx=5)
        
        self.refresh_btn = ctk.CTkButton(self.port_frame, text="🔄 Refresh", width=80, command=self.update_ports, fg_color="#34495e")
        self.refresh_btn.pack(side="left", padx=5)

        self.select_btn = ctk.CTkButton(self, text="📂 Generate 190-bit Matrix", command=self.select_file, fg_color="#6c5ce7", font=("Helvetica", 14, "bold"))
        self.select_btn.pack(pady=10)

        # Preview area
        self.preview_box = ctk.CTkTextbox(self, width=750, height=250, font=("Courier New", 14), wrap="none")
        self.preview_box.pack(pady=5, padx=20)

        # Buttons Row
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=10)

        self.save_btn = ctk.CTkButton(self.button_frame, text="💾 Export XML", command=self.save_to_file, state="disabled", fg_color="#9923a6")
        self.save_btn.pack(side="left", padx=10)

        self.upload_btn = ctk.CTkButton(self.button_frame, text="🚀 Upload to STM32", command=self.upload_to_hardware, state="disabled", fg_color="#e67e22")
        self.upload_btn.pack(side="left", padx=10)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(pady=10, padx=20, fill="x")

        # Console Box
        self.console = ctk.CTkTextbox(self, width=750, height=200, font=("Courier New", 12), fg_color="#1a1a1a", text_color="#00ff00")
        self.console.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.update_ports()
        self.log("System Initialized. Manual Port Control Active.")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.insert("end", f"[{timestamp}] {message}\n")
        self.console.see("end")

    def update_ports(self):
        """Scans for available COM ports and updates the dropdown."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if not ports:
            self.port_menu.configure(values=["No Ports Found"])
            self.selected_port.set("No Ports Found")
            self.log("No serial ports detected.")
        else:
            self.port_menu.configure(values=ports)
            if self.selected_port.get() not in ports:
                self.selected_port.set(ports[0])
            self.log(f"Scan complete: Found {len(ports)} ports.")

    def parse_to_binary_matrix(self, path):
        try:
            self.log(f"Parsing: {os.path.basename(path)}")
            input_tree = ET.parse(path)
            input_root = input_tree.getroot()
            full_matrix = [[0 for _ in range(20)] for _ in range(20)]

            for net in input_root.findall(".//net"):
                active_indices = []
                for connector in net.findall("connector"):
                    conn_id = connector.get("id") or connector.get("name") or ""
                    part_elem = connector.find("part")
                    if part_elem is not None:
                        label = part_elem.get("label", "")
                        if "Breadboard" in label or "Breadboard" in part_elem.get("title", ""):
                            match = re.search(r'([A-Ja-j])(\d+)', conn_id)
                            if match:
                                col, row = match.group(1).upper(), int(match.group(2))
                                if 1 <= row <= 10:
                                    idx = (row - 1) if col in "ABCDE" else (row + 9)
                                    active_indices.append(idx)

                for i in active_indices:
                    for j in active_indices:
                        if i != j: full_matrix[i][j] = 1

            triangle_bits = [str(full_matrix[i][j]) for i in range(20) for j in range(i + 1, 20)]
            bits_string = "".join(triangle_bits)
            return f"<Triangle190>\n#{bits_string}!\n</Triangle190>"
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            return ""

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("XML Netlist", "*.xml")])
        if file_path:
            self.processed_matrix = self.parse_to_binary_matrix(file_path)
            self.preview_box.delete("0.0", "end")
            self.preview_box.insert("0.0", self.processed_matrix)
            self.save_btn.configure(state="normal")
            self.upload_btn.configure(state="normal")

    def upload_to_hardware(self):
        try:
            match = re.search(r'(#[01]+!)', self.processed_matrix)
            if not match:
                self.log("Upload aborted: Matrix not generated.")
                return
            
            payload = match.group(1)
            port_to_use = self.selected_port.get()

            if port_to_use in ["Select COM Port", "No Ports Found", "Scanning..."]:
                self.log("ERROR: Please select a valid COM port from the dropdown.")
                return

            self.log(f"Opening {port_to_use}...")
            ser = serial.Serial(port_to_use, 115200, timeout=2)
            time.sleep(1.5) 
            
            self.log("Sending framed matrix...")
            ser.write(payload.encode('utf-8'))
            
            self.log("Waiting for hardware ACK...")
            response = ser.readline().decode('utf-8').strip()
            if response:
                self.log(f"STM32 SAYS: {response}")
            else:
                self.log("No response. Check your STM32 UART code!")

            ser.close()
            self.progress_animation("Success! 🚀")
            
        except Exception as e:
            self.log(f"UPLOAD ERROR: {e}")

    def save_to_file(self):
        try:
            output_path = os.path.join(os.path.dirname(__file__), "mapped_nodes.xml")
            with open(output_path, "w", encoding='utf-8') as f:
                f.write(self.processed_matrix)
            self.log(f"Saved: {output_path}")
            self.progress_animation("Exported! ✨")
        except Exception as e:
            self.log(f"SAVE ERROR: {e}")

    def progress_animation(self, success_msg):
        self.progress.set(0)
        for i in range(1, 11):
            time.sleep(0.04)
            self.progress.set(i / 10)
            self.update_idletasks()
        self.log(success_msg)

if __name__ == "__main__":
    app = STM32Uploader()
    app.mainloop()