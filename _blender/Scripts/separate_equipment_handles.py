r"""
Separate usable handle / moving lever parts on 3 gym equipment FBX models
so Player_Bomio (Mixamo IK) and Unity animations can grab & move them cleanly:
1. pullupbar.fbx
   -> PullUp_Frame, PullUp_TopBar, PullUp_DipBar_L, PullUp_DipBar_R + Grip Empties
2. ArmCurlBench_A_Collar.fbx
   -> ArmCurl_Frame, ArmCurl_LeverArm (pivoted on top hinge!),
      ArmCurl_Handles (child of LeverArm, pivoted on lower handle axle!),
      ArmCurl_WeightHorn + Grip_L / Grip_R Empties
3. ArmCurlBench_B_Symmetric.fbx
   -> Same clean hierarchy & pivots!

Outputs (without touching original source files):
- Blender files: G:\Unity_Gym\AI-Gym\_blender\Blend\<Name>_Separated.blend
- Unity FBX files: G:\Unity_Gym\AI-Gym\Assets\Gym\Separated\<Name>_Separated.fbx
"""
import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import Vector, Matrix

SRC_DIR    = r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\김태현"
OUT_BLEND  = r"G:\Unity_Gym\AI-Gym\_blender\Bomio_Exercises\02_Equipment_Separated"
OUT_FBX    = r"G:\Unity_Gym\AI-Gym\Assets\Bomio_Exercises\Equipment"
SCRATCH    = r"C:\Users\hyung\.gemini\antigravity\brain\bc816dce-1a90-4961-b863-c22ec5353e0c\scratch"

os.makedirs(OUT_BLEND, exist_ok=True)
os.makedirs(OUT_FBX, exist_ok=True)
os.makedirs(SCRATCH, exist_ok=True)

def set_origin_world(obj, world_pos):
    """Move object origin to world_pos without moving its geometry in world space."""
    mw = obj.matrix_world.copy()
    new_mw = Matrix.Translation(world_pos)
    delta = new_mw.inverted() @ mw
    obj.data.transform(delta)
    obj.matrix_world = new_mw
    obj.data.update()

def create_mesh_obj(name, bm, materials, parent=None, origin_world=None):
    """Create a clean Blender mesh object from a world-space BMesh."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    # Fill tiny boundary holes created by separation cuts (skip huge holes)
    open_edges = [e for e in bm.edges if e.is_boundary]
    if open_edges:
        try:
            bmesh.ops.holes_fill(bm, edges=open_edges, sides=64)
        except Exception:
            pass
    bm.normal_update()

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in materials:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True

    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if origin_world is not None:
        set_origin_world(ob, Vector(origin_world))
    if parent is not None:
        mw = ob.matrix_world.copy()
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
        ob.matrix_world = mw
    return ob

def add_grip_empty(name, world_pos, parent, rot_euler=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'ARROWS'
    e.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(e)
    e.location = Vector(world_pos)
    e.rotation_euler = rot_euler
    if parent is not None:
        mw = e.matrix_world.copy()
        e.parent = parent
        e.matrix_parent_inverse = parent.matrix_world.inverted()
        e.matrix_world = mw
    return e

def extract_submesh(bm_src, face_set):
    """Copy a set of BMFace objects into a brand new BMesh preserving UVs and material indices."""
    new_bm = bmesh.new()
    src_uv = bm_src.loops.layers.uv.active
    dst_uv = new_bm.loops.layers.uv.new(src_uv.name) if src_uv else None
    vmap = {}
    for f in face_set:
        vs = []
        for v in f.verts:
            if v.index not in vmap:
                vmap[v.index] = new_bm.verts.new(v.co)
            vs.append(vmap[v.index])
        try:
            nf = new_bm.faces.new(vs)
            nf.material_index = f.material_index
            nf.smooth = f.smooth
            if src_uv and dst_uv:
                for sl, dl in zip(f.loops, nf.loops):
                    dl[dst_uv].uv = sl[src_uv].uv.copy()
        except ValueError:
            pass
    new_bm.normal_update()
    return new_bm

def flood_faces(start_faces, allowed_face_fn):
    """BFS flood-fill across faces sharing vertices, staying inside allowed_face_fn."""
    visited = set(start_faces)
    queue = list(start_faces)
    while queue:
        f = queue.pop()
        for v in f.verts:
            for nf in v.link_faces:
                if nf not in visited and allowed_face_fn(nf):
                    visited.add(nf)
                    queue.append(nf)
    return visited

def export_clean_fbx(fbx_path):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.fbx(
        filepath=fbx_path,
        use_selection=True,
        object_types={'MESH', 'EMPTY'},
        use_mesh_modifiers=True,
        bake_anim=False,
        apply_scale_options='FBX_SCALE_NONE',
        axis_forward='-Z',
        axis_up='Y',
        path_mode='COPY',
        embed_textures=True,
    )

def make_debug_mat(name, rgba):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = 0.45
    return m

def render_verify(tag, cam_loc, cam_tgt, color_map=None, test_rot=None):
    """Render a quick visual verification shot (with temporary debug colors & optional pivot rotation test)."""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = sc.render.resolution_y = 640
    w = bpy.data.worlds.new("VW")
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs["Color"].default_value = (0.20, 0.23, 0.28, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    sc.world = w

    lights = []
    for nm, rot, en in [("VL1", (math.radians(40), 0, math.radians(30)), 3.0),
                        ("VL2", (math.radians(55), 0, math.radians(-135)), 1.5)]:
        ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = en
        lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo); lo.rotation_euler = rot
        lights.append((lo, ld))

    cd = bpy.data.cameras.new("VC")
    cam = bpy.data.objects.new("VC", cd); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = Vector(cam_loc)
    cam.rotation_euler = (Vector(cam_tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()

    # Save originals
    saved_mats = {}
    if color_map:
        for ob_name, rgba in color_map.items():
            ob = bpy.data.objects.get(ob_name)
            if ob and ob.type == 'MESH':
                saved_mats[ob_name] = list(ob.data.materials)
                ob.data.materials.clear()
                ob.data.materials.append(make_debug_mat(f"DBG_{ob_name}", rgba))
    saved_rots = {}
    if test_rot:
        for ob_name, rot in test_rot.items():
            ob = bpy.data.objects.get(ob_name)
            if ob:
                saved_rots[ob_name] = ob.rotation_euler.copy()
                ob.rotation_euler = rot

    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(SCRATCH, f"verify_{tag}.png")
    bpy.ops.render.render(write_still=True)

    # Restore everything cleanly before saving!
    for ob_name, rot in saved_rots.items():
        bpy.data.objects[ob_name].rotation_euler = rot
    for ob_name, mats in saved_mats.items():
        ob = bpy.data.objects[ob_name]
        ob.data.materials.clear()
        for m in mats:
            ob.data.materials.append(m)
    bpy.data.objects.remove(cam); bpy.data.cameras.remove(cd)
    for lo, ld in lights:
        bpy.data.objects.remove(lo); bpy.data.lights.remove(ld)
    bpy.context.view_layer.update()

# ==============================================================================
# 1. PULL-UP BAR (Top Pull-Up Handle Bar + Left/Right Dip Handle Bars)
# ==============================================================================
def process_pullupbar():
    src = os.path.join(SRC_DIR, "pullupbar.fbx")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=src)
    bpy.context.view_layer.update()

    orig = next(o for o in bpy.data.objects if o.type == 'MESH')
    mats = list(orig.data.materials)

    bm = bmesh.new()
    bm.from_mesh(orig.data)
    bmesh.ops.transform(bm, matrix=orig.matrix_world, verts=bm.verts)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Clean bisect cuts at the exact handle-to-frame junctions:
    # (a) Top pull-up bar rests on top of the two curved upright brackets around Z = 0.962 (in front Y < 0.048)
    #     Notice outer angled grip ends drop down to Z ~ 0.925 outside |X| > 0.165!
    #     So cut ONLY the two mounting collars inside |X| < 0.175 at Z = 0.962 (and Y = 0.036 at Z > 0.95)
    top_cut_geom = [f for f in bm.faces if 0.945 <= f.calc_center_median().z <= 0.985 and abs(f.calc_center_median().x) < 0.18]
    top_edges = list({e for f in top_cut_geom for e in f.edges})
    top_verts = list({v for f in top_cut_geom for v in f.verts})
    if top_cut_geom:
        bmesh.ops.bisect_plane(bm, geom=top_cut_geom + top_edges + top_verts,
                               plane_co=(0.0, 0.0, 0.966), plane_no=(0.0, 0.0, 1.0))

    # (b) Left & Right Dip bars stick straight forward (-Y) from vertical posts at Y = +0.055, Z in [0.515, 0.568]
    dip_cut_geom = [f for f in bm.faces if 0.505 <= f.calc_center_median().z <= 0.575 and 0.025 <= f.calc_center_median().y <= 0.080]
    dip_edges = list({e for f in dip_cut_geom for e in f.edges})
    dip_verts = list({v for f in dip_cut_geom for v in f.verts})
    if dip_cut_geom:
        bmesh.ops.bisect_plane(bm, geom=dip_cut_geom + dip_edges + dip_verts,
                               plane_co=(0.0, 0.052, 0.540), plane_no=(0.0, -1.0, 0.0))

    bm.verts.index_update()
    bm.faces.index_update()

    # Flood-fill Top Pull-Up Bar from center bar (|X| < 0.06, Z > 0.97)
    top_seeds = [f for f in bm.faces if abs(f.calc_center_median().x) < 0.08 and f.calc_center_median().z > 0.972]
    def is_top_bar(f):
        c = f.calc_center_median()
        if abs(c.x) > 0.165:
            return c.z > 0.910 and c.y < 0.055  # outer angled grips drop slightly below 0.966!
        return c.z >= 0.966 and c.y < 0.055
    top_faces = flood_faces(top_seeds, is_top_bar)

    # Flood-fill Dip Bar Left (X > 0) and Right (X < 0)
    dip_l_seeds = [f for f in bm.faces if f.calc_center_median().x > 0.10 and f.calc_center_median().y < -0.05 and 0.515 < f.calc_center_median().z < 0.565]
    dip_r_seeds = [f for f in bm.faces if f.calc_center_median().x < -0.10 and f.calc_center_median().y < -0.05 and 0.515 < f.calc_center_median().z < 0.565]
    dip_l_faces = flood_faces(dip_l_seeds, lambda f: f.calc_center_median().y <= 0.0525 and 0.505 < f.calc_center_median().z < 0.575 and f.calc_center_median().x > 0.05)
    dip_r_faces = flood_faces(dip_r_seeds, lambda f: f.calc_center_median().y <= 0.0525 and 0.505 < f.calc_center_median().z < 0.575 and f.calc_center_median().x < -0.05)

    used = top_faces | dip_l_faces | dip_r_faces
    frame_faces = [f for f in bm.faces if f not in used]

    print(f"[PullUpBar] Frame={len(frame_faces)} TopBar={len(top_faces)} DipL={len(dip_l_faces)} DipR={len(dip_r_faces)}")

    # Compute exact centers for pivots & grips
    def f_bounds(fset):
        pts = np.array([v.co for f in fset for v in f.verts])
        return pts.min(axis=0), pts.max(axis=0), pts.mean(axis=0)

    t_lo, t_hi, t_ctr = f_bounds(top_faces)
    dl_lo, dl_hi, dl_ctr = f_bounds(dip_l_faces)
    dr_lo, dr_hi, dr_ctr = f_bounds(dip_r_faces)

    # Remove original merged mesh
    bpy.data.objects.remove(orig, do_unlink=True)

    root = bpy.data.objects.new("PullUpBar_Root", None)
    bpy.context.scene.collection.objects.link(root)

    ob_frame = create_mesh_obj("PullUp_Frame",    extract_submesh(bm, frame_faces), mats, parent=root, origin_world=(0, 0, 0))
    ob_top   = create_mesh_obj("PullUp_TopBar",   extract_submesh(bm, top_faces),   mats, parent=root, origin_world=(0.0, float(t_ctr[1]), float((t_lo[2]+t_hi[2])*0.5)))
    ob_dipl  = create_mesh_obj("PullUp_DipBar_L", extract_submesh(bm, dip_l_faces), mats, parent=root, origin_world=(float(dl_ctr[0]), 0.052, float(dl_ctr[2])))
    ob_dipr  = create_mesh_obj("PullUp_DipBar_R", extract_submesh(bm, dip_r_faces), mats, parent=root, origin_world=(float(dr_ctr[0]), 0.052, float(dr_ctr[2])))
    bm.free()

    # Add convenient Grip Empties for avatar IK hand snapping!
    bar_y = float(t_ctr[1])
    bar_z = float(t_hi[2] - 0.012)
    add_grip_empty("Grip_PullUp_L",     ( 0.11, bar_y, bar_z), ob_top)
    add_grip_empty("Grip_PullUp_R",     (-0.11, bar_y, bar_z), ob_top)
    add_grip_empty("Grip_WidePullUp_L", ( 0.22, bar_y, bar_z - 0.015), ob_top)
    add_grip_empty("Grip_WidePullUp_R", (-0.22, bar_y, bar_z - 0.015), ob_top)
    add_grip_empty("Grip_Dip_L",        (float(dl_ctr[0]), float((dl_lo[1]+dl_hi[1])*0.5 - 0.02), float(dl_ctr[2])), ob_dipl)
    add_grip_empty("Grip_Dip_R",        (float(dr_ctr[0]), float((dr_lo[1]+dr_hi[1])*0.5 - 0.02), float(dr_ctr[2])), ob_dipr)

    # Visual verification (color-coded separated parts!)
    render_verify(
        "pullupbar_sep",
        cam_loc=(1.1, -1.35, 0.78),
        cam_tgt=(0.0, 0.0, 0.55),
        color_map={
            "PullUp_Frame":    (0.35, 0.38, 0.42, 1.0),
            "PullUp_TopBar":   (0.15, 0.85, 0.35, 1.0),
            "PullUp_DipBar_L": (0.95, 0.45, 0.10, 1.0),
            "PullUp_DipBar_R": (0.95, 0.45, 0.10, 1.0),
        }
    )

    blend_out = os.path.join(OUT_BLEND, "PullUpBar_Separated.blend")
    fbx_out   = os.path.join(OUT_FBX,   "PullUpBar_Separated.fbx")
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    export_clean_fbx(fbx_out)
    print(f"  Saved: {blend_out} & {fbx_out} ({os.path.getsize(fbx_out)/1024:.1f} KB)")

# ==============================================================================
# 2 & 3. ARM CURL BENCH A & B (Frame + Pivoted LeverArm + Swivel Handles + WeightHorn)
# ==============================================================================
def process_armcurl(filename, tag):
    src = os.path.join(SRC_DIR, filename)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=src)
    bpy.context.view_layer.update()

    orig = next(o for o in bpy.data.objects if o.type == 'MESH')
    mats = list(orig.data.materials)

    bm = bmesh.new()
    bm.from_mesh(orig.data)
    bmesh.ops.transform(bm, matrix=orig.matrix_world, verts=bm.verts)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Step 1: Extract loose island #1 (WeightHorn) first
    visited = set()
    islands = []
    for v in bm.verts:
        if v.index in visited: continue
        st = [v]; visited.add(v.index); comp = []
        while st:
            c = st.pop(); comp.append(c)
            for e in c.link_edges:
                nb = e.other_vert(c)
                if nb.index not in visited:
                    visited.add(nb.index); st.append(nb)
        islands.append(comp)
    islands.sort(key=len, reverse=True)
    horn_vset = set(v.index for v in islands[1]) if len(islands) > 1 else set()
    horn_faces = {f for f in bm.faces if any(v.index in horn_vset for v in f.verts)}

    # Step 2: Cleanly slice the top hinge neck where diagonal lever connects to horizontal frame bar!
    # Look at side view: horizontal bar runs from Y=0.0 forward to hinge at (Y ~ -0.145, Z ~ 0.655).
    # Bisect plane at Y = -0.132 cleanly separates the rotating lever arm from the stationary support bar!
    hinge_geom = [f for f in bm.faces if f not in horn_faces
                  and abs(f.calc_center_median().x) < 0.10
                  and 0.59 <= f.calc_center_median().z <= 0.72
                  and -0.18 <= f.calc_center_median().y <= -0.09]
    h_edges = list({e for f in hinge_geom for e in f.edges})
    h_verts = list({v for f in hinge_geom for v in f.verts})
    if hinge_geom:
        bmesh.ops.bisect_plane(bm, geom=hinge_geom + h_edges + h_verts,
                               plane_co=(0.0, -0.132, 0.655), plane_no=(0.0, -1.0, 0.0))

    # Also bisect cleanly at the lower handle-swivel axle (around Y = -0.355, Z = 0.390)
    # Wait: the V-handle rises UP and slightly FORWARD/BACK from the bottom bracket!
    # Let's first isolate the FULL moving assembly (LeverArm + Handles) via flood-fill from chrome grips!
    bm.verts.index_update()
    bm.faces.index_update()
    horn_faces = {f for f in bm.faces if f.calc_center_median().y > -0.245 and f.calc_center_median().y < -0.135
                  and 0.35 < f.calc_center_median().z < 0.455 and abs(f.calc_center_median().x) < 0.305}
    # Re-detect exact loose island for horn after bisect (cleanest!)
    visited2 = set(); islands2 = []
    for v in bm.verts:
        if v.index in visited2: continue
        st = [v]; visited2.add(v.index); comp = []
        while st:
            c = st.pop(); comp.append(c)
            for e in c.link_edges:
                nb = e.other_vert(c)
                if nb.index not in visited2:
                    visited2.add(nb.index); st.append(nb)
        islands2.append(comp)
    islands2.sort(key=len, reverse=True)
    # Find the island matching weight horn (around 2500 verts)
    horn_vset2 = set()
    for isl in islands2[1:]:
        if 1500 < len(isl) < 5000:
            horn_vset2 = set(v.index for v in isl)
            break
    horn_faces = {f for f in bm.faces if any(v.index in horn_vset2 for v in f.verts)}

    # Seed flood-fill on both chrome horizontal hand grips!
    grip_seeds = [f for f in bm.faces if f not in horn_faces
                  and 0.16 < abs(f.calc_center_median().x) < 0.30
                  and -0.36 < f.calc_center_median().y < -0.22
                  and 0.54 < f.calc_center_median().z < 0.63]

    def is_moving_assembly(f):
        if f in horn_faces:
            return False
        c = f.calc_center_median()
        # Stay strictly inside outer barbell rack posts (|X| < 0.305)
        if abs(c.x) > 0.305:
            return False
        # Stay below preacher pad and above base frame
        if c.z < 0.320 or c.z > 0.705:
            return False
        # Stay in front of the top hinge cut plane (Y <= -0.1315)
        if c.y > -0.1315:
            return False
        # Never bleed into the horizontal mid-frame stop pad (which sticks out to Y ~ -0.195 at Z in 0.45..0.52)
        if 0.44 < c.z < 0.53 and c.y > -0.215 and abs(c.x) < 0.14:
            return False
        return True

    moving_faces = flood_faces(grip_seeds, is_moving_assembly)

    # Separate Handles (V-arms + chrome hand grips) vs Diagonal Lever Arm cleanly!
    # Look at armcurl_side_posX.png & armcurl_close_lever.png:
    # The black central diagonal beam lies inside |X| < 0.055 and slopes from (Y=-0.15, Z=0.65) to (Y=-0.36, Z=0.38).
    # The V-shaped swivel handles sit IN FRONT of that diagonal beam (more negative Y) and flare out to |X|=0.30!
    # Line separating diagonal beam from V-handles in (Y, Z):
    # At Z=0.39 (bottom axle): Y_split = -0.365
    # At Z=0.58 (grip height): Y_split = -0.225 (beam is at Y ~ -0.20, handles are at Y ~ -0.29!)
    # Check each face in moving_faces: if it's strictly outside the central beam (|X| > 0.062) OR in front of the beam-to-handle divider line!
    def is_handle_part(f):
        c = f.calc_center_median()
        # Lower bracket & V-handle arms are outside |X| > 0.056 (beam width is ~0.052 half-width!)
        # OR at Z > 0.43 and Y < -0.35 + (c.z - 0.38) * 0.42 (clearly forward of diagonal beam!)
        y_beam_front = -0.375 + (c.z - 0.38) * 0.72
        if abs(c.x) > 0.058 and c.z > 0.415:
            return True
        if c.z > 0.42 and c.y < y_beam_front - 0.025:
            return True
        return False

    # Flood-fill handles cleanly from chrome grip seeds inside is_handle_part
    handle_faces = flood_faces(grip_seeds, lambda f: (f in moving_faces) and is_handle_part(f))
    lever_faces  = moving_faces - handle_faces
    frame_faces  = [f for f in bm.faces if f not in moving_faces and f not in horn_faces]

    print(f"[{tag}] Frame={len(frame_faces)} LeverArm={len(lever_faces)} Handles={len(handle_faces)} WeightHorn={len(horn_faces)}")

    # Compute exact pivot origins from geometry!
    # Top hinge pivot = highest-rearward cylinder center of LeverArm (around Y=-0.155, Z=0.650)
    lev_pts = np.array([v.co for f in lever_faces for v in f.verts])
    top_zone = lev_pts[lev_pts[:, 2] > lev_pts[:, 2].max() - 0.06]
    pivot_top = Vector((0.0, float(top_zone[:, 1].mean()), float(top_zone[:, 2].mean())))

    # Bottom handle swivel axle = lowest point of LeverArm/Handles (around Y=-0.365, Z=0.390)
    bot_zone = lev_pts[lev_pts[:, 2] < lev_pts[:, 2].min() + 0.05]
    pivot_bot = Vector((0.0, float(bot_zone[:, 1].mean()), float(bot_zone[:, 2].mean())))

    # Left & Right Chrome Grip exact centroids!
    h_pts = np.array([v.co for f in handle_faces for v in f.verts])
    gl_pts = h_pts[(h_pts[:, 0] > 0.14) & (h_pts[:, 2] > 0.54)]
    gr_pts = h_pts[(h_pts[:, 0] < -0.14) & (h_pts[:, 2] > 0.54)]
    grip_l_pos = Vector(gl_pts.mean(axis=0)) if len(gl_pts) else Vector(( 0.21, -0.29, 0.58))
    grip_r_pos = Vector(gr_pts.mean(axis=0)) if len(gr_pts) else Vector((-0.21, -0.29, 0.58))

    horn_pts = np.array([v.co for f in horn_faces for v in f.verts])
    horn_ctr = Vector((0.0, float(horn_pts[:, 1].mean()), float(horn_pts[:, 2].mean()))) if len(horn_pts) else Vector((0, -0.19, 0.40))

    print(f"  pivot_top={tuple(round(v,3) for v in pivot_top)}  pivot_bot={tuple(round(v,3) for v in pivot_bot)}")
    print(f"  grip_L={tuple(round(v,3) for v in grip_l_pos)}  grip_R={tuple(round(v,3) for v in grip_r_pos)}")

    # Remove original merged mesh
    bpy.data.objects.remove(orig, do_unlink=True)

    root = bpy.data.objects.new(f"{tag}_Root", None)
    bpy.context.scene.collection.objects.link(root)

    ob_frame  = create_mesh_obj("ArmCurl_Frame",      extract_submesh(bm, frame_faces),  mats, parent=root,     origin_world=(0, 0, 0))
    # Fix Tripo AI's off-center seat & rear leg (originally shifted ~13.3cm toward -X while front/pad are at X=0!)
    fbm = bmesh.new()
    fbm.from_mesh(ob_frame.data)
    def smstep(a, b, v):
        t = max(0.0, min(1.0, (v - a) / (b - a)))
        return t * t * (3.0 - 2.0 * t)
    for v in fbm.verts:
        p = v.co
        if p.z < 0.702 and p.y > 0.065:
            # Upper seat cushion, rear support post & mid brace (Z >= 0.22)
            if p.z >= 0.215:
                # Exclude anything belonging to the centered main upright column (Y < 0.085 and X > -0.05)
                w_y = smstep(0.075, 0.145, p.y)
                w_z = smstep(0.215, 0.255, p.z)
                # Also pull the lower rear leg/foot cleanly onto X=0 when Y > 0.34
                w_low_rear = smstep(0.33, 0.41, p.y)
                w = max(w_y * w_z, w_low_rear)
                p.x += 0.133 * w
            else:
                # Bottom floor beam already sits at X=0 up to Y=0.33; smoothly straighten rear elbow/foot onto X=0!
                w_foot = smstep(0.32, 0.42, p.y)
                if w_foot > 0.0:
                    # Shift rear post/foot center (-0.114) -> 0.0 without creating a sideways bend
                    p.x += 0.114 * w_foot * smstep(0.03, -0.04, p.x)
    fbm.normal_update()
    fbm.to_mesh(ob_frame.data)
    fbm.free()
    ob_frame.data.update()

    ob_lever  = create_mesh_obj("ArmCurl_LeverArm",   extract_submesh(bm, lever_faces),  mats, parent=root,     origin_world=pivot_top)
    ob_handle = create_mesh_obj("ArmCurl_Handles",    extract_submesh(bm, handle_faces), mats, parent=ob_lever, origin_world=pivot_bot)
    ob_horn   = create_mesh_obj("ArmCurl_WeightHorn", extract_submesh(bm, horn_faces),   mats, parent=root,     origin_world=horn_ctr)
    bm.free()

    # Add Grip Empties parented to ArmCurl_Handles (so they move automatically when LeverArm curls!)
    add_grip_empty("Grip_L", grip_l_pos, ob_handle)
    add_grip_empty("Grip_R", grip_r_pos, ob_handle)

    # Render TWO verification views for ArmCurl_A (rest color-coded + 45deg curled motion test!)
    if tag == "ArmCurlBench_A_Collar":
        cmap = {
            "ArmCurl_Frame":      (0.28, 0.30, 0.34, 1.0),
            "ArmCurl_LeverArm":   (0.15, 0.50, 0.95, 1.0),
            "ArmCurl_Handles":    (0.15, 0.88, 0.35, 1.0),
            "ArmCurl_WeightHorn": (0.95, 0.45, 0.10, 1.0),
        }
        render_verify(f"{tag}_rest", (1.65, -0.45, 0.62), (0.0, -0.08, 0.48), color_map=cmap)
        render_verify(f"{tag}_curled", (1.65, -0.45, 0.62), (0.0, -0.08, 0.48), color_map=cmap,
                      test_rot={"ArmCurl_LeverArm": (math.radians(-45), 0.0, 0.0)})

    blend_out = os.path.join(OUT_BLEND, f"{tag}_Separated.blend")
    fbx_out   = os.path.join(OUT_FBX,   f"{tag}_Separated.fbx")
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    export_clean_fbx(fbx_out)
    print(f"  Saved: {blend_out} & {fbx_out} ({os.path.getsize(fbx_out)/1024:.1f} KB)")

process_pullupbar()
process_armcurl("ArmCurlBench_A_Collar.fbx", "ArmCurlBench_A_Collar")
process_armcurl("ArmCurlBench_B_Symmetric.fbx", "ArmCurlBench_B_Symmetric")
print("ALL 3 EQUIPMENT MODELS SEPARATED SUCCESSFULLY!")
