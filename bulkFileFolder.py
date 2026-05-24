import os
import threading
import subprocess
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime

class BulkRenameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk Rename Tool")
        self.root.geometry("1000x650")
        self.root.minsize(800, 550)
        
        # Variabel untuk menyimpan data
        self.current_folder = ""
        self.files_list = []
        self.rename_history = []
        self.current_progress = 0
        self.total_files = 0
        
        # Setup styling minimalis
        self.setup_styling()
        
        # Setup UI
        self.setup_ui()
        
        # Bind events
        self.bind_events()
        
        # Inisialisasi mode awal
        self.toggle_mode()
        
    def setup_styling(self):
        """Setup theme dan styling minimalis"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Warna minimalis
        self.bg_color = "#f5f5f5"
        self.card_bg = "#ffffff"
        self.primary_color = "#2196f3"
        self.primary_hover = "#1976d2"
        self.log_bg = "#1e1e1e"
        
        self.root.configure(bg=self.bg_color)
        
        # Style untuk tombol
        style.configure("Primary.TButton", 
                       background=self.primary_color,
                       foreground="white",
                       borderwidth=0,
                       padding=6)
        style.map("Primary.TButton",
                 background=[('active', self.primary_hover)])
        
        # Style untuk tombol secondary
        style.configure("Secondary.TButton", 
                       background="#6c757d",
                       foreground="white",
                       borderwidth=0,
                       padding=6)
        style.map("Secondary.TButton",
                 background=[('active', '#5a6268')])
        
        # Style untuk frame
        style.configure("Card.TFrame", 
                       background=self.card_bg,
                       relief="flat",
                       borderwidth=1)
        
        # Style untuk Treeview
        style.configure("Treeview",
                       background="white",
                       foreground="black",
                       rowheight=24,
                       fieldbackground="white",
                       font=('Segoe UI', 9))
        style.configure("Treeview.Heading",
                       font=('Segoe UI', 9, 'bold'))
        
    def setup_ui(self):
        """Setup semua komponen UI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel kiri dan kanan
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Panel Kiri
        left_frame = self.setup_left_panel(paned)
        paned.add(left_frame, weight=1)
        
        # Panel Kanan
        right_frame = self.setup_right_panel(paned)
        paned.add(right_frame, weight=1)
        
        # Panel Bawah (Log)
        self.setup_bottom_panel(main_frame)
        
        # Status bar
        self.setup_status_bar()
        
    def setup_left_panel(self, parent):
        """Panel kiri untuk folder dan daftar file"""
        left_frame = ttk.Frame(parent, style="Card.TFrame", padding="8")
        
        # Frame untuk tombol folder (horizontal)
        folder_buttons_frame = ttk.Frame(left_frame)
        folder_buttons_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Tombol pilih folder
        self.folder_btn = ttk.Button(folder_buttons_frame, text="📁 Pilih Folder", 
                                     command=self.select_folder, style="Primary.TButton")
        self.folder_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        
        # Tombol buka folder
        self.open_folder_btn = ttk.Button(folder_buttons_frame, text="📂 Buka Folder", 
                                         command=self.open_folder, style="Secondary.TButton")
        self.open_folder_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        
        # Info folder
        self.folder_path_var = tk.StringVar(value="Belum ada folder dipilih")
        folder_label = ttk.Label(left_frame, textvariable=self.folder_path_var, 
                                 wraplength=250, font=('Segoe UI', 8))
        folder_label.pack(fill=tk.X, pady=(0, 5))
        
        # Info jumlah file
        self.file_count_var = tk.StringVar(value="📄 Jumlah file: 0")
        count_label = ttk.Label(left_frame, textvariable=self.file_count_var, 
                                font=('Segoe UI', 9, 'bold'))
        count_label.pack(fill=tk.X, pady=(0, 8))
        
        # Tombol refresh
        self.refresh_btn = ttk.Button(left_frame, text="🔄 Refresh", 
                                     command=self.load_files)
        self.refresh_btn.pack(fill=tk.X, pady=(0, 8))
        
        # Treeview untuk daftar file
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame, columns=('name', 'size'), 
                                 show='tree headings', yscrollcommand=scrollbar.set,
                                 height=15)
        self.tree.heading('#0', text='No')
        self.tree.heading('name', text='Nama File')
        self.tree.heading('size', text='Ukuran')
        self.tree.column('#0', width=45)
        self.tree.column('name', width=220)
        self.tree.column('size', width=80)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        return left_frame
        
    def setup_right_panel(self, parent):
        """Panel kanan untuk konfigurasi rename"""
        right_frame = ttk.Frame(parent, style="Card.TFrame", padding="8")
        
        # Mode penamaan
        mode_frame = ttk.LabelFrame(right_frame, text="Mode Penamaan", padding="8")
        mode_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.rename_mode = tk.StringVar(value="find_replace")
        
        modes = [
            ("Find & Replace", "find_replace"),
            ("Ubah Nama + Ekstensi", "name_ext"),
            ("Ubah Nama (Ekstensi Asli)", "name_only"),
            ("Ganti Ekstensi Saja", "ext_only")
        ]
        
        for text, value in modes:
            rb = ttk.Radiobutton(mode_frame, text=text, variable=self.rename_mode, 
                                value=value, command=self.toggle_mode)
            rb.pack(anchor=tk.W, pady=2)
        
        # Container untuk input dinamis
        self.dynamic_frame = ttk.Frame(right_frame)
        self.dynamic_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Mode 1: Find & Replace
        self.find_replace_frame = ttk.Frame(self.dynamic_frame)
        ttk.Label(self.find_replace_frame, text="Find:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.find_text = ttk.Entry(self.find_replace_frame, width=25)
        self.find_text.grid(row=0, column=1, pady=3, padx=(5, 0))
        
        ttk.Label(self.find_replace_frame, text="Replace:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.replace_text = ttk.Entry(self.find_replace_frame, width=25)
        self.replace_text.grid(row=1, column=1, pady=3, padx=(5, 0))
        
        # Mode 2 & 3: Nama dasar
        self.name_frame = ttk.Frame(self.dynamic_frame)
        ttk.Label(self.name_frame, text="Nama Dasar:").pack(side=tk.LEFT)
        self.base_name = ttk.Entry(self.name_frame, width=25)
        self.base_name.pack(side=tk.LEFT, padx=(5, 0))
        
        # Ekstensi
        self.ext_frame = ttk.Frame(self.dynamic_frame)
        ttk.Label(self.ext_frame, text="Ekstensi:").pack(side=tk.LEFT)
        self.ext_combo = ttk.Combobox(self.ext_frame, values=['.txt', '.jpg', '.png', '.pdf', 
                                                              '.docx', '.xlsx', '.mp4', '.mp3', 
                                                              '.html', '.csv', '.json'], width=22)
        self.ext_combo.set('.txt')
        self.ext_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # Batas jumlah file
        limit_frame = ttk.LabelFrame(right_frame, text="Batas File", padding="5")
        limit_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.use_limit = tk.BooleanVar(value=False)
        self.limit_checkbox = ttk.Checkbutton(limit_frame, text="Batasi jumlah file", 
                                              variable=self.use_limit, 
                                              command=self.toggle_limit)
        self.limit_checkbox.pack(anchor=tk.W)
        
        self.limit_input_frame = ttk.Frame(limit_frame)
        self.limit_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(self.limit_input_frame, text="Jumlah:").pack(side=tk.LEFT)
        
        # Validasi angka
        vcmd = (self.root.register(self.validate_number), '%P')
        self.file_limit = tk.Spinbox(self.limit_input_frame, from_=1, to=9999, 
                                     width=20, validate='key', validatecommand=vcmd,
                                     state=tk.DISABLED)
        self.file_limit.pack(side=tk.LEFT, padx=(5, 0))
        self.file_limit.delete(0, tk.END)
        self.file_limit.insert(0, "1")
        
        # Kecualikan ekstensi
        exclude_frame = ttk.LabelFrame(right_frame, text="Kecualikan Ekstensi", padding="5")
        exclude_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.exclude_ext = ttk.Entry(exclude_frame, width=30)
        self.exclude_ext.pack(fill=tk.X)
        ttk.Label(exclude_frame, text="Contoh: .exe, .tmp, .log", 
                 font=('Segoe UI', 7, 'italic')).pack(anchor=tk.W, pady=(2, 0))
        
        # Tombol aksi
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.process_btn = ttk.Button(action_frame, text="🚀 Proses Rename", 
                                     command=self.start_rename, style="Primary.TButton")
        self.process_btn.pack(side=tk.LEFT, padx=(0, 8), fill=tk.X, expand=True)
        
        self.undo_btn = ttk.Button(action_frame, text="↩️ Undo", 
                                  command=self.undo_rename, state=tk.DISABLED)
        self.undo_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Progress bar
        self.progress = ttk.Progressbar(right_frame, mode='determinate')
        self.progress.pack(fill=tk.X)
        
        return right_frame
        
    def setup_bottom_panel(self, parent):
        """Panel bawah untuk log aktivitas"""
        log_frame = ttk.LabelFrame(parent, text="Log Aktivitas", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, 
                                                   bg=self.log_bg, 
                                                   fg="#00ff00",
                                                   font=('Consolas', 8))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags untuk warna
        self.log_text.tag_config("success", foreground="#4caf50")
        self.log_text.tag_config("error", foreground="#f44336")
        self.log_text.tag_config("info", foreground="#2196f3")
        self.log_text.tag_config("warning", foreground="#ff9800")
        
    def setup_status_bar(self):
        """Status bar di bagian bawah"""
        self.status_var = tk.StringVar(value="✓ Siap")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                               relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def bind_events(self):
        """Bind event handlers"""
        self.tree.bind('<Double-Button-1>', self.on_file_double_click)
        
    def open_folder(self):
        """Membuka folder yang sedang dipilih di file explorer"""
        if not self.current_folder:
            messagebox.showwarning("Peringatan", "Silakan pilih folder terlebih dahulu!")
            return
            
        if not os.path.exists(self.current_folder):
            messagebox.showerror("Error", "Folder tidak ditemukan!")
            return
            
        try:
            # Deteksi sistem operasi
            if platform.system() == "Windows":
                os.startfile(self.current_folder)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", self.current_folder])
            else:  # Linux
                subprocess.run(["xdg-open", self.current_folder])
                
            self.update_log(f"Membuka folder: {self.current_folder}", "info")
            self.status_var.set(f"✓ Membuka folder {self.current_folder}")
            
        except Exception as e:
            self.update_log(f"Gagal membuka folder: {str(e)}", "error")
            messagebox.showerror("Error", f"Gagal membuka folder:\n{str(e)}")
        
    def validate_number(self, value):
        """Validasi input angka untuk spinbox"""
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
            
    def toggle_limit(self):
        """Mengaktifkan/menonaktifkan input batas jumlah file"""
        if self.use_limit.get():
            self.file_limit.config(state=tk.NORMAL)
        else:
            self.file_limit.config(state=tk.DISABLED)
        
    def toggle_mode(self):
        """Menonaktifkan/mengaktifkan input sesuai mode yang dipilih"""
        # Sembunyikan semua frame
        for widget in self.find_replace_frame.winfo_children():
            widget.grid_remove()
        self.find_replace_frame.pack_forget()
        self.name_frame.pack_forget()
        self.ext_frame.pack_forget()
        
        mode = self.rename_mode.get()
        
        if mode == "find_replace":
            # Tampilkan kembali widget di find_replace_frame
            for widget in self.find_replace_frame.winfo_children():
                widget.grid()
            self.find_replace_frame.pack(fill=tk.X)
        elif mode == "name_ext":
            self.name_frame.pack(fill=tk.X, pady=(0, 5))
            self.ext_frame.pack(fill=tk.X)
        elif mode == "name_only":
            self.name_frame.pack(fill=tk.X)
        elif mode == "ext_only":
            self.ext_frame.pack(fill=tk.X)
            
    def select_folder(self):
        """Memilih folder sumber"""
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = folder
            self.folder_path_var.set(folder)
            self.load_files()
            self.update_log(f"Folder dipilih: {folder}", "info")
            
    def load_files(self):
        """Membaca dan menampilkan file dalam folder"""
        if not self.current_folder:
            messagebox.showwarning("Peringatan", "Silakan pilih folder terlebih dahulu!")
            return
            
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            files = [f for f in os.listdir(self.current_folder) 
                    if os.path.isfile(os.path.join(self.current_folder, f))]
            files.sort()
            
            self.files_list = files
            self.file_count_var.set(f"📄 Jumlah file: {len(files)}")
            
            for idx, file in enumerate(files, 1):
                file_path = os.path.join(self.current_folder, file)
                size = os.path.getsize(file_path)
                size_str = self.format_size(size)
                
                self.tree.insert('', 'end', text=str(idx), 
                               values=(file, size_str))
                               
            self.update_log(f"Daftar file di-refresh: {len(files)} file ditemukan", "info")
            self.status_var.set(f"✓ Loaded {len(files)} files")
            
        except Exception as e:
            self.update_log(f"Error loading files: {str(e)}", "error")
            
    def format_size(self, size):
        """Format ukuran file"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"
        
    def start_rename(self):
        """Memulai proses rename dalam thread terpisah"""
        if not self.current_folder:
            messagebox.showwarning("Peringatan", "Silakan pilih folder terlebih dahulu!")
            return
            
        if not self.files_list:
            messagebox.showwarning("Peringatan", "Tidak ada file dalam folder!")
            return
            
        # Validasi input
        if not self.validate_input():
            return
            
        # Konfirmasi
        if not messagebox.askyesno("Konfirmasi", "Yakin ingin merename file?"):
            return
            
        # Disable tombol proses selama rename
        self.process_btn.config(state=tk.DISABLED)
        self.undo_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        # Start rename di thread terpisah
        thread = threading.Thread(target=self.process_rename)
        thread.daemon = True
        thread.start()
        
    def validate_input(self):
        """Validasi input sebelum proses"""
        mode = self.rename_mode.get()
        
        if mode == "find_replace":
            if not self.find_text.get().strip():
                messagebox.showwarning("Peringatan", "Find Text tidak boleh kosong!")
                return False
        elif mode in ["name_ext", "name_only"]:
            if not self.base_name.get().strip():
                messagebox.showwarning("Peringatan", "Nama Dasar tidak boleh kosong!")
                return False
                
        # Validasi batas jumlah file
        if self.use_limit.get():
            try:
                limit = int(self.file_limit.get())
                if limit <= 0:
                    messagebox.showwarning("Peringatan", "Jumlah file harus lebih dari 0!")
                    return False
            except ValueError:
                messagebox.showwarning("Peringatan", "Jumlah file harus berupa angka!")
                return False
                
        return True
        
    def process_rename(self):
        """Proses rename file (dijalankan di thread)"""
        self.rename_history = []
        mode = self.rename_mode.get()
        
        # Dapatkan daftar ekstensi yang dikecualikan
        exclude_exts = [ext.strip().lower() for ext in self.exclude_ext.get().split(',') if ext.strip()]
        
        # Dapatkan batas file
        if self.use_limit.get():
            try:
                limit = int(self.file_limit.get())
            except ValueError:
                limit = None
        else:
            limit = None
            
        files_to_process = self.files_list[:limit] if limit else self.files_list
        self.total_files = len(files_to_process)
        
        if self.total_files == 0:
            self.root.after(0, lambda: self.update_log("Tidak ada file yang diproses!", "warning"))
            self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL))
            return
        
        success_count = 0
        error_count = 0
        
        self.update_log(f"Memulai proses rename {self.total_files} file...", "info")
        
        for idx, old_name in enumerate(files_to_process, 1):
            old_path = os.path.join(self.current_folder, old_name)
            name_without_ext, ext = os.path.splitext(old_name)
            
            # Cek ekstensi yang dikecualikan
            if ext.lower() in exclude_exts:
                self.update_log(f"Skip {old_name}: ekstensi {ext} dikecualikan", "warning")
                self.update_progress(idx)
                continue
                
            try:
                # Tentukan nama baru berdasarkan mode
                if mode == "find_replace":
                    find = self.find_text.get()
                    replace = self.replace_text.get()
                    new_name_without_ext = name_without_ext.replace(find, replace)
                    new_name = new_name_without_ext + ext
                    
                elif mode == "name_ext":
                    new_ext = self.ext_combo.get()
                    new_name = f"{self.base_name.get()}{idx}{new_ext}"
                    
                elif mode == "name_only":
                    new_name = f"{self.base_name.get()}{idx}{ext}"
                    
                elif mode == "ext_only":
                    new_ext = self.ext_combo.get()
                    new_name = name_without_ext + new_ext
                else:
                    continue
                    
                new_path = os.path.join(self.current_folder, new_name)
                
                # Cek apakah file sudah ada
                if os.path.exists(new_path):
                    self.update_log(f"Error: {new_name} sudah ada!", "error")
                    error_count += 1
                    continue
                    
                # Rename file
                os.rename(old_path, new_path)
                
                # Simpan ke history
                self.rename_history.append({
                    'old_path': old_path,
                    'new_path': new_path,
                    'old_name': old_name,
                    'new_name': new_name
                })
                
                self.update_log(f"✓ {old_name} → {new_name}", "success")
                success_count += 1
                
            except PermissionError:
                self.update_log(f"✗ Tidak ada izin untuk {old_name}", "error")
                error_count += 1
            except OSError as e:
                self.update_log(f"✗ {str(e)}", "error")
                error_count += 1
            except Exception as e:
                self.update_log(f"✗ Error: {str(e)}", "error")
                error_count += 1
                
            # Update progress
            self.update_progress(idx)
            
        # Selesai proses
        self.root.after(0, self.on_rename_complete, success_count, error_count)
        
    def update_progress(self, current):
        """Update progress bar"""
        progress_value = (current / self.total_files) * 100
        self.root.after(0, lambda: self.progress.configure(value=progress_value))
        self.root.after(0, lambda: self.status_var.set(f"Processing {current}/{self.total_files}..."))
        
    def on_rename_complete(self, success_count, error_count):
        """Callback setelah rename selesai"""
        self.process_btn.config(state=tk.NORMAL)
        if self.rename_history:
            self.undo_btn.config(state=tk.NORMAL)
            
        self.update_log(f"✓ Selesai! Berhasil: {success_count}, Gagal: {error_count}", "info")
        self.status_var.set(f"✓ Selesai - Berhasil: {success_count}, Gagal: {error_count}")
        
        # Refresh daftar file
        self.load_files()
        
    def undo_rename(self):
        """Mengembalikan semua perubahan ke nama semula"""
        if not self.rename_history:
            messagebox.showinfo("Info", "Tidak ada history rename")
            return
            
        if not messagebox.askyesno("Konfirmasi", "Batalkan semua perubahan?"):
            return
            
        self.process_btn.config(state=tk.DISABLED)
        self.undo_btn.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self.process_undo)
        thread.daemon = True
        thread.start()
        
    def process_undo(self):
        """Proses undo rename"""
        success_count = 0
        error_count = 0
        
        total_undo = len(self.rename_history)
        self.update_log(f"Memulai undo untuk {total_undo} file...", "info")
        
        for idx, history in enumerate(reversed(self.rename_history), 1):
            try:
                if os.path.exists(history['new_path']):
                    os.rename(history['new_path'], history['old_path'])
                    self.update_log(f"✓ Undo: {history['new_name']} → {history['old_name']}", "success")
                    success_count += 1
                else:
                    self.update_log(f"✗ File {history['new_name']} tidak ditemukan", "error")
                    error_count += 1
            except Exception as e:
                self.update_log(f"✗ Error undo: {str(e)}", "error")
                error_count += 1
                
            # Update progress undo
            progress_value = (idx / total_undo) * 100
            self.root.after(0, lambda v=progress_value: self.progress.configure(value=v))
            
        self.root.after(0, lambda: self.on_undo_complete(success_count, error_count))
        
    def on_undo_complete(self, success_count, error_count):
        """Callback setelah undo selesai"""
        self.process_btn.config(state=tk.NORMAL)
        self.undo_btn.config(state=tk.DISABLED)
        self.rename_history = []
        
        self.update_log(f"✓ Undo selesai! Berhasil: {success_count}, Gagal: {error_count}", "info")
        self.status_var.set(f"✓ Undo - Berhasil: {success_count}, Gagal: {error_count}")
        
        # Refresh daftar file
        self.load_files()
        
        # Reset progress bar
        self.progress['value'] = 0
        
    def update_log(self, message, level="info"):
        """Update log dengan warna tertentu"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        def _update():
            self.log_text.insert(tk.END, log_message, level)
            self.log_text.see(tk.END)
            
        self.root.after(0, _update)
        
    def on_file_double_click(self, event):
        """Menampilkan nama lengkap file saat double-click"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            filename = item['values'][0]
            full_path = os.path.join(self.current_folder, filename)
            messagebox.showinfo("Detail File", f"📄 {filename}\n\n📁 {full_path}")

def main():
    root = tk.Tk()
    app = BulkRenameApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
