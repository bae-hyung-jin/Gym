import bpy
import bmesh
from mathutils import Vector, Matrix
import math
import os

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_in = r"G:\Unity_Gym\AI-Gym\Assets\PolyRonin\Old School Gym Equipment\Meshes\old-school-gym-equipment-1.fbx"
blend_out = r"G:\Unity_Gym\AI-Gym\_blender\Dumbbell2_Modular.blend"
fbx_out = r"G:\Unity_Gym\AI-Gym\Assets\PolyRonin\Old School Gym Equipment\Meshes\Dumbbell2_Modular.fbx"

bpy.ops.import_scene.fbx(filepath=fbx_in)

src = bpy.data.objects.get("Dumbbell2")
if src is None:
    raise RuntimeError("Dumbbell2 not found in FBX!")

# Inspect UV coordinates of handle vs plates before deleting other objects
src_me = src.data
src_mat = src_me.materials[0] if len(src_me.materials) > 0 else None

bm_src = bmesh.new()
bm_src.from_mesh(src_me)
bm_src.verts.ensure_lookup_table()
bm_src.faces.ensure_lookup_table()
uv_layer = bm_src.loops.layers.uv.active

plate_uv = (0.505, 0.831)
handle_uv = (0.841, 0.831)
if uv_layer:
    for f in bm_src.faces:
        c = f.calc_center_median()
        u = sum(l[uv_layer].uv.x for l in f.loops) / len(f.loops)
        v = sum(l[uv_layer].uv.y for l in f.loops) / len(f.loops)
        if abs(c.z) > 10.0:
            plate_uv = (u, v)
        elif abs(c.z) < 5.0:
            handle_uv = (u, v)
print(f"Sampled UVs -> handle={handle_uv}, plate={plate_uv}")

# Remember: in src local mesh space (cm):
#   X, Y in [-9.4949, +9.4949] cm, Z in [-20.6719, +20.6719] cm
# Notice src in Unity has long axis along Unity Z (±0.207m)!
# In Blender FBX export with apply_scale_options='FBX_SCALE_ALL' and axis_forward='-Z', axis_up='Y':
#   Blender X -> Unity -X (symmetric)
#   Blender Y -> Unity +Z (long axis!)
#   Blender Z -> Unity +Y (up axis!)
# Let's verify: original src had rotation_euler=(+90deg, 0, 0), scale=(0.01, 0.01, 0.01).
# Applying rotation_x(+90deg) maps local (x, y, z) -> (x, -z, y)!
# So in Blender world space (meters):
#   world X = local x * 0.01 (in [-0.095, +0.095])
#   world Y = -local z * 0.01 (in [-0.207, +0.207] -> maps to Unity Z!)
#   world Z = local y * 0.01 (in [-0.095, +0.095] -> maps to Unity Y!)
# Let's build each part directly in Blender world meters with this exact transform so Unity bounds match 100%!

def to_world_m(co_cm):
    # Rotate +90 deg around X and scale by 0.01 (cm -> m)
    return Vector((co_cm.x * 0.01, -co_cm.z * 0.01, co_cm.y * 0.01))

# Remove all imported objects except material
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Clean weld copy of source bmesh to classify faces cleanly
# First split Handle vs Plates from bm_src using Z bounds
# Handle island: all verts have |z| <= 7.75 and r < 4.0
# Plate slices in local Z (cm):
#   Front (+Z in local, -Y in Blender -> +Z in Unity): wait:
#     In Unity FBX import (Blender -Z forward, Y up):
#     Blender +Y -> Unity -Z, Blender -Y -> Unity +Z!
#     So local +Z -> Blender -Y -> Unity +Z! Perfect!
plate_slices = [
    ("Plate_Front_1",   7.3068,  11.7618),
    ("Plate_Front_2",  11.7618,  16.2168),
    ("Plate_Front_3",  16.2168,  20.6719),
    ("Plate_Back_1",  -11.7618,  -7.3068),
    ("Plate_Back_2",  -16.2168, -11.7618),
    ("Plate_Back_3",  -20.6719, -16.2168),
]

def create_mesh_obj(name, bm_part, pivot_world):
    # Recalculate normals outward cleanly
    bmesh.ops.recalc_face_normals(bm_part, faces=bm_part.faces)
    # Shift vertices by -pivot_world so object origin sits at pivot_world
    for v in bm_part.verts:
        v.co -= pivot_world
    # Flat shading (matches PolyRonin low-poly aesthetic)
    for f in bm_part.faces:
        f.smooth = False
    me = bpy.data.meshes.new(name)
    bm_part.to_mesh(me)
    bm_part.free()
    if src_mat is not None:
        me.materials.append(src_mat)
    obj = bpy.data.objects.new(name, me)
    obj.location = pivot_world
    bpy.context.collection.objects.link(obj)
    return obj

# 1. Build Handle directly from source handle faces (all vertices have radius < 4.0 cm)
bm_handle = bmesh.new()
uv_h = bm_handle.loops.layers.uv.new("UVMap")
vert_map = {}
for f in bm_src.faces:
    # Check if handle face (all verts radius < 4.0 cm)
    if all((v.co.x**2 + v.co.y**2)**0.5 < 4.0 for v in f.verts):
        new_verts = []
        for v in f.verts:
            key = (round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
            if key not in vert_map:
                vert_map[key] = bm_handle.verts.new(to_world_m(v.co))
            new_verts.append(vert_map[key])
        try:
            nf = bm_handle.faces.new(new_verts)
            for nl, ol in zip(nf.loops, f.loops):
                if uv_layer:
                    nl[uv_h].uv = ol[uv_layer].uv.copy()
                else:
                    nl[uv_h].uv = handle_uv
        except ValueError:
            pass

# Also cap both ends of Handle (z = ±7.7478) just in case they are open
bmesh.ops.holes_fill(bm_handle, edges=[e for e in bm_handle.edges if e.is_boundary], sides=16)
for f in bm_handle.faces:
    for l in f.loops:
        if l[uv_h].uv.length < 0.001:
            l[uv_h].uv = handle_uv

handle_obj = create_mesh_obj("Handle", bm_handle, Vector((0, 0, 0)))

# 2. Build each of the 6 weight plates cleanly from the exact source faces in that Z slice,
#    then cap any open boundary ring cleanly so every single plate is a 100% solid watertight disc!
eps = 0.05  # 0.5 mm tolerance in cm
plate_objs = []
for pname, zmin, zmax in plate_slices:
    bm_p = bmesh.new()
    uv_p = bm_p.loops.layers.uv.new("UVMap")
    vmap = {}
    for f in bm_src.faces:
        # Skip handle faces
        if all((v.co.x**2 + v.co.y**2)**0.5 < 4.0 for v in f.verts):
            continue
        cz = f.calc_center_median().z
        if zmin - eps <= cz <= zmax + eps:
            # Verify all verts are within slice (excluding faces crossing into neighbor)
            if all(zmin - eps <= v.co.z <= zmax + eps for v in f.verts):
                nvs = []
                for v in f.verts:
                    key = (round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
                    if key not in vmap:
                        vmap[key] = bm_p.verts.new(to_world_m(v.co))
                    nvs.append(vmap[key])
                try:
                    nf = bm_p.faces.new(nvs)
                    for nl, ol in zip(nf.loops, f.loops):
                        if uv_layer:
                            nl[uv_p].uv = ol[uv_layer].uv.copy()
                        else:
                            nl[uv_p].uv = plate_uv
                except ValueError:
                    pass

    # Cap open boundary loops (the cut plane between plates!) with clean flat faces + center fan
    bmesh.ops.remove_doubles(bm_p, verts=bm_p.verts, dist=0.0001)
    boundary_edges = [e for e in bm_p.edges if e.is_boundary]
    if boundary_edges:
        res = bmesh.ops.holes_fill(bm_p, edges=boundary_edges, sides=24)
        for nf in res.get("faces", []):
            # Triangulate/poke cap to match original end cap topology (center vertex fan)
            for l in nf.loops:
                l[uv_p].uv = plate_uv

    # Pivot at exact center of this plate
    z_mid = 0.5 * (zmin + zmax)
    pivot = to_world_m(Vector((0.0, 0.0, z_mid)))
    pobj = create_mesh_obj(pname, bm_p, pivot)
    plate_objs.append(pobj)
    print(f"Created {pname}: verts={len(pobj.data.vertices)}, polys={len(pobj.data.polygons)}, pivot={pivot}")

bm_src.free()

# Save .blend file for future edits
os.makedirs(os.path.dirname(blend_out), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=blend_out)

# Export clean FBX for Unity
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(
    filepath=fbx_out,
    use_selection=True,
    global_scale=1.0,
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y',
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    bake_space_transform=True,
    object_types={'MESH'},
    path_mode='AUTO',
)
print("Exported:", fbx_out)
