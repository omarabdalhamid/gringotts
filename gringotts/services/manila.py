import time
from oslo.config import cfg

from gringotts import utils
from gringotts import constants as const

from gringotts.services import wrap_exception
from gringotts.services import Resource
from manilaclient.v1 import client as manila_client
from cinderclient.exceptions import NotFound
from gringotts.services import keystone as ks_client
from gringotts.openstack.common import uuidutils
from gringotts.openstack.common import timeutils
from gringotts.openstack.common import log


LOG = log.getLogger(__name__)


class Share(Resource):
    def to_message(self):
        msg = {
            'event_type': 'share.create.end.again',
            'payload': {
                'share_id': self.id,
                'display_name': self.name,
                'size': self.size,
                'volume_type': self.volume_type,
                'user_id': self.user_id,
                'tenant_id': self.project_id,
                'created_at': self.created_at
            },
            'timestamp': utils.format_datetime(timeutils.strtime())
        }
        return msg


def get_manilaclient(region_name=None):
    os_cfg = cfg.CONF.service_credentials
    endpoint = ks_client.get_endpoint(region_name, 'share')
    auth_token = ks_client.get_token()
    c = manila_client.Client(os_cfg.os_username,
                             os_cfg.os_password,
                             None,
                             auth_url=os_cfg.os_auth_url)
    c.client.auth_token = auth_token
    c.client.management_url = endpoint
    return c


@wrap_exception(exc_type='get')
def share_get(share_id, region_name=None):
    m_client = get_manilaclient(region_name)
    try:
        share = m_client.shares.get(share_id)
    except NotFound:
        return None
    status = utils.transform_status(share.status)
    return Share(id=share.id,
                 name=share.name,
                 status=status,
                 original_status=share.status,
                 resource_type=const.RESOURCE_SHARE)


@wrap_exception(exc_type='list')
def share_list(project_id, region_name=None, detailed=True, project_name=None):
    """To see all shares in the cloud as admin.
    """
    m_client = get_manilaclient(region_name)
    search_opts = {'all_tenants': 1,
                   'project_id': project_id}
    if m_client is None:
        return []
    shares = m_client.shares.list(detailed, search_opts=search_opts)
    formatted_shares = []
    for share in shares:
        created_at = utils.format_datetime(share.created_at)
        status = utils.transform_status(share.status)
        formatted_shares.append(Share(id=share.id,
                                      name=share.name,
                                      size=share.size,
                                      volume_type=share.volume_type,
                                      status=status,
                                      original_status=share.status,
                                      resource_type=const.RESOURCE_SHARE,
                                      user_id = None,
                                      project_id = project_id,
                                      project_name=project_name,
                                      created_at=created_at))
    return formatted_shares


@wrap_exception(exc_type='bulk')
def delete_shares(project_id, region_name=None):
    """Delete all shares that belong to project_id
    """
    client = get_manilaclient(region_name)
    search_opts = {'all_tenants': 1,
                   'project_id': project_id}
    shares = client.shares.list(detailed=False, search_opts=search_opts)

    # Force delete or detach and then delete
    for share in shares:
        client.shares.delete(share)
        LOG.warn("Delete share: %s" % share.id)


@wrap_exception(exc_type='delete')
def delete_share(share_id, region_name=None):
    client = get_manilaclient(region_name)
    client.shares.delete(share_id)


@wrap_exception(exc_type='stop')
def stop_share(share_id, region_name=None):
    return True


@wrap_exception(exc_type='put')
def quota_update(project_id, user_id=None, region_name=None, **kwargs):
    """
    kwargs = {"share_networks": "10",
              'shares': 10}
    """
    client = get_manilaclient(region_name)
    client.quotas.update(project_id, **kwargs)