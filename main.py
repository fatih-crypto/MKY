import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import math

from calculations import calculate_angle, calculate_joint_angle
from file_manager import (load_labels, save_labels, export_to_csv, 
                          load_images_from_folder, save_session_info, load_session_info)
from drawing import DrawingManager, LabelRenderer, EditManager


class NorbergOlsenLabelingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Norberg-Olsen Labeling Tool")
        self.root.geometry("1280x800")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.bg_color = "#f5f5f7"
        self.accent_color = "#0078d7"
        self.highlight_color = "#ff6b00"
        self.text_color = "#333333"
        self.canvas_bg = "#ffffff"
        self.toolbar_bg = "#e8e8e8"
        self.status_bar_bg = "#e0e0e0"
        
        self.style.configure('TButton', 
                            font=('Segoe UI', 9), 
                            background=self.bg_color, 
                            foreground=self.text_color,
                            padding=4)
        
        self.style.configure('TLabel', 
                            font=('Segoe UI', 9), 
                            background=self.bg_color, 
                            foreground=self.text_color)
        
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('Canvas.TFrame', background=self.canvas_bg)
        self.style.configure('Toolbar.TFrame', background=self.toolbar_bg)
        self.style.configure('StatusBar.TFrame', background=self.status_bar_bg)
        
        self.style.configure('Tool.TButton', 
                            padding=6,
                            font=('Segoe UI', 9, 'bold'))
        
        self.style.map('TButton',
                       foreground=[('active', '#ffffff')],
                       background=[('active', self.accent_color)])
        
        self.current_folder = None
        self.image_files = []
        self.current_image_index = -1
        self.current_image = None
        self.pil_image = None
        self.tk_image = None
        self.labels = {}
        self.current_labels = {}
        self.drawing_mode = None
        self.tooltips = {}
        
        self.selected_item = None
        self.selected_tag = None
        self.moving = False
        self.last_x = 0
        self.last_y = 0
        
        self.resize_mode = False 
        self.resize_type = None
        
        self.zoom_factor = 1.0
        self.zoom_min = 0.1
        self.zoom_max = 5.0
        
        self.show_labels = True
        self.show_label_text = True
        
        self.last_folder_path = None
        
        self.context_menu = tk.Menu(root, tearoff=0, bg=self.bg_color, fg=self.text_color,
                                   activebackground=self.accent_color, activeforeground='white',
                                   font=('Segoe UI', 9))
        self.context_menu.add_command(label="Move", command=self.start_move_mode)
        self.context_menu.add_command(label="Edit", command=self.start_edit_mode)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        
        self.create_menu()
        self.create_toolbar()
        self.create_canvas()
        self.create_status_bar()
        
        self.drawing_manager = None
        self.label_renderer = None
        self.edit_manager = None
        
        self.root.bind("<Left>", lambda e: self.prev_image())
        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Escape>", lambda e: self.cancel_drawing())
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<Control-s>", lambda e: self.save_labels_handler())
        self.root.bind("<Control-o>", lambda e: self.open_folder())
        self.root.bind("<Control-z>", lambda e: self.clear_labels())
        
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<Button-4>", self.zoom)
        self.canvas.bind("<Button-5>", self.zoom)
        
        self.root.configure(bg=self.bg_color)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)
        
        self.check_last_session()
    
    def create_tooltip(self, widget, text):
        tooltip = tk.Label(self.root, text=text, bg="#ffffaa", fg="#000000",
                         relief="solid", borderwidth=1, font=("Segoe UI", 8))
        
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            tooltip.lift()
            tooltip.place(x=x, y=y)
            
        def leave(event):
            tooltip.place_forget()
            
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
        
        self.tooltips[widget] = tooltip
    
    def check_last_session(self):
        config = load_session_info()
        
        if config and "last_folder" in config and os.path.exists(config["last_folder"]):
            self.current_folder = config["last_folder"]
            self.image_files = load_images_from_folder(self.current_folder)
            self.labels = load_labels(self.current_folder)
            
            if self.image_files:
                if "last_image_index" in config and 0 <= config["last_image_index"] < len(self.image_files):
                    self.current_image_index = config["last_image_index"]
                else:
                    self.current_image_index = 0
                
                self.display_image()
    
    def create_menu(self):
        menubar = tk.Menu(self.root, bg=self.bg_color, fg=self.text_color,
                         activebackground=self.accent_color, activeforeground='white',
                         font=('Segoe UI', 9))
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.bg_color, fg=self.text_color,
                           activebackground=self.accent_color, activeforeground='white',
                           font=('Segoe UI', 9))
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Folder (Ctrl+O)", command=self.open_folder)
        file_menu.add_command(label="Save Labels (Ctrl+S)", command=self.save_labels_handler)
        file_menu.add_separator()
        file_menu.add_command(label="Export to CSV", command=self.export_to_csv_handler)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        view_menu = tk.Menu(menubar, tearoff=0, bg=self.bg_color, fg=self.text_color,
                           activebackground=self.accent_color, activeforeground='white',
                           font=('Segoe UI', 9))
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Labels", command=self.toggle_labels)
        view_menu.add_command(label="Toggle Label Text", command=self.toggle_label_text)
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", command=self.zoom_out)
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom)
        
        tools_menu = tk.Menu(menubar, tearoff=0, bg=self.bg_color, fg=self.text_color,
                            activebackground=self.accent_color, activeforeground='white',
                            font=('Segoe UI', 9))
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Calculate Angles", command=self.calculate_hip_angles)
        tools_menu.add_command(label="Clear All Labels (Ctrl+Z)", command=self.clear_labels)
        
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.bg_color, fg=self.text_color,
                           activebackground=self.accent_color, activeforeground='white',
                           font=('Segoe UI', 9))
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Instructions", command=self.show_instructions)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_toolbar(self):
        toolbar_frame = ttk.Frame(self.root, style='Toolbar.TFrame', padding=(5, 5))
        toolbar_frame.grid(row=0, column=0, sticky="ew")
        
        folder_btn = ttk.Button(toolbar_frame, text="📁 Open Folder", 
                               command=self.open_folder, style='Tool.TButton')
        folder_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(folder_btn, "Open a folder containing X-ray images (Ctrl+O)")
        
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        self.rectangle_btn = ttk.Button(toolbar_frame, text="▭ Rectangle", 
                                       command=self.draw_rectangle_mode, style='Tool.TButton')
        self.rectangle_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(self.rectangle_btn, "Draw pelvis rectangle (R)")
        
        self.left_keypoint_btn = ttk.Button(toolbar_frame, text="⦿ Left Point", 
                                           command=self.draw_left_keypoint_mode, style='Tool.TButton')
        self.left_keypoint_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(self.left_keypoint_btn, "Mark left acetabulum point (L)")
        
        self.right_keypoint_btn = ttk.Button(toolbar_frame, text="⦿ Right Point", 
                                            command=self.draw_right_keypoint_mode, style='Tool.TButton')
        self.right_keypoint_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(self.right_keypoint_btn, "Mark right acetabulum point (R)")
        
        self.left_circle_btn = ttk.Button(toolbar_frame, text="◯ Left Circle", 
                                         command=self.draw_left_circle_mode, style='Tool.TButton')
        self.left_circle_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(self.left_circle_btn, "Draw left femur head circle (C)")
        
        self.right_circle_btn = ttk.Button(toolbar_frame, text="◯ Right Circle", 
                                          command=self.draw_right_circle_mode, style='Tool.TButton')
        self.right_circle_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(self.right_circle_btn, "Draw right femur head circle (C)")
        
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        calculate_btn = ttk.Button(toolbar_frame, text="📐 Calculate", 
                                  command=self.calculate_hip_angles, style='Tool.TButton')
        calculate_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(calculate_btn, "Calculate Norberg and Joint angles")
        
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        clear_btn = ttk.Button(toolbar_frame, text="🗑️ Clear", 
                              command=self.clear_labels, style='Tool.TButton')
        clear_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(clear_btn, "Clear all labels for current image (Ctrl+Z)")
        
        save_btn = ttk.Button(toolbar_frame, text="💾 Save", 
                             command=self.save_labels_handler, style='Tool.TButton')
        save_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(save_btn, "Save all labels to JSON file (Ctrl+S)")
        
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        prev_btn = ttk.Button(toolbar_frame, text="◀ Previous", 
                             command=self.prev_image, style='Tool.TButton')
        prev_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(prev_btn, "Previous image (Left Arrow)")
        
        next_btn = ttk.Button(toolbar_frame, text="Next ▶", 
                             command=self.next_image, style='Tool.TButton')
        next_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(next_btn, "Next image (Right Arrow)")
        
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        zoom_in_btn = ttk.Button(toolbar_frame, text="🔍+", 
                                command=self.zoom_in, style='Tool.TButton')
        zoom_in_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(zoom_in_btn, "Zoom in (Mouse wheel up)")
        
        zoom_out_btn = ttk.Button(toolbar_frame, text="🔍-", 
                                 command=self.zoom_out, style='Tool.TButton')
        zoom_out_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(zoom_out_btn, "Zoom out (Mouse wheel down)")
        
        reset_zoom_btn = ttk.Button(toolbar_frame, text="1:1", 
                                    command=self.reset_zoom, style='Tool.TButton')
        reset_zoom_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(reset_zoom_btn, "Reset zoom to 100%")
    
    def create_canvas(self):
        canvas_frame = ttk.Frame(self.root, style='Canvas.TFrame')
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.canvas_bg, 
                               highlightthickness=1, highlightbackground=self.accent_color)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
    
    def create_status_bar(self):
        status_frame = ttk.Frame(self.root, style='StatusBar.TFrame', padding=(5, 3))
        status_frame.grid(row=2, column=0, sticky="ew")
        
        self.status_text = tk.StringVar(value="Ready. Open a folder to begin.")
        status_label = ttk.Label(status_frame, textvariable=self.status_text, 
                                style='TLabel', font=('Segoe UI', 9))
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.zoom_text = tk.StringVar(value="Zoom: 100%")
        zoom_label = ttk.Label(status_frame, textvariable=self.zoom_text, 
                              style='TLabel', font=('Segoe UI', 9))
        zoom_label.pack(side=tk.RIGHT, padx=(10, 0))
    
    def initialize_managers(self):
        self.drawing_manager = DrawingManager(self.canvas, self.zoom_factor, self.current_labels)
        self.label_renderer = LabelRenderer(self.canvas, self.zoom_factor, self.show_labels, self.show_label_text)
        self.edit_manager = EditManager(self.canvas, self.zoom_factor)
    
    def open_folder(self):
        initial_dir = self.last_folder_path if self.last_folder_path else os.path.expanduser("~")
        
        folder_path = filedialog.askdirectory(title="Select Folder with X-ray Images",
                                              initialdir=initial_dir)
        
        if folder_path:
            self.current_folder = folder_path
            self.last_folder_path = folder_path
            self.image_files = load_images_from_folder(folder_path)
            self.labels = load_labels(folder_path)
            
            if self.image_files:
                self.current_image_index = 0
                self.display_image()
            else:
                messagebox.showwarning("No Images", "No image files found in the selected folder.")
    
    def display_image(self):
        if not self.image_files or self.current_image_index < 0:
            return
        
        image_path = self.image_files[self.current_image_index]
        
        try:
            self.pil_image = Image.open(image_path)
            
            img_width = int(self.pil_image.width * self.zoom_factor)
            img_height = int(self.pil_image.height * self.zoom_factor)
            
            resized_image = self.pil_image.resize((img_width, img_height), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(resized_image)
            
            self.canvas.delete("all")
            self.current_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
            
            self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))
            
            file_name = os.path.basename(image_path)
            self.status_text.set(f"Image: {file_name} ({self.current_image_index + 1}/{len(self.image_files)})")
            
            self.load_current_labels()
            self.initialize_managers()
            self.redraw_labels()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image: {str(e)}")
    
    def load_current_labels(self):
        if self.current_image_index < 0 or not self.image_files:
            return
        
        file_name = os.path.basename(self.image_files[self.current_image_index])
        
        if file_name in self.labels:
            self.current_labels = self.labels[file_name]
        else:
            self.current_labels = {}
    
    def redraw_labels(self):
        if self.label_renderer:
            self.label_renderer.zoom_factor = self.zoom_factor
            self.label_renderer.show_labels = self.show_labels
            self.label_renderer.show_label_text = self.show_label_text
            self.label_renderer.redraw_all(self.current_labels)
    
    def draw_rectangle_mode(self):
        self.drawing_mode = "rectangle"
        self.status_text.set("Click and drag to draw pelvis rectangle")
    
    def draw_left_keypoint_mode(self):
        self.drawing_mode = "left_keypoint"
        self.status_text.set("Click to place left acetabulum point")
    
    def draw_right_keypoint_mode(self):
        self.drawing_mode = "right_keypoint"
        self.status_text.set("Click to place right acetabulum point")
    
    def draw_left_circle_mode(self):
        self.drawing_mode = "left_circle"
        self.status_text.set("Click center, then drag to set left femur head circle radius")
    
    def draw_right_circle_mode(self):
        self.drawing_mode = "right_circle"
        self.status_text.set("Click center, then drag to set right femur head circle radius")
    
    def on_canvas_click(self, event):
        x = self.canvas.canvasx(event.x) / self.zoom_factor
        y = self.canvas.canvasy(event.y) / self.zoom_factor
        
        if self.drawing_mode == "rectangle":
            self.drawing_manager.start_drawing(x, y, self.drawing_mode)
        
        elif self.drawing_mode == "left_keypoint":
            self.current_labels["left_keypoint"] = {"x": x, "y": y}
            self.redraw_labels()
            self.drawing_mode = None
            self.status_text.set("Left acetabulum point placed")
            self.save_current_labels()
        
        elif self.drawing_mode == "right_keypoint":
            self.current_labels["right_keypoint"] = {"x": x, "y": y}
            self.redraw_labels()
            self.drawing_mode = None
            self.status_text.set("Right acetabulum point placed")
            self.save_current_labels()
        
        elif self.drawing_mode in ["left_circle", "right_circle"]:
            if self.drawing_manager.start_x is None:
                self.drawing_manager.start_drawing(x, y, self.drawing_mode)
    
    def on_canvas_drag(self, event):
        x = self.canvas.canvasx(event.x) / self.zoom_factor
        y = self.canvas.canvasy(event.y) / self.zoom_factor
        
        if self.drawing_mode == "rectangle" and self.drawing_manager.start_x is not None:
            self.drawing_manager.draw_temp_rectangle(x, y)
        
        elif self.drawing_mode in ["left_circle", "right_circle"] and self.drawing_manager.start_x is not None:
            color = "#ff4500" if self.drawing_mode == "left_circle" else "#4169e1"
            self.drawing_manager.draw_temp_circle(x, y, color)
    
    def on_canvas_release(self, event):
        x = self.canvas.canvasx(event.x) / self.zoom_factor
        y = self.canvas.canvasy(event.y) / self.zoom_factor
        
        if self.drawing_mode == "rectangle" and self.drawing_manager.start_x is not None:
            self.current_labels["rectangle"] = self.drawing_manager.finalize_rectangle(x, y)
            self.redraw_labels()
            self.drawing_mode = None
            self.status_text.set("Pelvis rectangle drawn")
            self.save_current_labels()
        
        elif self.drawing_mode in ["left_circle", "right_circle"] and self.drawing_manager.start_x is not None:
            circle_data = self.drawing_manager.finalize_circle(x, y)
            
            if self.drawing_mode == "left_circle":
                self.current_labels["left_circle"] = circle_data
                self.status_text.set("Left femur head circle drawn")
            else:
                self.current_labels["right_circle"] = circle_data
                self.status_text.set("Right femur head circle drawn")
            
            self.redraw_labels()
            self.drawing_mode = None
            self.save_current_labels()
    
    def on_right_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        
        for item in items:
            tags = self.canvas.gettags(item)
            
            if "annotation" in tags:
                self.selected_item = item
                
                if "rectangle" in tags:
                    self.selected_tag = "rectangle"
                elif "left_keypoint" in tags:
                    self.selected_tag = "left_keypoint"
                elif "right_keypoint" in tags:
                    self.selected_tag = "right_keypoint"
                elif "left_circle" in tags:
                    self.selected_tag = "left_circle"
                elif "right_circle" in tags:
                    self.selected_tag = "right_circle"
                
                self.context_menu.post(event.x_root, event.y_root)
                break
    
    def start_move_mode(self):
        self.status_text.set(f"Move mode active for {self.selected_tag}. Click and drag to move.")
        self.moving = True
        
        self.canvas.bind("<Button-1>", self.start_moving)
        self.canvas.bind("<B1-Motion>", self.do_move)
        self.canvas.bind("<ButtonRelease-1>", self.stop_moving)
    
    def start_moving(self, event):
        self.last_x = self.canvas.canvasx(event.x)
        self.last_y = self.canvas.canvasy(event.y)
    
    def do_move(self, event):
        if not self.moving:
            return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        dx = (x - self.last_x) / self.zoom_factor
        dy = (y - self.last_y) / self.zoom_factor
        
        if self.selected_tag == "rectangle":
            if "rectangle" in self.current_labels:
                rect = self.current_labels["rectangle"]
                rect["x1"] += dx
                rect["y1"] += dy
                rect["x2"] += dx
                rect["y2"] += dy
        
        elif self.selected_tag == "left_keypoint":
            if "left_keypoint" in self.current_labels:
                kp = self.current_labels["left_keypoint"]
                kp["x"] += dx
                kp["y"] += dy
        
        elif self.selected_tag == "right_keypoint":
            if "right_keypoint" in self.current_labels:
                kp = self.current_labels["right_keypoint"]
                kp["x"] += dx
                kp["y"] += dy
        
        elif self.selected_tag == "left_circle":
            if "left_circle" in self.current_labels:
                circle = self.current_labels["left_circle"]
                circle["center_x"] += dx
                circle["center_y"] += dy
        
        elif self.selected_tag == "right_circle":
            if "right_circle" in self.current_labels:
                circle = self.current_labels["right_circle"]
                circle["center_x"] += dx
                circle["center_y"] += dy
        
        self.redraw_labels()
        
        self.last_x = x
        self.last_y = y
    
    def stop_moving(self, event):
        self.moving = False
        self.selected_item = None
        self.selected_tag = None
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        self.status_text.set("Move completed. Annotation moved.")
        self.save_current_labels()
    
    def start_edit_mode(self):
        if self.selected_tag == "rectangle":
            self.edit_rectangle()
        elif self.selected_tag in ["left_circle", "right_circle"]:
            self.edit_circle()
        else:
            messagebox.showinfo("Edit Mode", "Edit mode only works for rectangles and circles.")
    
    def edit_rectangle(self):
        self.status_text.set("Edit rectangle: drag corners to resize")
        self.resize_mode = True
        self.resize_type = "rectangle"
        
        self.edit_manager.draw_rectangle_handles(self.current_labels["rectangle"])
        
        self.canvas.bind("<Button-1>", self.start_resize)
        self.canvas.bind("<B1-Motion>", self.do_resize)
        self.canvas.bind("<ButtonRelease-1>", self.stop_resize)
    
    def edit_circle(self):
        self.status_text.set("Edit circle: drag edge to resize")
        self.resize_mode = True
        self.resize_type = self.selected_tag
        
        self.edit_manager.draw_circle_handles(self.current_labels[self.selected_tag])
        
        self.canvas.bind("<Button-1>", self.start_circle_resize)
        self.canvas.bind("<B1-Motion>", self.do_circle_resize)
        self.canvas.bind("<ButtonRelease-1>", self.stop_circle_resize)
    
    def start_resize(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        self.edit_manager.resize_handle = self.edit_manager.find_handle(x, y)
        if self.edit_manager.resize_handle:
            self.edit_manager.last_x = x
            self.edit_manager.last_y = y
    
    def do_resize(self, event):
        if not self.edit_manager.resize_handle:
            return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        dx = (x - self.edit_manager.last_x) / self.zoom_factor
        dy = (y - self.edit_manager.last_y) / self.zoom_factor
        
        if "rectangle" in self.current_labels:
            self.edit_manager.resize_rectangle(self.current_labels["rectangle"], 
                                               self.edit_manager.resize_handle, dx, dy)
        
        self.redraw_labels()
        self.edit_manager.draw_rectangle_handles(self.current_labels["rectangle"])
        
        self.edit_manager.last_x = x
        self.edit_manager.last_y = y
    
    def stop_resize(self, event):
        if self.resize_mode:
            self.edit_manager.clear_handles()
            self.resize_mode = False
            
            self.canvas.bind("<Button-1>", self.on_canvas_click)
            self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
            
            self.status_text.set("Edit completed")
            self.save_current_labels()
    
    def start_circle_resize(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        
        for item in items:
            tags = self.canvas.gettags(item)
            if "resize_handle" in tags:
                self.edit_manager.resize_handle = True
                self.edit_manager.last_x = x
                self.edit_manager.last_y = y
                break
    
    def do_circle_resize(self, event):
        if not self.edit_manager.resize_handle:
            return
        
        x = self.canvas.canvasx(event.x) / self.zoom_factor
        y = self.canvas.canvasy(event.y) / self.zoom_factor
        
        if self.resize_type in self.current_labels:
            self.edit_manager.resize_circle(self.current_labels[self.resize_type], x, y)
        
        self.redraw_labels()
        self.edit_manager.draw_circle_handles(self.current_labels[self.resize_type])
    
    def stop_circle_resize(self, event):
        if self.resize_mode:
            self.edit_manager.clear_handles()
            self.resize_mode = False
            
            self.canvas.bind("<Button-1>", self.on_canvas_click)
            self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
            
            self.status_text.set("Edit completed")
            self.save_current_labels()
    
    def delete_selected(self):
        if self.selected_tag and self.selected_tag in self.current_labels:
            del self.current_labels[self.selected_tag]
            self.redraw_labels()
            self.status_text.set(f"{self.selected_tag} deleted")
            self.save_current_labels()
            self.selected_item = None
            self.selected_tag = None
    
    def cancel_drawing(self):
        self.drawing_mode = None
        if self.drawing_manager:
            self.drawing_manager.clear_temp_items()
            self.drawing_manager.reset()
        self.status_text.set("Drawing cancelled")
    
    def clear_labels(self):
        response = messagebox.askyesno("Clear Labels", 
                                       "Are you sure you want to clear all labels for this image?")
        
        if response:
            self.current_labels = {}
            self.redraw_labels()
            self.status_text.set("All labels cleared for current image")
            self.save_current_labels()
    
    def save_current_labels(self):
        if self.current_image_index < 0 or not self.image_files:
            return
        
        file_name = os.path.basename(self.image_files[self.current_image_index])
        
        if self.current_labels:
            self.labels[file_name] = self.current_labels
        elif file_name in self.labels:
            del self.labels[file_name]
    
    def save_labels_handler(self):
        if save_labels(self.current_folder, self.labels):
            json_path = os.path.join(self.current_folder, "norberg_olsen_labels.json")
            self.status_text.set(f"Labels saved to {json_path}")
            messagebox.showinfo("Success", f"Labels saved successfully to:\n{json_path}")
            save_session_info(self.current_folder, self.current_image_index)
        else:
            self.status_text.set("Failed to save labels")
    
    def export_to_csv_handler(self):
        if not self.labels:
            messagebox.showwarning("No Labels", "No labels to export.")
            return
        
        csv_path = filedialog.asksaveasfilename(
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not csv_path:
            return
        
        if export_to_csv(csv_path, self.labels):
            messagebox.showinfo("Success", f"Data exported successfully to:\n{csv_path}")
    
    def prev_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_image()
            save_session_info(self.current_folder, self.current_image_index)
    
    def next_image(self):
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.display_image()
            save_session_info(self.current_folder, self.current_image_index)
    
    def zoom_in(self):
        if self.zoom_factor < self.zoom_max:
            self.zoom_factor = min(self.zoom_factor * 1.2, self.zoom_max)
            self.zoom_text.set(f"Zoom: {int(self.zoom_factor * 100)}%")
            self.display_image()
    
    def zoom_out(self):
        if self.zoom_factor > self.zoom_min:
            self.zoom_factor = max(self.zoom_factor / 1.2, self.zoom_min)
            self.zoom_text.set(f"Zoom: {int(self.zoom_factor * 100)}%")
            self.display_image()
    
    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.zoom_text.set("Zoom: 100%")
        self.display_image()
    
    def zoom(self, event):
        if event.num == 4 or event.delta > 0:
            self.zoom_in()
        elif event.num == 5 or event.delta < 0:
            self.zoom_out()
    
    def toggle_labels(self):
        self.show_labels = not self.show_labels
        self.redraw_labels()
        
        status = "visible" if self.show_labels else "hidden"
        self.status_text.set(f"Labels are now {status}")
    
    def toggle_label_text(self):
        self.show_label_text = not self.show_label_text
        self.redraw_labels()
        
        status = "visible" if self.show_label_text else "hidden"
        self.status_text.set(f"Label text is now {status}")
    
    def show_instructions(self):
        instructions = """
Norberg-Olsen Hip Dysplasia Labeling Tool - Instructions

1. Open Folder: Select a folder containing X-ray images
2. Draw Pelvis Rectangle: Click 'Rectangle' button and drag on image
3. Mark Acetabulum Points: Click 'Left Point' / 'Right Point' and click on image
4. Draw Femur Head Circles: Click 'Left Circle' / 'Right Circle', click center, then drag
5. Calculate Angles: Click 'Calculate' to compute Norberg and Joint angles
6. Save: Click 'Save' to save labels to JSON file

Keyboard Shortcuts:
- Left/Right Arrow: Navigate images
- Ctrl+S: Save labels
- Ctrl+O: Open folder
- Ctrl+Z: Clear labels
- Escape: Cancel drawing
- Delete: Delete selected annotation

Mouse Controls:
- Right-click: Context menu (Move/Edit/Delete)
- Mouse wheel: Zoom in/out
        """
        
        messagebox.showinfo("Instructions", instructions)
    
    def show_about(self):
        about_text = """
Norberg-Olsen Hip Dysplasia Labeling Tool
Version 1.0

A specialized tool for annotating canine hip X-rays
to measure Norberg angles and joint angles for
hip dysplasia assessment.

Developed for veterinary orthopedic research.
        """
        
        messagebox.showinfo("About", about_text)
    
    def calculate_hip_angles(self):
        if "rectangle" not in self.current_labels:
            messagebox.showwarning("Missing Data", "Please draw the pelvis rectangle first.")
            return
        
        if "left_keypoint" not in self.current_labels:
            messagebox.showwarning("Missing Data", "Please mark the left acetabulum point.")
            return
        
        if "right_keypoint" not in self.current_labels:
            messagebox.showwarning("Missing Data", "Please mark the right acetabulum point.")
            return
        
        if "left_circle" not in self.current_labels:
            messagebox.showwarning("Missing Data", "Please draw the left femur head circle.")
            return
        
        if "right_circle" not in self.current_labels:
            messagebox.showwarning("Missing Data", "Please draw the right femur head circle.")
            return
        
        left_keypoint = self.current_labels["left_keypoint"]
        right_keypoint = self.current_labels["right_keypoint"]
        left_femur = self.current_labels["left_circle"]
        right_femur = self.current_labels["right_circle"]
        
        left_norberg_angle = calculate_angle(
            left_femur["center_x"], left_femur["center_y"],
            left_keypoint["x"], left_keypoint["y"]
        )
        
        right_norberg_angle = calculate_angle(
            right_femur["center_x"], right_femur["center_y"],
            right_keypoint["x"], right_keypoint["y"]
        )
        
        left_femur_angle = calculate_joint_angle(
            left_keypoint["x"], left_keypoint["y"],
            left_femur["center_x"], left_femur["center_y"],
            right_femur["center_x"], right_femur["center_y"]
        )
        
        right_femur_angle = calculate_joint_angle(
            right_keypoint["x"], right_keypoint["y"],
            right_femur["center_x"], right_femur["center_y"],
            left_femur["center_x"], left_femur["center_y"]
        )
        
        self.current_labels["left_angle"] = left_norberg_angle
        self.current_labels["right_angle"] = right_norberg_angle
        self.current_labels["left_femur_angle"] = left_femur_angle
        self.current_labels["right_femur_angle"] = right_femur_angle
        
        file_name = os.path.basename(self.image_files[self.current_image_index])
        self.labels[file_name] = self.current_labels
        
        if self.show_labels:
            self.redraw_labels()
        
        messagebox.showinfo("Hip Angle Measurements", 
                          f"Image: {file_name}\n\n"
                          f"LEFT MEASUREMENTS:\n"
                          f"Norberg Angle: {left_norberg_angle:.1f}°\n"
                          f"Joint Angle: {left_femur_angle:.1f}°\n\n"
                          f"RIGHT MEASUREMENTS:\n"
                          f"Norberg Angle: {right_norberg_angle:.1f}°\n"
                          f"Joint Angle: {right_femur_angle:.1f}°\n\n"
                          f"AVERAGE MEASUREMENTS:\n"
                          f"Norberg Angle: {(left_norberg_angle + right_norberg_angle)/2:.1f}°\n"
                          f"Joint Angle: {(left_femur_angle + right_femur_angle)/2:.1f}°")
        
        save_session_info(self.current_folder, self.current_image_index)


if __name__ == "__main__":
    root = tk.Tk()
    app = NorbergOlsenLabelingApp(root)
    root.mainloop()
