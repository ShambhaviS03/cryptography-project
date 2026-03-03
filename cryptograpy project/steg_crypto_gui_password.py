import tkinter as tk
from tkinter import filedialog, messagebox
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from PIL import Image
import base64

# ---------------- Key Derivation ----------------

def derive_key(password: str, salt: bytes):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

SALT = b'static_salt_12345'

# ---------------- Encryption ----------------

def encrypt_message(message, password):
    key = derive_key(password, SALT)
    return Fernet(key).encrypt(message.encode())

def decrypt_message(ciphertext, password):
    key = derive_key(password, SALT)
    return Fernet(key).decrypt(ciphertext).decode()

# ---------------- Binary Helpers ----------------

def to_binary(data):
    return ''.join(format(byte, '08b') for byte in data)

def from_binary(binary_data):
    bytes_list = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    return bytes(int(b, 2) for b in bytes_list)

# ---------------- Steganography ----------------

def hide_data(image_path, binary_data, output_path):
    img = Image.open(image_path).convert("RGB")
    pixels = img.load()

    binary_data = format(len(binary_data), '032b') + binary_data
    idx = 0

    for y in range(img.height):
        for x in range(img.width):
            if idx >= len(binary_data):
                img.save(output_path)
                return

            r, g, b = pixels[x, y]

            r = (r & ~1) | int(binary_data[idx]); idx += 1
            if idx < len(binary_data):
                g = (g & ~1) | int(binary_data[idx]); idx += 1
            if idx < len(binary_data):
                b = (b & ~1) | int(binary_data[idx]); idx += 1

            pixels[x, y] = (r, g, b)

    img.save(output_path)

def extract_data(image_path):
    img = Image.open(image_path).convert("RGB")
    pixels = img.load()

    bits = ""

    for y in range(img.height):
        for x in range(img.width):
            r, g, b = pixels[x, y]
            bits += str(r & 1) + str(g & 1) + str(b & 1)

    length = int(bits[:32], 2)
    return bits[32:32 + length]

# ---------------- GUI Logic ----------------

def select_image():
    path = filedialog.askopenfilename(filetypes=[("PNG Images", "*.png")])
    image_path.set(path)

def hide_message():
    try:
        msg = message_box.get("1.0", tk.END).strip()
        password = password_entry.get()
        img_path = image_path.get()

        if not msg or not password or not img_path:
            messagebox.showerror("Error", "Fill all fields")
            return

        ciphertext = encrypt_message(msg, password)
        binary_data = to_binary(ciphertext)

        output_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                  filetypes=[("PNG Images", "*.png")])
        if output_path:
            hide_data(img_path, binary_data, output_path)
            messagebox.showinfo("Success", "Message Hidden!")

    except Exception as e:
        messagebox.showerror("Error", str(e))

def extract_message():
    try:
        password = password_entry.get()
        img_path = image_path.get()

        if not password or not img_path:
            messagebox.showerror("Error", "Password & image required")
            return

        binary_data = extract_data(img_path)
        ciphertext = from_binary(binary_data)
        message = decrypt_message(ciphertext, password)

        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, message)

    except:
        messagebox.showerror("Error", "Wrong password / invalid image")

# ---------------- Fancy Effects ----------------

def hover_effect(widget, color_on, color_off):
    widget.bind("<Enter>", lambda e: widget.config(bg=color_on))
    widget.bind("<Leave>", lambda e: widget.config(bg=color_off))

def animate_title():
    colors = ["#ff4d6d", "#ff8fab", "#c77dff", "#7b2cbf"]
    current = title_label.cget("fg")
    next_color = colors[(colors.index(current) + 1) % len(colors)] if current in colors else colors[0]
    title_label.config(fg=next_color)
    root.after(400, animate_title)

# ---------------- UI ----------------

root = tk.Tk()
root.title("Steganography + Cryptography")
root.geometry("620x540")
root.configure(bg="#0f172a")

image_path = tk.StringVar()

title_label = tk.Label(root,
                       text="🔐 Steganography + Cryptography",
                       font=("Helvetica", 20, "bold"),
                       fg="#ff4d6d",
                       bg="#0f172a")
title_label.pack(pady=15)

animate_title()

main_frame = tk.Frame(root, bg="#111827", padx=25, pady=25)
main_frame.pack(padx=20, pady=10, fill="both", expand=True)

label_style = {"fg": "white", "bg": "#111827", "font": ("Helvetica", 11)}

tk.Label(main_frame, text="Password", **label_style).pack(anchor="w")
password_entry = tk.Entry(main_frame, width=45, show="*", font=("Helvetica", 11))
password_entry.pack(pady=5)

tk.Label(main_frame, text="Secret Message", **label_style).pack(anchor="w")
message_box = tk.Text(main_frame, height=4, width=55, font=("Helvetica", 10))
message_box.pack(pady=5)

select_btn = tk.Button(main_frame, text="Select PNG Image",
                       command=select_image,
                       bg="#2563eb", fg="white",
                       font=("Helvetica", 10), relief="flat", padx=10)
select_btn.pack(pady=8)

tk.Label(main_frame, textvariable=image_path, fg="lightgray",
         bg="#111827", wraplength=500).pack()

btn_frame = tk.Frame(main_frame, bg="#111827")
btn_frame.pack(pady=12)

hide_btn = tk.Button(btn_frame, text="Hide Message",
                     command=hide_message,
                     bg="#22c55e", fg="black",
                     font=("Helvetica", 10, "bold"),
                     relief="flat", padx=20, pady=5)
hide_btn.grid(row=0, column=0, padx=10)

extract_btn = tk.Button(btn_frame, text="Extract Message",
                        command=extract_message,
                        bg="#f59e0b", fg="black",
                        font=("Helvetica", 10, "bold"),
                        relief="flat", padx=20, pady=5)
extract_btn.grid(row=0, column=1, padx=10)

hover_effect(hide_btn, "#4ade80", "#22c55e")
hover_effect(extract_btn, "#fbbf24", "#f59e0b")

tk.Label(main_frame, text="Extracted Message", **label_style).pack(anchor="w")
output_box = tk.Text(main_frame, height=4, width=55, font=("Helvetica", 10))
output_box.pack(pady=5)

root.mainloop()