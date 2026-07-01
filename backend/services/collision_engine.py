import math
from typing import List, Dict

def resolve_collisions(components: List[Dict], padding: float = 0.5, max_iterations: int = 50) -> List[Dict]:
    """
    Menyelesaikan tabrakan antar objek 3D di koordinat XZ.
    Menggunakan algoritma relaksasi (push apart) berdasarkan bounding box (scale_3d).
    """
    # Pisahkan base land (yang tidak boleh digeser) dan objek lain
    base_comp = None
    objects = []
    
    for comp in components:
        is_base = comp.get("original_id") == 1 or comp.get("id") == 0
        if is_base:
            base_comp = comp
        else:
            # Gunakan initial guess dari depth engine (X_meter dan Z_meter)
            # Karena di depth engine Z_meter adalah jarak dari kamera, kita gunakan sebagai sumbu Z.
            # X_meter sebagai sumbu X.
            sp = comp.get("spatial_data", {}).get("spatial_3d_coordinates", {})
            
            # Default ke 0 jika tidak ada
            x = sp.get("X_meter", 0.0)
            z = sp.get("Z_meter", 0.0)
            
            # Asumsi scale_3d = [width, height, depth]
            scale = comp.get("scale_3d", [1.0, 1.0, 1.0])
            width = scale[0]
            depth = scale[2]
            
            objects.append({
                "comp": comp,
                "x": x,
                "z": z,
                "w": width + padding,
                "d": depth + padding
            })
            
    # Pusatkan semua objek di sekitar origin (agar tidak terlalu jauh di kamera)
    if len(objects) > 0:
        avg_x = sum(o["x"] for o in objects) / len(objects)
        avg_z = sum(o["z"] for o in objects) / len(objects)
        
        # Center them
        for o in objects:
            o["x"] -= avg_x
            o["z"] -= avg_z
            
    # Collision Resolution Loop
    for _ in range(max_iterations):
        moved = False
        for i in range(len(objects)):
            for j in range(i + 1, len(objects)):
                o1 = objects[i]
                o2 = objects[j]
                
                # Jarak antar titik tengah
                dx = o2["x"] - o1["x"]
                dz = o2["z"] - o1["z"]
                
                # Jarak minimum yang diperbolehkan antar pusat
                min_dist_x = (o1["w"] / 2.0) + (o2["w"] / 2.0)
                min_dist_z = (o1["d"] / 2.0) + (o2["d"] / 2.0)
                
                # Cek overlap
                if abs(dx) < min_dist_x and abs(dz) < min_dist_z:
                    moved = True
                    # Hitung overlap
                    overlap_x = min_dist_x - abs(dx)
                    overlap_z = min_dist_z - abs(dz)
                    
                    # Push on the axis of least penetration
                    if overlap_x < overlap_z:
                        sign = 1 if dx > 0 else -1
                        if dx == 0: sign = 1
                        push = (overlap_x / 2.0) + 0.1
                        o1["x"] -= push * sign
                        o2["x"] += push * sign
                    else:
                        sign = 1 if dz > 0 else -1
                        if dz == 0: sign = 1
                        push = (overlap_z / 2.0) + 0.1
                        o1["z"] -= push * sign
                        o2["z"] += push * sign
                        
        if not moved:
            break  # Tidak ada tabrakan lagi
            
    # Kembalikan koordinat baru ke component
    for o in objects:
        comp = o["comp"]
        sp = comp.get("spatial_data", {})
        coords = sp.get("spatial_3d_coordinates", {})
        
        # Simpan koordinat baru (menggunakan konvensi map Z ke Y jika dibutuhkan, 
        # tapi di sini kita simpan sebagai X_meter dan Z_meter definitif)
        coords["X_meter"] = round(o["x"], 2)
        coords["Z_meter"] = round(o["z"], 2)
        
        sp["spatial_3d_coordinates"] = coords
        comp["spatial_data"] = sp
        
    # Kalkulasi ukuran base model agar mencakup semua objek
    if base_comp and len(objects) > 0:
        min_x = min((o["x"] - o["w"]/2) for o in objects)
        max_x = max((o["x"] + o["w"]/2) for o in objects)
        min_z = min((o["z"] - o["d"]/2) for o in objects)
        max_z = max((o["z"] + o["d"]/2) for o in objects)
        
        # Tambahkan padding ekstra untuk tanah
        req_width = max((max_x - min_x) + 4.0, 8.0) # minimal 8x8 meter
        req_depth = max((max_z - min_z) + 4.0, 8.0)
        
        base_scale = base_comp.get("scale_3d", [8.0, 0.5, 8.0])
        base_scale[0] = round(req_width, 2)
        base_scale[2] = round(req_depth, 2)
        base_comp["scale_3d"] = base_scale

    final_components = [base_comp] if base_comp else []
    for o in objects:
        final_components.append(o["comp"])
        
    # Pastikan urutan id sesuai aslinya (di-sort kembali berdasarkan index aslinya jika perlu)
    final_components.sort(key=lambda x: x.get("id", 0))
    
    return final_components
