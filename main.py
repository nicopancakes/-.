import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import threading
from datetime import datetime
import shutil

class FolderHawk:
    def __init__(self, root):
        self.root = root
        self.root.title("フォルダーホーク github.com/nicopancakes/-.")
        self.root.geometry("1180x760")
        
        try:
            self.root.iconbitmap(default="")
        except:
            pass
        
        self.current_dir = os.getcwd()
        self.history = [self.current_dir]  
        self.items = []
        self.scanning = False
        self.stop_event = threading.Event()
        
        self.create_ui()
    
    def create_ui(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=12, pady=10)
        
        self.back_btn = ttk.Button(top_frame, text="← Back", command=self.go_back, state='disabled')
        self.back_btn.pack(side=tk.LEFT)
        
        ttk.Button(top_frame, text="Choose Folder", command=self.choose_folder).pack(side=tk.LEFT, padx=5)
        
        self.start_btn = ttk.Button(top_frame, text="Start Scan", command=self.start_scan)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(top_frame, text="Stop Scan", command=self.stop_scan, state='disabled')
        self.stop_btn.pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="Current Folder:").pack(side=tk.LEFT, padx=(20,5))
        self.dir_label = ttk.Label(top_frame, text=self.current_dir, font=("Segoe UI", 10))
        self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(top_frame, text="Refresh", command=self.refresh).pack(side=tk.RIGHT)
        
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill=tk.X, padx=12, pady=8)
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        self.status_label = ttk.Label(progress_frame, text="Ready - Select a folder and click Start Scan", font=("Segoe UI", 10))
        self.status_label.pack(fill=tk.X, padx=5)
        
        log_frame = ttk.LabelFrame(self.root, text="Scan Log", padding=6)
        log_frame.pack(fill=tk.X, padx=12, pady=8)
        self.log_text = tk.Text(log_frame, height=7, state='disabled', font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(fill=tk.X, padx=12, pady=8)
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self.filter_entry.bind("<KeyRelease>", self.filter_items)
        
        columns = ("Name", "Type", "Size", "Modified", "Full Path")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        
        self.tree.heading("Name", text="Name")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Size", text="Size")
        self.tree.heading("Modified", text="Last Modified")
        self.tree.heading("Full Path", text="Full Location")
        
        self.tree.column("Name", width=360)
        self.tree.column("Type", width=90)
        self.tree.column("Size", width=130)
        self.tree.column("Modified", width=160)
        self.tree.column("Full Path", width=420)
        
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.open_selected)
        self.context_menu.add_command(label="Show in Explorer / Finder", command=self.show_in_explorer)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Scan Inside This Folder", command=self.scan_inside_folder)
        self.context_menu.add_command(label="Delete File/Folder", command=self.delete_selected)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def update_back_button(self):
        self.back_btn.config(state='normal' if len(self.history) > 1 else 'disabled')
    
    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()  
            self.current_dir = self.history[-1]
            self.dir_label.config(text=self.current_dir)
            self.root.title("フォルダーホーク github.com/nicopancakes/-.")
            self.refresh()
    
    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.current_dir, title="Select Folder to Scan")
        if folder:
            self.current_dir = os.path.abspath(folder)
            self.history.append(self.current_dir)
            self.dir_label.config(text=self.current_dir)
            self.root.title("フォルダーホーク  github.com/nicopancakes/-.")
            self.update_back_button()
            self.log(f"Selected folder: {self.current_dir}")
    
    def scan_inside_folder(self):
        selection = self.tree.selection()
        if not selection:
            return
        full_path = self.tree.item(selection[0], "values")[4]
        
        if not os.path.isdir(full_path):
            messagebox.showinfo("Info", "Selected item is not a folder.")
            return
        
        self.current_dir = full_path
        self.history.append(self.current_dir)
        self.dir_label.config(text=self.current_dir)
        self.root.title("フォルダーホーク github.com/nicopancakes/-.")
        self.update_back_button()
        self.log(f"Navigated into: {full_path}")
        self.start_scan()
  
    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        full_path = values[4]
        name = values[0].split(" ", 1)[-1]  
        
        if not os.path.exists(full_path):
            messagebox.showerror("Error", "This item no longer exists.")
            return
      
        if not messagebox.askyesno("WARNING (1/2)", 
            f"You are about to DELETE:\n\n{full_path}\n\n"
            f"This action cannot be undone.\n\nContinue?", icon='warning'):
            return
      
        if not messagebox.askyesno("WARNING! (2/2) ", 
            f"Last WARNING!\n\nYou are about to permanently delete:\n\n{name}\n\n"
            f"Are you absolutely sure?", icon='warning'):
            return
        confirm = tk.simpledialog.askstring("Final Confirmation", "Type DELETE to proceed:")
        if confirm != "DELETE":
            messagebox.showinfo("Cancelled", "Deletion cancelled.")
            return
      
        try:
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
                self.log(f"Folder deleted: {name}")
            else:
                os.remove(full_path)
                self.log(f"File deleted: {name}")
            
            messagebox.showinfo("Success", f"Successfully deleted:\n{name}")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Delete Error", f"Could not delete:\n{str(e)}")
    
    def get_emoji(self, name, is_folder):
        if is_folder:
            return "📂"
        ext = os.path.splitext(name.lower())[1]
        video_exts = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg'}
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.heic'}
        zip_exts = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}
        
        if ext in video_exts:
            return "🎥"
        elif ext in image_exts:
            return "📷"
        elif ext in zip_exts:
            return "🗃"
        else:
            return "❓"
    
    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()
    
    def start_scan(self):
        if not self.current_dir or not os.path.exists(self.current_dir):
            messagebox.showwarning("Warning", "Please select a valid folder first.")
            return
        if self.scanning:
            return
        
        self.scanning = True
        self.stop_event.clear()
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.tree.delete(*self.tree.get_children())
        self.items.clear()
        
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        
        self.progress['value'] = 0
        self.status_label.config(text="Scanning in progress...")
        
        threading.Thread(target=self._scan_worker, daemon=True).start()
    
    def stop_scan(self):
        if self.scanning:
            self.stop_event.set()
            self.log("Stop requested by user...")
    
    def _scan_worker(self):
        try:
            entries = os.listdir(self.current_dir)
            total = len(entries)
            processed = 0
            
            self.log(f"Starting scan: {self.current_dir}")
            
            for entry in entries:
                if self.stop_event.is_set():
                    self.root.after(0, lambda: self.status_label.config(text="Scan stopped."))
                    break
                
                full_path = os.path.join(self.current_dir, entry)
                
                try:
                    mtime = os.path.getmtime(full_path)
                    mod_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                    
                    if os.path.isdir(full_path):
                        self.log(f"Calculating size of folder: {entry}")
                        size = self.get_folder_size(full_path)
                        item_type = 'Folder'
                        emoji = "📂"
                    else:
                        size = os.path.getsize(full_path)
                        item_type = 'File'
                        emoji = self.get_emoji(entry, False)
                    
                    display_name = f"{emoji} {entry}"
                    
                    self.items.append({
                        'name': entry,
                        'display_name': display_name,
                        'type': item_type,
                        'size': size,
                        'size_str': self.format_size(size),
                        'modified': mod_str,
                        'path': os.path.abspath(full_path),
                        'rel_path': entry
                    })
                    
                except Exception as e:
                    self.log(f"Skipped {entry} - {e}")
                
                processed += 1
                progress = int((processed / total) * 100)
                self.root.after(0, lambda p=progress, c=processed, t=total: 
                    (self.progress.configure(value=p),
                     self.status_label.config(text=f"Processed {c} of {t} items")))
            
            if not self.stop_event.is_set():
                self.items.sort(key=lambda x: x['size'], reverse=True)
                self.root.after(0, self._populate_tree)
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, self._scan_finished)
    
    def _populate_tree(self):
        for item in self.items:
            self.tree.insert("", "end", values=(
                item['display_name'],
                item['type'],
                item['size_str'],
                item['modified'],
                item['path']
            ))
        self.status_label.config(text=f"Scan complete — {len(self.items)} items")
        self.log("Scan completed successfully.")
    
    def _scan_finished(self):
        self.scanning = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress['value'] = 100 if not self.stop_event.is_set() else self.progress['value']
    
    def get_folder_size(self, folder_path):
        total = 0
        try:
            for dirpath, _, filenames in os.walk(folder_path):
                if self.stop_event.is_set():
                    return total
                for f in filenames:
                    try:
                        total += os.path.getsize(os.path.join(dirpath, f))
                    except:
                        pass
        except:
            pass
        return total
    
    def format_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def show_context_menu(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        is_folder = values[1] == 'Folder'
        
        if is_folder:
            self.context_menu.entryconfig("Scan Inside This Folder", state='normal')
        else:
            self.context_menu.entryconfig("Scan Inside This Folder", state='disabled')
        
        self.context_menu.post(event.x_root, event.y_root)
    
    def open_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        full_path = self.tree.item(selection[0], "values")[4]
        self._open_path(full_path)
    
    def show_in_explorer(self):
        selection = self.tree.selection()
        if not selection:
            return
        full_path = self.tree.item(selection[0], "values")[4]
        try:
            if os.name == 'nt':
                subprocess.call(['explorer', '/select,', full_path])
            else:
                path = os.path.dirname(full_path) if os.path.isfile(full_path) else full_path
                opener = 'open' if 'darwin' in os.sys.platform else 'xdg-open'
                subprocess.call([opener, path])
        except:
            messagebox.showerror("Error", "Could not open location in file explorer.")
    
    def _open_path(self, path):
        if not os.path.exists(path):
            messagebox.showerror("Error", f"Path no longer exists:\n{path}")
            return
        try:
            if os.name == 'nt':
                os.startfile(path)
            else:
                opener = 'open' if 'darwin' in os.sys.platform else 'xdg-open'
                subprocess.call([opener, path])
            self.log(f"Opened: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open:\n{path}\n\nError: {e}")
    
    def filter_items(self, event=None):
        filter_text = self.filter_var.get().lower().strip()
        self.tree.delete(*self.tree.get_children())
        for item in self.items:
            if (not filter_text or 
                filter_text in item['name'].lower() or 
                filter_text in item['path'].lower()):
                self.tree.insert("", "end", values=(
                    item['display_name'],
                    item['type'],
                    item['size_str'],
                    item['modified'],
                    item['path']
                ))
    
    def refresh(self):
        if self.scanning:
            messagebox.showinfo("Info", "Please stop the current scan first.")
            return
        self.start_scan()

if __name__ == "__main__":
    root = tk.Tk()
    app = FolderHawk(root)
    root.mainloop()
