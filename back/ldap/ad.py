from dataclasses import dataclass
from ms_active_directory import ADDomain,ADSession,ADGroup,ADUser
from .ldap import posixAccount,inetOrgPerson
@dataclass
class AdConfig:
    DOMAIN_DNS_NAME:str = None
    AD_HOST_NAME:str = None
    PRINCIPAL_SUFFIX:str = None
    CERT_FILE:str = None
    DOMAIN:str = None
    BIND_USER:str = None
    BIND_PASSWORD:str = None
    USER_BASE_RDN:str = None

    def ADDomain(self) -> ADDomain:
        return ADDomain(
            domain=self.DOMAIN_DNS_NAME,
            ldap_servers_or_uris=[self.AD_HOST_NAME],
            ca_certificates_file_path=self.CERT_FILE
        )
    
    def ADSession(self) -> ADSession:
        ad_domain = self.ADDomain()
        return ad_domain.create_session_as_user(
            user=self.BIND_USER,
            password=self.BIND_PASSWORD
        )


class AD_OP():
    def __init__(self, ldap_config: AdConfig = None, **kwarg) -> None:
        self.__server: ADDomain = None
        self.__conn: ADSession = None
        if ldap_config is not None and isinstance(ldap_config,AdConfig):
            self.ad_config = ldap_config
        else:
            self.__ad_config = AdConfig()


    @property
    def ldap_config(self) -> AdConfig:
        return self.__ad_config

    @property
    def ad_config(self) -> AdConfig:
        return self.__ad_config
    
    @ad_config.setter
    def ad_config(self, ad_config: AdConfig):
        if issubclass(type(ad_config), AdConfig):
            self.__ad_config = ad_config
            self.connect()
        else:
            raise ValueError("ad_config must be a AdConfig type")



    @property
    def conn(self) -> ADSession:
        return self.__conn

    @property
    def server(self) -> ADDomain:
        return self.__server

    @property
    def conn_status(self) -> bool:
        if self.conn is not None and isinstance(self.conn, ADSession):
            return self.conn.is_open()
        return False

    def connect(self) -> bool:
        try:
            self.__server = self.__ad_config.ADDomain()
            self.__conn = self.__ad_config.ADSession()
        except:
            pass
        return self.conn_status
    
    def disconnect(self):
        if self.conn_status:
            self.conn.get_ldap_connection().unbind()
            self.conn=None

    def add_user(self, user: posixAccount | inetOrgPerson, groups: list[str] = None) -> ADUser:
        username = user.uid
        first_name = user.givenName
        last_name = user.sn
        location=self.ad_config.USER_BASE_RDN
        mail=user.mail
        password=user.userPassword
        PRINCIPAL_SUFFIX=self.ad_config.PRINCIPAL_SUFFIX
        if PRINCIPAL_SUFFIX is not None and isinstance(PRINCIPAL_SUFFIX,str) and len(PRINCIPAL_SUFFIX) > 0 :
            suffix = self.ad_config.PRINCIPAL_SUFFIX.split('@')[-1]
        else:
            suffix=self.ad_config.DOMAIN_DNS_NAME
        userPrincipalName = f"{username}@{suffix}"
        user=self.conn.create_user(
            username=username,
            user_password=password,
            first_name=first_name,
            last_name=last_name,
            object_location=location,
            mail=mail,
            userPrincipalName=userPrincipalName
        )
        if groups is not None:
            self.add_user_to_groups(username, groups)
        return user

    def add_user_to_groups(self, username: str, groups: list[str]) -> list[str | ADGroup]:
        return self.conn.add_users_to_groups(
                users_to_add=[username],
                groups_to_add_them_to=groups
            )
    
    def add_user_to_group(self, username: str, group: str) -> str|ADGroup:
        groups= self.conn.add_users_to_groups(users_to_add=[username],groups_to_add_them_to=[group])
        return groups[0]
    
    def add_users_to_group(self, usernames: list[str], group: str) -> str|ADGroup:
        groups= self.conn.add_users_to_groups(users_to_add=usernames,groups_to_add_them_to=[group])
        return groups[0]
    
    def create_group_B(self, group_name: str, group_location: str = None,members:list[str]=None,ignore_errors:bool=False) -> ADGroup:
        if ignore_errors:
            try:
                return self.create_group(group_name,group_location,members)
            except:
                pass
        return self.create_group(group_name,group_location,members)
    
    def create_group(self, group_name: str, group_location: str = None,members:list[str]=None) -> ADGroup:
        group=self.conn.create_group(group_name=group_name,object_location=group_location)
        if members is not None:
            self.add_users_to_group(members,group_name)
        return group

    def find_user_groups(self, username: str) -> list[str]:
        ad_groups=self.conn.find_groups_for_user(username)
        return [group.name for group in ad_groups]

    def modify_passwd(self, username: str, password: str) -> bool:
        return self.conn.reset_password_for_account(
            username=username,
            new_password=password
        )