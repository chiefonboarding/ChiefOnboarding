
from .ldap import LdapConfig, inetOrgPerson, posixAccount, LDAP_OP
from .toLdapGroup import *
import re
from os import path

from django.conf import settings
# from django.utils.translation import gettext as _


__all__=['LdapSync','ldap_add_user','ldap_delete_user','ldap_sync_role','ldap_set_password','LdapConfig', 'inetOrgPerson', 'posixAccount']

class LdapSync:
    def __init__(self,ldap_config: LdapConfig = None):
        self.__ldap: LDAP_OP = None
        self.init(ldap_config=ldap_config)

    def init(self, ldap_config: LdapConfig = None):
        if ldap_config is None:
            ldap_config = self.get_ldap_config()
        is_log=settings.LDAP_LOG
        is_log=True
        ldap = LDAP_OP(ldap_config,is_log=is_log)
        self.ldap = ldap

    @property
    def ldap(self):
        return self.__ldap

    @ldap.setter
    def ldap(self, ldap: LDAP_OP):
        self.__ldap = ldap
        self.ldap.connect()

    def close(self):
        self.ldap.disconnect()

    def add_user(self, user, password:str=None,need_hash_pw:bool=True,algorithm:str='SSHA'):
        ldap_user = self.user_2_ldap(user, password=password,need_hash_pw=need_hash_pw,algorithm=algorithm)        
        i = 1
        uid = ldap_user.uid
        while True:
            if self.ldap.add_user(ldap_user,need_hash_pw=False):
                user.set_password(password)
                user.save()
                break
            elif self.ldap.last_error == 'entryAlreadyExists':
                ldap_user.uid = '{uid}{i}'.format(uid=uid, i=i)
                user.username = ldap_user.uid
                i += 1
            else:
                break
        department_name=None
        if user.department is not None:
            department_name = user.department.name
        groups_info=self.get_default_groups_from_file(department_name=department_name)
        self.create_group(groups_info=groups_info,member=user.username)
        self.add_user_to_group(uid=user.username,groups_info=groups_info)
        return user


    def add_user_to_group(self, uid:str, groups_info:GroupsInfo):
        for group in groups_info.ldap_groups:
            self.ldap.add_user_to_group(uid=uid,group_name=group.dn)
        for group in groups_info.posixGroups:
            self.ldap.add_user_to_group(uid=uid,group_name=group.dn,is_posix=True)

    def create_group(self, groups_info:GroupsInfo,member:str):
        for group in groups_info.ldap_groups:
            self.ldap.create_group(group.dn,objectClass=group.objectClass,members=[member])
        for group in groups_info.posixGroups:
            self.ldap.create_posix_group(group.dn,gidNumber=group.gidNumber,members=[member])

    def del_user(self, user):
        uid = user.username
        if uid is None or uid.strip() == '':
            return user
        user_tmp_ou=self.get_user_tmp_ou()
        self.ldap.del_uid_tmp(uid=uid,tmp_user_ou=user_tmp_ou)
        return user
        
    def sync_role_from_ldap(self, user):
        uid = user.username
        entry = self.ldap.search_user(uid)
        if 'memberOf' in entry:
            group = entry['memberOf']
            role_map, default_role = self.get_role_map()
            role = self.analyze_role(
                group_list=group, role_map=role_map, default_role=default_role)
            user.role = role
        return user

    def sync(self):
        self.sync_user()
        self.sync_group()
        self.sync_role()

    def set_password(self, user,new_password:str):
        uid = user.username
        self.ldap.modify_passwd(uid, new_password)
        user.set_password(new_password)
        return user
    
    @classmethod
    def analyze_role(cls, group_list: list[str], role_map: dict[int, str] = {1: r'^cn=Administrators.*', 2: r'^cn=Manage.*'}, default_role: int = 3) -> int:
        role_list: list[int] = []
        for role, pattern in role_map.items():
            for group in group_list:
                if re.search(pattern, group):
                    role_list.append(role)
                    break
        if len(role_list) == 0:
            return default_role
        else:
            return min(role_list)

    @classmethod
    def get_ldap_config(cls) -> LdapConfig:
        ldap_config = LdapConfig()
        ldap_config.HOST = settings.LDAP_HOST
        ldap_config.PORT = settings.LDAP_PORT
        ldap_config.TLS = settings.LDAP_TLS
        ldap_config.BASE_DN = settings.LDAP_BASE_DN
        ldap_config.BIND_DN = settings.LDAP_BIND_DN
        ldap_config.BIND_PW = settings.LDAP_BIND_PW
        ldap_config.USER_BASE_RDN = settings.LDAP_USER_BASE_RDN
        ldap_config.GROUP_BASE_RDN = settings.LDAP_GROUP_BASE_RDN
        ldap_config.USER_FILTER = settings.LDAP_USER_FILTER
        ldap_config.GROUP_FILTER = settings.LDAP_GROUP_FILTER
        ldap_config.POSIX_GROUP_RDN=settings.LDAP_POSIX_GROUP_RDN
        return ldap_config

    @classmethod
    def user_2_ldap(cls, user,password:str=None,need_hash_pw:bool=True,algorithm:str='SSHA'):
        ldap_user = inetOrgPerson(
            uid=user.username,
            sn=user.last_name,
            givenName=user.first_name,
            mail=user.email,
            telephoneNumber=user.phone,
        )
        if ldap_user.telephoneNumber is not None and ldap_user.telephoneNumber.strip() == '':
            ldap_user.telephoneNumber = None
        if user.department is not None:
            ldap_user.title = user.department.name
        if password is not None:
            if need_hash_pw:
                ps=LDAP_OP.hash(password,algorithm=algorithm)
            else:
                ps=password
            ldap_user.userPassword = ps
        try:
            if settings.LDAP_ACCOUNT_TYPE == "inetOrgPerson":
                return ldap_user
        except:
            pass
        ldap_user2 = posixAccount(
            uid="", sn="", givenName="", mail="", telephoneNumber=None)
        ldap_user2.copy_from(ldap_user)
        homeDirectory = settings.LDAP_USER_HOME_DIRECTORY+'/{uid}'.format(uid=ldap_user2.uid)
        ldap_user2.homeDirectory = homeDirectory
        return ldap_user2

    @classmethod
    def get_role_map(cls) -> tuple[dict[int, str], int]:
        admin_pattern = settings.LDAP_ROLE_ADMIN_PATTERN
        manage_pattern = settings.LDAP_ROLE_MANAGE_PATTERN
        role_map = {1: admin_pattern, 2: manage_pattern}
        default_role = settings.LDAP_ROLE_DEFAULT
        return role_map, default_role

    @classmethod
    def get_user_tmp_ou(cls) -> str:
        return settings.LDAP_USER_TMP_OU
    
    @classmethod
    def get_default_groups_from_env(cls) -> GroupsInfo:
        default=settings.LDAP_DEFAULT_GROUPS.strip()
        if default=='' or default is None:
            groups=[]
        else:
            groups=default.split(' ')
        output=GroupsInfo()
        for group in list(set(groups)):
            output.ldap_groups.append(Group(name=group))
        return output

    @classmethod
    def get_default_groups_filename(cls) -> str:
        # return 'department.yaml'
        return settings.LDAP_DEFAULT_GROUPS_FILENAME.strip()
    
    @classmethod
    def get_default_groups_from_file(cls,department_name:str) -> GroupsInfo:
        filename=cls.get_default_groups_filename()
        output=GroupsInfo()
        if filename is None or not path.exists(filename):
            return cls.get_default_groups_from_env()
        config=toLdapGroup()
        config.load_from_yaml(filename)
        output=config.get_groups(department_name)
        return output
    
def ldap_add_user(user,password:str=None,need_hash_pw:bool=True,algorithm:str='SSHA'):
    # Drop if LDAP is not enabled
    if (not settings.LDAP_SYNC):
        return
    ldap = LdapSync()
    user=ldap.add_user(user,password=password,need_hash_pw=need_hash_pw,algorithm=algorithm)
    user.ldap = True
    ldap.close()
    user.save()
    return user

def ldap_delete_user(user):
    # Drop if LDAP is not enabled
    if (not settings.LDAP_SYNC):
        return
    ldap = LdapSync()
    user=ldap.del_user(user)
    ldap.close()
    user.save()
    return user

def ldap_sync_role(users=[]):
    # Drop if LDAP is not enabled
    if (not settings.LDAP_SYNC):
        return
    ldap = LdapSync()
    for user in users:
        user=ldap.sync_role_from_ldap(user)
        user.save()
        ldap.close()
    return users

def ldap_set_password(user,password:str):
    # Drop if LDAP is not enabled
    if (not settings.LDAP_SYNC):
        return
    ldap = LdapSync()
    ldap.set_password(user,password)
    ldap.close()
    return user