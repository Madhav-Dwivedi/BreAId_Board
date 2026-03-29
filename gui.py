import customtkinter as ctk
from tkinter import filedialog
import xml.etree.ElementTree as ET
import time
import os
import re
import serial  # pip install pyserial
import serial.tools.list_ports

class STM32Uploader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Boolean Boys -> BreAId-Board")
        self.geometry("850x850")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- UI Elements ---
        self.label = ctk.CTkLabel(self, text="BreAId-Board Netlist Parser", font=("Helvetica", 24, "bold"))
        self.label.pack(pady=20)

        self.file_label = ctk.CTkLabel(self, text="Output: 1s (Connected) and 0s (Open) | 10x10 Grid", text_color="gray")
        self.file_label.pack(pady=5)

        self.select_btn = ctk.CTkButton(self, text="📂 Generate Binary Matrix", command=self.select_file, fg_color="#6c5ce7")
        self.select_btn.pack(pady=10)

        self.preview_box = ctk.CTkTextbox(self, width=750, height=350, font=("Courier New", 16), wrap="none")
        self.preview_box.pack(pady=10, padx=20)
        self.preview_box.insert("0.0", "Binary grid will appear here...")

        # Button 1: Export to File
        self.save_btn = ctk.CTkButton(self, text="💾 Export mapped_nodes.xml", command=self.save_to_file, state="disabled", fg_color="#9923a6")
        self.save_btn.pack(pady=5)

        # Button 2: Upload to Hardware
        self.upload_btn = ctk.CTkButton(self, text="🚀 Upload to STM32", command=self.upload_to_hardware, state="disabled", fg_color="#e67e22")
        self.upload_btn.pack(pady=10)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(pady=20, padx=20, fill="x")

        self.processed_matrix = ""

    def parse_to_binary_matrix(self, path):
        """Creates a raw 10x10 binary string grid."""
        try:
            input_tree = ET.parse(path)
            input_root = input_tree.getroot()
            matrix = [['0' for _ in range(10)] for _ in range(10)]

            for net in input_root.findall(".//net"):
                input_rows, output_rows = [], []
                for connector in net.findall("connector"):
                    conn_id = connector.get("id") or connector.get("name") or ""
                    part_elem = connector.find("part")
                    if part_elem is not None:
                        title = part_elem.get("title", "")
                        label = part_elem.get("label", "")
                        if "Breadboard" in title or "Breadboard" in label:
                            match = re.search(r'([A-Ja-j])(\d+)', conn_id)
                            if match:
                                col, row = match.group(1).upper(), int(match.group(2))
                                if 1 <= row <= 10:
                                    if col in "ABCDE": output_rows.append(row)
                                    else: input_rows.append(row)

                for in_row in input_rows:
                    for out_row in output_rows:
                        matrix[in_row-1][out_row-1] = '1'

            matrix_string = "\n".join([" ".join(row) for row in matrix])
            return f"<Matrix>\n{matrix_string}\n</Matrix>"
        except Exception as e:
            return f""

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("XML Netlist", "*.xml")])
        if file_path:
            self.file_label.configure(text=f"Parsing: {os.path.basename(file_path)}", text_color="white")
            self.processed_matrix = self.parse_to_binary_matrix(file_path)
            self.preview_box.delete("0.0", "end")
            self.preview_box.insert("0.0", self.processed_matrix)
            self.save_btn.configure(state="normal")
            self.upload_btn.configure(state="normal")

    def save_to_file(self):
        try:
            ieee_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(ieee_dir, "mapped_nodes.xml")
            with open(output_path, "w", encoding='utf-8') as f:
                f.write(self.processed_matrix)
            self.progress_animation("Binary Matrix Exported! ✨")
        except Exception as e:
            self.label.configure(text="Export Failed ❌", text_color="#f80000")

    def upload_to_hardware(self):
        """Sends the raw 100-bit string to the STM32 over Serial."""
        try:
            # 1. Strip XML tags and spaces to get exactly 100 bits
            raw_data = self.processed_matrix.replace("<Matrix>", "").replace("</Matrix>", "")
            clean_bits = "".join(raw_data.split()) # Removes all whitespace/newlines

            # 2. Find the COM port
            ports = list(serial.tools.list_ports.comports())
            if not ports:
                self.label.configure(text="No STM32 Detected! 🔌", text_color="#c8a401")
                return

            # 3. Connect and Send
            # Using 115200 baud (standard for STM32). Adjust if your friend used 9600.
            ser = serial.Serial(ports[0].device, 115200, timeout=1)
            time.sleep(2) # Give connection a moment to stabilize
            
            ser.write(clean_bits.encode('utf-8'))
            ser.write(b'\n') # End of line signal
            ser.close()

            self.progress_animation("Upload Successful! 🚀")
        except Exception as e:
            self.label.configure(text="Upload Error ❌", text_color="#ff0000")
            print(f"Serial Error: {e}")

    def progress_animation(self, success_msg):
        for i in range(1, 11):
            time.sleep(0.04)
            self.progress.set(i / 10)
            self.update_idletasks()
        self.label.configure(text=success_msg, text_color="#0b9d74")

if __name__ == "__main__":
    app = STM32Uploader()
    app.mainloop()