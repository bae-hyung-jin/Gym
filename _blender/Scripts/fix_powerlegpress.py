import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

SRC_FBX = r"D:\Unity\Gym\Assets\Gym\PowerLegPress.fbx"
OUT_BLEND = r"D:\Unity\Gym\_blender\Cleaned\PowerLegPress\PowerLegPress_Clean.blend"
OUT_FBX = r"D:\Unity\Gym\_blender\Cleaned\PowerLegPress\PowerLegPress_Clean.fbx"
PREVIEW_DIR = r"C:\Users\User\.gemini\antigravity\brain\5341817e-21d8-4bf0-a858-9b4e0faed54e\scratch"

os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC_FBX)

root = bpy.data.objects["PowerLegPress"]
pivot = bpy.data.objects["Lever_Pivot"]

# -------------------------------------------------------------------------
# 1. Reconstruct true Blender Z-up world transforms (fix broken FBX hierarchy)
# -------------------------------------------------------------------------
true_world = {}
for o in bpy.data.objects:
    if o.parent == pivot:
        pw = pivot.matrix_world.translation
        tx = pw.x + o.location.x
        ty = pivot.location.y + o.location.y
        tz = pivot.location.z + o.location.z
        true_rot = o.rotation_euler.copy()
        true_world[o.name] = Matrix.Translation(Vector((tx, ty, tz))) @ true_rot.to_matrix().to_4x4()
    else:
        true_world[o.name] = o.matrix_world.copy()

pivot_world_pos = true_world["Lever_Pivot"].translation.copy()
true_world["PowerLegPress"] = Matrix.Identity(4)
true_world["Lever_Pivot"] = Matrix.Translation(pivot_world_pos)

parent_map = {o.name: o.parent.name if o.parent else None for o in bpy.data.objects}

for o in bpy.data.objects:
    o.parent = None
    o.matrix_world = true_world[o.name]

bpy.context.view_layer.update()

# Bake mesh object rotations/scales cleanly into mesh data (rot=0, scale=1)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.data:
        rot_scale = o.matrix_world.to_3x3().to_4x4()
        o.data.transform(rot_scale)
        o.data.update()
        pos = o.matrix_world.translation.copy()
        o.matrix_world = Matrix.Translation(pos)

bpy.context.view_layer.update()

# Helper to create clean beveled structural tubes/brackets matching existing style
def make_beveled_box(name, size, center, rot_euler=(0.0, 0.0, 0.0), bevel_width=0.006, mat_name="M_Frame_Silver", parent_name="PowerLegPress"):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel_width > 0:
        bmesh.ops.bevel(
            bm,
            geom=list(bm.edges),
            offset=bevel_width,
            segments=2,
            affect='EDGES',
            clamp_overlap=True,
        )
    if rot_euler != (0.0, 0.0, 0.0):
        bmesh.ops.rotate(bm, verts=bm.verts, matrix=Euler(rot_euler, 'XYZ').to_matrix())
    bm.to_mesh(mesh)
    bm.free()

    for p in mesh.polygons:
        p.use_smooth = False

    mat = bpy.data.materials.get(mat_name)
    if mat:
        mesh.materials.append(mat)

    obj.matrix_world = Matrix.Translation(Vector(center))
    parent_map[name] = parent_name
    return obj

def make_beam_between(name, p0, p1, width_x, thickness_perp, bevel_width=0.005, mat_name="M_Frame_Silver", parent_name="PowerLegPress"):
    """Create a beveled rectangular tube connecting p0 and p1 in the YZ plane (or general 3D)."""
    v0 = Vector(p0)
    v1 = Vector(p1)
    diff = v1 - v0
    length = diff.length
    mid = (v0 + v1) * 0.5
    # Align local Z with diff
    quat = diff.normalized().to_track_quat('Z', 'X')
    return make_beveled_box(
        name=name,
        size=(width_x, thickness_perp, length),
        center=mid,
        rot_euler=tuple(quat.to_euler('XYZ')),
        bevel_width=bevel_width,
        mat_name=mat_name,
        parent_name=parent_name,
    )

def make_cylinder_between(name, p0, p1, radius, segments=20, mat_name="M_Frame_Silver", parent_name="PowerLegPress"):
    v0 = Vector(p0)
    v1 = Vector(p1)
    diff = v1 - v0
    length = diff.length
    mid = (v0 + v1) * 0.5
    quat = diff.normalized().to_track_quat('Z', 'X')

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=length,
    )
    bmesh.ops.rotate(bm, verts=bm.verts, matrix=quat.to_matrix())
    bm.to_mesh(mesh)
    bm.free()

    for p in mesh.polygons:
        p.use_smooth = True

    mat = bpy.data.materials.get(mat_name)
    if mat:
        mesh.materials.append(mat)

    obj.matrix_world = Matrix.Translation(mid)
    parent_map[name] = parent_name
    return obj

# -------------------------------------------------------------------------
# 2. Geometric Refinements (fix misalignments, overlapping plates, floating parts)
# -------------------------------------------------------------------------

# 2A. Align FootPlate_Grip flush on FootPlate front face & FootPlate_Rim at bottom-front heel lip
fp = bpy.data.objects["FootPlate"]
fp_center = fp.matrix_world.translation.copy()
tilt = math.radians(20.0)
u_plate = Vector((0.0, -math.sin(tilt), math.cos(tilt)))  # Up along plate surface
n_plate = Vector((0.0,  math.cos(tilt), math.sin(tilt)))  # Normal facing seat (+Y, +Z)

fp_grip = bpy.data.objects["FootPlate_Grip"]
fp_grip.matrix_world = Matrix.Translation(fp_center + n_plate * 0.020)

fp_rim = bpy.data.objects["FootPlate_Rim"]
fp_rim.matrix_world = Matrix.Translation(fp_center - u_plate * 0.265 + n_plate * 0.015)

# Add twin heavy-duty mounting brackets welding FootPlate back onto Lever_Cross
for side, sx in (("L", -0.22), ("R", 0.22)):
    make_beam_between(
        f"FootPlate_Mount_{side}",
        (sx, -0.65, 0.57),
        (sx, -0.575, 0.60),
        width_x=0.055,
        thickness_perp=0.055,
        bevel_width=0.004,
        mat_name="M_Frame_Graphite",
        parent_name="Lever_Pivot",
    )
    make_beam_between(
        f"FootPlate_Brace_{side}",
        (sx, -0.65, 0.57),
        (sx, -0.645, 0.78),
        width_x=0.045,
        thickness_perp=0.045,
        bevel_width=0.004,
        mat_name="M_Frame_Graphite",
        parent_name="Lever_Pivot",
    )

# 2B. Center Lever_Cross_Low directly onto Lever_Arm_L/R axis (between (-0.88,0.16) and (-0.65,0.57))
# At z=0.32 -> t = 0.16/0.41 = 0.39024 -> y = -0.88 + 0.39024 * 0.23 = -0.7902
lcl = bpy.data.objects["Lever_Cross_Low"]
lcl.matrix_world = Matrix.Translation(Vector((0.0, -0.790, 0.32)))

# 2C. Separate overlapping rear weight storage plates cleanly & extend Storage_Post_L/R
# Lower plate (diam 0.40m) at z=0.24 [0.04..0.44]; Upper plate (diam 0.32m) at z=0.64 [0.48..0.80]
for side, sx in (("L", -0.42), ("R", 0.42)):
    post = bpy.data.objects[f"Storage_Post_{side}"]
    # Stretch post cleanly so bottom stays at z=0.08 and top reaches z=0.72
    wpts = [post.matrix_world @ v.co for v in post.data.vertices]
    zmin = min(p.z for p in wpts)
    zmax = max(p.z for p in wpts)
    old_h = zmax - zmin
    new_zmin, new_zmax = 0.08, 0.72
    new_h = new_zmax - new_zmin
    for v in post.data.vertices:
        wz = post.matrix_world.translation.z + v.co.z
        t = (wz - zmin) / old_h
        new_wz = new_zmin + t * new_h
        v.co.z = new_wz - post.matrix_world.translation.z
    post.data.update()

    # Shift lower horn/plate to z=0.24, upper horn/plate to z=0.64
    for obj_name, target_z in (
        (f"Storage_Horn_{side}1", 0.24),
        (f"Stored_Plate_{side}1", 0.24),
        (f"Storage_Horn_{side}2", 0.64),
        (f"Stored_Plate_{side}2", 0.64),
    ):
        o = bpy.data.objects[obj_name]
        pos = o.matrix_world.translation.copy()
        pos.z = target_z
        o.matrix_world = Matrix.Translation(pos)

# 2D. Ground floating Seat_Frame & Back_Post onto base chassis
# Seat_Frame runs diagonally: front end near (0, -0.15, 0.27), back end near (0, 0.48, 0.16)
make_beveled_box(
    "Base_Cross_Seat_Front",
    size=(0.84, 0.075, 0.075),
    center=(0.0, -0.06, 0.06),
    bevel_width=0.006,
    mat_name="M_Frame_Silver",
    parent_name="PowerLegPress",
)
make_beveled_box(
    "Base_Cross_Seat_Back",
    size=(0.84, 0.075, 0.075),
    center=(0.0, 0.44, 0.06),
    bevel_width=0.006,
    mat_name="M_Frame_Silver",
    parent_name="PowerLegPress",
)
make_beam_between(
    "Seat_Support_Front",
    (0.0, -0.06, 0.06),
    (0.0, -0.06, 0.255),
    width_x=0.095,
    thickness_perp=0.095,
    bevel_width=0.006,
    mat_name="M_Frame_Silver",
    parent_name="PowerLegPress",
)
make_beam_between(
    "Seat_Support_Back",
    (0.0, 0.44, 0.06),
    (0.0, 0.44, 0.175),
    width_x=0.095,
    thickness_perp=0.095,
    bevel_width=0.006,
    mat_name="M_Frame_Silver",
    parent_name="PowerLegPress",
)
# Heavy diagonal backrest rear strut connecting Base_Cross_Back to Back_Post
make_beam_between(
    "Backrest_Rear_Strut",
    (0.0, 0.68, 0.07),
    (0.0, 0.56, 0.72),
    width_x=0.075,
    thickness_perp=0.075,
    bevel_width=0.006,
    mat_name="M_Frame_Silver",
    parent_name="PowerLegPress",
)

# 2E. Ground floating Safety_Lever onto Base_Rail_R with a clean pivot bracket
# Replace/extend Safety_Lever mesh so it runs cleanly from Base_Rail_R mount up to Safety_Knob
knob = bpy.data.objects["Safety_Knob"]
knob_pos = knob.matrix_world.translation.copy()  # (0.38, -0.12, 0.64)
lever_base_pos = Vector((0.38, -0.02, 0.08))

# Rebuild Safety_Lever geometry cleanly in-place (keeps exact object name & material!)
safety_lever = bpy.data.objects["Safety_Lever"]
bm = bmesh.new()
diff = knob_pos - lever_base_pos
bmesh.ops.create_cone(
    bm,
    cap_ends=True,
    cap_tris=False,
    segments=16,
    radius1=0.014,
    radius2=0.012,
    depth=diff.length,
)
bmesh.ops.rotate(bm, verts=bm.verts, matrix=diff.normalized().to_track_quat('Z', 'X').to_matrix())
bm.to_mesh(safety_lever.data)
bm.free()
for p in safety_lever.data.polygons:
    p.use_smooth = True
safety_lever.data.update()
safety_lever.matrix_world = Matrix.Translation((lever_base_pos + knob_pos) * 0.5)

make_beveled_box(
    "Safety_Bracket",
    size=(0.08, 0.085, 0.09),
    center=(0.40, -0.02, 0.08),
    bevel_width=0.005,
    mat_name="M_Frame_Graphite",
    parent_name="PowerLegPress",
)

# 2F. Ground floating Start_Stop bumper bar onto Base_Cross_Mid with twin brackets
for side, sx in (("L", -0.28), ("R", 0.28)):
    make_beam_between(
        f"Start_Stop_Bracket_{side}",
        (sx, -0.45, 0.065),
        (sx, -0.50, 0.195),
        width_x=0.045,
        thickness_perp=0.045,
        bevel_width=0.004,
        mat_name="M_Frame_Graphite",
        parent_name="PowerLegPress",
    )

# 2G. Mount Placard_Panel / Placard / Placard_Text flush against Front_Guard_R (close 1.5cm air gap)
for name in ("Placard_Panel", "Placard", "Placard_Text"):
    o = bpy.data.objects[name]
    pos = o.matrix_world.translation.copy()
    pos.x -= 0.017
    o.matrix_world = Matrix.Translation(pos)

bpy.context.view_layer.update()

# -------------------------------------------------------------------------
# 3. Reparent cleanly with Identity matrix_parent_inverse
# -------------------------------------------------------------------------
for name, pname in parent_map.items():
    if pname is None or name not in bpy.data.objects:
        continue
    o = bpy.data.objects[name]
    p = bpy.data.objects[pname]
    w_mat = o.matrix_world.copy()
    o.parent = p
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_local = p.matrix_world.inverted() @ w_mat

bpy.context.view_layer.update()

# -------------------------------------------------------------------------
# 4. Save clean .blend and export clean .fbx
# -------------------------------------------------------------------------
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(
    filepath=OUT_FBX,
    use_selection=True,
    object_types={'MESH', 'EMPTY'},
    path_mode='AUTO',
    embed_textures=False,
)
print(f"Saved {OUT_BLEND} ({os.path.getsize(OUT_BLEND)/1024:.1f} KB)")
print(f"Saved {OUT_FBX} ({os.path.getsize(OUT_FBX)/1024:.1f} KB)")

# -------------------------------------------------------------------------
# 5. Render verification previews (temp lights + camera NOT saved!)
# -------------------------------------------------------------------------
all_wpts = [o.matrix_world @ v.co for o in bpy.data.objects if o.type == 'MESH' for v in o.data.vertices]
bmin = Vector((min(p.x for p in all_wpts), min(p.y for p in all_wpts), min(p.z for p in all_wpts)))
bmax = Vector((max(p.x for p in all_wpts), max(p.y for p in all_wpts), max(p.z for p in all_wpts)))
center = (bmin + bmax) * 0.5
size = bmax - bmin
radius = max(size.x, size.y, size.z, 0.5)
print("FINAL WORLD BB:", tuple(round(v, 3) for v in bmin), "..", tuple(round(v, 3) for v in bmax), "size=", tuple(round(v, 3) for v in size))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 1024
scene.render.resolution_y = 768

world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.18, 0.20, 0.24, 1.0)

def add_light(loc, energy):
    ld = bpy.data.lights.new("L", type='AREA'); ld.energy = energy; ld.size = 3.0
    lo = bpy.data.objects.new("L", ld); lo.location = loc
    lo.rotation_euler = (center - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.collection.objects.link(lo)

d = radius * 1.40
add_light((center.x + d, center.y - d, center.z + d), 420)
add_light((center.x - d, center.y - d * 0.7, center.z + d * 0.8), 240)
add_light((center.x, center.y + d, center.z + d), 240)

cd = bpy.data.cameras.new("C"); cd.lens = 45
co = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(co); scene.camera = co

views = [
    ("clean_iso1.png", center + Vector((-d * 0.90, -d * 0.90, d * 0.52))),
    ("clean_iso2.png", center + Vector(( d * 0.90,  d * 0.90, d * 0.52))),
    ("clean_side.png", center + Vector(( d * 1.25,  0.0,      d * 0.08))),
    ("clean_front.png", center + Vector((0.0,      -d * 1.20, d * 0.20))),
]

for fname, pos in views:
    co.location = pos
    co.rotation_euler = (center - pos).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(PREVIEW_DIR, fname)
    bpy.ops.render.render(write_still=True)

# Also render a pressed-pose verification shot (Lever_Pivot rotated +25 deg X)
pivot.rotation_euler = Euler((math.radians(25.0), 0.0, 0.0), 'XYZ')
bpy.context.view_layer.update()
pos = center + Vector((d * 1.25, 0.0, d * 0.08))
co.location = pos
co.rotation_euler = (center - pos).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = os.path.join(PREVIEW_DIR, "clean_side_pressed.png")
bpy.ops.render.render(write_still=True)
print("All verification renders completed.")
