feature_dict = {"highway":0,"avoid_highway":1,"urban":2,"oneway":3,"both_ways":4,"limited_access":5,"paved":6,"ramp":7,"manoeuvre":8,
                "roundabout":9,"one_lane":10,"multiple_lanes":11,"traffic_lights":12,"railway_crossing":13,"no_overtaking":14,
                "traffic_signs":15,"stop_signs":16,"school_zone":17,"icy_road":18,"crosswalk":19,
                "animal_crossing":20,"lane_merge_right":21,"lane_merge_left":22,"falling_rocks":23,
                "hills":24,"tunnel":25,"bridge":26,'road_roughness_good':27,'road_roughness_fair':28,'road_roughness_poor':29,
                "speed_bump":30,"toll_station":31,'lane_marker_long_dashed':32,'lane_marker_short_dashed':33,'lane_marker_double_dashed':34,
                'lane_marker_double_solid':35,'lane_marker_single_solid':36,'lane_marker_inner_solid_outter_dashed':37,
                'lane_marker_inner_dashed_outter_solid':38,'lane_marker_no_divider':39,'lane_marker_physical_divider':40,
                'hov_lane':41,'reversible_lane':42,'express_lane':43,'slow_lane':44,'auxiliary_lane':45,'shoulder_lane':46,
                'passing_lane':47,'turn_lane':48,'parking_lane':49,'center_turn_lane':50,'parking_lot':51,'functional_class_1':52,
                'functional_class_2':53,'functional_class_3':54,'functional_class_4':55,'functional_class_5':56}


traffics_sign_dict = {1 : "START OF NO OVERTAKING", 10 : "RAILWAY CROSSING UNPROTECTED", 11 : "ROAD NARROWS", 
                      12 : "SHARP CURVE LEFT 10 sharp curve", 13 : "SHARP CURVE RIGHT 10 sharp curve", 
                      14 : "WINDING ROAD STARTING LEFT", 15 : "WINDING ROAD STARTING RIGHT", 
                      16 : "START OF NO OVERTAKING TRUCKS", 17 : "END OF NO OVERTAKING TRUCKS", 
                      18 : "STEEP HILL UPWARDS", 19 : "STEEP HILL DOWNWARDS", 2 : "END OF NO OVERTAKING", 
                      20 : "STOP SIGN", 21 : "LATERAL WIND", 22 : "GENERAL WARNING 70-80", 23 : "RISK OF GROUNDING", 
                      24 : "GENERAL CURVE", 25 : "END OF ALL RESTRICTIONS", 26 : "GENERAL HILL", 
                      27 : "ANIMAL CROSSING 30 Deer Crossing", 28 : "ICY CONDITIONS", 
                      29 : "SLIPPERY ROAD 40 Sleppery", 3 : "PROTECTED OVERTAKING - EXTRA LANE", 
                      30 : "FALLING ROCKS", 31 : "SCHOOL ZONE school zone", 32 : "TRAMWAY CROSSING", 
                      33 : "CONGESTION HAZARD", 34 : "ACCIDENT HAZARD", 35 : "PRIORITY OVER ONCOMING TRAFFIC", 
                      36 : "YIELD TO ONCOMING TRAFFIC", 37 : "CROSSING WITH PRIORITY FROM THE RIGHT", 
                      4 : "PROTECTED OVERTAKING - EXTRA LANE RIGHT", 41 : "PEDESTRIAN CROSSING", 42 : "YIELD", 
                      43 : "DOUBLE HAIRPIN", 44 : "TRIPLE HAIRPIN", 45 : "EMBANKMENT", 46 : "TWO-WAY TRAFFIC", 
                      47 : "URBAN AREA", 48 : "HUMP BRIDGE", 49 : "UNEVEN ROAD", 
                      5 : "PROTECTED OVERTAKING - EXTRA LANE LEFT", 50 : "FLOOD AREA", 51 : "OBSTACLE", 
                      52 : "HORN SIGN", 53 : "NO ENGINE BRAKE", 54 : "END OF NO ENGINE BRAKE", 55 : "NO IDLING", 
                      56 : "TRUCK ROLLOVER", 57 : "LOW GEAR", 58 : "END OF LOW GEAR", 59 : "BICYCLE CROSSING", 
                      6 : "LANE MERGING FROM THE RIGHT", 60 : "YIELD TO BICYCLES", 61 : "NO TOWED CARAVAN ALLOWED", 
                      62 : "NO TOWED TRAILER ALLOWED", 63 : "NO CAMPER OR MOTORHOME ALLOWED", 64 : "NO TURN ON RED", 
                      65 : "TURN PERMITTED ON RED", 7 : "LANE MERGING FROM THE LEFT", 8 : "LANE MERGE CENTRE", 
                      9 : "RAILWAY CROSSING PROTECTED"}

traffic_condition_dict ={11 : "VARIABLE SPEED", 16 : "TRAFFIC_SIGNAL", 17: "TRAFFIC_SIGN", 18: "RAILWAY CROSSING",
                         19: "NO OVERTAKING", 21: "PROTECTED OVERTAKING", 38: "BLACKSPOT", 22: "EVACUATION ROUTE"}

lane_divider_dict = {0:"No Marker", 1:"Long dashed line", 2:"Double solid line", 3:"Single solid line",
                     4:"Inner solid - outer dashed line", 5:"Inner dashed - outer solid line", 6:"Short dashed line", 7:"Shaded area marking",
                     8:"Dashed blocks",9:"Physical divider < 3m",10:"Double dashed line",11:"No divider",12:"Crossing alert line",
                     13:"Center turn lane",14:"Unknown"}
                     
lane_type = {1:"REGULAR",2:"HOV",4:"REVERSIBLE",6:"HOV + REVERSIBLE",8:"EXPRESS",10:"HOV + EXPRESS",12:"REVERSIBLE + EXPRESS",
            14:"HOV + REVERSIBLE + EXPRESS",16:"ACCELERATION",18:"HOV + ACCELERATION",20:"REVERSIBLE + ACCELERATION",
            22:"HOV + REVERSIBLE + ACCELERATION",24:"EXPRESS + ACCELERATION",32:"DECELERATION",34:"HOV + DECELERATION",
            36:"REVERSIBLE + DECELERATION",38:"HOV + REVERSIBLE + DECELERATION",40:"EXPRESS + DECELERATION",
            64:"AUXILIARY",128:"SLOW",256:"PASSING",512:"SHOULDER",1024:"REGULATED ACCESS",2048:"TURN",
            4096:"CENTRE TURN",8192:"TRUCK PARKING",16384:"PARKING",32768:"VARIABLE DRIVING",65536:"BICYCLE"}