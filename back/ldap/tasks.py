from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import translation
from django.utils.formats import localize
from django.utils.translation import gettext as _

from admin.integrations.models import Integration
from organization.models import Organization, WelcomeMessage
from users.models import ResourceUser, ToDoUser
from .ldap import LdapConfig, inetOrgPerson, posixAccount, LDAP_OP
import re
from os import path

__all__=['LdapSync','ldap_add_user','ldap_delete_user','ldap_sync_role','ldap_set_pw','LdapConfig', 'inetOrgPerson', 'posixAccount']

class LdapSync:
    def __init__(self):
        self.__ldap: LDAP_OP = None
        self.init()

    def init(self):
        ldap_config = self.get_ldap_config()
        ldap = LDAP_OP(ldap_config)
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
        groups = self.get_default_groups()
        if user.department is not None:
            groups.append(user.department.name)
        groups=list(set(groups))
        i = 1
        uid = ldap_user.uid
        while True:
            if self.ldap.add_user(ldap_user,groups=groups,need_hash_pw=False):
                user.set_password(password)
                return user
            elif self.ldap.last_error == 'entryAlreadyExists':
                ldap_user.uid = '{uid}{i}'.format(uid=uid, i=i)
                user.username = ldap_user.uid
                i += 1
            else:
                return user

    def del_user(self, user):
        uid = user.username
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
        password = user.password
        self.ldap.modify_passwd(uid, password)
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
        if password is not None:
            if need_hash_pw:
                ps=LDAP_OP.hash(password,algorithm=algorithm)
            else:
                ps=password
            ldap_user.userPassword = ps
        if settings.LDAP_ACCOUNT_TYPE == "inetOrgPerson":
            return ldap_user
        else:
            ldap_user2 = posixAccount(
                uid="", sn="", givenName="", mail="", telephoneNumber="")
            ldap_user2.copy_from(ldap_user)
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
    def get_default_groups(cls) -> list[str]:
        default=settings.LDAP_DEFAULT_GROUPS.strip()
        if default=='' or default is None:
            groups=[]
        else:
            groups=default.split(' ')
        groups_from_file=cls.get_default_groups_from_file()
        groups.extend(groups_from_file)
        return list(set(groups))

    @classmethod
    def get_default_groups_filename(cls) -> str:
        return settings.LDAP_DEFAULT_GROUPS_FILENAME.strip()
    
    @classmethod
    def get_default_groups_from_file(cls) -> list[str]:
        filename=cls.get_default_groups_filename()
        if filename is None or not path.exists(filename):
            return []
        groups=[]
        try:
            with open(filename,'r') as f:
                for line in f.readlines():
                    line=line.strip()
                    if line=='':
                        continue
                    groups.append(line)
        except:
            pass
        return groups


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

def ldap_set_pw(user,password:str):
    # Drop if LDAP is not enabled
    if (not settings.LDAP_SYNC):
        return
    ldap = LdapSync()
    ldap.set_password(user,password)
    ldap.close()
    return user