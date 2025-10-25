import math

class DrawingManager:
    def __init__(self, canvas, zoom_factor, current_labels):
        self.canvas = canvas
        self.zoom_factor = zoom_factor
        self.current_labels = current_labels
        self.temp_items = []
        self.start_x = None
        self.start_y = None
        
    def start_drawing(self, x, y, mode):
        self.start_x = x
        self.start_y = y
        
    def draw_temp_rectangle(self, x, y):
        self.clear_temp_items()
        
        x1, y1 = self.start_x * self.zoom_factor, self.start_y * self.zoom_factor
        x2, y2 = x * self.zoom_factor, y * self.zoom_factor
        
        temp_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2, 
            outline="#00ff00", width=2, dash=(5, 3)
        )
        self.temp_items.append(temp_rect)
    
    def draw_temp_circle(self, x, y, color="#ff4500"):
        self.clear_temp_items()
        
        cx, cy = self.start_x * self.zoom_factor, self.start_y * self.zoom_factor
        dx = x * self.zoom_factor - cx
        dy = y * self.zoom_factor - cy
        radius = math.sqrt(dx**2 + dy**2)
        
        temp_circle = self.canvas.create_oval(
            cx-radius, cy-radius, cx+radius, cy+radius, 
            outline=color, width=2, dash=(5, 3)
        )
        self.temp_items.append(temp_circle)
        
        temp_center = self.canvas.create_oval(
            cx-3, cy-3, cx+3, cy+3, 
            fill=color, outline="#ffffff"
        )
        self.temp_items.append(temp_center)
    
    def clear_temp_items(self):
        for item in self.temp_items:
            self.canvas.delete(item)
        self.temp_items.clear()
    
    def finalize_rectangle(self, x, y):
        rect_data = {
            "x1": min(self.start_x, x),
            "y1": min(self.start_y, y),
            "x2": max(self.start_x, x),
            "y2": max(self.start_y, y)
        }
        self.clear_temp_items()
        self.reset()
        return rect_data
    
    def finalize_circle(self, x, y):
        dx = x - self.start_x
        dy = y - self.start_y
        radius = math.sqrt(dx**2 + dy**2)
        
        circle_data = {
            "center_x": self.start_x,
            "center_y": self.start_y,
            "radius": radius
        }
        self.clear_temp_items()
        self.reset()
        return circle_data
    
    def reset(self):
        self.start_x = None
        self.start_y = None


class LabelRenderer:
    def __init__(self, canvas, zoom_factor, show_labels, show_label_text):
        self.canvas = canvas
        self.zoom_factor = zoom_factor
        self.show_labels = show_labels
        self.show_label_text = show_label_text
    
    def redraw_all(self, current_labels):
        self.canvas.delete("annotation")
        
        if not self.show_labels:
            return
        
        if "rectangle" in current_labels:
            self.draw_rectangle(current_labels["rectangle"])
        
        if "left_keypoint" in current_labels:
            self.draw_keypoint(current_labels["left_keypoint"], "L-Acetabulum", "#ff0000")
        
        if "right_keypoint" in current_labels:
            self.draw_keypoint(current_labels["right_keypoint"], "R-Acetabulum", "#0000ff")
        
        if "left_circle" in current_labels:
            self.draw_circle(current_labels["left_circle"], "L-Femur", "#ff4500", "left_circle")
        
        if "right_circle" in current_labels:
            self.draw_circle(current_labels["right_circle"], "R-Femur", "#4169e1", "right_circle")
        
        if "left_angle" in current_labels:
            left_angle = current_labels.get("left_angle", 0)
            right_angle = current_labels.get("right_angle", 0)
            left_femur_angle = current_labels.get("left_femur_angle", 0)
            right_femur_angle = current_labels.get("right_femur_angle", 0)
            self.draw_angle_lines(current_labels, left_angle, right_angle, left_femur_angle, right_femur_angle)
    
    def draw_rectangle(self, rect):
        x1, y1 = rect["x1"] * self.zoom_factor, rect["y1"] * self.zoom_factor
        x2, y2 = rect["x2"] * self.zoom_factor, rect["y2"] * self.zoom_factor
        
        self.canvas.create_rectangle(
            x1, y1, x2, y2, 
            outline="#00ff00", width=2, 
            tags=("rectangle", "annotation")
        )
        
        if self.show_label_text:
            mid_x, mid_y = (x1 + x2) / 2, y1 - 10
            self.canvas.create_text(
                mid_x, mid_y, 
                text="Pelvis", 
                fill="#00ff00", 
                font=("Segoe UI", 10, "bold"),
                tags=("rectangle_label", "annotation")
            )
    
    def draw_keypoint(self, kp, label, color):
        x, y = kp["x"] * self.zoom_factor, kp["y"] * self.zoom_factor
        r = 5
        
        tag = "left_keypoint" if "Left" in label else "right_keypoint"
        
        self.canvas.create_oval(
            x-r, y-r, x+r, y+r, 
            fill=color, outline="#ffffff", width=2,
            tags=(tag, "annotation")
        )
        
        if self.show_label_text:
            self.canvas.create_text(
                x, y-15, 
                text=label, 
                fill=color, 
                font=("Segoe UI", 9, "bold"),
                tags=(f"{tag}_label", "annotation")
            )
    
    def draw_circle(self, circle, label, color, tag):
        cx, cy = circle["center_x"] * self.zoom_factor, circle["center_y"] * self.zoom_factor
        r = circle["radius"] * self.zoom_factor
        
        self.canvas.create_oval(
            cx-r, cy-r, cx+r, cy+r, 
            outline=color, width=2,
            tags=(tag, "annotation")
        )
        
        self.canvas.create_oval(
            cx-3, cy-3, cx+3, cy+3, 
            fill=color, outline="#ffffff",
            tags=(f"{tag}_center", "annotation")
        )
        
        if self.show_label_text:
            self.canvas.create_text(
                cx, cy-r-15, 
                text=label, 
                fill=color, 
                font=("Segoe UI", 9, "bold"),
                tags=(f"{tag}_label", "annotation")
            )
    
    def draw_angle_lines(self, labels, left_angle, right_angle, left_femur_angle, right_femur_angle):
        self.canvas.delete("angle_line")
        
        if "left_circle" not in labels or "right_circle" not in labels:
            return
        if "left_keypoint" not in labels or "right_keypoint" not in labels:
            return
        
        left_femur = labels["left_circle"]
        right_femur = labels["right_circle"]
        left_acetabulum = labels["left_keypoint"]
        right_acetabulum = labels["right_keypoint"]
        
        left_center_x = left_femur["center_x"] * self.zoom_factor
        left_center_y = left_femur["center_y"] * self.zoom_factor
        left_point_x = left_acetabulum["x"] * self.zoom_factor
        left_point_y = left_acetabulum["y"] * self.zoom_factor
        
        right_center_x = right_femur["center_x"] * self.zoom_factor
        right_center_y = right_femur["center_y"] * self.zoom_factor
        right_point_x = right_acetabulum["x"] * self.zoom_factor
        right_point_y = right_acetabulum["y"] * self.zoom_factor
        
        self.canvas.create_line(
            left_center_x, left_center_y, right_center_x, right_center_y,
            fill="#ffcc00", width=2, dash=(5, 3),
            tags=("angle_line", "annotation")
        )
        
        self.canvas.create_line(
            left_center_x, left_center_y, left_point_x, left_point_y,
            fill="#ff4500", width=2,
            tags=("angle_line", "annotation")
        )
        
        self.canvas.create_text(
            (left_center_x + left_point_x) / 2, (left_center_y + left_point_y) / 2 - 15,
            text=f"NA: {left_angle:.1f}°",
            fill="#ff4500", font=("Segoe UI", 9, "bold"),
            tags=("angle_line", "annotation")
        )
        
        self.canvas.create_text(
            left_center_x, left_center_y - 20,
            text=f"JA: {left_femur_angle:.1f}°",
            fill="#ffcc00", font=("Segoe UI", 9, "bold"),
            tags=("angle_line", "annotation")
        )
        
        self.canvas.create_line(
            right_center_x, right_center_y, right_point_x, right_point_y,
            fill="#4169e1", width=2,
            tags=("angle_line", "annotation")
        )
        
        self.canvas.create_text(
            (right_center_x + right_point_x) / 2, (right_center_y + right_point_y) / 2 - 15,
            text=f"NA: {right_angle:.1f}°",
            fill="#4169e1", font=("Segoe UI", 9, "bold"),
            tags=("angle_line", "annotation")
        )
        
        self.canvas.create_text(
            right_center_x, right_center_y - 20,
            text=f"JA: {right_femur_angle:.1f}°",
            fill="#ffcc00", font=("Segoe UI", 9, "bold"),
            tags=("angle_line", "annotation")
        )


class EditManager:
    def __init__(self, canvas, zoom_factor):
        self.canvas = canvas
        self.zoom_factor = zoom_factor
        self.resize_handle = None
        self.last_x = 0
        self.last_y = 0
    
    def draw_rectangle_handles(self, rect):
        self.canvas.delete("resize_handle")
        
        x1 = rect["x1"] * self.zoom_factor
        y1 = rect["y1"] * self.zoom_factor
        x2 = rect["x2"] * self.zoom_factor
        y2 = rect["y2"] * self.zoom_factor
        
        handle_size = 6
        corners = [
            (x1, y1, "nw"),
            (x2, y1, "ne"),
            (x1, y2, "sw"),
            (x2, y2, "se")
        ]
        
        for x, y, corner in corners:
            self.canvas.create_rectangle(
                x - handle_size, y - handle_size,
                x + handle_size, y + handle_size,
                fill="#ffff00", outline="#000000", width=2,
                tags=("resize_handle", corner)
            )
    
    def draw_circle_handles(self, circle):
        self.canvas.delete("resize_handle")
        
        cx = circle["center_x"] * self.zoom_factor
        cy = circle["center_y"] * self.zoom_factor
        r = circle["radius"] * self.zoom_factor
        
        handle_size = 6
        positions = [
            (cx + r, cy, "e"),
            (cx - r, cy, "w"),
            (cx, cy + r, "s"),
            (cx, cy - r, "n")
        ]
        
        for x, y, pos in positions:
            self.canvas.create_rectangle(
                x - handle_size, y - handle_size,
                x + handle_size, y + handle_size,
                fill="#ffff00", outline="#000000", width=2,
                tags=("resize_handle", pos)
            )
    
    def find_handle(self, x, y):
        items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        
        for item in items:
            tags = self.canvas.gettags(item)
            if "resize_handle" in tags:
                for tag in tags:
                    if tag in ["nw", "ne", "sw", "se"]:
                        return tag
        return None
    
    def resize_rectangle(self, rect, handle, dx, dy):
        if handle == "nw":
            rect["x1"] += dx
            rect["y1"] += dy
        elif handle == "ne":
            rect["x2"] += dx
            rect["y1"] += dy
        elif handle == "sw":
            rect["x1"] += dx
            rect["y2"] += dy
        elif handle == "se":
            rect["x2"] += dx
            rect["y2"] += dy
        
        if rect["x1"] > rect["x2"]:
            rect["x1"], rect["x2"] = rect["x2"], rect["x1"]
        if rect["y1"] > rect["y2"]:
            rect["y1"], rect["y2"] = rect["y2"], rect["y1"]
    
    def resize_circle(self, circle, x, y):
        cx = circle["center_x"]
        cy = circle["center_y"]
        
        dx = x - cx
        dy = y - cy
        new_radius = math.sqrt(dx**2 + dy**2)
        
        circle["radius"] = new_radius
    
    def clear_handles(self):
        self.canvas.delete("resize_handle")
        self.resize_handle = None
