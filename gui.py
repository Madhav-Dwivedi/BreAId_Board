import customtkinter as ctk
from tkinter import filedialog
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time
import os

class STM32Uploader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ECE 385 ➔ IEEE Folder Porter")
        self.geometry("850x750")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- UI Elements ---
        self.label = ctk.CTkLabel(self, text="IEEE Hackathon Node Mapper", font=("Helvetica", 24, "bold"))
        self.label.pack(pady=20)

        self.file_label = ctk.CTkLabel(self, text="Select an XML netlist from /parsing", text_color="gray")
        self.file_label.pack(pady=5)

        self.select_btn = ctk.CTkButton(self, text="📂 Open & Convert XML", command=self.select_file, fg_color="#6c5ce7")
        self.select_btn.pack(pady=10)

        self.preview_box = ctk.CTkTextbox(self, width=750, height=350, font=("Courier New", 13), wrap="none")
        self.preview_box.pack(pady=10, padx=20)
        self.preview_box.insert("0.0", "Structured XML output will appear here...")

        self.send_btn = ctk.CTkButton(self, text="💾 Export to IEEE Folder", command=self.save_to_file, state="disabled", fg_color="#80389c")
        self.send_btn.pack(pady=10)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(pady=20, padx=20, fill="x")

        self.processed_xml = ""

    def prettify(self, elem):
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def parse_to_new_xml(self, path):
        try:
            input_tree = ET.parse(path)
            input_root = input_tree.getroot()
            output_root = ET.Element("NodeList", date=time.strftime("%Y-%m-%d %H:%M:%S"))
            
            node_counter = 1
            for net in input_root.findall(".//net"):
                connections = []
                for connector in net.findall("connector"):
                    conn_name = connector.get("name") or connector.get("id", "??")
                    part = connector.find("part")
                    if part is not None:
                        label = part.get("label", "Unknown")
                        connections.append((label, conn_name))

                if connections:
                    node_elem = ET.SubElement(output_root, "Node", id=f"{node_counter:03d}")
                    for label, pin in sorted(connections):
                        ET.SubElement(node_elem, "Connection", part=label, pin=pin)
                    node_counter += 1
            
            return self.prettify(output_root)
        except Exception as e:
            return f""

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("XML Netlist", "*.xml")])
        if file_path:
            self.file_label.configure(text=f"Source: {os.path.basename(file_path)}", text_color="white")
            self.processed_xml = self.parse_to_new_xml(file_path)
            self.preview_box.delete("0.0", "end")
            self.preview_box.insert("0.0", self.processed_xml)
            self.send_btn.configure(state="normal")

    def save_to_file(self):
        try:
            # --- FOLDER LOGIC ---
            # Finds the directory where gui.py is located
            ieee_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(ieee_dir, "mapped_nodes.xml")
            
            with open(output_path, "w", encoding='utf-8') as f:
                f.write(self.processed_xml)
            
            for i in range(1, 11):
                time.sleep(0.04)
                self.progress.set(i / 10)
                self.update_idletasks()
            
            self.label.configure(text="Saved in IEEE Folder! ✨", text_color="#55efc4")
            print(f"File saved to: {output_path}")
            
        except Exception as e:
            self.label.configure(text="Export Failed ❌", text_color="#ff7675")
            print(f"Error: {e}")

if __name__ == "__main__":
    app = STM32Uploader()
    app.mainloop()