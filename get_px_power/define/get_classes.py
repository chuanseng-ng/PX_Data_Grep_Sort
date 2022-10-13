# Class instantiation
## Hierarchy + Type datasheet class
class HierarchyTypeDatasheet(object):
    def __init__(self, data_list=None, power_rail_dict=None, run_name_count=None, run_name_dict=None):
        self.data_list           = data_list
        self.power_rail_dict     = power_rail_dict
        self.run_name_count      = run_name_count
        self.run_name_dict       = run_name_dict
        self.power_rail_position = 1