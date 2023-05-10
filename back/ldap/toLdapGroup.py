from __future__ import annotations
from dataclasses import dataclass, field
import yaml

__all__ = ['Group', 'posixGroup', 'Department',
           'Config', 'Default', 'toLdapGroup', 'force_to_list', 'deduplicate','GroupsInfo']

def deduplicate(list):
    output=[]
    for item in list:
        if item not in output:
            output.append(item)
    return output

def force_to_list(data):
    if isinstance(data, str):
        data = data.split(',')
    elif isinstance(data, list):
        data = data
    elif isinstance(data, dict):
        data = data.keys()
    elif isinstance(data, tuple):
        data = list(data)
    else:
        data = []
    return list(data)

@dataclass
class _base:
    description: str = None

    def asdict(self):
        return self.__dict__

    def load_from_dict(self, dict):
        for key, value in dict.items():
            setattr(self, key, value)


@dataclass
class Group(_base):
    name: str = None
    rdn: str = None
    exclude_department: list[str] = field(default_factory=list)
    objectClass:str='groupOfUniqueNames'

    def __post_init__(self):
        self.__check_exclude_department()

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Group) and self.name == __value.name and self.rdn == __value.rdn:
                return True
        return False
    
    @property
    def dn(self, base_dn:str=None, name: str = None):
        if name is None or name.strip() == '':
            basic=f'{self.name}'
        else:
            basic=f'{name}={self.name}'
        if self.rdn is not None and self.rdn.strip() != '':
            basic=f'{basic},{self.rdn}'
        if base_dn is not None and base_dn.strip() != '':
             basic=f'{basic},{base_dn}'
        return basic

    def __check_exclude_department(self):
        value = self.exclude_department
        self.exclude_department = force_to_list(value)
        
    def load_from_dict(self, dict):
        super().load_from_dict(dict)
        self.__check_exclude_department()

@dataclass
class posixGroup(Group):
    gidNumber: int = None
    objectClass:str='posixGroup'
    
    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, posixGroup) and self.rdn == __value.rdn and self.gidNumber == __value.gidNumber:
                return True
        return False


@dataclass
class Department(_base):
    name: str = None
    enable: bool = True
    ldap_groups: list[Group] = field(default_factory=list)
    posixGroups: list[posixGroup] = field(default_factory=list)

    def __post_init__(self):
        list1 = self.ldap_groups
        list2 = self.posixGroups
        if isinstance(list1, list) and len(list1) > 0 and isinstance(list1[0], dict):
            try:
                list11 = [Group(**group_dict) for group_dict in list1]
                self.ldap_groups = list11
            except:
                pass
        if isinstance(list2, list) and len(list2) > 0 and isinstance(list2[0], dict):
            try:
                list22 = [posixGroup(**group_dict) for group_dict in list2]
                self.posixGroups = list22
            except:
                pass

    def load_from_dict(self, dict):
        for key, value in dict.items():
            if key == 'ldap_groups':
                self.ldap_groups = []
                for group in value:
                    self.ldap_groups.append(Group(**group))
            elif key == 'posixGroups':
                self.posixGroups = []
                for group in value:
                    self.posixGroups.append(posixGroup(**group))
            else:
                setattr(self, key, value)


@dataclass
class Config(_base):
    create_missing_groups: bool = True


@dataclass
class Default(Department):
    departments: list[str] = field(default_factory=list)
    ldap_groups_if_no: list[Group] = field(default_factory=list)
    posixGroups_if_no: list[posixGroup] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        list1 = self.ldap_groups_if_no
        list2 = self.posixGroups_if_no
        if isinstance(list1, list) and len(list1) > 0 and isinstance(list1[0], dict):
            try:
                list11 = [Group(**group_dict) for group_dict in list1]
                self.ldap_groups_if_no = list11
            except:
                pass
        if isinstance(list2, list) and len(list2) > 0 and isinstance(list2[0], dict):
            try:
                list22 = [posixGroup(**group_dict) for group_dict in list2]
                self.posixGroups_if_no = list22
            except:
                pass
        self.departments = force_to_list(self.departments)

    def load_from_dict(self, dict):
        super().load_from_dict(dict)
        for key, value in dict.items():
            if key == 'ldap_groups_if_no':
                self.posixGroups_if_no = []
                for group in value:
                    self.posixGroups_if_no.append(Group(**group))
            elif key == 'posixGroups_if_no':
                self.posixGroups_if_no = []
                for group in value:
                    self.posixGroups_if_no.append(posixGroup(**group))
        self.departments = force_to_list(self.departments)
                    
    def check_default(self, department_name: str) -> GroupsInfo:
        output = GroupsInfo()
        if department_name in self.departments:
            output.ldap_groups = [group for group in self.ldap_groups if department_name not in group.exclude_department]
            output.posixGroups = [group for group in self.posixGroups if department_name not in group.exclude_department]
        else:
            output.ldap_groups = self.ldap_groups_if_no
            output.posixGroups = self.posixGroups_if_no
        return output.deduplicate()


@dataclass
class GroupsInfo(_base):
    ldap_groups: list[Group] = field(default_factory=list)
    posixGroups: list[posixGroup] = field(default_factory=list)


    def deduplicate(self):
        self.ldap_groups = deduplicate(self.ldap_groups)
        self.posixGroups = deduplicate(self.posixGroups)
        return self

    def extend(self, groups_info:GroupsInfo):
        self.ldap_groups.extend(groups_info.ldap_groups)
        self.posixGroups.extend(groups_info.posixGroups)
        return self

@dataclass
class toLdapGroup(_base):
    version: str = '1.0'
    config: Config = field(default_factory=Config)
    default: Default = field(default_factory=Default)
    departments: list[Department] = field(default_factory=list)

    def load_from_yaml(self, yaml_file):
        with open(yaml_file, 'r') as file:
            yaml_config = yaml.load(file, Loader=yaml.FullLoader)
        for key, value in yaml_config.items():
            if key == 'departments':
                for department in value:
                    self.departments.append(Department(**department))
            elif key == 'config':
                self.config = Config(**value)
            elif key == 'default':
                self.default = Default(**value)
            else:
                setattr(self, key, value)

    def get_groups(self, department_name: str) -> GroupsInfo:
        output = self.default.check_default(department_name)
        if department_name is None or department_name.strip() == '':
            return output
        for department in self.departments:
            if department.name == department_name:
                output.ldap_groups.extend(department.ldap_groups)
                output.posixGroups.extend(department.posixGroups)
                break
        return output.deduplicate()
