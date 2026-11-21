#V23

#V23









































# coding: utf-8



import clr

from System.Collections.Generic import List



# =========================================================

# SpaceClaim 2023 R1 / API V23

# 单流道 CFD 仿真版（1 × N）

#

# 已调整：

# 1) 防止 SpaceClaim / Workbench 重复触发同一几何

# 2) 每次真正重建前清理旧 bodies 和旧 named selections

# 3) 不再简单按 body 名称保留临时体，避免多个同名 Fluid_Domain 堆叠

# 4) 流道高度 H、流道宽度 W 设为独立变量

# 5) 特征数量 Feature_Count 设为独立变量

# 6) 换热主段长度随特征数量和 Feature_Pitch 自动缩放

#

# 功能：

# 1) 单一连续 fluid body

# 2) 保留入口段 / 主段 / 出口段整体几何长度

# 3) N 个沿流向的 bulge / dimple 特征

# 4) 高度 H、宽度 W 独立控制

# 5) 命名选择：

#    bulge / plate / develop_wall / inlet / outlet / symmetry

# =========================================================





# =========================================================

# 0. 执行控制参数

# =========================================================

# False：同一参数下，如果 Fluid_Domain 已存在，则跳过重复生成

# True ：无论是否已有几何，都强制清空并重新生成

FORCE_REBUILD = False



# 修改代码结构后，如果希望强制触发一次重建，可以改这个版本号

SCRIPT_GEOMETRY_VERSION = "single_channel_1xN_guard_v6_feature_pitch_outlet60"





# =========================================================

# 1. 防重复触发辅助函数

# =========================================================

def _get_geometry_key():

    """

    用于判断当前参数是否已经生成过。

    这里把 Bulge_Depth / Bulge_Diameter / H / W / Feature_Count / Feature_Pitch 都纳入 key。

    """

    try:

        bd = float(Parameters.Bulge_Depth)

    except:

        bd = 3.0



    try:

        bdiam = float(Parameters.Bulge_Diameter)

    except:

        bdiam = 20.0



    try:

        h_val = float(Parameters.H)

    except:

        h_val = (bd - 0.1) * 2.0



    try:

        w_val = float(Parameters.W)

    except:

        w_val = 50.0



    try:

        fc_val = int(round(float(Parameters.Feature_Count)))

    except:

        fc_val = 6



    try:

        fp_val = float(Parameters.Feature_Pitch)

    except:

        fp_val = 42.0



    return (

        SCRIPT_GEOMETRY_VERSION,

        round(bd, 6),

        round(bdiam, 6),

        round(h_val, 6),

        round(w_val, 6),

        int(fc_val),

        round(fp_val, 6)

    )





def _fluid_body_exists():

    """

    判断当前模型中是否已经存在主流体域。

    """

    try:

        for b in GetActivePart().Bodies:

            if b.Name == "Fluid_Domain":

                return True

    except:

        pass



    return False





def clear_model_before_rebuild():

    """

    比单独 ClearAll() 更稳：

    1) 删除已有 Named Selections

    2) 删除已有 Bodies

    3) 再尝试 ClearAll()

    """



    # 删除旧 Named Selections

    try:

        for ns in list(GetActivePart().NamedSelections):

            try:

                ns.Delete()

            except:

                pass

    except:

        pass



    # 删除旧 Bodies

    try:

        for b in list(GetActivePart().Bodies):

            try:

                b.Delete()

            except:

                pass

    except:

        pass



    # 防止其他残留

    try:

        ClearAll()

    except:

        pass





# =========================================================

# 2. 主几何生成函数

# =========================================================

def create_fluid_domain():



    # -----------------------------------------------------

    # 0. 清空当前几何

    # -----------------------------------------------------

    clear_model_before_rebuild()



    # -----------------------------------------------------

    # 1. 参数读取

    # -----------------------------------------------------

    try:

        Bulge_Depth = float(Parameters.Bulge_Depth)

    except:

        Bulge_Depth = 3.0



    try:

        Bulge_Diameter = float(Parameters.Bulge_Diameter)

    except:

        Bulge_Diameter = 20.0



    try:

        H = float(Parameters.H)

    except:

        H = (Bulge_Depth - 0.1) * 2.0



    try:

        W = float(Parameters.W)

    except:

        W = 50.0



    try:

        Feature_Count = int(round(float(Parameters.Feature_Count)))

    except:

        Feature_Count = 6



    try:

        Feature_Pitch = float(Parameters.Feature_Pitch)

    except:

        Feature_Pitch = 42.0



    if Bulge_Depth <= 0:

        raise Exception("Bulge_Depth 必须大于 0。")



    if H <= 0:

        raise Exception("H 必须大于 0。")



    if W <= 0:

        raise Exception("W 必须大于 0。")



    if Feature_Count <= 0:

        raise Exception("Feature_Count 必须大于 0。")



    if Feature_Pitch <= 0:

        raise Exception("Feature_Pitch 必须大于 0。")



    if Feature_Count % 2 != 0:

        raise Exception("Feature_Count 必须为偶数，例如 2 / 4 / 6 / 8 / 10。")



    # -----------------------------------------------------

    # 2. 基本尺寸，单位 mm

    # -----------------------------------------------------

    # 保持原 6 特征版本的节距与边缘余量逻辑

    FEATURE_PITCH = Feature_Pitch

    END_CLEARANCE = 20.0

    DEVELOP_LENGTH = 42.5
    OUTLET_EXTRA_LENGTH = 60.0



    # 主换热段长度：随特征数量变化

    # 当 Feature_Count = 6 时：

    # L_core = (6 - 1)*42 + 2*20 = 250 mm

    L_core = (Feature_Count - 1) * FEATURE_PITCH + 2.0 * END_CLEARANCE



    X_MAIN_MIN   = -L_core / 2.0

    X_MAIN_MAX   =  L_core / 2.0

    X_INLET_MIN  = X_MAIN_MIN - DEVELOP_LENGTH

    X_OUTLET_MAX = X_MAIN_MAX + DEVELOP_LENGTH + OUTLET_EXTRA_LENGTH



    NORMAL_TOL = 0.95

    X_TOL = 0.2

    Z_TOL = 0.2

    CUTTER_HALF_THK = 0.005



    # N 个沿流向分布的特征中心

    # 当 Feature_Count = 6 时，恢复为：

    # [-105, -63, -21, 21, 63, 105]

    X_coords = []

    x_start = -0.5 * (Feature_Count - 1) * FEATURE_PITCH

    for i in range(Feature_Count):

        X_coords.append(x_start + i * FEATURE_PITCH)



    # 固定交替排列：B, D, B, D, ...

    types = []

    for i in range(Feature_Count):

        if i % 2 == 0:

            types.append("B")

        else:

            types.append("D")



    # 由弦长和拱高反算母球半径

    radius = (Bulge_Diameter**2 / 4.0 + Bulge_Depth**2) / (2.0 * Bulge_Depth)



    intersect_options = MakeSolidsOptions()



    # -----------------------------------------------------

    # 3. 工具函数

    # -----------------------------------------------------

    def log(msg):

        print(msg)



    def create_block(x_min, x_max, y_min, y_max, z_min, z_max, name):

        p1 = Point.Create(MM(x_min), MM(y_min), MM(z_min))

        p2 = Point.Create(MM(x_max), MM(y_max), MM(z_max))



        body = BlockBody.Create(

            p1,

            p2,

            ExtrudeType.ForceIndependent

        ).CreatedBodies[0]



        body.Name = name

        return body



    def get_all_bodies():

        return list(GetActivePart().Bodies)



    def reacquire_body_by_name(name):

        for b in get_all_bodies():

            if b.Name == name:

                return b

        return None



    def reacquire_largest_body(new_name=None):

        bodies = get_all_bodies()



        if not bodies:

            return None



        bodies.sort(key=lambda b: b.Shape.Volume, reverse=True)



        if new_name:

            bodies[0].Name = new_name



        return bodies[0]



    def reacquire_fluid_body():

        """

        优先按名称找 Fluid_Domain。

        如果找不到，则把当前最大 body 重新命名为 Fluid_Domain。

        """

        b = reacquire_body_by_name("Fluid_Domain")



        if b:

            return b



        return reacquire_largest_body("Fluid_Domain")



    def get_temp_bodies(keep_names=None):

        """

        返回除当前主 Fluid_Domain 之外的所有临时 body。

        不再单纯按名称判断，避免多个同名 Fluid_Domain 被保留。

        """

        fluid = reacquire_fluid_body()

        temp_bodies = []



        for b in get_all_bodies():

            if fluid is not None and b == fluid:

                continue



            temp_bodies.append(b)



        return temp_bodies



    def cleanup_temp_bodies(keep_names=None):

        """

        只保留当前主 Fluid_Domain，删除其他临时 body。

        这是防止几何重复堆叠的关键。

        """

        fluid = reacquire_fluid_body()



        for b in get_all_bodies():

            if fluid is not None and b == fluid:

                continue



            try:

                b.Delete()

            except:

                pass



        fluid = reacquire_fluid_body()



        if fluid is not None:

            fluid.Name = "Fluid_Domain"



    def get_f_info(face):

        g_type = "Unknown"



        nx, ny, nz = 0.0, 0.0, 0.0

        x_mm, y_mm, z_mm = 0.0, 0.0, 0.0



        try:

            geom = face.Shape.Geometry

            g_type = geom.GetType().Name

        except:

            pass



        try:

            ev = face.EvalMid()



            try:

                n = ev.Normal

                nx, ny, nz = n.X, n.Y, n.Z

            except:

                pass



            p = None



            try:

                p = ev.Point

            except:

                try:

                    p = ev.Position

                except:

                    p = None



            if p:

                x_mm = p.X * 1000.0

                y_mm = p.Y * 1000.0

                z_mm = p.Z * 1000.0



        except:

            pass



        return g_type, nx, ny, nz, x_mm, y_mm, z_mm



    def create_ns(faces, name):

        if faces and len(faces) > 0:

            NamedSelection.Create(

                Selection.Create(faces),

                Selection.Empty()

            ).CreatedNamedSelection.Name = name



    def bool_merge(target_body, tool_body, tag):

        try:

            Combine.Merge(

                Selection.Create([target_body, tool_body])

            )

        except Exception as e:

            raise Exception(

                "Merge failed at {0}: {1}".format(tag, str(e))

            )



    def bool_intersect(body_a, body_b, tag):

        try:

            Combine.Intersect(

                Selection.Create(body_a),

                Selection.Create(body_b),

                intersect_options

            )

        except Exception as e:

            raise Exception(

                "Intersect failed at {0}: {1}".format(tag, str(e))

            )



    def bool_subtract_design_body(target_design_body, cutter_design_body, tag):

        try:

            target_body = target_design_body.Shape

            cutter_body = cutter_design_body.Shape



            cutters = List[Body]()

            cutters.Add(cutter_body)



            target_body.Subtract(cutters)



        except Exception as e:

            raise Exception(

                "Subtract failed at {0}: {1}".format(tag, str(e))

            )



    def get_cutter_face(cutter_body, x_cut):

        cand = []



        for f in cutter_body.Faces:

            g_type, nx, ny, nz, x_mm, y_mm, z_mm = get_f_info(f)



            if "Plane" in g_type and abs(nx) > NORMAL_TOL:

                cand.append((abs(x_mm - x_cut), f))



        if not cand:

            return None



        cand.sort(key=lambda item: item[0])

        return cand[0][1]



    def get_top_planar_faces():

        fluid = reacquire_fluid_body()



        if fluid is None:

            return []



        faces = []

        z_top = H / 2.0



        for f in fluid.Faces:

            g_type, nx, ny, nz, x_mm, y_mm, z_mm = get_f_info(f)



            if "Plane" in g_type and abs(z_mm - z_top) <= Z_TOL:

                faces.append(f)



        return faces



    def get_bottom_planar_faces():

        fluid = reacquire_fluid_body()



        if fluid is None:

            return []



        faces = []

        z_bottom = -H / 2.0



        for f in fluid.Faces:

            g_type, nx, ny, nz, x_mm, y_mm, z_mm = get_f_info(f)



            if "Plane" in g_type and abs(z_mm - z_bottom) <= Z_TOL:

                faces.append(f)



        return faces



    def split_faces_with_cutter(target_faces, cutter_face, tag):

        if not target_faces:

            raise Exception(

                "No target faces for split at {0}".format(tag)

            )



        if cutter_face is None:

            raise Exception(

                "No cutter face for split at {0}".format(tag)

            )



        errors = []



        try:

            for tf in target_faces:

                SplitFace.ByCutter(

                    Selection.Create(tf),

                    Selection.Create(cutter_face)

                )

            return

        except Exception as e:

            errors.append(

                "loop SplitFace.ByCutter(sel(face), sel(face)): " + str(e)

            )



        try:

            for tf in target_faces:

                SplitFace.ByCutter(

                    Selection.Create(tf),

                    Selection.Create(cutter_face),

                    False

                )

            return

        except Exception as e:

            errors.append(

                "loop SplitFace.ByCutter(sel(face), sel(face), False): " + str(e)

            )



        try:

            SplitFace.ByCutter(

                Selection.Create(target_faces),

                Selection.Create(cutter_face)

            )

            return

        except Exception as e:

            errors.append(

                "SplitFace.ByCutter(sel(list), sel(face)): " + str(e)

            )



        try:

            SplitFace.ByCutter(

                Selection.Create(target_faces),

                Selection.Create(cutter_face),

                False

            )

            return

        except Exception as e:

            errors.append(

                "SplitFace.ByCutter(sel(list), sel(face), False): " + str(e)

            )



        raise Exception(

            "SplitFace failed at {0}: {1}".format(

                tag,

                " | ".join(errors)

            )

        )



    def split_top_bottom_at_x(x_cut, tag):

        cutter = create_block(

            x_cut - CUTTER_HALF_THK,

            x_cut + CUTTER_HALF_THK,

            -W,

            W,

            -H,

            H,

            "Cutter_{0}".format(tag)

        )



        cutter_face = get_cutter_face(cutter, x_cut)



        if cutter_face is None:

            raise Exception(

                "No cutter face found at x = {0} for {1}".format(x_cut, tag)

            )



        top_faces = get_top_planar_faces()

        split_faces_with_cutter(top_faces, cutter_face, "top_" + tag)



        bottom_faces = get_bottom_planar_faces()

        split_faces_with_cutter(bottom_faces, cutter_face, "bottom_" + tag)



        try:

            cutter.Delete()

        except:

            pass



    # -----------------------------------------------------

    # 4. 创建单一连续流体体

    # -----------------------------------------------------

    log("Create seed block...")



    fluid = create_block(

        X_INLET_MIN,

        X_OUTLET_MAX,

        -W / 2.0,

        W / 2.0,

        -H / 2.0,

        H / 2.0,

        "Fluid_Domain"

    )



    # -----------------------------------------------------

    # 5. 在单体上生成 1 × N bulge / dimple

    # -----------------------------------------------------

    keep_names = ["Fluid_Domain"]



    for i, (x, t) in enumerate(zip(X_coords, types)):

        for z_side in ["top", "bottom"]:



            log(

                "Feature {0} | x={1} | type={2} | side={3}".format(

                    i + 1,

                    x,

                    t,

                    z_side

                )

            )



            is_top = (z_side == "top")

            sign = 1 if is_top else -1

            z_base = (H / 2.0) * sign



            if t == "B":

                z_center = z_base - sign * (radius - Bulge_Depth)

            else:

                z_center = z_base + sign * (radius - Bulge_Depth)



            p_center = Point.Create(

                MM(x),

                0,

                MM(z_center)

            )



            p_surface = Point.Create(

                MM(x),

                MM(radius),

                MM(z_center)

            )



            sphere = SphereBody.Create(

                p_center,

                p_surface,

                ExtrudeType.ForceIndependent

            ).CreatedBodies[0]



            # -----------------------------

            # bulge：提取局部球冠并 merge

            # -----------------------------

            if t == "B":

                large_val = radius + 50.0



                if is_top:

                    z1, z2 = (z_base, z_base + large_val)

                else:

                    z1, z2 = (z_base - large_val, z_base)



                keeper_box = create_block(

                    x - large_val,

                    x + large_val,

                    -large_val,

                    large_val,

                    z1,

                    z2,

                    "Keeper_{0}_{1}".format(x, z_side)

                )



                fluid = reacquire_fluid_body()



                if fluid is None:

                    raise Exception(

                        "Fluid_Domain lost before bulge at x={0}, side={1}".format(

                            x,

                            z_side

                        )

                    )



                bool_intersect(

                    sphere,

                    keeper_box,

                    "bulge_cap_x{0}_{1}".format(x, z_side)

                )



                temp_bodies = get_temp_bodies(keep_names)



                if not temp_bodies:

                    raise Exception(

                        "No temp body found after bulge cap intersect at x={0}, side={1}".format(

                            x,

                            z_side

                        )

                    )



                temp_bodies.sort(key=lambda b: b.Shape.Volume)



                cap = temp_bodies[0]



                for b in temp_bodies[1:]:

                    try:

                        b.Delete()

                    except:

                        pass



                fluid = reacquire_fluid_body()



                bool_merge(

                    fluid,

                    cap,

                    "bulge_merge_x{0}_{1}".format(x, z_side)

                )



                cleanup_temp_bodies(keep_names)



            # -----------------------------

            # dimple：直接减去球体

            # -----------------------------

            else:

                fluid = reacquire_fluid_body()



                if fluid is None:

                    raise Exception(

                        "Fluid_Domain lost before dimple subtract at x={0}, side={1}".format(

                            x,

                            z_side

                        )

                    )



                bool_subtract_design_body(

                    fluid,

                    sphere,

                    "dimple_subtract_x{0}_{1}".format(x, z_side)

                )



                try:

                    sphere.Delete()

                except:

                    pass



                cleanup_temp_bodies(keep_names)



    fluid = reacquire_fluid_body()



    if fluid is None:

        raise Exception("Fluid_Domain lost after feature generation.")



    # -----------------------------------------------------

    # 6. 在主段两端对 top / bottom face 进行 split

    # -----------------------------------------------------

    log(

        "Split top/bottom faces at x = {0} and x = {1} ...".format(

            X_MAIN_MIN,

            X_MAIN_MAX

        )

    )



    split_top_bottom_at_x(X_MAIN_MIN, "left")

    split_top_bottom_at_x(X_MAIN_MAX, "right")



    # -----------------------------------------------------

    # 7. 创建命名选择

    # -----------------------------------------------------

    log("Create named selections...")



    fluid = reacquire_fluid_body()



    if fluid is None:

        raise Exception("Fluid_Domain not found before naming.")



    bulge_faces = []

    plate_faces = []

    develop_wall_faces = []

    inlet_faces = []

    outlet_faces = []

    symmetry_faces = []

    check_faces = []



    for f in fluid.Faces:

        g_type, nx, ny, nz, x_mm, y_mm, z_mm = get_f_info(f)



        # 非平面 -> bulge

        if "Plane" not in g_type:

            bulge_faces.append(f)

            continue



        # x 法向面 -> inlet / outlet

        if abs(nx) > NORMAL_TOL:

            if x_mm <= X_INLET_MIN + X_TOL:

                inlet_faces.append(f)



            elif x_mm >= X_OUTLET_MAX - X_TOL:

                outlet_faces.append(f)



            else:

                check_faces.append(f)



            continue



        # y 法向面 -> symmetry

        if abs(ny) > NORMAL_TOL:

            symmetry_faces.append(f)

            continue



        # top / bottom 平面按 x 位置分为主段与发展段

        if abs(z_mm - H / 2.0) <= Z_TOL or abs(z_mm + H / 2.0) <= Z_TOL:

            if (X_MAIN_MIN - X_TOL) <= x_mm <= (X_MAIN_MAX + X_TOL):

                plate_faces.append(f)



            else:

                develop_wall_faces.append(f)



            continue



        check_faces.append(f)



    create_ns(bulge_faces, "bulge")

    create_ns(plate_faces, "plate")

    create_ns(develop_wall_faces, "develop_wall")

    create_ns(inlet_faces, "inlet")

    create_ns(outlet_faces, "outlet")

    create_ns(symmetry_faces, "symmetry")

    create_ns(check_faces, "check_faces")





# =========================================================

# 3. 安全执行入口

# =========================================================

def run_fluid_domain_generator():

    """

    防止 SpaceClaim / Workbench 因参数刷新而重复执行生成。

    """



    global _SC_FLUID_DOMAIN_RUNNING

    global _SC_FLUID_DOMAIN_LAST_KEY



    current_key = _get_geometry_key()



    try:

        running = _SC_FLUID_DOMAIN_RUNNING

    except NameError:

        running = False



    if running:

        print("Skip duplicated trigger: script is already running.")

        return



    try:

        last_key = _SC_FLUID_DOMAIN_LAST_KEY

    except NameError:

        last_key = None



    if not FORCE_REBUILD:

        if last_key == current_key and _fluid_body_exists():

            print("Skip duplicated generation: same geometry already exists.")

            return



    _SC_FLUID_DOMAIN_RUNNING = True



    try:

        create_fluid_domain()

        _SC_FLUID_DOMAIN_LAST_KEY = current_key



    finally:

        _SC_FLUID_DOMAIN_RUNNING = False





# =========================================================

# 4. 执行

# =========================================================

run_fluid_domain_generator()



