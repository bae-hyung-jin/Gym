import bpy, math, os
from mathutils import Vector

OUT_FBX = r"G:\Unity_Gym\AI-Gym\Assets\Bomio_Exercises\Equipment\Gym_TabletStand.fbx"
os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

def make_mat(name, rgba, met=0.0, rough=0.4):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Metallic"].default_value = met
        bsdf.inputs["Roughness"].default_value = rough
    return m

m_base   = make_mat("Mat_Tablet_Stand",  (0.11, 0.12, 0.15, 1.0), met=0.45, rough=0.38)
m_chrome = make_mat("Mat_Tablet_Chrome", (0.82, 0.85, 0.88, 1.0), met=0.92, rough=0.18)
m_bezel  = make_mat("Mat_Tablet_Bezel",  (0.06, 0.07, 0.09, 1.0), met=0.25, rough=0.28)
m_screen = make_mat("Mat_Tablet_Screen", (0.12, 0.58, 0.50, 1.0), met=0.05, rough=0.14)

def add_cyl(name, r, depth, loc, rot=(0,0,0), mat=None, segs=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segs, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    if mat: o.data.materials.append(mat)
    return o

def add_box(name, size, loc, rot=(0,0,0), mat=None, bevel=0.008):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        mod = o.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        bpy.ops.object.modifier_apply(modifier="Bevel")
    if mat: o.data.materials.append(mat)
    return o

# 1. Weighted floor base + rubber foot ring
add_cyl("Stand_BasePlate",  0.19, 0.024, (0, 0, 0.012), mat=m_base)
add_cyl("Stand_BaseAccent", 0.195, 0.006, (0, 0, 0.025), mat=m_chrome)

# 2. Upright sleek column (H = 1.15m) + chrome collar
add_cyl("Stand_Column",       0.028, 1.12, (0, 0, 0.58), mat=m_base)
add_cyl("Stand_Collar_Bot",   0.042, 0.04, (0, 0, 0.044), mat=m_chrome)
add_cyl("Stand_Collar_Top",   0.036, 0.03, (0, 0, 1.14), mat=m_chrome)

# 3. Tilted ergonomic tablet housing (tilted 38 deg back so user looking from -Y sees screen clearly!)
tilt = math.radians(52.0) # screen faces -Y and UP (+Z)
piv = bpy.data.objects.new("Tablet_Head", None)
bpy.context.scene.collection.objects.link(piv)
piv.location = (0, -0.02, 1.22)
piv.rotation_euler = (tilt, 0, 0)

bezel  = add_box("Tablet_Bezel",  (0.38, 0.26, 0.020), (0, 0, 0), mat=m_bezel, bevel=0.009)
trim   = add_box("Tablet_Trim",   (0.386, 0.266, 0.008), (0, 0, -0.002), mat=m_chrome, bevel=0.004)
screen = add_box("Tablet_Screen", (0.34, 0.22, 0.004), (0, 0, 0.011), mat=m_screen, bevel=0.001)
# Small mint power/home button indicator on bezel
btn    = add_cyl("Tablet_HomeBtn", 0.008, 0.005, (0, -0.118, 0.010), mat=m_chrome, segs=20)

for ch in (bezel, trim, screen, btn):
    ch.parent = piv

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(
    filepath=OUT_FBX,
    use_selection=True,
    object_types={'MESH', 'EMPTY'},
    use_mesh_modifiers=True,
    apply_scale_options='FBX_SCALE_NONE',
    axis_forward='-Z',
    axis_up='Y',
)
print(f"Exported 3D Gym Tablet Stand: {OUT_FBX} ({os.path.getsize(OUT_FBX):,} bytes)")
