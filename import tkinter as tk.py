import tkinter as tk
from tkinter import ttk, messagebox
import random


class PacketFragmentationSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Packet Fragmentation and Reassembly Simulator")
        self.root.geometry("1050x700")
        self.root.minsize(850, 600)

        self.fragments = []
        self.original_payload = b""

        self.build_gui()

    def build_gui(self):
        title = tk.Label(
            self.root,
            text="Packet Fragmentation and Reassembly Simulator",
            font=("Arial", 18, "bold"),
            fg="navy"
        )
        title.pack(pady=12)

        # Input section
        input_frame = ttk.LabelFrame(
            self.root, text="Packet Configuration", padding=12
        )
        input_frame.pack(fill="x", padx=15, pady=5)

        ttk.Label(input_frame, text="Payload Size (bytes):").grid(
            row=0, column=0, padx=8, pady=8, sticky="w"
        )
        self.payload_entry = ttk.Entry(input_frame, width=15)
        self.payload_entry.insert(0, "3800")
        self.payload_entry.grid(row=0, column=1, padx=8)

        ttk.Label(input_frame, text="MTU (bytes):").grid(
            row=0, column=2, padx=8, pady=8, sticky="w"
        )
        self.mtu_entry = ttk.Entry(input_frame, width=15)
        self.mtu_entry.insert(0, "1500")
        self.mtu_entry.grid(row=0, column=3, padx=8)

        ttk.Label(input_frame, text="IPv4 Header (bytes):").grid(
            row=1, column=0, padx=8, pady=8, sticky="w"
        )
        self.header_entry = ttk.Entry(input_frame, width=15)
        self.header_entry.insert(0, "20")
        self.header_entry.grid(row=1, column=1, padx=8)

        self.shuffle_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            input_frame,
            text="Deliver fragments out of order",
            variable=self.shuffle_var
        ).grid(row=1, column=2, columnspan=2, padx=8, sticky="w")

        self.drop_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            input_frame,
            text="Drop one fragment (test failure)",
            variable=self.drop_var
        ).grid(row=2, column=2, columnspan=2, padx=8, sticky="w")

        # Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="Fragment Packet",
            command=self.fragment_packet
        ).pack(side="left", padx=8)

        ttk.Button(
            button_frame,
            text="Transmit & Reassemble",
            command=self.reassemble_packet
        ).pack(side="left", padx=8)

        ttk.Button(
            button_frame,
            text="Clear",
            command=self.clear_all
        ).pack(side="left", padx=8)

        # Fragment table
        table_frame = ttk.LabelFrame(
            self.root, text="Fragment Details", padding=10
        )
        table_frame.pack(fill="both", expand=True, padx=15, pady=5)

        columns = (
            "number", "offset", "payload", "header",
            "total", "mf", "identification"
        )

        self.table = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=10
        )

        headings = {
            "number": "Fragment",
            "offset": "Offset (8-byte units)",
            "payload": "Payload (bytes)",
            "header": "Header (bytes)",
            "total": "Total Length",
            "mf": "MF Flag",
            "identification": "Identification"
        }

        widths = {
            "number": 75,
            "offset": 150,
            "payload": 125,
            "header": 110,
            "total": 110,
            "mf": 85,
            "identification": 125
        }

        for column in columns:
            self.table.heading(column, text=headings[column])
            self.table.column(
                column, width=widths[column], anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.table.yview
        )
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Output
        output_frame = ttk.LabelFrame(
            self.root, text="Simulation Results", padding=10
        )
        output_frame.pack(fill="x", padx=15, pady=8)

        self.output = tk.Text(
            output_frame, height=7, wrap="word",
            font=("Consolas", 10)
        )
        self.output.pack(fill="x")

        self.write_output(
            "Welcome!\n"
            "1. Enter the payload size and MTU.\n"
            "2. Click Fragment Packet.\n"
            "3. Click Transmit & Reassemble to test reconstruction."
        )

    def write_output(self, text):
        self.output.config(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)
        self.output.config(state="disabled")

    def get_configuration(self):
        try:
            payload_size = int(self.payload_entry.get())
            mtu = int(self.mtu_entry.get())
            header_size = int(self.header_entry.get())
        except ValueError:
            raise ValueError("Enter valid whole numbers in all fields.")

        if payload_size <= 0:
            raise ValueError("Payload size must be greater than zero.")

        if header_size < 20 or header_size > 60 or header_size % 4:
            raise ValueError(
                "IPv4 header must be 20-60 bytes and a multiple of 4."
            )

        if mtu < header_size + 8 or mtu > 65535:
            raise ValueError(
                "MTU must be greater than header size + 7 "
                "and no greater than 65535."
            )

        # IPv4 total length cannot exceed 65535 bytes.
        if payload_size + header_size > 65535:
            raise ValueError(
                "Original IPv4 packet is too large. "
                "Payload + header must not exceed 65535 bytes."
            )

        return payload_size, mtu, header_size

    def fragment_packet(self):
        try:
            payload_size, mtu, header_size = self.get_configuration()
        except ValueError as error:
            messagebox.showerror("Invalid Input", str(error))
            return

        self.fragments = []

        # Generate reproducible test data.
        self.original_payload = bytes(
            i % 256 for i in range(payload_size)
        )

        # Largest non-final fragment payload divisible by 8.
        max_fragment_payload = (
            (mtu - header_size) // 8
        ) * 8

        if max_fragment_payload < 8:
            messagebox.showerror(
                "Invalid MTU",
                "MTU is too small for IPv4 fragmentation."
            )
            return

        offset_bytes = 0
        fragment_number = 1

        while offset_bytes < payload_size:
            remaining = payload_size - offset_bytes

            if remaining > max_fragment_payload:
                fragment_size = max_fragment_payload
            else:
                fragment_size = remaining

            fragment_data = self.original_payload[
                offset_bytes:offset_bytes + fragment_size
            ]

            more_fragments = (
                offset_bytes + fragment_size < payload_size
            )

            fragment = {
                "number": fragment_number,
                "offset_bytes": offset_bytes,
                "offset": offset_bytes // 8,
                "data": fragment_data,
                "payload_size": fragment_size,
                "header_size": header_size,
                "total_length": header_size + fragment_size,
                "mf": 1 if more_fragments else 0,
                "identification": 1001
            }

            self.fragments.append(fragment)

            offset_bytes += fragment_size
            fragment_number += 1

        self.show_fragments(self.fragments)

        self.write_output(
            "FRAGMENTATION SUCCESSFUL\n\n"
            f"Original payload: {payload_size} bytes\n"
            f"MTU: {mtu} bytes\n"
            f"IPv4 header per fragment: {header_size} bytes\n"
            f"Maximum non-final fragment payload: "
            f"{max_fragment_payload} bytes\n"
            f"Number of fragments: {len(self.fragments)}\n\n"
            "MF = 1: More fragments follow\n"
            "MF = 0: This is the final fragment\n"
            "Offset is measured in 8-byte units."
        )

    def show_fragments(self, fragments):
        for item in self.table.get_children():
            self.table.delete(item)

        for fragment in fragments:
            self.table.insert(
                "",
                tk.END,
                values=(
                    fragment["number"],
                    fragment["offset"],
                    fragment["payload_size"],
                    fragment["header_size"],
                    fragment["total_length"],
                    fragment["mf"],
                    fragment["identification"]
                )
            )

    def reassemble_packet(self):
        if not self.fragments:
            messagebox.showwarning(
                "No Fragments",
                "Click Fragment Packet first."
            )
            return

        transmitted = self.fragments.copy()

        # Optional network loss simulation.
        dropped_fragment = None
        if self.drop_var.get():
            dropped_fragment = transmitted.pop()
        
        # Optional out-of-order delivery.
        if self.shuffle_var.get():
            random.shuffle(transmitted)

        received_order = [
            item["number"] for item in transmitted
        ]

        # Reassemble by byte offset, not arrival order.
        transmitted.sort(key=lambda item: item["offset_bytes"])

        expected_offset = 0
        reconstructed_parts = []
        valid = True

        for fragment in transmitted:
            if fragment["offset_bytes"] != expected_offset:
                valid = False
                break

            reconstructed_parts.append(fragment["data"])
            expected_offset += fragment["payload_size"]

        reconstructed_payload = b"".join(reconstructed_parts)

        # Confirm complete coverage and exact payload equality.
        success = (
            valid
            and expected_offset == len(self.original_payload)
            and reconstructed_payload == self.original_payload
            and bool(transmitted)
            and transmitted[-1]["mf"] == 0
        )

        result = (
            "TRANSMISSION AND REASSEMBLY\n\n"
            f"Fragments generated: {len(self.fragments)}\n"
            f"Fragments received: {len(transmitted)}\n"
            f"Arrival order: {received_order}\n"
        )

        if dropped_fragment:
            result += (
                f"Dropped fragment: {dropped_fragment['number']}\n"
            )

        result += (
            f"\nOriginal payload size: "
            f"{len(self.original_payload)} bytes\n"
            f"Reconstructed payload size: "
            f"{len(reconstructed_payload)} bytes\n"
        )

        if success:
            result += (
                "\nSTATUS: SUCCESS\n"
                "All fragments received and reassembled correctly.\n"
                "Original and reconstructed payloads match."
            )
        else:
            result += (
                "\nSTATUS: FAILED\n"
                "The packet is incomplete or invalid.\n"
                "Check for missing fragments or gaps in offsets."
            )

        self.write_output(result)

    def clear_all(self):
        self.fragments = []
        self.original_payload = b""

        for item in self.table.get_children():
            self.table.delete(item)

        self.write_output("Cleared. Enter new packet parameters.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PacketFragmentationSimulator(root)
    root.mainloop()