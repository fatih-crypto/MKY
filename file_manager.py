import os
import json
import csv
from tkinter import messagebox

def load_labels(folder_path):
    if not folder_path:
        return {}
    
    json_path = os.path.join(folder_path, "norberg_olsen_labels.json")
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                labels = json.load(f)
            return labels
        except Exception as e:
            messagebox.showerror("Error", f"Could not load labels: {str(e)}")
            return {}
    return {}

def save_labels(folder_path, labels):
    if not folder_path:
        messagebox.showwarning("No Folder", "Please open a folder first.")
        return False
    
    json_path = os.path.join(folder_path, "norberg_olsen_labels.json")
    
    try:
        with open(json_path, 'w') as f:
            json.dump(labels, f, indent=4)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Could not save labels: {str(e)}")
        return False

def export_to_csv(csv_path, labels):
    try:
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = ['Image', 'Left_Norberg_Angle', 'Right_Norberg_Angle', 
                         'Left_Joint_Angle', 'Right_Joint_Angle',
                         'Avg_Norberg_Angle', 'Avg_Joint_Angle']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for image_name, data in labels.items():
                row = {'Image': image_name}
                
                if 'left_angle' in data:
                    row['Left_Norberg_Angle'] = f"{data['left_angle']:.2f}"
                
                if 'right_angle' in data:
                    row['Right_Norberg_Angle'] = f"{data['right_angle']:.2f}"
                
                if 'left_femur_angle' in data:
                    row['Left_Joint_Angle'] = f"{data['left_femur_angle']:.2f}"
                
                if 'right_femur_angle' in data:
                    row['Right_Joint_Angle'] = f"{data['right_femur_angle']:.2f}"
                
                if 'left_angle' in data and 'right_angle' in data:
                    avg = (data['left_angle'] + data['right_angle']) / 2
                    row['Avg_Norberg_Angle'] = f"{avg:.2f}"
                
                if 'left_femur_angle' in data and 'right_femur_angle' in data:
                    avg = (data['left_femur_angle'] + data['right_femur_angle']) / 2
                    row['Avg_Joint_Angle'] = f"{avg:.2f}"
                
                writer.writerow(row)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Could not export to CSV: {str(e)}")
        return False

def load_images_from_folder(folder_path):
    if not folder_path:
        return []
    
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')
    image_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(supported_formats)
    ]
    image_files.sort()
    return image_files

def save_session_info(folder_path, image_index):
    config_file = os.path.join(os.path.expanduser("~"), "norberg_olsen_config.json")
    
    config = {
        "last_folder": folder_path,
        "last_image_index": image_index
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f)
    except:
        pass

def load_session_info():
    config_file = os.path.join(os.path.expanduser("~"), "norberg_olsen_config.json")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return None
