import bpy
import math
import os
from mathutils import Vector, Matrix, Euler

SRC_FBX = r"G:\Unity_Gym\AI-Gym\Assets\Gym\ChestPress.fbx"
OUT_BLEND = r"G:\Unity_Gym\AI-Gym\_blender\ChestPress_Clean.blend"
OUT_FBX = r"G:\Unity_Gym\AI-Gym\_blender\ChestPress_Clean.fbx"
RENDER_OUT = r"C:\Users\hyung\.gemini\antigravity\brain\bc816dce-1a90-4961-b863-c22ec5353e0c\scratch\chestpress_clean_preview.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC_FBX)

root = bpy.data.objects["ChestPress"]
pivot = bpy.data.objects["PressArm_Pivot"]
stack = bpy.data.objects["Weight_Stack"]

# First fix the double-rotated/swapped children of PressArm_Pivot and Weight_Stack
# In the broken FBX, each child c of p (where p has localPos (px, py, pz) in +90X ChestPress):
#   true_world_pos = (p.world.x + c.loc.x, p.loc.y + c.loc.y, p.loc.z + c.loc.z)
#   true_world_rot = (0, 0, 0) (or +90X? Let's check mesh bounding dimensions of Arm_Hub_L & Plate_1 first!)
for check_name in ("Plate_Fixed_4", "Plate_1", "Press_Arm_L", "Grip_Horizontal_L", "Grip_Vertical_L"):
    o = bpy.data.objects[check_name]
    pts = [v.co for v in o.data.vertices]
    xs=[v.x for v in pts]; ys=[v.y for v in pts]; zs=[v.z for v in pts]
    print(f"LOCAL MESH {check_name:20s}: dx={max(xs)-min(xs):.3f} dy={max(ys)-min(ys):.3f} dz={max(zs)-min(zs):.3f} | worldRot={tuple(round(math.degrees(a),1) for a in o.matrix_world.to_euler())}")

# Notice: Plate_Fixed_4 is a direct child of ChestPress (+90X) with localRot=(0,0,0) -> worldRot=(+90, 0, 0)!
# Wait: Plate_1 has localRot=(+90, 0, 0) inside ChestPress (+90X) -> worldRot=(180, 0, 0)!
# So if Plate_1's mesh axes match Plate_Fixed_4's mesh axes, true_world_rot = (+90, 0, 0) (same as Plate_Fixed_4!),
# OR if Plate_1's mesh axes are already Z-up, true_world_rot = (0, 0, 0)! Let's check automatically by comparing dz vs dy of Plate_1 vs Plate_Fixed_4!
pf4 = bpy.data.objects["Plate_Fixed_4"]
p1  = bpy.data.objects["Plate_1"]
pf4_sz = Vector((max(v.co.x for v in pf4.data.vertices)-min(v.co.x for v in pf4.data.vertices),
                 max(v.co.y for v in pf4.data.vertices)-min(v.co.y for v in pf4.data.vertices),
                 max(v.co.z for v in pf4.data.vertices)-min(v.co.z for v in pf4.data.vertices)))
p1_sz  = Vector((max(v.co.x for v in p1.data.vertices)-min(v.co.x for v in p1.data.vertices),
                 max(v.co.y for v in p1.data.vertices)-min(v.co.y for v in p1.data.vertices),
                 max(v.co.z for v in p1.data.vertices)-min(v.co.z for v in p1.data.vertices)))
# Plate thickness is 0.032m! If p1_sz.z is ~0.032, mesh is Z-up (needs worldRot=0); if p1_sz.y is ~0.032, mesh is Y-up (needs worldRot=+90X)
child_world_rot = Euler((0.0, 0.0, 0.0), 'XYZ') if p1_sz.z < p1_sz.y else Euler((math.pi / 2.0, 0.0, 0.0), 'XYZ')
print("Detected child mesh orientation -> child_world_rot deg:", tuple(round(math.degrees(a), 1) for a in child_world_rot))

# Record exact true world transforms for EVERY object first, then rebuild clean Blender Z-up hierarchy!
true_world = {}
for o in bpy.data.objects:
    if o.parent in (pivot, stack):
        p = o.parent
        pw = p.matrix_world.translation
        tx = pw.x + o.location.x
        ty = p.location.y + o.location.y
        tz = p.location.z + o.location.z
        true_world[o.name] = Matrix.Translation(Vector((tx, ty, tz))) @ child_world_rot.to_matrix().to_4x4()
    else:
        true_world[o.name] = o.matrix_world.copy()

# Normalize parent Empties (ChestPress, PressArm_Pivot, Weight_Stack) to clean identity Z-up rotation (0, 0, 0)!
# That way in Blender: PressArm_Pivot rotates cleanly on X, Weight_Stack moves cleanly on Z!
pivot_world_pos = true_world["PressArm_Pivot"].translation.copy()
stack_world_pos = true_world["Weight_Stack"].translation.copy()

true_world["ChestPress"]     = Matrix.Identity(4)
true_world["PressArm_Pivot"] = Matrix.Translation(pivot_world_pos)
true_world["Weight_Stack"]   = Matrix.Translation(stack_world_pos)

# Apply clean hierarchy & world matrices
# Unparent all first, set world transforms, then reparent cleanly with exact matrix_parent_inverse = Identity!
parent_map = {o.name: o.parent.name if o.parent else None for o in bpy.data.objects}

for o in bpy.data.objects:
    o.parent = None
    o.matrix_world = true_world[o.name]

bpy.context.view_layer.update()

# Bake mesh object rotations cleanly into their mesh data so every object has rotation=(0,0,0) and scale=(1,1,1)!
for o in bpy.data.objects:
    if o.type == 'MESH':
        rot_scale = o.matrix_world.to_3x3().to_4x4()
        o.data.transform(rot_scale)
        o.data.update()
        pos = o.matrix_world.translation.copy()
        o.matrix_world = Matrix.Translation(pos)

# Reparent cleanly with clean local offsets (matrix_parent_inverse = Identity)
for name, pname in parent_map.items():
    if pname is None:
        continue
    o = bpy.data.objects[name]
    p = bpy.data.objects[pname]
    w_mat = o.matrix_world.copy()
    o.parent = p
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_local = p.matrix_world.inverted() @ w_mat

bpy.context.view_layer.update()

# Verify key assembled positions!
for n in ("Pivot_Housing_L", "Arm_Hub_L", "Press_Arm_L", "Grip_Horizontal_L", "Plate_Fixed_4", "Plate_1", "Head_Plate", "Selector_Pin"):
    o = bpy.data.objects[n]
    print(f"ASSEMBLED {n:20s}: worldPos={tuple(round(v,3) for v in o.matrix_world.translation)} parent={o.parent.name if o.parent else None}")

# Save clean .blend and export clean .fbx!
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(
    filepath=OUT_FBX,
    use_selection=True,
    object_types={'MESH', 'EMPTY'},
    path_mode='AUTO',
    embed_textures=False,
)
print(f"Saved {OUT_BLEND} & {OUT_FBX} ({os.path.getsize(OUT_FBX)/1024:.1f} KB)")

# Render verification preview (temp lights + camera NOT saved!)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 960
scene.render.resolution_y = 720
world = bpy.data.worlds.new("W")
scene.world = world
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.18, 0.20, 0.24, 1.0)

def add_light(loc, energy):
    ld = bpy.data.lights.new("L", type='AREA'); ld.energy = energy; ld.size = 3.0
    lo = bpy.data.objects.new("L", ld); lo.location = loc
    lo.rotation_euler = (Vector((0.2, 0.0, 0.8)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.collection.objects.link(lo)

add_light(( 2.5, -2.5, 2.8), 350)
add_light((-2.5, -1.8, 2.0), 180)
add_light(( 0.0,  2.5, 2.5), 180)

cd = bpy.data.cameras.new("C"); cd.lens = 45
co = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(co); scene.camera = co
co.location = Vector((-1.9, -2.2, 1.65))
co.rotation_euler = (Vector((0.15, 0.10, 0.82)) - co.location).to_track_quat('-Z', 'Y').to_euler()

scene.render.filepath = RENDER_OUT
bpy.ops.render.render(write_still=True)
print("Rendered preview:", RENDER_OUT)
