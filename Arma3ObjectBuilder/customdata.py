# def get_rvmat_templates():
#     import os
#     from . import addon_dir

#     template_dir = os.path.join(addon_dir, "scripts")

#     templates = {
#         "PBR (VBS)": os.path.join(template_dir, "pbr_vbs.rvmat_template"),
#         "Super - Cloth": os.path.join(template_dir, "super_cloth.rvmat_template"),
#         "Super - Weapon": os.path.join(template_dir, "super_weapon.rvmat_template")
#     }

#     return templates


common_data = {
    "proxies": {
        "Weapon: optic": r"P:\a3\data_f\proxies\weapon_slots\top.p3d",
        "Weapon: pointer": r"P:\a3\data_f\proxies\weapon_slots\side.p3d",
        "Weapon: suppressor": r"P:\a3\data_f\proxies\weapon_slots\muzzle.p3d",
        "Weapon: magazine": r"P:\a3\data_f\proxies\weapon_slots\magazineslot.p3d",
        "Weapon: bipod": r"P:\a3\data_f_mark\proxies\weapon_slots\underbarrel.p3d",
        "Driver: offroad": r"P:\a3\data_f\proxies\driver_offroad\driver.p3d",
        "Passenger: offroad": r"P:\a3\data_f\proxies\passenger_low01\cargo01.p3d",
        "Gunner: hunter": r"P:\a3\data_f\proxies\gunner_hunter\gunner.p3d",
        "Commander: hunter": r"P:\a3\data_f\proxies\gunner_hunter\commander.p3d",
        "Light volume: car": r"P:\a3\data_f\volumelightcar.p3d"
    },
    "namedprops": {
        "autocenter": "0",
        "buoyancy": "1",
        "class": "house",
        "forcenotalpha": "1",
        "lodnoshadow": "1",
        "map": "house",
        "prefershadowvolume": "1"
    },
    "materials": {
        "Glass": r"P:\a3\data_f\glass_veh.rvmat",
        "Collimator": r"P:\a3\weapons_f\acc\data\collimdot_cshader.rvmat",
        "VR Armor Emissive": r"P:\a3\characters_f_bootcamp\common\data\vrarmoremmisive.rvmat"
    },
    "materials_penetration": {
        "Armor": r"P:\a3\data_f\penetration\armour.rvmat",
        "Armor Plate": r"P:\a3\data_f\penetration\armour_plate.rvmat",
        "Engine": r"P:\a3\data_f\penetration\engine.rvmat",
        "Fuel tank": r"P:\a3\data_f\penetration\fueltank.rvmat",
        "Glass": r"P:\a3\data_f\penetration\glass.rvmat",
        "Interior": r"P:\a3\data_f\penetration\vehicle_interior.rvmat",
        "Meat (limbs)": r"P:\a3\data_f\penetration\meat.rvmat",
        "Meat + Bones (body)": r"P:\a3\data_f\penetration\meatbones.rvmat",
        "Plastic": r"P:\a3\data_f\penetration\plastic.rvmat"
    },
    "procedurals": {
        "PIP": "#(argb,512,512,1)r2t(rendertarget0,1.0)"
    },
    "rvmat_templates": {}
    # "rvmat_templates": get_rvmat_templates()
}
