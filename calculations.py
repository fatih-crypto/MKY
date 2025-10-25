import math

def calculate_angle(center_x, center_y, point_x, point_y):
    ref_y = center_y - 100
    
    v1 = [0, ref_y - center_y]
    v2 = [point_x - center_x, point_y - center_y]
    
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    magnitude1 = math.sqrt(v1[0]**2 + v1[1]**2)
    magnitude2 = math.sqrt(v2[0]**2 + v2[1]**2)
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
        
    angle_rad = math.acos(dot_product / (magnitude1 * magnitude2))
    angle_deg = math.degrees(angle_rad)
    
    if point_x < center_x:
        angle_deg = 180 - angle_deg
        
    return angle_deg

def calculate_joint_angle(point1_x, point1_y, center_x, center_y, point2_x, point2_y):
    v1 = [point1_x - center_x, point1_y - center_y]
    v2 = [point2_x - center_x, point2_y - center_y]
    
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    magnitude1 = math.sqrt(v1[0]**2 + v1[1]**2)
    magnitude2 = math.sqrt(v2[0]**2 + v2[1]**2)
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
        
    cos_angle = dot_product / (magnitude1 * magnitude2)
    cos_angle = min(1.0, max(-1.0, cos_angle))
    angle_rad = math.acos(cos_angle)
    angle_deg = math.degrees(angle_rad)
        
    return angle_deg
