"""this is the class for the different profiles"""
from math import ceil

class frd_profiles(object):

    def __init__(self,vehicle_profile, direction_profile, penalty_profile, dtm_size):

        self.vehicle_profile = vehicle_profile
        self.direction_profile = direction_profile
        self.penalty_profile = penalty_profile
        self.dtm_size = dtm_size
        self.num_options = 3
        self.params = {}
    
    def slope_radius_params(self, option):
        if self.vehicle_profile == 0 : #todoterreno
            if option == 0:
                self.params["max_slope_pct"] = 8
            if option == 1:
                self.params["max_slope_pct"] = 12
            if option == 2:
                self.params["max_slope_pct"] = 15

            self.params["min_slope_pct"] = 1            
            self.params["semi_size"] = ceil(8/self.dtm_size)
            self.params["min_curve_radio_m"] = 8

        if self.vehicle_profile == 1 : # autobomma / camión forestal
            if option == 0:
                self.params["max_slope_pct"] = 6
            if option == 1:
                self.params["max_slope_pct"] = 8
            if option == 2:
                self.params["max_slope_pct"] = 12

            self.params["min_slope_pct"] = 1            
            self.params["semi_size"] = ceil(10/self.dtm_size)
            self.params["min_curve_radio_m"] = 10

        if self.vehicle_profile == 2 : #camión trailer
            if option == 0:
                self.params["max_slope_pct"] = 6
            if option == 1:
                self.params["max_slope_pct"] = 8
            if option == 2:
                self.params["max_slope_pct"] = 12

            self.params["min_slope_pct"] = 1            
            self.params["semi_size"] = ceil(12/self.dtm_size)
            self.params["min_curve_radio_m"] = 12

    def direc_params(self):
        if self.direction_profile == 0: # alta / alta
            self.params["penalty_factor_xy"] = 0
            self.params["penalty_factor_z"] = 0

        if self.direction_profile == 1: # alta / media
            self.params["penalty_factor_xy"] = 0
            self.params["penalty_factor_z"] = 20

        if self.direction_profile == 2: # media / alta
            self.params["penalty_factor_xy"] = 20
            self.params["penalty_factor_z"] = 0

        if self.direction_profile == 3: # media / media
            self.params["penalty_factor_xy"] = 20
            self.params["penalty_factor_z"] = 20

        if self.direction_profile == 4: # media / baja
            self.params["penalty_factor_xy"] = 20
            self.params["penalty_factor_z"] = 40

        if self.direction_profile == 5: # baja / media
            self.params["penalty_factor_xy"] = 40
            self.params["penalty_factor_z"] = 20

        if self.direction_profile == 6: # baja / baja
            self.params["penalty_factor_xy"] = 40
            self.params["penalty_factor_z"] = 40

    def penalty_params(self): 

        if self.penalty_profile == 0: #Equilibrado
            self.params["slope_penalty_factor"] = 1
            self.params["radius_penalty_factor"] = 1
        
        if self.penalty_profile == 1: #pendiente
            self.params["slope_penalty_factor"] = 5
            self.params["radius_penalty_factor"] = 1
        
        if self.penalty_profile == 2: #radio
            self.params["slope_penalty_factor"] = 1
            self.params["radius_penalty_factor"] = 5