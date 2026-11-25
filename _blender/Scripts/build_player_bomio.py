"""
Build a sleek, lightweight (~2.5 MB), 100% Mixamo-IK-compatible
slim-athletic muscular player avatar (Player_Bomio) in a black zip-up tracksuit
from Ch38_nonPBR.fbx.
- Preserves exact Mixamo 65-bone Armature (standardized 'mixamorig:' prefix,
  exact 0.01 scale / 90deg rot & leaf bones -> Blender Mixamo Control Rig + Unity Humanoid 1-click!)
- Slim athletic V-taper muscular physique (broad capped deltoids, defined pecs & lats,
  lean tapered waist, toned biceps/triceps/forearms, slim athletic quads & calves).
- Matte-satin charcoal-black zip-up track jacket with 3D high stand-up collar,
  metallic center zipper & collar pull, raglan seam detailing, crisp white maple crest
  on left chest, and bold white vertical lettering along the outer left sleeve.
- Matching slim-tapered black track pants with left-thigh white crest & pocket seams,
  plus sleek black-and-white athletic running sneakers.
- Clean natural hair, warm smooth PBR skin, bare hands (all 30 finger weights preserved!).
"""
import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import Vector, Matrix, kdtree
from mathutils.bvhtree import BVHTree

SRC_FBX     = r"G:\Unity_Gym\AI-Gym\Assets\Characters\Ch38_nonPBR.fbx"
SRC_TEX_DIR = r"G:\Unity_Gym\AI-Gym\Assets\Characters\Textures"
OUT_TEX_DIR = r"G:\Unity_Gym\AI-Gym\Assets\Characters\Textures_PlayerBomio"
OUT_BLEND   = r"G:\Unity_Gym\AI-Gym\_blender\Bomio_Exercises\01_Avatar\Player_Bomio.blend"
OUT_FBX     = r"G:\Unity_Gym\AI-Gym\Assets\Characters\Player_Bomio.fbx"
PREV_FRONT  = r"C:\Users\hyung\.gemini\antigravity\brain\bc816dce-1a90-4961-b863-c22ec5353e0c\scratch\bomio_front.png"
PREV_CLOSE  = r"C:\Users\hyung\.gemini\antigravity\brain\bc816dce-1a90-4961-b863-c22ec5353e0c\scratch\bomio_close.png"
PREV_BACK   = r"C:\Users\hyung\.gemini\antigravity\brain\bc816dce-1a90-4961-b863-c22ec5353e0c\scratch\bomio_back.png"
PREV_SIDE   = r"C:\Users\hyung\.gemini\antigravity\brain\bc816dce-1a90-4961-b863-c22ec5353e0c\scratch\bomio_side.png"

os.makedirs(OUT_TEX_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
os.makedirs(os.path.dirname(PREV_FRONT), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Import pristine Ch38_nonPBR.fbx
bpy.ops.import_scene.fbx(filepath=SRC_FBX, automatic_bone_orientation=False)
scene = bpy.context.scene
col = scene.collection
bpy.context.view_layer.update()

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.name = "Armature"

# 2. Standardize bone prefix 'mixamorig5:' -> 'mixamorig:' (100% Mixamo IK addon compatibility)
for b in arm.data.bones:
    if b.name.startswith("mixamorig5:"):
        b.name = "mixamorig:" + b.name[len("mixamorig5:"):]
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        for vg in ob.vertex_groups:
            if vg.name.startswith("mixamorig5:"):
                vg.name = "mixamorig:" + vg.name[len("mixamorig5:"):]
bpy.context.view_layer.update()

M = {o.name.split('_', 1)[1]: o for o in bpy.data.objects if o.type == 'MESH' and '_' in o.name}
body      = M["Body"]
shirt     = M["Shirt"]
shorts    = M["Shorts"]
socks     = M["Socks"]
shoes     = M["Shoes"]
hair      = M["Hair"]
eyelashes = M.get("Eyelashes")

def bone_pos(suffix, tail=False):
    b = next(b for b in arm.data.bones if b.name == f"mixamorig:{suffix}")
    return arm.matrix_world @ (b.tail_local if tail else b.head_local)

# 3. Slim-Athletic Muscular Sculpt (inspired by MAN lean athletic reference!)
# Applied identically in world-space to Body/Shirt/Shorts/Socks so layers never clip & 65 bones stay exact.
def sculpt_slim_muscular_point(p):
    x, y, z = p.x, p.y, p.z
    ax = abs(x)
    sx = 1.0 if x >= 0.0 else -1.0

    def g1(v, c, s):
        d = (v - c) / s
        return math.exp(-0.5 * d * d)

    torso_m = 1.0 if ax <= 0.19 else math.exp(-0.5 * ((ax - 0.19) / 0.055) ** 2)
    y_mid = -0.025 + 0.045 * max(0.0, min(1.0, (z - 0.92) / 0.55))

    dx, dy, dz = 0.0, 0.0, 0.0

    # (1) Slim V-taper waist (lean midsection)
    w_waist = g1(z, 1.07, 0.125) * torso_m
    dx -= x * 0.140 * w_waist
    dy -= (y - y_mid) * 0.110 * w_waist

    # (2) Lean pelvis & firm athletic glutes
    w_hips = g1(z, 0.90, 0.11) * torso_m
    dx -= x * 0.070 * w_hips
    if y > y_mid:
        w_glute = g1(z, 0.88, 0.075) * g1(ax, 0.085, 0.06) * min(1.0, (y - y_mid) / 0.06)
        dy += 0.011 * w_glute
        dz += 0.005 * w_glute

    # (3) Defined Pectorals (front chest volume + crisp sternum line)
    if y < y_mid + 0.015:
        front_f = min(1.0, max(0.0, (y_mid + 0.015 - y) / 0.065))
        w_pec = g1(z, 1.325, 0.062) * g1(ax, 0.088, 0.062) * front_f
        sternum_cut = 1.0 - 0.55 * g1(ax, 0.0, 0.018)
        dy -= 0.023 * w_pec * sternum_cut
        dz += 0.004 * w_pec

        # Subtle flat-firm upper abs contour
        w_abs = g1(z, 1.15, 0.075) * g1(ax, 0.045, 0.045) * front_f
        dy -= 0.004 * w_abs * (1.0 - 0.4 * g1(ax, 0.0, 0.014))

    # (4) Smooth V-Taper Lats & Upper Back
    if y > y_mid - 0.02:
        back_f = min(1.0, max(0.0, (y - (y_mid - 0.02)) / 0.065))
        w_lat = g1(z, 1.305, 0.092) * g1(ax, 0.155, 0.062)
        dx += sx * 0.014 * w_lat
        dy += 0.010 * w_lat * back_f

        w_uback = g1(z, 1.375, 0.058) * g1(ax, 0.095, 0.058) * back_f
        spine_cut = 1.0 - 0.5 * g1(ax, 0.0, 0.018)
        dy += 0.014 * w_uback * spine_cut

    # (5) Capped Deltoids (rounded athletic shoulders) & Traps
    w_delt = g1(ax, 0.228, 0.068) * g1(z, 1.430, 0.058) * g1(y, 0.025, 0.072)
    dx += sx * 0.022 * w_delt
    if z > 1.405:
        dz += 0.018 * w_delt * min(1.0, (z - 1.405) / 0.045)
    dy += (y - 0.025) * 0.24 * w_delt

    w_trap = g1(ax, 0.088, 0.046) * g1(z, 1.472, 0.036) * g1(y, 0.025, 0.065)
    dz += 0.012 * w_trap

    # (6) Sculpted Arms: Biceps + Triceps + Athletic Forearms (slim elbow & wrist)
    if 0.24 < ax < 0.68 and abs(z - 1.418) < 0.14:
        arm_y, arm_z = 0.036, 1.418
        ry = y - arm_y
        rz = z - arm_z
        r = math.sqrt(ry * ry + rz * rz)
        if r > 1e-4:
            uy, uz = ry / r, rz / r
            w_uarm = g1(ax, 0.342, 0.068)
            bi_bias  = max(0.0, -uy * 0.65 + uz * 0.75)
            tri_bias = max(0.0,  uy * 0.75 - uz * 0.65)
            rad_u = (0.008 + 0.011 * bi_bias + 0.009 * tri_bias) * w_uarm
            dy += uy * rad_u
            dz += uz * rad_u

            w_elb = g1(ax, 0.468, 0.032)
            dy -= ry * 0.06 * w_elb
            dz -= rz * 0.06 * w_elb

            w_farm = g1(ax, 0.540, 0.052)
            rad_f = 0.0095 * w_farm
            dy += uy * rad_f
            dz += uz * rad_f

    # (7) Slim Toned Legs (lean tapered silhouette + defined quads & calves)
    if 0.07 < z < 0.85 and ax < 0.28:
        if z >= 0.519:
            t = (z - 0.519) / (0.875 - 0.519)
            lx = sx * (0.125 + (0.091 - 0.125) * t)
            ly = 0.002 + (-0.019 - 0.002) * t
        else:
            t = max(0.0, (z - 0.119) / (0.519 - 0.119))
            lx = sx * (0.146 + (0.125 - 0.146) * t)
            ly = 0.036 + (0.002 - 0.036) * t
        rx, ry_l = x - lx, y - ly
        rl = math.sqrt(rx * rx + ry_l * ry_l)
        if rl > 1e-4:
            slim_f = 0.065 * (1.0 - g1(z, 0.85, 0.08))
            dx -= rx * slim_f
            dy -= ry_l * slim_f

            w_quad = g1(z, 0.695, 0.095)
            q_dir = max(0.0, (-ry_l / rl) * 0.8 + (rx * sx / rl) * 0.45)
            dy += (ry_l / rl) * 0.012 * q_dir * w_quad
            dx += (rx / rl)   * 0.010 * q_dir * w_quad

            w_calf = g1(z, 0.345, 0.072)
            c_dir = max(0.0, (ry_l / rl) * 0.85 + (rx * sx / rl) * 0.35)
            dy += (ry_l / rl) * 0.010 * c_dir * w_calf
            dx += (rx / rl)   * 0.006 * c_dir * w_calf

    return Vector((x + dx, y + dy, z + dz))

def apply_athletic_sculpt(ob, taper_shorts_hem=False):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.transform(bm, matrix=ob.matrix_world, verts=bm.verts)
    for v in bm.verts:
        p = sculpt_slim_muscular_point(v.co)
        # Smoothly taper Ch38_Shorts bottom hem so there is ZERO baggy knee step!
        if taper_shorts_hem and p.z < 0.665:
            sx = 1.0 if p.x >= 0.0 else -1.0
            lx, ly = sx * 0.122, -0.001
            t = max(0.0, min(1.0, (0.665 - p.z) / 0.092))
            t = t * t * (3.0 - 2.0 * t)
            p.x = lx + (p.x - lx) * (1.0 - 0.135 * t)
            p.y = ly + (p.y - ly) * (1.0 - 0.125 * t)
        v.co = p
    bmesh.ops.transform(bm, matrix=ob.matrix_world.inverted(), verts=bm.verts)
    bm.normal_update()
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()

apply_athletic_sculpt(body)
apply_athletic_sculpt(shirt)
apply_athletic_sculpt(shorts, taper_shorts_hem=True)
apply_athletic_sculpt(socks)
bpy.context.view_layer.update()

# 4. Lightweight 1024px smooth skin & natural hair textures
def save_1024_tex(src_name, out_name, is_non_color=False):
    src_path = os.path.join(SRC_TEX_DIR, src_name)
    out_path = os.path.join(OUT_TEX_DIR, out_name)
    img = bpy.data.images.load(src_path, check_existing=False)
    if is_non_color:
        img.colorspace_settings.name = 'Non-Color'
    if img.size[0] > 1024 or img.size[1] > 1024:
        img.scale(1024, 1024)
    img.filepath_raw = out_path
    img.file_format = 'PNG'
    img.save()
    return img

tex_skin_col = save_1024_tex("Ch38_1001_Diffuse.png", "Bomio_Skin_Albedo.png", False)
tex_skin_nrm = save_1024_tex("Ch38_1001_Normal.png",  "Bomio_Skin_Normal.png", True)
tex_hair_col = save_1024_tex("Ch38_1002_Diffuse.png", "Bomio_Hair_Albedo.png", False)
tex_hair_nrm = save_1024_tex("Ch38_1002_Normal.png",  "Bomio_Hair_Normal.png", True)

# 5. Crisp 3D-World-Space -> UV-Space Anti-Aliased Texture Baker
def srgb_to_arr(hex_str):
    h = hex_str.lstrip("#")
    return np.array([int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0], dtype=np.float32)

def bake_world_uv(obj, out_path, color_fn, tex_size=1024, bg_hex="#1B1D22"):
    me = obj.data
    me.calc_loop_triangles()
    uv_layer = me.uv_layers.active
    mw = obj.matrix_world
    wverts = np.array([mw @ v.co for v in me.vertices], dtype=np.float32)

    W = H = tex_size
    wx_buf = np.zeros((H, W), dtype=np.float32)
    wy_buf = np.zeros((H, W), dtype=np.float32)
    wz_buf = np.zeros((H, W), dtype=np.float32)
    mask   = np.zeros((H, W), dtype=bool)

    for tri in me.loop_triangles:
        l0, l1, l2 = tri.loops
        v0, v1, v2 = tri.vertices
        u0, vv0 = uv_layer.data[l0].uv
        u1, vv1 = uv_layer.data[l1].uv
        u2, vv2 = uv_layer.data[l2].uv

        x0, y0 = u0 * (W - 1), vv0 * (H - 1)
        x1, y1 = u1 * (W - 1), vv1 * (H - 1)
        x2, y2 = u2 * (W - 1), vv2 * (H - 1)

        minx = max(0, int(math.floor(min(x0, x1, x2))))
        maxx = min(W - 1, int(math.ceil(max(x0, x1, x2))))
        miny = max(0, int(math.floor(min(y0, y1, y2))))
        maxy = min(H - 1, int(math.ceil(max(y0, y1, y2))))
        if maxx < minx or maxy < miny:
            continue

        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denom) < 1e-8:
            continue

        gy, gx = np.mgrid[miny:maxy + 1, minx:maxx + 1]
        a = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / denom
        b = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / denom
        c = 1.0 - a - b
        inside = (a >= -1e-4) & (b >= -1e-4) & (c >= -1e-4)
        if not np.any(inside):
            continue

        p0, p1, p2 = wverts[v0], wverts[v1], wverts[v2]
        sl = (slice(miny, maxy + 1), slice(minx, maxx + 1))
        ai, bi, ci = a[inside], b[inside], c[inside]
        wx_buf[sl][inside] = ai * p0[0] + bi * p1[0] + ci * p2[0]
        wy_buf[sl][inside] = ai * p0[1] + bi * p1[1] + ci * p2[1]
        wz_buf[sl][inside] = ai * p0[2] + bi * p1[2] + ci * p2[2]
        mask[sl][inside] = True

    rgb = np.zeros((H, W, 3), dtype=np.float32)
    rgb[:, :] = srgb_to_arr(bg_hex)
    if np.any(mask):
        rgb[mask] = color_fn(wx_buf[mask], wy_buf[mask], wz_buf[mask])

    # Dilate UV islands by 6px so mipmaps never bleed across seams
    cur_m = mask.copy()
    for _ in range(6):
        grown = cur_m.copy()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            shifted_m = np.roll(cur_m, (dy, dx), axis=(0, 1))
            fill = (~grown) & shifted_m
            if np.any(fill):
                rgb[fill] = np.roll(rgb, (dy, dx), axis=(0, 1))[fill]
                grown |= fill
        cur_m = grown

    rgba = np.ones((H, W, 4), dtype=np.float32)
    rgba[..., :3] = rgb
    img = bpy.data.images.new(os.path.basename(out_path), width=W, height=H, alpha=False)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = out_path
    img.file_format = 'PNG'
    img.save()
    return img

# Crisp SDF helpers for maple-leaf athletic crest & bold sleeve lettering
def sdf_seg(px, py, x1, y1, x2, y2):
    vx, vy = x2 - x1, y2 - y1
    wx, wy = px - x1, py - y1
    l2 = vx * vx + vy * vy + 1e-12
    t = np.clip((wx * vx + wy * vy) / l2, 0.0, 1.0)
    return np.sqrt((wx - t * vx) ** 2 + (wy - t * vy) ** 2)

def maple_crest_alpha(px, py, scale):
    """Crisp symmetrical stylized maple/athletic leaf emblem matching reference jacket."""
    u = px / scale
    v = py / scale
    au = np.abs(u)
    # 5-lobe maple silhouette built from smooth union of diamond lobes + stem
    top_lobe   = (au / 0.36) + np.abs(v - 0.38) / 0.62 < 1.0
    mid_lobe   = ((au - 0.42) / 0.56) ** 2 + ((v - 0.10 - 0.16 * au) / 0.34) ** 2 < 1.0
    low_lobe   = ((au - 0.46) / 0.48) ** 2 + ((v + 0.18) / 0.24) ** 2 < 1.0
    center_hub = (au < 0.48) & (v > -0.34) & (v < 0.45)
    stem       = (au < 0.075) & (v <= -0.25) & (v >= -0.78)
    # Sharp leaf points
    tip_t = (au < np.clip(0.32 * (1.0 - (v - 0.35) / 0.68), 0.0, 1.0)) & (v >= 0.30) & (v <= 1.02)
    tip_s = (np.abs(v - (0.08 + 0.32 * (au - 0.35))) < np.clip(0.28 * (1.0 - (au - 0.35) / 0.68), 0.0, 1.0)) & (au >= 0.30) & (au <= 1.02)
    leaf = top_lobe | mid_lobe | low_lobe | center_hub | stem | tip_t | tip_s
    # Clean dark center micro-bar inside the white maple emblem (just like reference crest!)
    inner_txt = (au < 0.22) & (np.abs(v - 0.02) < 0.045)
    inner_txt2 = (au < 0.14) & (np.abs(v + 0.09) < 0.032)
    mask = leaf & (~inner_txt) & (~inner_txt2)
    return mask.astype(np.float32)

# Bold athletic block glyph strokes in normalized [0..1]x[0..1] box (horizontal left-to-right u, bottom-to-top v)
GLYPHS = {
    'T': [((0.05, 0.92), (0.95, 0.92)), ((0.50, 0.92), (0.50, 0.08))],
    'R': [((0.15, 0.08), (0.15, 0.92)), ((0.15, 0.92), (0.72, 0.92)), ((0.72, 0.92), (0.85, 0.72)),
          ((0.85, 0.72), (0.72, 0.50)), ((0.72, 0.50), (0.15, 0.50)), ((0.48, 0.50), (0.88, 0.08))],
    'A': [((0.10, 0.08), (0.50, 0.92)), ((0.50, 0.92), (0.90, 0.08)), ((0.24, 0.38), (0.76, 0.38))],
    'I': [((0.50, 0.08), (0.50, 0.92)), ((0.22, 0.92), (0.78, 0.92)), ((0.22, 0.08), (0.78, 0.08))],
    'N': [((0.15, 0.08), (0.15, 0.92)), ((0.15, 0.92), (0.85, 0.08)), ((0.85, 0.08), (0.85, 0.92))],
    'G': [((0.85, 0.78), (0.65, 0.92)), ((0.65, 0.92), (0.30, 0.92)), ((0.30, 0.92), (0.12, 0.65)),
          ((0.12, 0.65), (0.12, 0.35)), ((0.12, 0.35), (0.30, 0.08)), ((0.30, 0.08), (0.75, 0.08)),
          ((0.75, 0.08), (0.88, 0.35)), ((0.88, 0.35), (0.88, 0.48)), ((0.88, 0.48), (0.52, 0.48))],
    'F': [((0.18, 0.08), (0.18, 0.92)), ((0.18, 0.92), (0.86, 0.92)), ((0.18, 0.52), (0.74, 0.52))],
    'O': [((0.25, 0.92), (0.75, 0.92)), ((0.75, 0.92), (0.88, 0.68)), ((0.88, 0.68), (0.88, 0.32)),
          ((0.88, 0.32), (0.75, 0.08)), ((0.75, 0.08), (0.25, 0.08)), ((0.25, 0.08), (0.12, 0.32)),
          ((0.12, 0.32), (0.12, 0.68)), ((0.12, 0.68), (0.25, 0.92))],
    'L': [((0.18, 0.92), (0.18, 0.08)), ((0.18, 0.08), (0.86, 0.08))],
    'Y': [((0.12, 0.92), (0.50, 0.50)), ((0.88, 0.92), (0.50, 0.50)), ((0.50, 0.50), (0.50, 0.08))],
    'U': [((0.16, 0.92), (0.16, 0.25)), ((0.16, 0.25), (0.35, 0.08)), ((0.35, 0.08), (0.65, 0.08)),
          ((0.65, 0.08), (0.84, 0.25)), ((0.84, 0.25), (0.84, 0.92))],
    'P': [((0.18, 0.08), (0.18, 0.92)), ((0.18, 0.92), (0.72, 0.92)), ((0.72, 0.92), (0.86, 0.72)),
          ((0.86, 0.72), (0.72, 0.50)), ((0.72, 0.50), (0.18, 0.50))],
}

def render_word_alpha(u, v, word, stroke_r=0.115):
    """Render bold crisp sans-serif word in u in [0, len(word)], v in [0, 1]."""
    dist = np.full_like(u, 99.0, dtype=np.float32)
    active = (u >= -0.2) & (u <= len(word) + 0.2) & (v >= -0.2) & (v <= 1.2)
    if not np.any(active):
        return np.zeros_like(u, dtype=np.float32)
    ua = u[active]
    va = v[active]
    da = np.full_like(ua, 99.0)
    for idx, ch in enumerate(word):
        if ch == ' ' or ch not in GLYPHS:
            continue
        lu = ua - idx
        near = (lu >= -0.2) & (lu <= 1.2)
        if not np.any(near):
            continue
        lu_n, va_n = lu[near], va[near]
        d_ch = np.full_like(lu_n, 99.0)
        for (x1, y1), (x2, y2) in GLYPHS[ch]:
            d_ch = np.minimum(d_ch, sdf_seg(lu_n, va_n, x1, y1, x2, y2))
        da[near] = np.minimum(da[near], d_ch)
    dist[active] = da
    return np.clip((stroke_r - dist) / 0.032 + 0.5, 0.0, 1.0)

# Color palette — Rich matte athletic black tracksuit (matching reference photo!)
C_BLK      = srgb_to_arr("#1B1D22")
C_BLK_RIB  = srgb_to_arr("#14161B")
C_SEAM     = srgb_to_arr("#292C35")
C_ZIP_BASE = srgb_to_arr("#111317")
C_ZIP_MTL  = srgb_to_arr("#343844") # sleek tonal dark-gunmetal zipper teeth like reference!
C_WHITE    = srgb_to_arr("#F4F6FA")

def track_jacket_shader(wx, wy, wz):
    n = wx.shape[0]
    col_out = np.tile(C_BLK, (n, 1))
    ax = np.abs(wx)

    # Very subtle matte tricot knit micro-grain
    weave = 0.005 * np.sin(wx * 420.0) * np.sin(wz * 420.0)
    col_out = np.clip(col_out + weave[:, None], 0.0, 1.0)

    # Subtle athletic muscle contour shading (clean slim-muscular depth under matte fabric)
    pec_hi   = np.where(wy < 0.0, np.exp(-0.5 * ((wz - 1.345) / 0.040) ** 2) * np.exp(-0.5 * ((ax - 0.088) / 0.055) ** 2), 0.0)
    pec_sh   = np.where(wy < 0.0, np.exp(-0.5 * ((wz - 1.268) / 0.022) ** 2) * np.exp(-0.5 * ((ax - 0.085) / 0.062) ** 2), 0.0)
    delt_hi  = np.exp(-0.5 * ((ax - 0.232) / 0.055) ** 2) * np.exp(-0.5 * ((wz - 1.455) / 0.035) ** 2)
    bicep_hi = np.where(wy < 0.045, np.exp(-0.5 * ((ax - 0.345) / 0.055) ** 2) * np.exp(-0.5 * ((wz - 1.445) / 0.030) ** 2), 0.0)
    waist_sh = np.exp(-0.5 * ((wz - 1.07) / 0.085) ** 2) * np.clip((ax - 0.08) / 0.09, 0.0, 1.0)
    shade = 1.0 + 0.14 * pec_hi + 0.12 * delt_hi + 0.10 * bicep_hi - 0.15 * pec_sh - 0.12 * waist_sh
    col_out = np.clip(col_out * shade[:, None], 0.0, 1.0)

    # Ribbed dark hem at waist & ribbed cuffs at wrists
    is_hem  = (wz < 0.960) & (ax < 0.24)
    is_cuff = (ax > 0.635)
    rib_tex = 0.008 * np.sin(wx * 520.0 + wy * 520.0)
    col_out[is_hem | is_cuff] = np.clip(C_BLK_RIB + rib_tex[is_hem | is_cuff, None], 0.0, 1.0)
    hem_seam  = (np.abs(wz - 0.960) < 0.0025) & (ax < 0.24)
    cuff_seam = np.abs(ax - 0.635) < 0.0025
    col_out[hem_seam | cuff_seam] = C_SEAM

    # Raglan shoulder seam lines (front & back, sweeping collar -> armpit like reference!)
    raglan_z = 1.485 - (ax - 0.056) * 1.42
    is_raglan = (ax >= 0.056) & (ax <= 0.180) & (np.abs(wz - raglan_z) < 0.0028)
    col_out[is_raglan] = C_SEAM

    # Sleek tonal dark-charcoal center zipper (subtle matte-black track just like reference!)
    is_zip_band = (wy < -0.01) & (ax < 0.0070)
    col_out[is_zip_band] = C_ZIP_BASE
    zip_edge = (wy < -0.01) & (np.abs(ax - 0.0072) < 0.0014)
    col_out[zip_edge] = C_SEAM
    teeth = (wy < -0.01) & (ax < 0.0024) & (np.sin(wz * 900.0) > 0.2)
    col_out[teeth] = C_ZIP_MTL

    # Crisp white maple/athletic crest on left chest (+X side, front)
    front_chest = (wy < -0.02) & (wx > 0.03) & (wx < 0.16) & (wz > 1.29) & (wz < 1.42)
    if np.any(front_chest):
        la = maple_crest_alpha(wx[front_chest] - 0.088, wz[front_chest] - 1.352, scale=0.023)[:, None]
        col_out[front_chest] = col_out[front_chest] * (1.0 - la) + C_WHITE * la

    # Bold white vertical sleeve print ("TRAINING") mapped cleanly in cylindrical arm coordinates (ZERO stretch!)
    l_sleeve = (wx > 0.27) & (wx < 0.60)
    if np.any(l_sleeve):
        word = "TRAINING"
        # Cylindrical angle around left arm axis (y=0.036, z=1.418); ang = pi/2 is top-outer (+Z)
        ang = np.arctan2(wz[l_sleeve] - 1.418, -(wy[l_sleeve] - 0.036))
        # Center lettering at top-outer-front (~1.25 rad) spanning +/- 0.42 rad
        u = (wx[l_sleeve] - 0.295) / 0.034
        v = (ang - 0.90) / 0.72
        wa = render_word_alpha(u, v, word, stroke_r=0.115)[:, None]
        col_out[l_sleeve] = col_out[l_sleeve] * (1.0 - wa) + C_WHITE * wa

    return col_out

def track_pants_shader(wx, wy, wz):
    n = wx.shape[0]
    col_out = np.tile(C_BLK, (n, 1))
    ax = np.abs(wx)

    # Fade micro-weave out toward knee hem so lower pant leg blends 100% seamlessly!
    fade_knee = np.clip((wz - 0.60) / 0.10, 0.0, 1.0)
    weave = 0.005 * fade_knee * np.sin(wx * 420.0) * np.sin(wz * 420.0)
    col_out = np.clip(col_out + weave[:, None], 0.0, 1.0)

    # Elastic ribbed waistband at top
    is_band = wz > 0.915
    col_out[is_band] = C_BLK_RIB
    band_seam = np.abs(wz - 0.915) < 0.0025
    col_out[band_seam] = C_SEAM

    # Subtle vertical side pocket seam on outer upper thigh
    pocket_seam = (wz > 0.73) & (wz < 0.89) & (wy < 0.01) & (wy > -0.065) & (np.abs(ax - 0.155) < 0.0030)
    col_out[pocket_seam] = C_SEAM

    # Matching crisp white maple/athletic crest on left thigh (+X front, just like reference pants!)
    l_thigh = (wy < -0.01) & (wx > 0.06) & (wx < 0.20) & (wz > 0.70) & (wz < 0.85)
    if np.any(l_thigh):
        la = maple_crest_alpha(wx[l_thigh] - 0.120, wz[l_thigh] - 0.775, scale=0.022)[:, None]
        col_out[l_thigh] = col_out[l_thigh] * (1.0 - la) + C_WHITE * la

    return col_out

def sneaker_shader(wx, wy, wz):
    n = wx.shape[0]
    col_out = np.tile(srgb_to_arr("#16181D"), (n, 1))
    # Crisp bright white athletic sneaker midsole band!
    sole_a = np.clip((0.038 - wz) / 0.003 + 0.5, 0.0, 1.0)[:, None]
    col_out = col_out * (1.0 - sole_a) + C_WHITE * sole_a
    # Clean dark-charcoal heel & collar trim
    trim = (wz > 0.088) & (wz < 0.105)
    col_out[trim] = srgb_to_arr("#2A2E38")
    return col_out

# Flatten soccer-cleat studs on Ch38_Shoes into clean flat athletic running sneaker outsoles!
sh_bm = bmesh.new()
sh_bm.from_mesh(shoes.data)
bmesh.ops.transform(sh_bm, matrix=shoes.matrix_world, verts=sh_bm.verts)
for v in sh_bm.verts:
    if v.co.z < 0.022:
        v.co.z = 0.014
bmesh.ops.transform(sh_bm, matrix=shoes.matrix_world.inverted(), verts=sh_bm.verts)
sh_bm.normal_update()
sh_bm.to_mesh(shoes.data)
sh_bm.free()
shoes.data.update()

tex_jacket  = bake_world_uv(shirt,  os.path.join(OUT_TEX_DIR, "Bomio_TrackJacket_Albedo.png"), track_jacket_shader, 1024, "#1B1D22")
tex_pants   = bake_world_uv(shorts, os.path.join(OUT_TEX_DIR, "Bomio_TrackPants_Albedo.png"),  track_pants_shader,  1024, "#1B1D22")
tex_sneaker = bake_world_uv(shoes,  os.path.join(OUT_TEX_DIR, "Bomio_Sneaker_Albedo.png"),     sneaker_shader,       512, "#16181D")

# 6. PBR Material Builders (true matte sportswear roughness + low specular so fabric looks soft & real!)
def srgb_to_lin_rgba(hex_str):
    a = srgb_to_arr(hex_str)
    lin = [float(((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92) for c in a]
    return (lin[0], lin[1], lin[2], 1.0)

def make_pbr_mat(name, rgba, rough=0.78, metal=0.0, spec=0.25):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = spec
    return m

def make_tex_mat(name, col_img, nrm_img=None, rough=0.78, spec=0.25, sss=0.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = spec
    if sss > 0.0 and "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = sss
        if "Subsurface Scale" in bsdf.inputs:
            bsdf.inputs["Subsurface Scale"].default_value = 0.008
    t_col = nt.nodes.new("ShaderNodeTexImage")
    t_col.image = col_img
    nt.links.new(t_col.outputs["Color"], bsdf.inputs["Base Color"])
    if nrm_img is not None:
        t_nrm = nt.nodes.new("ShaderNodeTexImage")
        t_nrm.image = nrm_img
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 0.45
        nt.links.new(t_nrm.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m

# Smooth realistic skin + soft matte charcoal-black athletic jersey fabrics (exact color match across all pant parts!)
MAT_SKIN   = make_tex_mat("M_Bomio_Skin",        tex_skin_col, tex_skin_nrm, rough=0.44, spec=0.45, sss=0.12)
MAT_HAIR   = make_tex_mat("M_Bomio_Hair",        tex_hair_col, tex_hair_nrm, rough=0.50, spec=0.35)
MAT_JACKET = make_tex_mat("M_Bomio_TrackJacket", tex_jacket,   None,         rough=0.78, spec=0.22)
MAT_PANTS  = make_tex_mat("M_Bomio_TrackPants",  tex_pants,    None,         rough=0.78, spec=0.22)
MAT_BLACK  = make_pbr_mat("M_Bomio_TrackBlack",  srgb_to_lin_rgba("#1B1D22"), rough=0.78, metal=0.0, spec=0.22)
MAT_SILVER = make_pbr_mat("M_Bomio_ZipperMetal", (0.78, 0.80, 0.84, 1.0),     rough=0.20, metal=0.90, spec=0.50)
MAT_SHOE   = make_tex_mat("M_Bomio_Sneaker",     tex_sneaker,  None,         rough=0.52, spec=0.35)

body.data.materials.clear();   body.data.materials.append(MAT_SKIN)
hair.data.materials.clear();   hair.data.materials.append(MAT_HAIR)
shirt.data.materials.clear();  shirt.data.materials.append(MAT_JACKET)
shorts.data.materials.clear(); shorts.data.materials.append(MAT_PANTS)
socks.data.materials.clear();  socks.data.materials.append(MAT_BLACK)
shoes.data.materials.clear();  shoes.data.materials.append(MAT_SHOE)
if eyelashes:
    bpy.data.objects.remove(eyelashes, do_unlink=True)
    eyelashes = None

def world_bm(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.transform(bm, matrix=ob.matrix_world, verts=bm.verts)
    bm.normal_update()
    bm.verts.index_update()
    return bm

# Tuck lower Socks vertices inside shoe collar so ZERO fabric pokes through sneakers!
sb = world_bm(socks)
for v in sb.verts:
    if v.co.z < 0.118:
        v.co -= v.normal * 0.008
    elif v.co.z < 0.145:
        t = (v.co.z - 0.118) / (0.145 - 0.118)
        v.co += v.normal * (-0.008 + 0.018 * t)
    else:
        v.co += v.normal * 0.010
bmesh.ops.transform(sb, matrix=socks.matrix_world.inverted(), verts=sb.verts)
sb.to_mesh(socks.data)
sb.free()
socks.data.update()

for o in (body, shirt, shorts, socks, shoes, hair):
    for p in o.data.polygons:
        p.use_smooth = True

# 7. Helpers for clean skinned parts
KD = {}
def kd_of(ob):
    kd = kdtree.KDTree(len(ob.data.vertices))
    for v in ob.data.vertices:
        kd.insert(ob.matrix_world @ v.co, v.index)
    kd.balance()
    return kd

def add_skinned_part(name, bm, mats, src, rigid_bone=None, smooth=True):
    bmesh.ops.transform(bm, matrix=src.matrix_world.inverted(), verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    if not isinstance(mats, (list, tuple)):
        mats = [mats]
    for m in mats:
        me.materials.append(m)
    ob = src.copy()
    ob.name = name
    ob.data = me
    col.objects.link(ob)

    ob.vertex_groups.clear()
    for vg in src.vertex_groups:
        ob.vertex_groups.new(name=vg.name)

    if rigid_bone is not None:
        if rigid_bone not in ob.vertex_groups:
            ob.vertex_groups.new(name=rigid_bone)
        ob.vertex_groups[rigid_bone].add([v.index for v in me.vertices], 1.0, 'REPLACE')
    else:
        kd = KD.setdefault(src.name, kd_of(src))
        for v in me.vertices:
            _co, idx, _d = kd.find(ob.matrix_world @ v.co)
            for g in src.data.vertices[idx].groups:
                ob.vertex_groups[src.vertex_groups[g.group].name].add([v.index], g.weight, 'REPLACE')
    return ob

def extract_shell(src_bm, pred, offset):
    new = bmesh.new()
    vm = {}
    for f in src_bm.faces:
        if not pred(f.calc_center_median()):
            continue
        vs = []
        for v in f.verts:
            if v.index not in vm:
                vm[v.index] = new.verts.new(v.co + v.normal * offset)
            vs.append(vm[v.index])
        try:
            new.faces.new(vs)
        except ValueError:
            pass
    new.normal_update()
    return new

body_bm   = world_bm(body)
shorts_bm = world_bm(shorts)
shoes_bm  = world_bm(shoes)
short_min_z = min(v.co.z for v in shorts_bm.verts)
shoe_top_z  = max(v.co.z for v in shoes_bm.verts)
shorts_bm.free()
shoes_bm.free()

# 8. Slim-Tapered Full-Length Track Pants Lower Leg (seamless flow from shorts down to sneakers!)
pants_lower = extract_shell(
    body_bm,
    lambda c: (shoe_top_z - 0.025 <= c.z <= short_min_z + 0.095) and abs(c.x) < 0.30,
    offset=0.012
)
add_skinned_part("TrackPants_Lower", pants_lower, MAT_BLACK, body)

# 9. Tailored 3D High Stand-Up Track Jacket Collar + Metallic Silver Zipper Pull (snug around neck!)
neck_vs = [v.co for v in body_bm.verts if 1.490 <= v.co.z <= 1.520 and abs(v.co.x) < 0.085]
ncx = sum(v.x for v in neck_vs) / len(neck_vs)
ncy = sum(v.y for v in neck_vs) / len(neck_vs)
nrx = min(0.072, max(abs(v.x - ncx) for v in neck_vs) + 0.008)
nry = min(0.074, max(abs(v.y - ncy) for v in neck_vs) + 0.008)

collar_bm = bmesh.new()
segs_u = 44
rings_z = [
    (1.456, 1.20, 1.15, 0.007),  # tucked cleanly into jacket shoulder seam
    (1.478, 1.04, 1.04, 0.006),
    (1.500, 1.01, 1.02, 0.0055),
    (1.522, 1.00, 1.01, 0.005),  # crisp tailored stand-up rim below chin!
]
outer_rings, inner_rings = [], []
for rz, sx_m, sy_m, thick in rings_z:
    o_row, i_row = [], []
    t_h = (rz - 1.456) / (1.522 - 1.456)
    for i in range(segs_u):
        th = 2.0 * math.pi * i / segs_u
        # Slight tailored rise in back, subtle V-dip at front zipper (th ~ -pi/2 -> y < 0)
        front_dip = 0.010 * max(0.0, -math.sin(th)) ** 2
        back_rise = 0.006 * max(0.0,  math.sin(th)) ** 2
        zz = rz + (back_rise - front_dip) * t_h
        ox = ncx + nrx * sx_m * math.cos(th)
        oy = ncy + nry * sy_m * math.sin(th)
        ix = ncx + (nrx * sx_m - thick) * math.cos(th)
        iy = ncy + (nry * sy_m - thick) * math.sin(th)
        o_row.append(collar_bm.verts.new((ox, oy, zz)))
        i_row.append(collar_bm.verts.new((ix, iy, zz)))
    outer_rings.append(o_row)
    inner_rings.append(i_row)

for r in range(len(rings_z) - 1):
    for i in range(segs_u):
        ni = (i + 1) % segs_u
        collar_bm.faces.new((outer_rings[r][i], outer_rings[r][ni], outer_rings[r + 1][ni], outer_rings[r + 1][i]))
        collar_bm.faces.new((inner_rings[r][ni], inner_rings[r][i], inner_rings[r + 1][i], inner_rings[r + 1][ni]))
for i in range(segs_u):
    ni = (i + 1) % segs_u
    collar_bm.faces.new((outer_rings[-1][i], outer_rings[-1][ni], inner_rings[-1][ni], inner_rings[-1][i]))
collar_bm.normal_update()
add_skinned_part("Jacket_Collar", collar_bm, MAT_BLACK, body, rigid_bone="mixamorig:Neck")

# Tiny sleek metallic silver zipper pull tab right at front collar notch!
zip_bm = bmesh.new()
bmesh.ops.create_uvsphere(zip_bm, u_segments=16, v_segments=10, radius=1.0)
zip_y = ncy - nry * 1.02 - 0.004
zip_z = 1.505
bmesh.ops.transform(
    zip_bm,
    matrix=Matrix.Translation((0.0, zip_y, zip_z)) @ Matrix.Diagonal((0.005, 0.0035, 0.009, 1.0)),
    verts=zip_bm.verts
)
zip_bm.normal_update()
add_skinned_part("Jacket_ZipperPull", zip_bm, MAT_SILVER, body, rigid_bone="mixamorig:Neck")

body_bm.free()

# 9.5 Upgrade Ch38_Body hand skinning to full 30-bone articulated fingers (Ch38_nonPBR leaves Middle/Ring/Pinky unweighted!)
def assign_articulated_finger_weights(mesh_obj, arm_obj):
    mw_a = arm_obj.matrix_world
    mw_m = mesh_obj.matrix_world
    def seg_dist(p, a, b):
        ab = b - a
        l2 = ab.length_squared
        if l2 < 1e-10:
            return (p - a).length
        t = max(0.0, min(1.0, (p - a).dot(ab) / l2))
        return (p - (a + ab * t)).length

    finger_prefixes = ("Thumb", "Index", "Middle", "Ring", "Pinky")
    for side, sgn in (("Left", 1.0), ("Right", -1.0)):
        hand_bn = f"mixamorig:{side}Hand"
        hand_b = arm_obj.data.bones[hand_bn]
        h_head = mw_a @ hand_b.head_local
        h_tail = mw_a @ hand_b.tail_local
        segs = [(hand_bn, h_head, h_tail)]
        for fp in finger_prefixes:
            for k in (1, 2, 3):
                bn = f"mixamorig:{side}Hand{fp}{k}"
                if bn in arm_obj.data.bones:
                    b = arm_obj.data.bones[bn]
                    segs.append((bn, mw_a @ b.head_local, mw_a @ b.tail_local))
                    if bn not in mesh_obj.vertex_groups:
                        mesh_obj.vertex_groups.new(name=bn)

        # Find vertices in the hand/finger region (past wrist X)
        wrist_x = abs(h_head.x) + 0.015
        for v in mesh_obj.data.vertices:
            wp = mw_m @ v.co
            if wp.x * sgn < wrist_x or wp.z < 1.25:
                continue
            # Distance to palm vs finger segments
            d_hand = seg_dist(wp, h_head, h_tail)
            f_dists = sorted([(seg_dist(wp, a, b), bn) for (bn, a, b) in segs[1:]], key=lambda it: it[0])
            d0, bn0 = f_dists[0]
            # Only reskin vertices that clearly belong to fingers (closer to a finger bone than palm or past knuckles)
            if d0 < d_hand * 1.15 or (wp.x * sgn > abs(h_head.x) + 0.075):
                # Smooth blend between nearest 2 segments (including palm near knuckles)
                cands = sorted([(seg_dist(wp, a, b), bn) for (bn, a, b) in segs], key=lambda it: it[0])[:2]
                # Remove old hand/finger weights on this vertex
                for bn_old, _, _ in segs:
                    if bn_old in mesh_obj.vertex_groups:
                        mesh_obj.vertex_groups[bn_old].remove([v.index])
                # Inverse-sharpness Gaussian weights for crisp knuckle bends
                ws = [math.exp(-((d / 0.014) ** 2)) for d, _ in cands]
                s_w = sum(ws) + 1e-12
                for w_val, (_, bn_sel) in zip(ws, cands):
                    if w_val / s_w > 0.01:
                        mesh_obj.vertex_groups[bn_sel].add([v.index], w_val / s_w, 'REPLACE')

assign_articulated_finger_weights(body, arm)

# 10. Pack textures into .blend (so moving .blend folders NEVER turns textures pink!) & Save .blend
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

# 11. Render crisp studio previews (Front, Close-up, Back, 3/4 Side)
def render_previews():
    sc = scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 768, 960
    sc.view_settings.view_transform = 'Standard'

    lights = []
    for name, loc, energy, sz in [
        ("KeyL",  (2.4, -3.0, 2.5), 320, 2.0),
        ("FillL", (-2.2, -2.5, 1.6), 170, 2.5),
        ("BackL", (0.0,  3.2, 2.2), 260, 2.5),
    ]:
        ld = bpy.data.lights.new(name, type='AREA')
        ld.energy = energy
        ld.size = sz
        lo_ob = bpy.data.objects.new(name, ld)
        col.objects.link(lo_ob)
        lo_ob.location = Vector(loc)
        lo_ob.rotation_euler = (Vector((0, 0, 1.0)) - lo_ob.location).to_track_quat('-Z', 'Y').to_euler()
        lights.append((lo_ob, ld))

    w = bpy.data.worlds.new("PrevW")
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs["Color"].default_value = (0.24, 0.28, 0.34, 1.0)
    bg.inputs["Strength"].default_value = 0.9
    sc.world = w

    cam_data = bpy.data.cameras.new("PrevCam")
    cam = bpy.data.objects.new("PrevCam", cam_data)
    col.objects.link(cam)
    sc.camera = cam

    for path, loc, target, lens in [
        (PREV_FRONT, (0.0,  -3.4, 0.95), (0.0, 0.0, 0.90), 50),
        (PREV_CLOSE, (0.38, -1.60, 1.42), (0.0, 0.0, 1.32), 55),
        (PREV_BACK,  (0.0,   3.4, 0.95), (0.0, 0.0, 0.90), 50),
        (PREV_SIDE,  (2.3,  -2.2, 1.05), (0.0, 0.0, 0.95), 50),
    ]:
        cam_data.lens = lens
        cam.location = Vector(loc)
        cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)

    bpy.data.objects.remove(cam); bpy.data.cameras.remove(cam_data)
    for lo_ob, ld in lights:
        bpy.data.objects.remove(lo_ob); bpy.data.lights.remove(ld)

render_previews()

# 12. Export FBX (100% Mixamo-standard Armature + lightweight external textures!)
for ob in bpy.context.view_layer.objects:
    ob.select_set(False)
for ob in bpy.data.objects:
    if ob.type in {'ARMATURE', 'MESH'}:
        ob.select_set(True)
bpy.context.view_layer.objects.active = arm

bpy.ops.export_scene.fbx(
    filepath=OUT_FBX,
    use_selection=True,
    object_types={'ARMATURE', 'MESH'},
    use_mesh_modifiers=True,
    add_leaf_bones=True,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    armature_nodetype='NULL',
    bake_anim=False,
    apply_scale_options='FBX_SCALE_NONE',
    axis_forward='-Z',
    axis_up='Y',
    path_mode='AUTO',
    embed_textures=False
)
print(f"SUCCESS! Player_Bomio.fbx = {os.path.getsize(OUT_FBX)/1048576:.2f} MB, bones={len(arm.data.bones)}")
